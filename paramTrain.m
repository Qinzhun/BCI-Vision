function window=paramTrain(path, trials)

FrequencyPoint=[8 30];
channel=[1,3:16];   %which channel do you need?
N=3;

fid = fopen(path, 'r');
x=fread(fid,'uint16','ieee-le');
fclose(fid);

window=4200;
alltime_ms=floor(window/43)*695;
StartTimePoint=1000;
EndTimePoint=4000;

index=find(x(:,1)==1000);
index_trigger=index-4;
trigger=x(index_trigger(:,1),1);
one=find(trigger(:,1)==1);
two=find(trigger(:,1)==2);
class_one=index_trigger(one(:,1));
class_two=index_trigger(two(:,1)); 

header_size=7;
nchans =16;
nsamples = 43;
ttldata_size=0;
sample_size=nchans*nsamples;
bu_size=header_size+sample_size+ttldata_size;

times=1;

class_one_action=cell(1,trials);
class_one_action_channel=cell(1,trials);
class_two_action=cell(1,trials);
class_two_action_channel=cell(1,trials);
class_one_rest=cell(1,trials);
class_two_rest=cell(1,trials);
class_one_rest_channel=cell(1,trials);
class_two_rest_channel=cell(1,trials);


for i=1:trials
    class_one_action{i}=x(class_one(i,1):class_one(i,1)+alltime_ms-1);
    class_one_action_channel{i}=python_readata_online(class_one_action{i},channel);
    class_two_action{i}=x(class_two(i,1):class_two(i,1)+alltime_ms-1);
    class_two_action_channel{i}=python_readata_online(class_two_action{i},channel);
    
    class_one_rest{i}=x(class_one(i,1)-alltime_ms:class_one(i,1)-1);
    class_one_rest_channel{i}=python_readata_online(class_one_rest{i},channel);
    class_two_rest{i}=x(class_two(i,1)-alltime_ms:class_two(i,1)-1);
    class_two_rest_channel{i}=python_readata_online(class_two_rest{i},channel);
end

[F, w, b, TypeOneSign]=train_para_4( class_one_action_channel,class_two_action_channel,StartTimePoint,EndTimePoint,times,FrequencyPoint,trials,channel,N);
window=0;
save('E:\Python\BCI-Vision\JAGA_data\PARAM.mat', 'F', 'w', 'b', 'TypeOneSign');



   
