#||AUM||
#||Shree Ganeshaya Namaha||


import nilearn.image as ni
from sklearn.feature_extraction import img_to_graph


sub_img = '/home/ajoshi/mydocker/fetal_scan_6_8_2022/haste_head/10_t2_haste_tra_brain_rep2_p.nii.gz'
sub_msk = '/home/ajoshi/mydocker/fetal_scan_6_8_2022/haste_head/10_t2_haste_tra_brain_rep2_p_mask.nii.gz'
out_file = '/home/ajoshi/mydocker/fetal_scan_6_8_2022/haste_head/10_t2_haste_tra_brain_rep2_p_masked.nii.gz'


s = ni.load_img(sub_img).get_fdata() * (ni.load_img(sub_msk).get_fdata() > 0)


so = ni.new_img_like(sub_img,s,copy_header=True)

so = ni.crop_img(so,pad=True)

dt= ni.load_img(sub_img).get_data_dtype()

so.set_data_dtype(dt)
so.to_filename(out_file)



