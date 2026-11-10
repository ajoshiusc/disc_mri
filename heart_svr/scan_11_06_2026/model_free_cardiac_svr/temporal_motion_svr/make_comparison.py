from pathlib import Path
import json,csv
import numpy as np,nibabel as nib
from scipy.spatial.transform import Rotation
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).resolve().parent
report=json.loads((P/'results/comparison.json').read_text())
phases=report['parameters']['phases'];methods=['independent','temporal_motion']
arrays={};allposes={};native={}
cache=Path(report['parameters']['cache'])
for ph in phases:
 d=dict(np.load(cache/f'phase_{ph:02d}/native_data.npz'));native[ph]=d['poses']
 for method in methods:
  folder=P/'results'/method/f'phase_{ph:02d}'
  arrays[ph,method]=nib.load(folder/'reconstruction.nii.gz').get_fdata()
  allposes[ph,method]=np.load(folder/'poses.npy')
center=np.concatenate([native[p][:,:,3] for p in phases]).mean(0)
im=nib.load(P/f'results/independent/phase_{phases[0]:02d}/reconstruction.nii.gz')
ix,iy,iz=np.rint((np.linalg.inv(im.affine)@np.r_[center,1])[:3]).astype(int)
view=lambda d:[d[ix,:,:].T,d[:,iy,:].T,d[:,:,iz].T]
views={k:view(d) for k,d in arrays.items()}
bounds=[]
for ci in range(3):
 support=np.any(np.stack([v[ci]>0 for v in views.values()]),axis=0)
 ij=np.argwhere(support);lo=np.maximum(ij.min(0)-3,0);hi=np.minimum(ij.max(0)+4,support.shape)
 bounds.append((slice(lo[0],hi[0]),slice(lo[1],hi[1])))
vmax=np.percentile(np.concatenate([d[d>0][::10] for d in arrays.values()]),99.6)
fig,axs=plt.subplots(len(phases),6,figsize=(19,9),facecolor='black',gridspec_kw=dict(wspace=.03,hspace=.15))
for ri,ph in enumerate(phases):
 for vi in range(3):
  for mi,method in enumerate(methods):
   ax=axs[ri,vi*2+mi]
   ax.imshow(views[ph,method][vi][bounds[vi]],origin='lower',cmap='gray',vmin=0,vmax=vmax,interpolation='nearest');ax.axis('off')
   if ri==0:ax.set_title(f'Grid {"XYZ"[vi]}\n'+('Independent' if mi==0 else 'Temporal motion'),color='white',fontsize=12)
   if vi==0 and mi==0:ax.text(-.05,.5,f'Phase {ph:02d}',transform=ax.transAxes,color='white',ha='right',va='center',fontsize=13)
fig.suptitle('Matched validation reconstructions — shared slice positions and intensity window',color='white',fontsize=18)
fig.savefig(P/'comparison.png',dpi=140,bbox_inches='tight',facecolor='black');plt.close(fig)
links=json.loads((P/'results/motion_edges.json').read_text())
a=np.array([r[0] for r in links]);b=np.array([r[1] for r in links]);jitter={}
for method in methods:
 ps=[]
 for ph in phases:
  orig=native[ph];new=allposes[ph,method]
  rot=Rotation.from_matrix(new[:,:,:3]@orig[:,:,:3].transpose(0,2,1)).as_rotvec(degrees=True)
  ps.append(np.c_[rot,new[:,:,3]-orig[:,:,3]])
 ps=np.concatenate(ps);delta=ps[a]-ps[b]
 jitter[method]=dict(edge_translation_rms_mm=float(np.sqrt(np.mean(np.sum(delta[:,3:]**2,axis=1)))),edge_rotation_rms_deg=float(np.sqrt(np.mean(np.sum(delta[:,:3]**2,axis=1)))))
report['motion_graph_differences']=jitter
(P/'results/comparison.json').write_text(json.dumps(report,indent=2))
keys=['phase','method','heldout_cardiac_rmse','heldout_cardiac_ncc','heldout_rmse','heldout_ncc']
with (P/'metrics.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows({k:r[k] for k in keys} for r in report['results'])
print(json.dumps({k:v for k,v in report.items() if k in ['seconds','motion_graph_differences']},indent=2))
for ph in phases:
 base=next(r for r in report['results'] if r['phase']==ph and r['method']=='independent')
 new=next(r for r in report['results'] if r['phase']==ph and r['method']=='temporal_motion')
 print(ph,base['heldout_cardiac_rmse'],new['heldout_cardiac_rmse'],100*(new['heldout_cardiac_rmse']/base['heldout_cardiac_rmse']-1),base['heldout_cardiac_ncc'],new['heldout_cardiac_ncc'])
