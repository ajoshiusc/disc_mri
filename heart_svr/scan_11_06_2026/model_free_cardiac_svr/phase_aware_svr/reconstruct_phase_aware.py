#!/usr/bin/env python3
"""Pilot of beat-normalized, temporally weighted native-slice cardiac SVR.
Uses approximate RR inferred from trigger resets and original slice/frame order.
Validates against whole held-out six-frame slice groups. No learned anatomy.
"""
import os
os.environ.setdefault('OMP_NUM_THREADS','4');os.environ.setdefault('MKL_NUM_THREADS','4')
os.environ.setdefault('PYTORCH_CUDA_ALLOC_CONF','expandable_segments:True')
import argparse,json,re,sys,time,logging
from pathlib import Path
import numpy as np,nibabel as nib,torch
ROOT=Path('/home/ajoshi/project2_ajoshi_27/data/heart_svr/heart_svr_acquisition_11_06_2026')

def timing_map(path):
 rows=json.loads(path.read_text());summary={}
 for r in rows:r['slice'],r['frame']=map(int,re.search(r'slice_(\d+)_frame_(\d+)',r['file']).groups())
 for st in sorted(set(r['stack'] for r in rows)):
  ordered=sorted([r for r in rows if r['stack']==st],key=lambda r:(r['slice'],r['frame']))
  t=np.array([r['trigger'] for r in ordered]);dt=np.diff(t);cadence=float(np.median(dt[(dt>20)&(dt<50)]))
  cuts=np.r_[0,np.where(dt < -100)[0]+1,len(t)];periods=[];disagreement=[]
  for ci,(a,b) in enumerate(zip(cuts,cuts[1:])):
   period=float(t[b-1]+cadence-t[b]) if b<len(t) else None
   usable=bool(ci>0 and b<len(t) and 450<period<1400)
   # Reject unexplained within-cycle backwards jumps or long gaps.
   if usable:usable=bool(np.all(np.diff(t[a:b])>=0) and np.all(np.diff(t[a:b])<=60))
   for j in range(a,b):
    r=ordered[j];r.update(cycle=ci,rr_ms=period,timing_usable=usable,estimated_phase=float(t[j]/period) if usable else None)
    if usable:disagreement.append(abs(r['estimated_phase']-(r['phase']-1)/r['n']))
   if usable:periods.append(period)
  summary[st]=dict(cadence_ms=cadence,complete_cycles=len(periods),median_rr_ms=float(np.median(periods)),median_fraction_disagreement=float(np.median(disagreement)))
 return rows,summary

def delta(q,target):return abs((q-target+.5)%1-.5)

def prepare(args,rows):
 lookup={r['file']:r for r in rows};chosen={};tests={}
 for ph in args.phases:
  target=(ph-1)/args.bins
  tests[ph]=set() if args.fit_all else {r['file'] for r in rows if r['timing_usable'] and r['slice']%7==0 and delta(r['estimated_phase'],target)*args.bins<=.5}
  for method in args.methods:
   chosen[ph,method]={r['file'] for r in rows if (args.fit_all or r['slice']%7!=0) and (r['phase']==ph if method=='original_bins' else r['timing_usable'] and delta(r['estimated_phase'],target)*args.bins<=args.radius_bins)}
 required=set().union(*chosen.values(),*tests.values());loaded={};geometry=None
 for folder in sorted(args.cache.glob('phase_*')):
  record=json.loads((folder/'inputs.json').read_text())['records']
  ids=[i for i,r in enumerate(record) if r['file'] in required]
  if not ids:continue
  d=dict(np.load(folder/'native_data.npz'))
  if geometry is None:geometry={k:d[k] for k in ['affine','shape','support']}
  elif not np.allclose(geometry['affine'],d['affine']):raise ValueError('Cached grids differ')
  for i in ids:
   r=record[i];loaded[r['file']]=dict(values=d['values'][i]*r['normalization_p99'],mask=d['mask'][i],poses=d['poses'][i],spacing=d['spacing'][i],group=int(d['groups'][i]))
  logging.info('loaded source %s, %d selected frames',folder.name,len(ids))
 missing=required-set(loaded)
 if missing:raise ValueError(f'{len(missing)} required observations missing from cache')
 # A common intensity scale for both methods, estimated from training frames only.
 scales={}
 train=set().union(*chosen.values())
 for group in [0,1,2]:
  samples=[d['values'][d['mask']][::8] for f,d in loaded.items() if f in train and d['group']==group]
  scales[group]=float(np.percentile(np.concatenate(samples),99))
 for d in loaded.values():d['values']/=scales[d['group']]
 return lookup,chosen,tests,loaded,geometry,scales

def state(files,loaded,geometry,target,args,weighted):
 files=sorted(files);ds=[loaded[f] for f in files]
 data={k:np.stack([d[k] for d in ds]) for k in ['values','mask','poses','spacing']}
 data['groups']=np.array([d['group'] for d in ds]);data.update(geometry)
 op=Acquisition(data['mask'],data['poses'],data['spacing'],data['affine'],data['shape'],device='cuda',quadrature=(5,5,13),chunk_rows=512)
 if weighted:tw=np.array([np.exp(-.5*(delta(LOOKUP[f]['estimated_phase'],target)*args.bins/args.sigma_bins)**2) for f in files],np.float32)
 else:tw=np.ones(len(ds),np.float32)
 # A common ROI center across methods and holdout frames.
 h,w=data['mask'].shape[-2:];gy,gx=np.mgrid[:h,:w];heart=[]
 for T,sp in zip(data['poses'],data['spacing']):
  xyz=np.stack([(gx-(w-1)/2)*sp[0],(gy-(h-1)/2)*sp[1],np.zeros_like(gx)],-1)@T[:,:3].T+T[:,3]
  heart.append(np.linalg.norm(xyz-CENTER,axis=-1)<=55)
 y=torch.as_tensor(data['values'],device='cuda')[op.mask]
 return dict(op=op,data=data,files=files,y=y,tw=torch.as_tensor(tw,device='cuda'),heart=np.stack(heart))

def solve(s,conf):
 op=s['op'];y=s['y'];sid=op.sid;n=len(op.transforms);tw=s['tw'][sid]
 weight=tw.clone();gains=torch.ones(n,device='cuda');history=[]
 for outer in range(conf.outer_iterations):
  if outer:
   roi=s['heart']&s['data']['mask'];sub=Acquisition(roi,op.transforms,op.spacing_tensor.cpu().numpy(),op.affine.cpu().numpy(),op.shape,device='cuda',quadrature=(5,5,13),chunk_rows=512)
   selected=torch.as_tensor(s['heart'],device='cuda')[op.mask]
   solver.fit_motion(sub,x,y[selected],gains,conf);op.transforms=sub.transforms
  op.build();coverage=op.adjoint(tw)
  support=solver.reconstruction_support(coverage)&torch.as_tensor(s['data']['support'],device='cuda')
  if not bool(support.any()):raise ValueError('Empty support')
  if outer==0:x=(op.adjoint(tw*y)/coverage.clamp_min(.05)).clamp_min(0);prior=x.clone()
  for inner in range(conf.irls_iterations):
   pred=op.forward(x);gains=solver.fit_gains(pred,y,weight,sid,n);res=gains[sid]*pred-y
   sigma=(res.abs().median()*1.4826).clamp_min(conf.robust_floor)
   robust=(1+(res/(2.5*sigma)).square()).reciprocal().clamp_min(.02)
   sr=(solver.slice_sum(robust*res.square(),sid,n)/solver.slice_sum(robust,sid,n).clamp_min(1)).sqrt()
   weight=robust*(1+(sr/(3*sigma)).square()).reciprocal().clamp_min(.1)[sid]*tw
   eff=weight*gains[sid].square();ew=solver.edge_weights(x,conf.edge_scale)
   mc=coverage[support].median().clamp_min(.1);lam=conf.regularization*mc;ridge=conf.ridge*mc
   rhs=op.adjoint(weight*gains[sid]*y)+ridge*prior
   diag=op.diagonal(eff)+lam*solver.laplacian_diagonal(ew,x.shape)+ridge
   def mv(v):return op.adjoint(eff*op.forward(v))+lam*solver.laplacian(v,ew)+ridge*v
   x,ch=solver.pcg(mv,rhs,x,diag,conf.cg_iterations);x=x.clamp_min(0)*support
   fit=gains[sid]*op.forward(x)-y;err=float((weight*fit.square()).sum().div(weight.sum()).sqrt())
   history.append(dict(outer=outer,inner=inner,weighted_rmse=err));logging.info('outer %d inner %d weighted RMSE %.6f',outer+1,inner+1,err)
  op.blocks=[];torch.cuda.empty_cache()
 s.update(image=x,gains=gains,history=history)


def evaluate(s,testfiles,loaded,geometry,args):
 test=state(testfiles,loaded,geometry,0,args,False);op=test['op']
 with torch.no_grad():pred=op.sample(s['image'])
 # Held-out slice poses remain original scanner geometry. No held-out data fit.
 med=torch.stack([s['gains'][torch.as_tensor(s['data']['groups']==g,device='cuda')].median() for g in [0,1,2]])
 group=torch.as_tensor(test['data']['groups'],device='cuda')[op.sid]
 pred=(pred*med[group]).cpu().numpy();y=test['data']['values'][test['data']['mask']]
 cardiac=test['heart'][test['data']['mask']]
 return dict(whole_frame_rmse=float(np.sqrt(np.mean((pred-y)**2))),whole_frame_ncc=float(np.corrcoef(pred,y)[0,1]),cardiac_rmse=float(np.sqrt(np.mean((pred[cardiac]-y[cardiac])**2))),cardiac_ncc=float(np.corrcoef(pred[cardiac],y[cardiac])[0,1]),test_frames=len(testfiles),test_pixels=len(y))

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--repo',type=Path,default=Path('/home/ajoshi/Projects/svr_gpu'))
 p.add_argument('--cache',type=Path,default=ROOT/'heart_svr_model_free_1p5mm_motion3mm3deg')
 p.add_argument('--timing-index',type=Path,default=Path(__file__).with_name('dicom_timing_index.json'))
 p.add_argument('--output',type=Path,default=Path(__file__).with_name('results'))
 p.add_argument('--phases',type=int,nargs='+',default=[7,14]);p.add_argument('--bins',type=int,default=26)
 p.add_argument('--sigma-bins',type=float,default=.35);p.add_argument('--radius-bins',type=float,default=.6)
 p.add_argument('--fit-all',action='store_true',help='Include every eligible slice group; skip held-out evaluation')
 p.add_argument('--methods',nargs='+',choices=['original_bins','phase_aware'],default=['original_bins','phase_aware'])
 args=p.parse_args()
 if args.fit_all and args.methods==['original_bins','phase_aware']:args.methods=['phase_aware']
 if args.sigma_bins<=0 or args.radius_bins<=0:raise ValueError('Kernel widths must be positive')
 if len(set(args.phases))!=len(args.phases) or any(ph<1 or ph>args.bins for ph in args.phases):raise ValueError('Phases must be distinct valid output bins')
 args.output.mkdir(parents=True,exist_ok=True)
 global Acquisition,solver,LOOKUP,CENTER
 sys.path.insert(0,str(args.repo))
 from standalone_inlined.svr.operators import Acquisition
 from standalone_inlined.svr import solver
 torch.set_num_threads(4);torch.manual_seed(0)
 if not torch.cuda.is_available():raise RuntimeError('CUDA required')
 started=time.monotonic();rows,summary=timing_map(args.timing_index)
 (args.output/'timing_map.json').write_text(json.dumps(dict(summary=summary,records=rows)))
 LOOKUP,chosen,tests,loaded,geometry,scales=prepare(args,rows)
 CENTER=np.mean(np.stack([d['poses'][:,3] for d in loaded.values()]),axis=0)
 conf=solver.Config(outer_iterations=2,irls_iterations=3,cg_iterations=25,regularization=.08,motion_steps=35,motion_lr=.08,max_motion_mm=3,max_motion_deg=3)
 results=[]
 for ph in args.phases:
  if not args.fit_all and len(tests[ph])<10:raise ValueError(f'Too few held-out frames for phase {ph}')
  for method in args.methods:
   logging.info('phase %02d %s: train %d frames; test %d',ph,method,len(chosen[ph,method]),len(tests[ph]))
   s=state(chosen[ph,method],loaded,geometry,(ph-1)/args.bins,args,method=='phase_aware');solve(s,conf)
   folder=args.output/method/f'phase_{ph:02d}';folder.mkdir(parents=True,exist_ok=True)
   im=nib.Nifti1Image(s['image'].cpu().numpy().transpose(2,1,0),geometry['affine']);im.header.set_xyzt_units('mm');im.set_qform(geometry['affine'],1);im.set_sform(geometry['affine'],1);nib.save(im,folder/'reconstruction.nii.gz')
   np.save(folder/'poses.npy',s['op'].transforms.cpu().numpy())
   metrics=evaluate(s,tests[ph],loaded,geometry,args) if not args.fit_all else dict(validation='none; all eligible observations used')
   metrics.update(phase=ph,method=method,train_frames=len(chosen[ph,method]),history=s['history'])
   (folder/'metrics.json').write_text(json.dumps(metrics,indent=2))
   (folder/'train_files.json').write_text(json.dumps(s['files']));(folder/'test_files.json').write_text(json.dumps(sorted(tests[ph])))
   results.append(metrics);logging.info('RESULT %s',json.dumps(metrics))
   del s;torch.cuda.empty_cache()
 report=dict(parameters={k:str(v) if isinstance(v,Path) else v for k,v in vars(args).items()},timing_summary=summary,normalization_scales=scales,roi_center_ras_mm=CENTER.tolist(),solver_config=vars(conf),results=results,seconds=time.monotonic()-started,validation=('No holdout: all eligible observations used' if args.fit_all else 'Every 7th original six-frame slice group withheld from all fitting, normalization and motion. Both methods evaluated on identical trigger-normalized near-target held-out frames in original scanner poses; no test-frame gain or motion fitted.'))
 (args.output/'comparison.json').write_text(json.dumps(report,indent=2))
if __name__=='__main__':
 logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s');main()
