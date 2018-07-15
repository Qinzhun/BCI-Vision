function [F, w, b, TypeOneSign] = train_para_4( class_one,class_two,StartTimePoint,EndTimePoint,times,FrequencyPoint,trials,channel,N)
%PYTHON_PROCESSING 此处显示有关此函数的摘要
%   此处显示详细说明
Fs=1000;
filt_n =4; 
Wn=[FrequencyPoint(1) FrequencyPoint(2)]/(Fs/2);
[filter_b,filter_a]=butter(filt_n,Wn);


DATA_CHANNEL=size(channel);
DATA_CHANNEL=DATA_CHANNEL(2);

R1=zeros(DATA_CHANNEL,DATA_CHANNEL);
R2=zeros(DATA_CHANNEL,DATA_CHANNEL);
TrainSet1=cell(1,trials*times);          
TrainSet2=cell(1,trials*times);
    
inter=(EndTimePoint-StartTimePoint+1)/times;

for i=1:trials
    Dr=class_one{i};
%   Dr=data_filter(:,StartTimePoint:EndTimePoint);

    for m=1:times
        data_filter=filter(filter_b,filter_a,Dr,[],2);
        data_origin=data_filter(:, StartTimePoint+(m-1)*inter:StartTimePoint+m*inter-1);
        TrainSet1{i*times-times+m}=data_origin*data_origin'; 
        R1=R1+ TrainSet1{i*times-times+m};
    end


      Dr=class_two{i};
%           Dr=data_filter(:,StartTimePoint:EndTimePoint);
      for m=1:times
          data_filter=filter(filter_b,filter_a,Dr,[],2);
          data_origin=data_filter(:, StartTimePoint+(m-1)*inter:StartTimePoint+m*inter-1);
          TrainSet2{i*times-times+m}=data_origin*data_origin'; 
          R2=R2+TrainSet2{i*times-times+m};
      end

end

R1=R1/trace(R1);
R2=R2/trace(R2);
R3=R1+R2;

[U0,Sigma]=eig(R3);
P=Sigma^(-0.5)*U0';
YL=P*R1*P';
[UL,SigmaL]=eig(YL);
[Y,I]=sort(diag(SigmaL), 'descend');
F=P'*UL(:,I([1:N,DATA_CHANNEL-N+1:DATA_CHANNEL]));


f1=[];f2=[];f=zeros(2*N,1);

for i=1:length(TrainSet1)
    for j=1:2*N
        f(j)=log(F(:,j)'*TrainSet1{i}*F(:,j));
    end
    f1=[f1,f];
    for j=1:2*N
        f(j)=log(F(:,j)'*TrainSet2{i}*F(:,j));
    end
    f2=[f2,f];
end

F1=f1';F2=f2';

M1=mean(F1,1)';M2=mean(F2,1)';
count1=size(f1,2)-1;count2=size(f2,2)-1;
w=(inv((count1*cov(F1)+count2*cov(F2))/(count1+count2))*(M2-M1))';
b=-w*(M1+M2)/2;
TypeOneSign=w*M1+b;
TypeTwoSign=w*M2+b;

%   save('E:\Matlab\Jaga_online\params.mat', 'F', 'w', 'b', 'TypeOneSign');

end



