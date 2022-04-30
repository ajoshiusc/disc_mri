
%% Set static and moving image

function [Iw,Xw,Yw,Tx,Ty]=demon_image_registration_mri(I1,I2,alpha)

%clear all;close all;clc;

if ~exist('alpha','var')
    alpha=15;
end
%figure; imagesc(I1(:,:,1)); colormap gray;
%figure; imagesc(I1(:,:,2)); colormap gray;
%figure; imagesc(I2(:,:,1));colormap gray;
NIT=500;
S=I1; M=I2;
%figure; imagesc(I2(:,:,1)); colormap gray;hold on;

costiter=zeros(NIT,1);
res1=[128,256];
Tx=0;Ty=0;
Mo=M;So=S;itt1=1;
for r1=1:length(res1)
    
    NPTS=res1(r1);
    [X,Y]=meshgrid(1:NPTS);
    
    if r1>1
        % upsample the grid and the deformation field
        Tx=2*Tx;Ty=2*Ty;
        Tx=interp2(Tx,min(0.5*NPTS,max(1,((0.5*NPTS-1)/(NPTS-1))*(X-1)+1)),min(0.5*NPTS,max(1,((0.5*NPTS-1)/(NPTS-1))*(Y-1)+1)));
        Ty=interp2(Ty,min(0.5*NPTS,max(1,((0.5*NPTS-1)/(NPTS-1))*(X-1)+1)),min(0.5*NPTS,max(1,((0.5*NPTS-1)/(NPTS-1))*(Y-1)+1)));
    end
    
    M=zeros(NPTS,NPTS,size(Mo,3));S=M;I2=M;
    nT=size(M,3); NPTS_1=NPTS-1;
    for kk=1:nT
        M(:,:,kk)=interp2(Mo(:,:,kk),max(min(1+(255/NPTS_1)*(X+Tx-1),256),1),max(min(1+(255/NPTS_1)*(Y+Ty-1),256),1));
        S(:,:,kk)=interp2(So(:,:,kk),max(min(1+(255/NPTS_1)*(X-1),256),1),max(min(1+(255/NPTS_1)*(Y-1),256),1));
        I2(:,:,kk)=interp2(Mo(:,:,kk),max(min(1+(255/NPTS_1)*(X-1),256),1),max(min(1+(255/NPTS_1)*(Y-1),256),1));
    end
    [Sx,Sy] = gradient(S);
    %    ks=SMPARA*(NPTS/256);
    %    Hsmooth=fspecial('gaussian',round([6*ks 6*ks]),ks);
    %%fprintf('NIT=param.NIT*NPTS/256');
    for itt=1:NIT
        

        
        SMPARA=11*round(((NIT-itt)/(NIT-1))*7+3);
        ks=SMPARA*(NPTS/256);
        %ks=2;
        Hsmooth=fspecial('gaussian',round([6*ks 6*ks]),ks);
        
        % Difference image between moving and static image
        Idiff=M-S;
        
        % Extended demon force. With forces from the gradients from both
        % moving as static image. (Cachier 1999, He Wang 2005)
        [Mx,My] = gradient(M);
        Ux = sum(-Idiff.*  ((Sx./(sum(Sx.^2+Sy.^2,3)+alpha^2*sum(Idiff.^2,3)))+(Mx./(sum(Mx.^2+My.^2,3)+alpha^2*sum(Idiff.^2,3)))),3);
        Uy = sum(-Idiff.*  ((Sy./(sum(Sx.^2+Sy.^2,3)+alpha^2*sum(Idiff.^2,3)))+(My./(sum(Mx.^2+My.^2,3)+alpha^2*sum(Idiff.^2,3)))),3);
        
        % When divided by zero
        Ux(isnan(Ux))=0; Uy(isnan(Uy))=0;
        
        % Smooth the transformation field
        Uxs=imfilter(Ux,Hsmooth);
        Uys=imfilter(Uy,Hsmooth);
        
        % Add the new transformation field to the total transformation field.
        Tx=Tx+Uxs;
        Ty=Ty+Uys;
                
        costiter(itt1)=norm(M(:)-S(:))/(NPTS*NPTS);itt1=itt1+1;
        
        %  Warp the fmri data
        for kk=1:size(M,3)
            M(:,:,kk)=interp2(I2(:,:,kk),max(min(X+Tx,size(X,1)),1),max(min(Y+Ty,size(Y,1)),1));
        end
        %fprintf('res=%d iter = %d, diff=%g, def=%g\n',res1(r1),itt,costiter(itt1-1),sqrt(mean((Tx(:)).^2+(Ty(:)).^2)));
        %clf;imagesc(M);drawnow;
    end
end
Xw=max(min(X+Tx,size(X,1)),1);
Yw=max(min(Y+Ty,size(Y,1)),1);
Iw=M;
%clf;imagesc(Iw(:,:,1));drawnow;
end
