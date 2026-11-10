from pathlib import Path
import json,csv,argparse
import numpy as np,nibabel as nib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).resolve().parent
r=json.loads((P/'results/comparison.json').read_text())
parser=argparse.ArgumentParser();parser.add_argument('--methods',nargs='+',default=['original_bins','phase_aware']);parser.add_argument('--filename',default='comparison.png');args=parser.parse_args()
methods=args.methods
for f in sorted((P/'results/cardiac_confidence').glob('phase_*/metrics.json')):r['results'].append(json.loads(f.read_text()))
phases=r['parameters']['phases'];center=r['roi_center_ras_mm']
imgs={(ph,m):nib.load(P/f'results/{m}/phase_{ph:02d}/reconstruction.nii.gz') for ph in phases for m in methods}
aff=next(iter(imgs.values())).affine
ix,iy,iz=np.rint((np.linalg.inv(aff)@np.r_[center,1])[:3]).astype(int)
arrays={k:im.get_fdata() for k,im in imgs.items()}
views={k:[d[ix,:,:].T,d[:,iy,:].T,d[:,:,iz].T] for k,d in arrays.items()}
bounds=[]
for vi in range(3):
 mask=np.any(np.stack([v[vi]>0 for v in views.values()]),axis=0);ij=np.argwhere(mask)
 lo=np.maximum(ij.min(0)-3,0);hi=np.minimum(ij.max(0)+4,mask.shape)
 bounds.append((slice(lo[0],hi[0]),slice(lo[1],hi[1])))
vmax=np.percentile(np.concatenate([d[d>0][::10] for d in arrays.values()]),99.6)
fig,axs=plt.subplots(len(phases),6,figsize=(19,7),facecolor='black',gridspec_kw=dict(wspace=.03,hspace=.15),squeeze=False)
for ri,ph in enumerate(phases):
 for vi in range(3):
  for mi,m in enumerate(methods):
   ax=axs[ri,vi*2+mi];ax.imshow(views[ph,m][vi][bounds[vi]],origin='lower',cmap='gray',vmin=0,vmax=vmax,interpolation='nearest');ax.axis('off')
   if ri==0:ax.set_title(f'Grid {"XYZ"[vi]}\n'+{'original_bins':'Original bins','phase_aware':'Phase aware','cardiac_confidence':'Cardiac confidence'}[m],color='white',fontsize=12)
   if vi==0 and mi==0:ax.text(-.03,.5,f'Phase {ph:02d}\n{100*(ph-1)/r["parameters"]["bins"]:.0f}% cycle',transform=ax.transAxes,color='white',ha='right',va='center',fontsize=12)
fig.suptitle('Whole-slice-group validation — common image planes and intensity window',color='white',fontsize=18)
fig.savefig(P/args.filename,dpi=140,bbox_inches='tight',facecolor='black');plt.close(fig)
keys=['phase','method','train_frames','test_frames','cardiac_rmse','cardiac_ncc','whole_frame_rmse','whole_frame_ncc']
with (P/'metrics.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows({k:a[k] for k in keys} for a in r['results'])
for ph in phases:
 a,b=[next(x for x in r['results'] if x['phase']==ph and x['method']==m) for m in methods]
 print(ph,'cardiac RMSE',a['cardiac_rmse'],b['cardiac_rmse'],'change%',100*(b['cardiac_rmse']/a['cardiac_rmse']-1),'NCC',a['cardiac_ncc'],b['cardiac_ncc'])
print('elapsed seconds',r['seconds'])
