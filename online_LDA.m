function FeedBackSignal=online_LDA(ifinal)
load('E:\Python\BCI-Vision\JAGA_data\PARAM.mat');

Fs=1000;
filt_n =4;

FrequencyPoint=[8 30];
timepoint=[500 3800];
N=3;

channels=[1,3:16];

Wn=[FrequencyPoint(1) FrequencyPoint(2)]/(Fs/2);
[filter_b,filter_a]=butter(filt_n,Wn);


header_size=6;
nchans =16;
nsamples = 43;
sample_size=nchans*nsamples;
bu_size=header_size+sample_size;
%ifinal=23;
array_length=43*(ifinal+1);
data_array=zeros(array_length,nchans);
y2 = [];

%==========================================the above should be run before

    infile='E:\Python\BCI-Vision\JAGA_data\online.dat';
    fid = fopen(infile, 'r');
    x=fread(fid,'uint16','ieee-le');
    fclose(fid);
%    FeedBackSignal=1;
%    len=length(x);


 %   if size(x,1)==61072
        for i=0:ifinal
            nstart=i*bu_size+1;
            nend=nstart+bu_size-1;
            y=x(nstart:nend); %a chuck of datagram (header+samples+TTL data)

            for k=header_size+1:header_size+sample_size;
                  y2(end+1)=y(k);
            end
        end
        
        for i=1:nchans
             data_array(:,i)=y2(i:nchans:end);
        end
        
        samples_pre = data_array(:,channels(:))';
        
        data_filter=filter(filter_b,filter_a,samples_pre,[],2);
        
        samples=data_filter(:,timepoint(1):timepoint(2));
        
        Cov = samples * samples';
        f = zeros(2*N, 1);
        for j=1:2*N
          f(j) = log(F(:,j)'*Cov*F(:,j));
        end
        
        y=w*f+b;
        if y*TypeOneSign>=0
          FeedBackSignal = 1.5;
        else
          FeedBackSignal = 0.5;
        end
end
  

