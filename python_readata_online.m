function samples  = python_readata_online(x,channel)
%PYTHON_READATA 此处显示有关此函数的摘要
%   此处显示详细说明

header_size=7;
nchans =16;
TTL_DATA=0;
sampling_rate=1000;
nsamples = 43;
ttldata_size=0;

sample_size=nchans*nsamples;
bu_size=header_size+sample_size+ttldata_size;
ifinal=numel(x)/bu_size-1;
y2 = [];
y3 = [];

for i=0:ifinal
    nstart=i*bu_size+1;
    nend=nstart+bu_size-1;
    y=x(nstart:nend); %a chuck of datagram (header+samples+TTL data)
    for k=header_size+1:header_size+sample_size;
      y2(end+1)=y(k);
    end
end

%  Converting the samples into a data-array
array_length=length(y2)/nchans;
data_array=zeros(array_length,nchans);
    
for i=1:nchans
    data_array(:,i)=y2(i:nchans:end);
end
samples = data_array(:,channel(1,:))';

   
    % to plot ith channel; type on the command line >> plot(data_array (:,i))
    
    % to plot in mV (y axis) and sec (in x axis)
    % >> plot((1:length(data_array(:,3)))/sampling_rate,(data_array(:,3)-32768)*0.17*0.001) 
    
    % (max(data_array (:,1))+ min(data_array(:,1)))/2: no-bias-referencing
end
