# jupyter notebook


    self.fh = io.BytesIO()
    data = queues.get()  # Blocks until data is available.
        self.fh.seek(0)
        self.fh.write(data)
        self.fh.seek(0)

    # self.plotData = numpy.zeros((channels, samples_per_packet))

from struct_methods import *
import io
import numpy
from scipy.signal import butter, lfilter
import math

#  从文件里面读数据
def read_Data(buffer, num):
    finalPacketMatrics = numpy.zeros(shape=(43*num,16))
    for n in range(num):
        # trigger = read_char(buffer)
        header = []
        for i in range(6):
            header.append(read_uint16le(buffer))
        """Read all the data samples from the packet"""
        all_samples = []
        for i in range(samples_per_packet):
            samples = []
            for j in range(channels):
                sample = read_uint16le(buffer)
                samples.append(sample)
            all_samples.append(samples)
        per_samples = numpy.array(all_samples)
        currentPacketMatrics = per_samples.reshape((samples_per_packet,channels))
        finalPacketMatrics[43*n:43*n+43, :] = currentPacketMatrics
    return trigger, header, finalPacketMatrics.T

trigger, head, data = read_Data(f, 1)
 
dataTofilter = data[channels, :]
dataFiltered = lfilter(filter_b, filter_a, dataTofilter, axis=1)
dataForClassify = dataFiltered[:, timepoint[0]:timepoint[1]]
cov = dataForClassify * dataForClassify.T
f = numpy.zeros((2*N, 1))
for j in range(2*N):
    f[j] = math.log(F[:,j].T * cov * F[:,j])
y = w*f+b
if y*TypeOneSign >= 0:
    FeedBackSignal = 1.5
else:
    FeedBackSignal = 0.5




# params 导入
Fs = 1000
filt_n = 4
FrequencyPoint=[8, 30]
timepoint=[500, 4000]
N = 3
channelRaw = [1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
channels = [i-1 for i in channelRaw]
Wn = [FrequencyPoint[0]/(Fs/2), FrequencyPoint[1]/(Fs/2)]
filter_b, filter_a = butter(filt_n, Wn, btype='band')






