#!/usr/bin/env python3
"""Test cardiac ROI NCC outlier confidence, using the timing pilot's exact split.
This preserves original phase assignments; it adds heart-specific reliability
weights to the existing whole-frame robust reconstruction.
"""
import argparse,json,logging,time,sys
from pathlib import Path
from types import SimpleNamespace
import reconstruct_phase_aware as core
import numpy as np,nibabel as nib,torch

def solve(s,conf):
 op=s['op'];y=s['y'];sid=op.sid;n=len(op.transforms)
 weight=torch.ones_like(y);gains=torch.ones(n,device='cuda');history=[]
 cardiac=torch.as_tensor(s['heart'],device='cuda')[op.mask];hsid=sid[cardiac]
 for outer in range(conf.outer_iterations):
  if outer:
   roi=s['heart']&s['data']['mask'];sub=core.Acquisition(roi,op.transforms,op.spacing_tensor.cpu().numpy(),op.affine.cpu().numpy(),op.shape,device='cuda',quadrature=(5,5,13),chunk_rows=512)
   core.solver.fit_motion(sub,x,y[cardiac],gains,conf);op.transforms=sub.transforms
  op.build();coverage=op.adjoint(torch.ones_like(y));support=core.solver.reconstruction_support(coverage)&torch.as_tensor(s['data']['support'],device='cuda')
  if outer==0:x=(op.adjoint(y)/coverage.clamp_min(.05)).clamp_min(0);prior=x.clone()
  for inner in range(conf.irls_iterations):
   pred=op.forward(x);gains=core.solver.fit_gains(pred,y,weight,sid,n);res=gains[sid]*pred-y
   sigma=(res.abs().median()*1.4826).clamp_min(conf.robust_floor)
   robust=(1+(res/(2.5*sigma)).square()).reciprocal().clamp_min(.02)
   sr=(core.solver.slice_sum(robust*res.square(),sid,n)/core.solver.slice_sum(robust,sid,n).clamp_min(1)).sqrt()
   weight=robust*(1+(sr/(3*sigma)).square()).reciprocal().clamp_min(.1)[sid]
   confidence=torch.ones(n,device='cuda')
   if inner or outer:
    w=robust[cardiac];p=pred[cardiac];target=y[cardiac]
    sm=lambda z:core.solver.slice_sum(z,hsid,n)
    mass=sm(w).clamp_min(1e-5);sx=sm(w*p);sy=sm(w*target)
    xx=sm(w*p*p)-sx*sx/mass;yy=sm(w*target*target)-sy*sy/mass
    rho=(sm(w*p*target)-sx*sy/mass)/(xx.clamp_min(1e-5)*yy.clamp_min(1e-5)).sqrt()
    err=1-rho.clamp(-1,1)
    for group in [0,1,2]:
     ids=torch.as_tensor(s['data']['groups']==group,device='cuda')&(mass>100)
     if ids.sum()<5:continue
     med=err[ids].median();mad=((err[ids]-med).abs().median()*1.4826).clamp_min(.03)
     confidence[ids]=(1+((err[ids]-med).clamp_min(0)/(3*mad)).square()).reciprocal().clamp_min(.1)
    weight*=confidence[sid]
   eff=weight*gains[sid].square();ew=core.solver.edge_weights(x,conf.edge_scale)
   mc=coverage[support].median().clamp_min(.1);lam=conf.regularization*mc;ridge=conf.ridge*mc
   rhs=op.adjoint(weight*gains[sid]*y)+ridge*prior
   diag=op.diagonal(eff)+lam*core.solver.laplacian_diagonal(ew,x.shape)+ridge
   def mv(v):return op.adjoint(eff*op.forward(v))+lam*core.solver.laplacian(v,ew)+ridge*v
   x,ch=core.solver.pcg(mv,rhs,x,diag,conf.cg_iterations);x=x.clamp_min(0)*support
   fit=gains[sid]*op.forward(x)-y;err=float((weight*fit.square()).sum().div(weight.sum()).sqrt())
   history.append(dict(outer=outer,inner=inner,weighted_rmse=err,mean_cardiac_confidence=float(confidence.mean())))
   logging.info('outer %d inner %d RMSE %.6f confidence %.3f',outer+1,inner+1,err,float(confidence.mean()))
  op.blocks=[];torch.cuda.empty_cache()
 s.update(image=x,gains=gains,history=history,confidence=confidence.cpu().numpy())

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--pilot',type=Path,default=Path(__file__).with_name('results')/'comparison.json')
 p.add_argument('--phases',type=int,nargs='+',default=[7,14])
 p.add_argument('--fit-all',action='store_true',help='Use all original-bin frames; no held-out evaluation')
 p.add_argument('--output',type=Path)
 args=p.parse_args()
 report=json.loads(args.pilot.read_text());opts=report['parameters'].copy()
 for key in ['repo','cache','timing_index','output']:opts[key]=Path(opts[key])
 # Preserve the pilot's full preparation selection for identical scaling/ROI.
 opts['fit_all']=args.fit_all;opts['methods']=['original_bins','phase_aware']
 opts['output']=args.output if args.output else args.pilot.parent
 local_index=Path(__file__).with_name('dicom_timing_index.json')
 if local_index.exists():opts['timing_index']=local_index
 if args.fit_all:opts['phases']=args.phases
 options=SimpleNamespace(**opts)
 sys.path.insert(0,str(options.repo))
 from standalone_inlined.svr.operators import Acquisition
 from standalone_inlined.svr import solver
 core.Acquisition=Acquisition;core.solver=solver;torch.set_num_threads(4);torch.manual_seed(0)
 rows,_=core.timing_map(options.timing_index)
 core.LOOKUP,chosen,tests,loaded,geometry,scales=core.prepare(options,rows)
 core.CENTER=np.mean(np.stack([d['poses'][:,3] for d in loaded.values()]),axis=0)
 if not args.fit_all and not np.allclose(core.CENTER,report['roi_center_ras_mm']):raise ValueError('Pilot calibration differs')
 conf=solver.Config(**report['solver_config']);results=[];started=time.monotonic()
 for ph in args.phases:
  s=core.state(chosen[ph,'original_bins'],loaded,geometry,(ph-1)/options.bins,options,False)
  logging.info('cardiac confidence phase %d: %d training frames',ph,len(s['files']));solve(s,conf)
  folder=options.output/'cardiac_confidence'/f'phase_{ph:02d}';folder.mkdir(parents=True,exist_ok=True)
  im=nib.Nifti1Image(s['image'].cpu().numpy().transpose(2,1,0),geometry['affine']);im.header.set_xyzt_units('mm');im.set_qform(geometry['affine'],1);im.set_sform(geometry['affine'],1);nib.save(im,folder/'reconstruction.nii.gz')
  np.save(folder/'poses.npy',s['op'].transforms.cpu().numpy());np.save(folder/'cardiac_confidence.npy',s['confidence'])
  metrics=core.evaluate(s,tests[ph],loaded,geometry,options) if not args.fit_all else dict(validation='none; all original-bin observations fitted')
  metrics.update(phase=ph,method='cardiac_confidence',train_frames=len(s['files']),history=s['history'])
  (folder/'metrics.json').write_text(json.dumps(metrics,indent=2));results.append(metrics);logging.info('RESULT %s',json.dumps(metrics));del s;torch.cuda.empty_cache()
 (options.output/'cardiac_confidence_comparison.json').write_text(json.dumps(dict(pilot=str(args.pilot),fit_all=args.fit_all,phases=args.phases,results=results,seconds=time.monotonic()-started),indent=2))
if __name__=='__main__':
 logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s');main()
