clear all;close all;clc;

I1 = zeros(256,256);
I2 = zeros(256,256);


I1(100:176,100:176)=255;

[X,Y]=meshgrid(1:256,1:256);

R=sqrt((X-128).^2+(Y-128).^2);
I2=255*(R<28);


[Iw,Tx,Ty] = demon_image_registration(I1,I2);


IC=checkerboard(4,64,64);IC=255*double(IC);
ICW=interp2(IC,Tx,Ty);

figure;
imagesc(255*ICW);colormap gray;
