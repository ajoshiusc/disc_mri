#!/usr/bin/env python3
"""Reproduce the model-free cardiac reconstructions of phases 1 and 2.

No SVoRT, brain segmentation, or learned anatomical prior is used. Each DICOM
plane retains its own scanner-space pose and reported 6-mm slice profile.
An existing, spatially checked thoracic mask supplies broad reconstruction
support; bounded rigid slice corrections are fitted inside a central heart ROI.

Defaults reproduce the selected 1.5-mm-grid, 3-mm/3-degree-bounded reconstruction.
Use --validation for a train-only-initialized 90/10 native-pixel prediction check.
The template is used only as a binary mask, never as an intensity reference.
"""
import os
os.environ.setdefault('OMP_NUM_THREADS','4');os.environ.setdefault('MKL_NUM_THREADS','4')
os.environ.setdefault('PYTORCH_CUDA_ALLOC_CONF','expandable_segments:True')
import argparse,json,hashlib,logging,time,sys,shutil
from pathlib import Path
import numpy as np,nibabel as nib,pydicom
from scipy.ndimage import map_coordinates,distance_transform_edt,gaussian_filter

ROOT=Path('/home/ajoshi/project2_ajoshi_27/data/heart_svr/heart_svr_acquisition_11_06_2026')
REPO=Path('/home/ajoshi/Projects/svr_gpu')
MASK=ROOT/'test_data_24cm_template/p8213_id8_stack_2_phase_13_24cm.mask.nii.gz'

def dump(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,a,affine):
 im=nib.Nifti1Image(np.asarray(a,dtype=np.float32),affine);im.header.set_xyzt_units('mm');im.set_sform(affine,code=1);im.set_qform(affine,code=1);nib.save(im,p)

def prepare(args,phase):
 out=args.output/f'phase_{phase:02d}';out.mkdir(parents=True,exist_ok=True)
 cache=out/'native_data.npz'
 if cache.exists():
  data=dict(np.load(cache));record=json.loads((out/'inputs.json').read_text())
  if record['mask_sha256']!=sha(args.mask) or not np.allclose(np.linalg.norm(data['affine'][:3,:3],axis=0),args.resolution):raise ValueError('Cached preparation differs from requested mask/resolution; use a new output directory')
  for row in record['records']:
   if sha(row['file'])!=row['sha256']:raise ValueError('Cached DICOM input has changed: '+row['file'])
  return data,out
 template=nib.load(args.mask);mv=template.get_fdata()>0;sp=np.linalg.norm(template.affine[:3,:3],axis=0)
 dilated=distance_transform_edt(~mv,sampling=sp)<=5.
 inv=np.linalg.inv(template.affine);inds=np.argwhere(dilated);lo=np.maximum(inds.min(0)-3,0);hi=np.minimum(inds.max(0)+3,np.array(mv.shape)-1)
 direction=template.affine[:3,:3]/sp;affine=np.eye(4);affine[:3,:3]=direction*args.resolution;affine[:3,3]=(template.affine@np.r_[lo,1])[:3]
 shape=np.ceil((hi-lo)*sp/args.resolution).astype(int)+1
 xx,yy,zz=np.meshgrid(*(np.arange(n) for n in shape),indexing='ij');world=np.stack([xx,yy,zz],-1)@affine[:3,:3].T+affine[:3,3]
 ix=world@inv[:3,:3].T+inv[:3,3];support=map_coordinates(dilated.astype(float),ix.transpose(3,0,1,2),order=0,mode='constant')>0
 values=[];masks=[];poses=[];spacing=[];groups=[];records=[];interpolated=[]
 for group,folder in enumerate(sorted((args.input/f'phase_{phase:02d}').glob('stack_*'))):
  rows=[]
  for f in folder.glob('*.dcm'):
   d=pydicom.dcmread(f);ori=np.array(d.ImageOrientationPatient,float);R=np.diag([-1.,-1.,1.])@np.column_stack([ori[:3],ori[3:],np.cross(ori[:3],ori[3:])]);dy,dx=map(float,d.PixelSpacing);v=d.pixel_array.astype(np.float32)*float(getattr(d,'RescaleSlope',1))+float(getattr(d,'RescaleIntercept',0));h,w=v.shape
   assert int(d.TemporalPositionIdentifier)==phase
   center=np.array(d.ImagePositionPatient,float)+ori[:3]*(w-1)*dx/2+ori[3:]*(h-1)*dy/2;center*=np.array([-1,-1,1]);T=np.column_stack([R,center]);proj=center@R[:,2]
   y,x=np.mgrid[:h,:w];local=np.stack([(x-(w-1)/2)*dx,(y-(h-1)/2)*dy,np.zeros_like(x)],-1);ras=local@R.T+center;index=ras@inv[:3,:3].T+inv[:3,3]
   mask=map_coordinates(dilated.astype(float),index.transpose(2,0,1),order=0,mode='constant')>0
   rows.append((proj,int(d.InstanceNumber),f.name,v,mask,T,float(d.SliceThickness),dx,dy))
  rows.sort(key=lambda r:(r[0],r[1],r[2]));images=np.stack([r[3] for r in rows]);mm=np.stack([r[4] for r in rows]);scale=np.percentile(images[mm],99);images/=scale
  for i,r in enumerate(rows):
   values.append(images[i]);masks.append(mm[i]);poses.append(r[5]);spacing.append([r[7],r[8],r[6]]);groups.append(group);records.append(dict(file=str(folder/r[2]),sha256=sha(folder/r[2]),group=group,projection_mm=float(r[0]),instance=r[1],normalization_p99=float(scale)))
  z=np.array([r[0] for r in rows]);unique,inverse=np.unique(np.round(z,5),return_inverse=True);mean=np.zeros((len(unique),h,w),np.float32);counts=np.bincount(inverse)
  np.add.at(mean,inverse,images);mean/=counts[:,None,None]
  R=rows[0][5][:,:3];local=world@R;center=rows[0][5][:,3]@R
  ix=(local[...,0]-center[0])/dx+(w-1)/2;iy=(local[...,1]-center[1])/dy+(h-1)/2;iz=np.interp(local[...,2],unique,np.arange(len(unique)),left=-1,right=len(unique))
  vi=map_coordinates(mean,np.stack([iz,iy,ix]),order=1,mode='constant')
  valid=support&(iz>=0)&(iz<=len(unique)-1)&(ix>=0)&(ix<=w-1)&(iy>=0)&(iy<=h-1)
  interpolated.append((vi,valid));save(out/f'stack_{group+1:02d}_scanner_interp.nii.gz',vi*valid,affine)
  logging.info('phase %d stack %d: %d observations, %d mask pixels, normalization %.1f',phase,group+1,len(rows),mm.sum(),scale)
 numerator=sum(v*m for v,m in interpolated);denominator=sum(m.astype(float) for v,m in interpolated)
 initial=numerator/np.maximum(denominator,1)
 data=dict(values=np.stack(values),mask=np.stack(masks),poses=np.stack(poses).astype(np.float32),spacing=np.array(spacing),groups=np.array(groups),affine=affine,shape=shape[::-1],support=support.transpose(2,1,0),initial=initial.transpose(2,1,0))
 # Deterministic 10% interleaved pixel holdout. It tests prediction, not an independent scan.
 s,y,x=np.indices(data['mask'].shape);holdout=((x+3*y+7*s)%10)==0
 data['train']=data['mask']&~holdout;data['test']=data['mask']&holdout
 np.savez_compressed(cache,**data);dump(out/'inputs.json',dict(mask=str(args.mask),mask_sha256=sha(args.mask),mask_dilation_mm=5,records=records,native_geometry=True))
 save(out/'scanner_interpolation.nii.gz',initial,affine);save(out/'support.nii.gz',support,affine)
 return data,out

def run(args,data,out):
 import torch
 sys.path.insert(0,str(args.repo))
 from standalone_inlined.svr.operators import Acquisition
 from standalone_inlined.svr.solver import Config,reconstruct
 from standalone_inlined.svr import solver
 torch.set_num_threads(4);torch.manual_seed(0)
 if not torch.cuda.is_available():raise RuntimeError('CUDA required')
 device=torch.device('cuda:0');torch.cuda.set_device(device)
 torch.empty(1,device=device);torch.cuda.reset_peak_memory_stats(device)
 if args.validation:
  # No test intensities may set conditioning, the initial volume or its prior.
  data={**data,'values':data['values'].copy()}
  for group in np.unique(data['groups']):
   idx=data['groups']==group;scale=np.percentile(data['values'][idx][data['train'][idx]],99)
   data['values'][idx]/=scale
 mask=data['train'] if args.validation else data['mask']
 op=Acquisition(mask,data['poses'],data['spacing'],data['affine'],data['shape'],device=device,quadrature=(5,5,13),chunk_rows=512)
 y=torch.as_tensor(data['values'],device=device)[op.mask]
 # Motion fitting focuses on a central cardiac ROI while reconstruction keeps
 # the broader thoracic mask. No brightness threshold removes myocardium.
 center=data['poses'][:,:,3].mean(0);h,w=data['mask'].shape[-2:];gy,gx=np.mgrid[:h,:w];heart=[]
 for T,sp in zip(data['poses'],data['spacing']):
  xyz=np.stack([(gx-(w-1)/2)*sp[0],(gy-(h-1)/2)*sp[1],np.zeros_like(gx)],-1)@T[:,:3].T+T[:,3]
  heart.append(np.linalg.norm(xyz-center,axis=-1)<=55.)
 heart=np.stack(heart)&data['mask']
 if args.mode=='bounded':
  original_fit=solver.fit_motion
  def cardiac_motion(full,image,values,gains,config):
   roi=heart&full.mask.cpu().numpy()
   sub=Acquisition(roi,full.transforms,full.spacing_tensor.cpu().numpy(),full.affine.cpu().numpy(),full.shape,device=device,quadrature=(5,5,13),chunk_rows=512)
   selected=torch.as_tensor(heart,device=device)[full.mask]
   row=original_fit(sub,image,values[selected],gains,config);full.transforms=sub.transforms
   return row
  solver.fit_motion=cardiac_motion
 conf=Config(outer_iterations=args.outer,irls_iterations=3,cg_iterations=25,regularization=args.regularization,motion_steps=35 if args.mode=='bounded' else 0,motion_lr=.08,max_motion_mm=args.motion_mm,max_motion_deg=args.motion_deg)
 bounds=f'_mm{args.motion_mm:g}_deg{args.motion_deg:g}' if args.mode=='bounded' and (args.motion_mm!=1.5 or args.motion_deg!=1.5) else ''
 name=f'{args.mode}{bounds}_reg{args.regularization:g}'+('_validation' if args.validation else '')
 target=out/name;target.mkdir(exist_ok=True)
 started=time.monotonic()
 def callback(row,volume):
  logging.info('%s outer %d solve %d RMSE %.5f',name,row['outer']+1,row['inner']+1,row['robust_rmse'])
  if row['inner']==2:save(target/f'outer_{row["outer"]+1}.nii.gz',volume.detach().cpu().numpy().transpose(2,1,0),data['affine'])
 try:
  image,stats,coverage=reconstruct(op,y,conf,initial=None,callback=callback,fixed_support=torch.as_tensor(data['support'],device=device))
 finally:
  if args.mode=='bounded':solver.fit_motion=original_fit
 save(target/'reconstruction.nii.gz',image.cpu().numpy().transpose(2,1,0),data['affine']);save(target/'coverage.nii.gz',coverage.cpu().numpy().transpose(2,1,0),data['affine']);np.save(target/'poses.npy',op.transforms.cpu().numpy())
 op.blocks=[];torch.cuda.empty_cache()
 test=Acquisition(data['test'],op.transforms,data['spacing'],data['affine'],data['shape'],device=device,quadrature=(5,5,13),chunk_rows=512)
 with torch.no_grad():pred=test.sample(image);observed=torch.as_tensor(data['values'],device=device)[test.mask];gains=torch.as_tensor(stats['gains'],device=device);pred*=gains[test.sid]
 pp=pred.cpu().numpy();yy=observed.cpu().numpy();ncc=float(np.corrcoef(pp,yy)[0,1]);rmse=float(np.sqrt(np.mean((pp-yy)**2)))
 cardiac=heart[data['test']];cardiac_ncc=float(np.corrcoef(pp[cardiac],yy[cardiac])[0,1]);cardiac_rmse=float(np.sqrt(np.mean((pp[cardiac]-yy[cardiac])**2)))
 prefix='heldout' if args.validation else 'in_sample'
 stats.update(mode=args.mode,validation=args.validation,total_seconds=time.monotonic()-started,brain_models_used=False,output=str(target/'reconstruction.nii.gz'),gpu=torch.cuda.get_device_name(device),peak_torch_mb=torch.cuda.max_memory_allocated(device)/1024**2,input_frames=int(len(data['groups'])),frames_with_roi_pixels=int(data['mask'].any((1,2)).sum()))
 stats.update({f'{prefix}_pixel_ncc':ncc,f'{prefix}_pixel_rmse':rmse,f'{prefix}_cardiac_ncc':cardiac_ncc,f'{prefix}_cardiac_rmse':cardiac_rmse})
 dump(target/'result.json',stats);logging.info('Finished %s; %s NCC %.5f RMSE %.5f',name,prefix,ncc,rmse)
 if args.finalize and not args.validation:
  final=out/'final';final.mkdir(exist_ok=True)
  for filename in ['reconstruction.nii.gz','coverage.nii.gz','poses.npy']:shutil.copy2(target/filename,final/filename)
  dump(final/'result.json',{**stats,'source_method':name,'output':str(final/'reconstruction.nii.gz')})

def main():
 p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
 p.add_argument('--input',type=Path,default=ROOT/'test_data_24cm')
 p.add_argument('--repo',type=Path,default=REPO)
 p.add_argument('--mask',type=Path,default=MASK)
 p.add_argument('--output',type=Path,default=Path(__file__).resolve().parent/'results')
 p.add_argument('--phases',type=int,nargs='+',default=[1,2])
 p.add_argument('--resolution',type=float,default=1.5)
 p.add_argument('--prepare-only',action='store_true')
 p.add_argument('--validation',action='store_true',help='Withhold 10 percent of native pixels from all fitting and initialization')
 p.add_argument('--regularization',type=float,default=.08)
 p.add_argument('--outer',type=int,default=2)
 p.add_argument('--mode',choices=['fixed','bounded'],default='bounded')
 p.add_argument('--motion-mm',type=float,default=3,help='Per-axis translation limit for the motion update')
 p.add_argument('--motion-deg',type=float,default=3,help='Per-axis Euler rotation limit for the motion update')
 p.add_argument('--finalize',action=argparse.BooleanOptionalAction,default=True,help='Copy all-pixel outputs to phase_XX/final; validation fits are never finalized')
 args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True)
 for phase in args.phases:
  data,out=prepare(args,phase)
  if not args.prepare_only:
   run(args,data,out)
   import gc,torch
   gc.collect();torch.cuda.empty_cache()
if __name__=='__main__':
 logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s');main()
