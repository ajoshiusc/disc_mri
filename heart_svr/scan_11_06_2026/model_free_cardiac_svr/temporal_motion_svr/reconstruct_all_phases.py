#!/usr/bin/env python3
"""Full-data temporal-motion cardiac SVR, staged for a 6 GB CUDA GPU.

Stage 1: independent first outer solve, one phase at a time, checkpointed on disk.
Stage 2: one joint temporal-motion objective over all selected phases. Its compact
         ROI operators use exactly the pilot's deterministic sample positions.
Stage 3: second outer solve, one phase at a time, using the jointly fitted poses.

No phase image averaging, SVoRT, brain model, timing rebinning, or cardiac-NCC
confidence experiment is used. All native pixels inside the support mask are fit.
"""
import os
os.environ.setdefault('OMP_NUM_THREADS','4');os.environ.setdefault('MKL_NUM_THREADS','4')
os.environ.setdefault('PYTORCH_CUDA_ALLOC_CONF','expandable_segments:True')
import argparse,gc,hashlib,json,logging,math,sys,time
from pathlib import Path
import numpy as np
import torch
import reconstruct_temporal as pilot

HERE=Path(__file__).resolve().parent
LOCAL=Path('/home/ajoshi/Documents/Codex/2026-11-08/i-w/outputs/heart_svr_cardiac')
ORIGINAL=Path('/home/ajoshi/project2_ajoshi_27/data/heart_svr/heart_svr_acquisition_11_06_2026/heart_svr_model_free_1p5mm_motion3mm3deg')

def dump(path,value):
    path=Path(path);tmp=path.with_name(path.name+'.tmp')
    tmp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');os.replace(tmp,path)

def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def release():gc.collect();torch.cuda.empty_cache()

def load_state(phase,args):
    data=dict(np.load(args.cache/f'phase_{phase:02d}'/'native_data.npz'))
    # All-pixel run: retain cached per-stack normalization, as in the original full run.
    mask=data['mask'];op=pilot.Acquisition(mask,data['poses'],data['spacing'],data['affine'],data['shape'],device='cuda',quadrature=(5,5,13),chunk_rows=512)
    y=torch.as_tensor(data['values'],device='cuda')[op.mask]
    h,w=mask.shape[-2:];gy,gx=np.mgrid[:h,:w];center=data['poses'][:,:,3].mean(0);heart=[]
    for T,sp in zip(data['poses'],data['spacing']):
        xyz=np.stack([(gx-(w-1)/2)*sp[0],(gy-(h-1)/2)*sp[1],np.zeros_like(gx)],-1)@T[:,:3].T+T[:,3]
        heart.append(np.linalg.norm(xyz-center,axis=-1)<=55.)
    return dict(phase=phase,data=data,op=op,y=y,heart=np.stack(heart),gains=torch.ones(len(mask),device='cuda'),weight=torch.ones_like(y),history=[])

def validate_inputs(args):
    states=[];fingerprints={};affine=None
    for ph in args.phases:
        folder=args.cache/f'phase_{ph:02d}';cache=folder/'native_data.npz';manifest=folder/'inputs.json'
        if not cache.is_file() or not manifest.is_file():raise FileNotFoundError(f'Missing native cache/manifest for phase {ph}: {folder}')
        with np.load(cache) as d:
            poses=d['poses'];a=d['affine'];shape=d['shape'];spacing=d['spacing']
            if affine is None:affine=a
            if not np.allclose(a,affine) or not np.allclose(np.linalg.norm(a[:3,:3],axis=0),1.5):raise ValueError('Expected matching 1.5 mm grids')
            if not np.allclose(spacing[:,2],6.):raise ValueError('Expected the original 6 mm slice profile')
            records=json.loads(manifest.read_text())['records']
            if len(records)!=len(poses):raise ValueError('Manifest and native-frame counts differ')
        fingerprints[str(ph)]=dict(cache_sha256=digest(cache),manifest_sha256=digest(manifest))
        states.append(dict(phase=ph,data={'poses':poses},records=records))
    index=json.loads(args.timing_index.read_text())
    # Fail if a DICOM would be needed: this runner intentionally works with the caches
    # and archived timing index even when the original data mount is unavailable.
    indexed={r['file'] for r in index}
    missing=[r['file'] for s in states for r in s['records'] if r['file'] not in indexed]
    if missing:raise ValueError(f'Timing index lacks {len(missing)} observations')
    links=pilot.graph(states,index,args.max_trigger_gap_ms)
    offsets={};start=0
    for s in states:
        count=len(s['data']['poses']);offsets[str(s['phase'])]=[start,start+count];start+=count
    return links,offsets,fingerprints

def checkpoint_first(s,path):
    arrays={k:s[k].detach().cpu().numpy() for k in ['x','prior','gains','weight']}
    tmp=path.with_suffix('.tmp')
    with tmp.open('wb') as f:np.savez_compressed(f,**arrays)
    os.replace(tmp,path)
    dump(path.with_suffix('.json'),dict(phase=s['phase'],history=s['history']))

def first_stages(args,conf):
    for i,ph in enumerate(args.phases,1):
        ck=args.output/'checkpoints'/f'phase_{ph:02d}.npz'
        if args.resume and ck.exists() and ck.with_suffix('.json').exists():
            logging.info('Stage 1: reuse phase %02d checkpoint (%d/%d)',ph,i,len(args.phases));continue
        logging.info('Stage 1: phase %02d (%d/%d)',ph,i,len(args.phases))
        s=load_state(ph,args);pilot.solve_outer(s,0,conf);checkpoint_first(s,ck)
        del s;release()


def motion_context(ph,start,args):
    with np.load(args.cache/f'phase_{ph:02d}'/'native_data.npz') as d:
        mask=d['mask'];poses=d['poses'];spacing=d['spacing'];affine=d['affine'];shape=d['shape'];values=d['values']
    with np.load(args.output/'checkpoints'/f'phase_{ph:02d}.npz') as ck:
        x=torch.as_tensor(ck['x'],device='cuda');gains=torch.as_tensor(ck['gains'],device='cuda')
    h,w=mask.shape[-2:];gy,gx=np.mgrid[:h,:w];center=poses[:,:,3].mean(0);heart=[]
    for T,sp in zip(poses,spacing):
        xyz=np.stack([(gx-(w-1)/2)*sp[0],(gy-(h-1)/2)*sp[1],np.zeros_like(gx)],-1)@T[:,:3].T+T[:,3]
        heart.append(np.linalg.norm(xyz-center,axis=-1)<=55.)
    roi=np.stack(heart)&mask
    coords=np.argwhere(roi);stride=max(4,math.ceil(len(coords)/65536));coords=coords[::stride]
    compact=np.zeros_like(roi);compact[tuple(coords.T)]=True
    # Selecting before operator construction preserves sample order, native slice IDs,
    # quadrature and values; it only removes unsampled ROI pixels from GPU storage.
    op=pilot.Acquisition(compact,poses,spacing,affine,shape,device='cuda',quadrature=(5,5,13),chunk_rows=512)
    sid=op.sid;target=torch.as_tensor(values[tuple(coords.T)],device='cuda');g=gains[sid];m=len(poses)
    base=op.transforms.detach().clone()
    with torch.no_grad():
        pred=op.sample(x,base)
        robust=(1+((g*pred-target)/.15).square()).reciprocal().clamp_min(.05)
        mass=pilot.solver.slice_sum(robust,sid,m).clamp_min(1e-5)
        sy=pilot.solver.slice_sum(robust*target,sid,m)
        yy=pilot.solver.slice_sum(robust*target.square(),sid,m)-sy.square()/mass
        counts=pilot.solver.slice_sum(torch.ones_like(target),sid,m).clamp_min(1)
    return dict(op=op,x=x,sid=sid,target=target,g=g,robust=robust,mass=mass,sy=sy,yy=yy,counts=counts,base=base,start=start,n=m)


def joint_motion(args,conf,links,offsets):
    targetfile=args.output/'joint_motion.npz';reportfile=args.output/'joint_motion.json'
    if args.resume and targetfile.exists() and reportfile.exists():
        logging.info('Stage 2: reuse completed joint motion');return
    n=max(b for a,b in offsets.values());contexts=[]
    for ph in args.phases:
        contexts.append(motion_context(ph,offsets[str(ph)][0],args))
        logging.info('Stage 2: loaded compact motion context for phase %02d',ph)
    param=torch.zeros((n,6),device='cuda',requires_grad=True)
    optim=torch.optim.Adam([param],lr=conf.motion_lr)
    edges=torch.tensor([[a,b] for a,b,*_ in links],device='cuda')
    ew=torch.tensor([1/max(dt,1) for _,_,dt,*_ in links],device='cuda');ew/=ew.mean()
    scale=torch.tensor([conf.max_motion_deg]*3+[conf.max_motion_mm]*3,device='cuda')
    def transform(base,p):
        return torch.cat((pilot.rotation_matrix(p[:,:3]*torch.pi/180)@base[:,:,:3],base[:,:,3:]+p[:,3:,None]),-1)
    def error(c):
        p=param[c['start']:c['start']+c['n']]
        pred=c['op'].sample(c['x'],transform(c['base'],p))
        sm=lambda v:pilot.solver.slice_sum(v,c['sid'],c['n'])
        sx=sm(c['robust']*pred);xx=sm(c['robust']*pred.square())-sx.square()/c['mass']
        xy=sm(c['robust']*pred*c['target'])-sx*c['sy']/c['mass']
        ncc=xy/(xx.clamp_min(1e-5)*c['yy'].clamp_min(1e-5)).sqrt()
        huber=sm(2*(torch.sqrt(1+((c['g']*pred-c['target'])/.15).square())-1))/c['counts']
        return (1-ncc.clamp(-1,1)+.02*huber).sum()/n
    best=float('inf');bestp=param.detach().clone();trace=[]
    for step in range(conf.motion_steps+1):
        optim.zero_grad();objective=0.
        for c in contexts:
            loss=error(c);objective+=float(loss.detach())
            if step<conf.motion_steps:loss.backward()
        smooth=((param[edges[:,0]]-param[edges[:,1]])/scale).square().mean(1)
        penalty=args.temporal_weight*(ew*smooth).mean()+.002*param.square().mean()
        objective+=float(penalty.detach());trace.append(objective)
        if objective<best:best=objective;bestp=param.detach().clone()
        if step<conf.motion_steps:
            penalty.backward();optim.step()
            with torch.no_grad():param[:,:3].clamp_(-conf.max_motion_deg,conf.max_motion_deg);param[:,3:].clamp_(-conf.max_motion_mm,conf.max_motion_mm)
        logging.info('Stage 2: joint motion step %d/%d objective %.7f',step,conf.motion_steps,objective)
    poses=[]
    with torch.no_grad():
        for c in contexts:poses.append(transform(c['base'],bestp[c['start']:c['start']+c['n']]).cpu().numpy())
    tmp=targetfile.with_suffix('.tmp')
    with tmp.open('wb') as f:np.savez_compressed(f,poses=np.concatenate(poses),corrections=bestp.cpu().numpy())
    os.replace(tmp,targetfile)
    dump(reportfile,dict(objective_trace=trace,best_objective=best,edge_count=len(links),temporal_weight=args.temporal_weight,peak_gpu_mb=torch.cuda.max_memory_allocated()/1024**2))
    del contexts,param,optim,poses;release()


def finish_phases(args,conf,offsets):
    allposes=np.load(args.output/'joint_motion.npz')['poses'];results=[]
    for i,ph in enumerate(args.phases,1):
        folder=args.output/f'phase_{ph:02d}'/'final';folder.mkdir(parents=True,exist_ok=True)
        resultfile=folder/'result.json'
        if args.resume and resultfile.exists() and (folder/'reconstruction.nii.gz').exists():
            results.append(json.loads(resultfile.read_text()));logging.info('Stage 3: reuse phase %02d final output',ph);continue
        logging.info('Stage 3: phase %02d (%d/%d)',ph,i,len(args.phases))
        started=time.monotonic();s=load_state(ph,args)
        ckpath=args.output/'checkpoints'/f'phase_{ph:02d}.npz'
        with np.load(ckpath) as ck:
            for k in ['x','prior','gains','weight']:s[k]=torch.as_tensor(ck[k],device='cuda')
        s['history']=json.loads(ckpath.with_suffix('.json').read_text())['history']
        a,b=offsets[str(ph)];s['op'].transforms=torch.as_tensor(allposes[a:b],device='cuda')
        pilot.solve_outer(s,1,conf)
        arr=s['x'].cpu().numpy().transpose(2,1,0)
        if not np.isfinite(arr).all() or not np.any(arr>0):raise ValueError(f'Invalid final reconstruction for phase {ph}')
        pilot.save(folder/'reconstruction.nii.gz',arr,s['data']['affine'])
        pilot.save(folder/'coverage.nii.gz',s['coverage'].cpu().numpy().transpose(2,1,0),s['data']['affine'])
        np.save(folder/'poses.npy',allposes[a:b])
        row=dict(phase=ph,method='temporal_motion_full_data',validation=False,input_frames=len(s['data']['poses']),orientation_groups=len(np.unique(s['data']['groups'])),resolution_mm=1.5,slice_thickness_mm=6,config=vars(conf),temporal_weight=args.temporal_weight,history=s['history'],gains=s['gains'].cpu().tolist(),final_solve_seconds=time.monotonic()-started,output=str(folder/'reconstruction.nii.gz'))
        dump(resultfile,row);results.append(row);del s;release()
    return results


def main():
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--cache',type=Path,default=ORIGINAL if ORIGINAL.exists() else LOCAL/'results_all_phases')
    p.add_argument('--repo',type=Path,default=Path('/home/ajoshi/Projects/svr_gpu'))
    p.add_argument('--timing-index',type=Path,default=HERE/'dicom_timing_index.json')
    p.add_argument('--output',type=Path,default=LOCAL/'temporal_motion_all_phases')
    p.add_argument('--phases',type=int,nargs='+',default=list(range(1,27)))
    p.add_argument('--temporal-weight',type=float,default=.05)
    p.add_argument('--max-trigger-gap-ms',type=float,default=100.)
    p.add_argument('--resume',action='store_true',help='Resume only when cached inputs, settings and source hashes match')
    p.add_argument('--check-only',action='store_true',help='Validate all caches and graph without CUDA or reconstruction')
    args=p.parse_args()
    if len(set(args.phases))!=len(args.phases) or any(ph<1 or ph>26 for ph in args.phases):raise ValueError('Phases must be distinct integers from 1 to 26')
    if args.temporal_weight<=0 or args.max_trigger_gap_ms<=0:raise ValueError('Temporal settings must be positive')
    args.phases=sorted(args.phases)
    links,offsets,fingerprints=validate_inputs(args)
    logging.info('Preflight: %d phases, %d native frames, %d edges (%d across phases)',len(args.phases),max(b for a,b in offsets.values()),len(links),sum(a!=b for _,_,_,a,b in links))
    if args.check_only:return
    sys.path.insert(0,str(args.repo))
    from standalone_inlined.svr.operators import Acquisition,rotation_matrix
    from standalone_inlined.svr import solver
    pilot.Acquisition=Acquisition;pilot.rotation_matrix=rotation_matrix;pilot.solver=solver
    torch.set_num_threads(4);torch.manual_seed(0)
    if not torch.cuda.is_available():raise RuntimeError('CUDA is required for reconstruction')
    torch.cuda.set_device(0)
    conf=solver.Config(outer_iterations=2,irls_iterations=3,cg_iterations=25,regularization=.08,motion_steps=35,motion_lr=.08,max_motion_mm=3,max_motion_deg=3)
    sourcefiles=[Path(__file__).resolve(),HERE/'reconstruct_temporal.py',args.repo/'standalone_inlined/svr/operators.py',args.repo/'standalone_inlined/svr/solver.py']
    config=dict(phases=args.phases,cache=str(args.cache.resolve()),timing_index_sha256=digest(args.timing_index),cache_fingerprints=fingerprints,solver_config=vars(conf),temporal_weight=args.temporal_weight,max_trigger_gap_ms=args.max_trigger_gap_ms,all_pixels=True,source_hashes={str(f):digest(f) for f in sourcefiles})
    # JSON canonicalization accounts for dataclass tuples serialized as lists.
    config=json.loads(json.dumps(config))
    args.output.mkdir(parents=True,exist_ok=True);configfile=args.output/'run_config.json'
    if configfile.exists():
        if not args.resume:raise ValueError('Output already contains a run; use --resume or a new --output')
        if json.loads(configfile.read_text())!=config:raise ValueError('Resume settings, sources or inputs changed; use a new output directory')
    else:
        if args.resume and any(args.output.iterdir()):raise ValueError('Cannot resume an unrecognized output directory')
        dump(configfile,config)
    loghandler=logging.FileHandler(args.output/'run.log');loghandler.setFormatter(logging.Formatter('%(asctime)s %(message)s'));logging.getLogger().addHandler(loghandler)
    (args.output/'checkpoints').mkdir(exist_ok=True)
    dump(args.output/'motion_edges.json',links);dump(args.output/'phase_offsets.json',offsets)
    started=time.monotonic();first_stages(args,conf);joint_motion(args,conf,links,offsets)
    results=finish_phases(args,conf,offsets)
    dump(args.output/'COMPLETED.json',dict(status='complete',phases=args.phases,finished_phase_count=len(results),this_invocation_seconds=time.monotonic()-started,results=results,gpu=torch.cuda.get_device_name(0),all_pixels=True))
    logging.info('COMPLETE: %d final phase reconstructions saved to %s',len(results),args.output)

if __name__=='__main__':
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s');main()
