#!/usr/bin/env python3
"""Compare independent cardiac SVR with acquisition-neighbor motion regularization.

A graph connects frames at the SAME scanner plane in the SAME stack when
AcquisitionNumber increases by one and TriggerTime increases by <=100 ms.
Neither volume intensities nor anatomical deformation are temporally averaged.
No wall-clock acquisition order is inferred from file/instance/phase numbers.
"""
import os
os.environ.setdefault('OMP_NUM_THREADS','4')
os.environ.setdefault('MKL_NUM_THREADS','4')
os.environ.setdefault('PYTORCH_CUDA_ALLOC_CONF','expandable_segments:True')
import argparse, json, sys, time, logging, csv
from pathlib import Path
import numpy as np
import nibabel as nib
import torch
import pydicom

ROOT=Path('/home/ajoshi/project2_ajoshi_27/data/heart_svr/heart_svr_acquisition_11_06_2026')

def save(path,x,affine):
    image=nib.Nifti1Image(np.asarray(x,dtype=np.float32),affine)
    image.header.set_xyzt_units('mm');image.set_sform(affine,1);image.set_qform(affine,1)
    nib.save(image,path)

def graph(states,index,max_gap):
    lookup={r['file']:r for r in index}
    groups={}; offset=0; links=[]
    for state in states:
        for i,record in enumerate(state['records']):
            r=lookup.get(record['file'])
            if r is None:
                d=pydicom.dcmread(record['file'],stop_before_pixels=True)
                r=dict(stack=Path(record['file']).parent.name,position=[round(float(x),3) for x in d.ImagePositionPatient],acq=int(d.AcquisitionNumber),trigger=float(d.TriggerTime))
            # Stack identity prevents connecting differently oriented planes.
            key=(r['stack'],tuple(r['position']))
            groups.setdefault(key,[]).append((r['acq'],r['trigger'],offset+i,state['phase']))
        offset+=len(state['data']['poses'])
    for rows in groups.values():
        rows=sorted(rows)
        for a,b in zip(rows,rows[1:]):
            dt=b[1]-a[1]
            if b[0]==a[0]+1 and 0<dt<=max_gap:
                links.append((a[2],b[2],dt,a[3],b[3]))
    if not links: raise ValueError('No reliable acquisition-neighbor edges; cannot apply temporal regularization')
    return links

def make_state(phase,args):
    folder=args.cache/f'phase_{phase:02d}'
    data=dict(np.load(folder/'native_data.npz'))
    records=json.loads((folder/'inputs.json').read_text())['records']
    # Cached per-stack all-pixel normalization is canceled by this train-only normalization.
    data['values']=data['values'].copy()
    for group in np.unique(data['groups']):
        ids=data['groups']==group
        scale=np.percentile(data['values'][ids][data['train'][ids]],99)
        data['values'][ids]/=scale
    mask=data['train']
    op=Acquisition(mask,data['poses'],data['spacing'],data['affine'],data['shape'],device='cuda',quadrature=(5,5,13),chunk_rows=512)
    y=torch.as_tensor(data['values'],device='cuda')[op.mask]
    h,w=mask.shape[-2:];gy,gx=np.mgrid[:h,:w];center=data['poses'][:,:,3].mean(0);heart=[]
    for T,sp in zip(data['poses'],data['spacing']):
        xyz=np.stack([(gx-(w-1)/2)*sp[0],(gy-(h-1)/2)*sp[1],np.zeros_like(gx)],-1)@T[:,:3].T+T[:,3]
        heart.append(np.linalg.norm(xyz-center,axis=-1)<=55.)
    return dict(phase=phase,data=data,records=records,op=op,y=y,heart=np.stack(heart),gains=torch.ones(len(mask),device='cuda'),weight=torch.ones_like(y),history=[])

def rebuild(s):
    op=s['op'];op.build();s['coverage']=op.adjoint(torch.ones_like(s['y']))
    s['support']=solver.reconstruction_support(s['coverage']) & torch.as_tensor(s['data']['support'],device='cuda')
    if not bool(s['support'].any()):raise ValueError('Empty reconstruction support')

def solve_outer(s,outer,conf):
    op=s['op'];y=s['y'];sid=op.sid;n=len(op.transforms)
    rebuild(s)
    if 'x' not in s:
        s['x']=(op.adjoint(y)/s['coverage'].clamp_min(.05)).clamp_min(0)
        s['prior']=s['x'].clone()
    x=s['x'];weight=s['weight'];gains=s['gains'];support=s['support']
    for inner in range(conf.irls_iterations):
        pred=op.forward(x);gains=solver.fit_gains(pred,y,weight,sid,n)
        residual=gains[sid]*pred-y
        sigma=(residual.abs().median()*1.4826).clamp_min(conf.robust_floor)
        weight=(1+(residual/(2.5*sigma)).square()).reciprocal().clamp_min(.02)
        rmse=(solver.slice_sum(weight*residual.square(),sid,n)/solver.slice_sum(weight,sid,n).clamp_min(1)).sqrt()
        weight*=(1+(rmse/(3*sigma)).square()).reciprocal().clamp_min(.1)[sid]
        effective=weight*gains[sid].square();ew=solver.edge_weights(x,conf.edge_scale)
        mc=s['coverage'][support].median().clamp_min(.1);lam=conf.regularization*mc;ridge=conf.ridge*mc
        rhs=op.adjoint(weight*gains[sid]*y)+ridge*s['prior']
        diag=op.diagonal(effective)+lam*solver.laplacian_diagonal(ew,x.shape)+ridge
        def mv(v):return op.adjoint(effective*op.forward(v))+lam*solver.laplacian(v,ew)+ridge*v
        x,ch=solver.pcg(mv,rhs,x,diag,conf.cg_iterations);x=x.clamp_min(0)*support
        fit=gains[sid]*op.forward(x)-y
        row=dict(outer=outer,inner=inner,robust_rmse=float((weight*fit.square()).sum().div(weight.sum()).sqrt()))
        s['history'].append(row);logging.info('phase %02d outer %d inner %d RMSE %.5f',s['phase'],outer+1,inner+1,row['robust_rmse'])
    s.update(x=x,weight=weight,gains=gains)
    op.blocks=[];torch.cuda.empty_cache()

def motion_roi(s):
    full=s['op'];mask=s['heart']&full.mask.cpu().numpy()
    op=Acquisition(mask,full.transforms,full.spacing_tensor.cpu().numpy(),full.affine.cpu().numpy(),full.shape,device='cuda',quadrature=(5,5,13),chunk_rows=512)
    return op,s['y'][torch.as_tensor(s['heart'],device='cuda')[full.mask]]

def temporal_motion(states,links,args,conf):
    n=sum(len(s['op'].transforms) for s in states)
    param=torch.zeros((n,6),device='cuda',requires_grad=True)
    opt=torch.optim.Adam([param],lr=conf.motion_lr)
    edges=torch.tensor([[a,b] for a,b,*_ in links],device='cuda')
    # Faster pairs receive more weight; mean weight is one.
    ew=torch.tensor([1/max(dt,1) for _,_,dt,*_ in links],device='cuda');ew/=ew.mean()
    scale=torch.tensor([conf.max_motion_deg]*3+[conf.max_motion_mm]*3,device='cuda')
    context=[];offset=0
    for s in states:
        op,y=motion_roi(s);base=op.transforms.clone();m=len(base)
        selected=torch.arange(0,op.nrows,max(4,int(np.ceil(op.nrows/65536))),device='cuda')
        sid=op.sid[selected];target=y[selected];g=s['gains'][sid]
        with torch.no_grad():
            pred=op.sample(s['x'],base,selected)
            robust=(1+((g*pred-target)/.15).square()).reciprocal().clamp_min(.05)
            mass=solver.slice_sum(robust,sid,m).clamp_min(1e-5)
            sy=solver.slice_sum(robust*target,sid,m)
            yy=solver.slice_sum(robust*target.square(),sid,m)-sy.square()/mass
            counts=solver.slice_sum(torch.ones_like(target),sid,m).clamp_min(1)
        context.append((s,op,base,selected,sid,target,g,robust,mass,sy,yy,counts,offset,m))
        offset+=m
    def transform(base,p):
        return torch.cat((rotation_matrix(p[:,:3]*torch.pi/180)@base[:,:,:3],base[:,:,3:]+p[:,3:,None]),-1)
    def error(c):
        s,op,base,sel,sid,target,g,robust,mass,sy,yy,counts,start,m=c
        pred=op.sample(s['x'],transform(base,param[start:start+m]),sel)
        sx=solver.slice_sum(robust*pred,sid,m)
        xx=solver.slice_sum(robust*pred.square(),sid,m)-sx.square()/mass
        xy=solver.slice_sum(robust*pred*target,sid,m)-sx*sy/mass
        ncc=xy/(xx.clamp_min(1e-5)*yy.clamp_min(1e-5)).sqrt()
        huber=solver.slice_sum(2*(torch.sqrt(1+((g*pred-target)/.15).square())-1),sid,m)/counts
        return (1-ncc.clamp(-1,1)+.02*huber).sum()/n
    best=float('inf');bestp=param.detach().clone();trace=[]
    for step in range(conf.motion_steps+1):
        opt.zero_grad();objective=0.
        for c in context:
            err=error(c);objective+=float(err.detach())
            if step<conf.motion_steps:err.backward()
        smooth=((param[edges[:,0]]-param[edges[:,1]])/scale).square().mean(1)
        penalty=args.temporal_weight*(ew*smooth).mean()+.002*param.square().mean()
        objective+=float(penalty.detach())
        trace.append(objective)
        if objective<best:best=objective;bestp=param.detach().clone()
        if step<conf.motion_steps:
            penalty.backward();opt.step()
            with torch.no_grad():param[:,:3].clamp_(-conf.max_motion_deg,conf.max_motion_deg);param[:,3:].clamp_(-conf.max_motion_mm,conf.max_motion_mm)
        if step%10==0:logging.info('joint motion step %d objective %.6f',step,objective)
    with torch.no_grad():
        for c in context:
            s,op,base,*_=c;start,m=c[-2:];s['op'].transforms=transform(base,bestp[start:start+m]).detach()
    return dict(objective_trace=trace,best_objective=best,edges=len(links),temporal_weight=args.temporal_weight)

def evaluate_save(s,out,method,conf):
    out=out/method/f'phase_{s["phase"]:02d}';out.mkdir(parents=True,exist_ok=True)
    d=s['data'];x=s['x'];op=s['op']
    save(out/'reconstruction.nii.gz',x.cpu().numpy().transpose(2,1,0),d['affine'])
    np.save(out/'poses.npy',op.transforms.cpu().numpy())
    test=Acquisition(d['test'],op.transforms,d['spacing'],d['affine'],d['shape'],device='cuda',quadrature=(5,5,13),chunk_rows=512)
    with torch.no_grad():
        pred=(test.sample(x)*s['gains'][test.sid]).cpu().numpy()
    y=d['values'][d['test']];heart=s['heart'][d['test']]
    result=dict(phase=s['phase'],method=method,heldout_rmse=float(np.sqrt(np.mean((pred-y)**2))),heldout_ncc=float(np.corrcoef(pred,y)[0,1]),heldout_cardiac_rmse=float(np.sqrt(np.mean((pred[heart]-y[heart])**2))),heldout_cardiac_ncc=float(np.corrcoef(pred[heart],y[heart])[0,1]),train_pixels=int(d['train'].sum()),test_pixels=int(d['test'].sum()),history=s['history'])
    (out/'metrics.json').write_text(json.dumps(result,indent=2))
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,default=Path('/home/ajoshi/Projects/svr_gpu'))
    p.add_argument('--cache',type=Path,default=ROOT/'heart_svr_model_free_1p5mm_motion3mm3deg')
    p.add_argument('--timing-index',type=Path,default=Path(__file__).with_name('dicom_timing_index.json'))
    p.add_argument('--output',type=Path,default=Path(__file__).with_name('results'))
    p.add_argument('--phases',type=int,nargs='+',default=[1,2,3])
    p.add_argument('--temporal-weight',type=float,default=.05)
    p.add_argument('--max-trigger-gap-ms',type=float,default=100.)
    args=p.parse_args()
    if args.temporal_weight<=0:raise ValueError('temporal-weight must be positive')
    if len(set(args.phases))!=len(args.phases):raise ValueError('Duplicate phase numbers')
    global Acquisition,solver,rotation_matrix
    sys.path.insert(0,str(args.repo))
    from standalone_inlined.svr.operators import Acquisition,rotation_matrix
    from standalone_inlined.svr import solver
    torch.set_num_threads(4);torch.manual_seed(0)
    if not torch.cuda.is_available():raise RuntimeError('CUDA required')
    args.output.mkdir(parents=True,exist_ok=True)
    conf=solver.Config(outer_iterations=2,irls_iterations=3,cg_iterations=25,regularization=.08,motion_steps=35,motion_lr=.08,max_motion_mm=3,max_motion_deg=3)
    started=time.monotonic();states=[make_state(ph,args) for ph in args.phases]
    index=json.loads(args.timing_index.read_text()) if args.timing_index.exists() else []
    links=graph(states,index,args.max_trigger_gap_ms)
    (args.output/'motion_edges.json').write_text(json.dumps(links))
    logging.info('%d frames, %d temporal edges (%d across phases)',sum(len(s['data']['poses']) for s in states),len(links),sum(a!=b for _,_,_,a,b in links))
    # The first outer solve is identical in both arms and is computed once.
    for s in states:
        solve_outer(s,0,conf)
        s['checkpoint']={k:s[k].clone() for k in ['x','prior','gains','weight']}
        s['checkpoint_history']=s['history'].copy()
    results=[]
    for s in states:
        sub,y=motion_roi(s);solver.fit_motion(sub,s['x'],y,s['gains'],conf);s['op'].transforms=sub.transforms
        solve_outer(s,1,conf)
        results.append(evaluate_save(s,args.output,'independent',conf))
        s.update({k:v.clone() for k,v in s['checkpoint'].items()});s['history']=s['checkpoint_history'].copy()
        s['op'].transforms=torch.as_tensor(s['data']['poses'],device='cuda').clone()
    motion=temporal_motion(states,links,args,conf)
    for s in states:
        solve_outer(s,1,conf)
        results.append(evaluate_save(s,args.output,'temporal_motion',conf))
    report=dict(parameters=vars(args),solver_config=vars(conf),motion=motion,results=results,seconds=time.monotonic()-started,validation='10% native-pixel holdout; all normalization, initialization, motion and fitting use training pixels only. This is not independent-scan validation.')
    report['parameters']={k:str(v) if isinstance(v,Path) else v for k,v in report['parameters'].items()}
    (args.output/'comparison.json').write_text(json.dumps(report,indent=2))
    for r in results:logging.info('%s phase %02d heldout cardiac RMSE %.6f NCC %.6f',r['method'],r['phase'],r['heldout_cardiac_rmse'],r['heldout_cardiac_ncc'])

if __name__=='__main__':
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s');main()
