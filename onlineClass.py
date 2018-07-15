from struct_methods import *
import io
import numpy
from scipy.signal import butter, lfilter
import math
import pickle


class ReadData(object):
    def __init__(self, channel, timepoint, frequency, num, param_file='Params.txt', N=3):
        self.Fs = 1000
        self.filt_n = 4
        self.N = N
        self.channelRaw = channel
        self.channels = [i-1 for i in self.channelRaw]
        self.DataLength = len(self.channels)
        self.num = num
        self.timepoint = timepoint
        self.frequencyPoint = frequency
        self.Wn = [self.frequencyPoint[0]/(self.Fs/2), self.frequencyPoint[1]/(self.Fs/2)]
        self.filter_b, self.filter_a = butter(self.filt_n, self.Wn, btype='band')
        with open(param_file, 'rb') as readParams:
            params = pickle.load(readParams)
        self.F = params[0]
        self.w = params[1]
        self.b = params[2]
        self.TypeOneSign = params[3]
        self.samples_per_packet = 43
        self.allChannels = 16
        # self.fh = io.BytesIO()
        self.finalMatrics = numpy.zeros(shape=(43*self.num, 16))

    def readOnlineData(self, data=[]):
        # self.fh.seek(0)
        # self.fh.write(data)
        # self.fh.seek(0)
        self.fh = open('./JAGA_data/online.dat', "rb")
        for n in range(self.num):
            header = []
            for i in range(6):
                header.append(read_uint16le(self.fh))
            """Read all the data samples from the packet"""
            all_samples = []
            for i in range(self.samples_per_packet):      
                samples = []
                for j in range(self.allChannels):
                    sample = read_uint16le(self.fh)
                    samples.append(sample)                
                all_samples.append(samples)                
            per_Packet = numpy.array(all_samples)            
            currentPacketMatrics = per_Packet.reshape((self.samples_per_packet, self.allChannels))
            self.finalMatrics[43*n:43*n+43, :] = currentPacketMatrics
        self.fh.close()        
        return self.finalMatrics.T

    def onlineClassify(self, rawData=[]):
        data = self.readOnlineData()
        dataTofilter = data[self.channels, :]
        dataFiltered = lfilter(self.filter_b, self.filter_a, dataTofilter, axis=1)
        dataForClassify = dataFiltered[:, self.timepoint[0]:self.timepoint[1]]
        cov = numpy.dot(dataForClassify, dataForClassify.T)
        f = numpy.zeros((2*self.N, 1))
        for j in range(2*self.N):
            f[j] = numpy.log(numpy.dot(numpy.dot(self.F[:,j].reshape(1, self.DataLength),cov),self.F[:,j]))
        y = numpy.dot(self.w, f)+self.b
        if y*self.TypeOneSign >= 0:
            FeedBackSignal = 1.5
        else:
            FeedBackSignal = 0.5
        return FeedBackSignal
