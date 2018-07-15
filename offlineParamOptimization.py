from struct_methods import *
import io
import numpy
from scipy.signal import butter, lfilter
import math
import pickle
import random


class offlineParamOpt(object):
    def __init__(self, channel, num, groups, N=3):
        self.Fs = 1000
        self.filt_n = 4
        self.N = N  
        self.channelRaw = channel
        self.channels = [i-1 for i in self.channelRaw]
        self.DataLength = len(self.channels)
        self.num = num
        self.samples_per_packet = 43
        self.allChannels = 16
        self.groups = groups
        self.NtoLastN = [i for i in range(N)]
        self.NtoLastN.extend([i for i in range(self.DataLength-N, self.DataLength)])
        self.classOne = numpy.zeros(shape=(16, 43*self.num, self.groups))
        self.classTwo = numpy.zeros(shape=(16, 43*self.num, self.groups))
        self.frequency = [[8,30], [8,13], [13,20], [20,30]]
        self.timepoint = [1000, 4000]

    def readOffData(self, path):
        self.fid = open(path, "rb")
        # self.fid.seek(0)
        currentGroupOne = 0
        currentGroupTwo = 0
        packets = 0
        while currentGroupOne != self.groups or currentGroupTwo != self.groups:
            trigger = read_uint16le(self.fid)
            packets += 1
            if trigger == 1:
                currentGroupOne += 1
                self.fid.seek(12, 1)
                all_samples = []
                for i in range(self.samples_per_packet):         
                    samples = []
                    for j in range(self.allChannels):
                        sample = read_uint16le(self.fid)
                        samples.append(sample)                
                    all_samples.append(samples)                  
                first_Packet = numpy.array(all_samples)
                firstPacketMatrics = first_Packet.reshape((self.samples_per_packet, self.allChannels))
                self.classOne[:, 0:43, currentGroupOne-1] = firstPacketMatrics.T
                for p in range(self.num-1):                    
                    self.fid.seek(14, 1)
                    all_samples = []
                    for i in range(self.samples_per_packet):         
                        samples = []
                        for j in range(self.allChannels):
                            sample = read_uint16le(self.fid)
                            samples.append(sample)                
                        all_samples.append(samples)
                    next_Packet = numpy.array(all_samples)
                    nextPacketMatrics = next_Packet.reshape((self.samples_per_packet, self.allChannels))
                    self.classOne[:, 43*p+43:43*p+86, currentGroupOne-1] = nextPacketMatrics.T
            elif trigger == 2:
                currentGroupTwo += 1
                self.fid.seek(12, 1)
                all_samples = []
                for i in range(self.samples_per_packet):         
                    samples = []
                    for j in range(self.allChannels):
                        sample = read_uint16le(self.fid)
                        samples.append(sample)                
                    all_samples.append(samples)                  
                first_Packet = numpy.array(all_samples)
                firstPacketMatrics = first_Packet.reshape((self.samples_per_packet, self.allChannels))
                self.classTwo[:, 0:43, currentGroupTwo-1] = firstPacketMatrics.T
                for p in range(self.num-1):                 
                    self.fid.seek(14, 1)
                    all_samples = []
                    for i in range(self.samples_per_packet):         
                        samples = []
                        for j in range(self.allChannels):
                            sample = read_uint16le(self.fid)
                            samples.append(sample)                
                        all_samples.append(samples)
                    next_Packet = numpy.array(all_samples)
                    nextPacketMatrics = next_Packet.reshape((self.samples_per_packet, self.allChannels))
                    self.classTwo[:, 43*p+43:43*p+86, currentGroupTwo-1] = nextPacketMatrics.T
            else:
                self.fid.seek(1388, 1)
        self.fid.close()

    def offlineClass(self, path):
        self.readOffData(path)
        trainGroups = int(0.8*self.groups)
        testGroups = self.groups - trainGroups
        acc = numpy.zeros((4,100))   # need to change
        for fre in range(4):
            Wn = [self.frequency[fre][0]/(self.Fs/2), self.frequency[fre][1]/(self.Fs/2)]
            filter_b, filter_a = butter(self.filt_n, Wn, btype='band')
            Cov1 = numpy.zeros(shape=(self.DataLength, self.DataLength, self.groups))       
            Cov2 = numpy.zeros(shape=(self.DataLength, self.DataLength, self.groups))
            for i in range(self.groups):
                dataTofilter = self.classOne[self.channels, :, i]
                dataFiltered = lfilter(filter_b, filter_a, dataTofilter, axis=1)
                Dr = dataFiltered[:, self.timepoint[0]:self.timepoint[1]]
                Cov1[:, :, i] = numpy.dot(Dr, Dr.T)
                dataTofilter = self.classTwo[self.channels, :, i]
                dataFiltered = lfilter(filter_b, filter_a, dataTofilter, axis=1)
                Dr = dataFiltered[:, self.timepoint[0]:self.timepoint[1]]
                Cov2[:, :, i] = numpy.dot(Dr, Dr.T)
            for cross in range(100):
                randGroup =[i for i in range(self.groups)]
                random.shuffle(randGroup)
                R1 = numpy.zeros(shape=(self.DataLength, self.DataLength))
                R2 = numpy.zeros(shape=(self.DataLength, self.DataLength))
                for t in range(trainGroups):
                    R1 += Cov1[:, :, randGroup[t]]
                    R2 += Cov2[:, :, randGroup[t]]
                R1 = R1/numpy.trace(R1)
                R2 = R2/numpy.trace(R2)
                R3 = R1 + R2
                sigma, U0 = numpy.linalg.eig(R3)
                P = numpy.dot(numpy.diag(sigma**(-0.5)), U0.T)
                YL = numpy.dot(numpy.dot(P,R1),P.T)
                sigmaL, UL = numpy.linalg.eig(YL)
                Isorted = numpy.argsort(-sigmaL)
                F = numpy.dot(P.T, UL[:, Isorted[self.NtoLastN]])
                f = numpy.zeros(shape=(2*self.N, 1))
                f1 = numpy.zeros(shape=(2*self.N, self.groups))
                f2 = numpy.zeros(shape=(2*self.N, self.groups))
                for i in range(trainGroups):
                    for j in range(2*self.N):
                        f[j, 0] = numpy.log(numpy.dot(numpy.dot(F[:,j].reshape(1, self.DataLength),Cov1[:,:,randGroup[i]]),F[:,j]))
                    f1[:, i] = f[:, 0]
                    for j in range(2*self.N):
                        f[j, 0] = numpy.log(numpy.dot(numpy.dot(F[:,j].reshape(1, self.DataLength),Cov2[:,:,randGroup[i]]),F[:,j]))
                    f2[:, i] = f[:, 0]
                F1 = f1.T
                F2 = f2.T
                M1 = numpy.mean(F1, 0)
                M1.shape = (2*self.N, 1)
                M2 = numpy.mean(F2, 0)
                M2.shape = (2*self.N, 1)
                count1 = numpy.size(f1, 1)-1
                count2 = numpy.size(f2, 1)-1 
                w = numpy.dot(numpy.linalg.inv((count1*numpy.cov(F1.T)+count2*numpy.cov(F2.T))/(count1+count2)),(M2-M1)).reshape(1,2*self.N)
                b = -numpy.dot(w,M1+M2)/2
                TypeOneSign = numpy.dot(w, M1)+b
                right = 0
                for i in range(trainGroups, self.groups):
                    for j in range(2*self.N):                        
                        f[j, 0] = numpy.log(numpy.dot(numpy.dot(F[:,j].reshape(1, self.DataLength),Cov1[:,:,randGroup[i]]),F[:,j]))
                    y = numpy.dot(w, f)+b
                    if y*TypeOneSign >= 0:
                        right +=1 
                    for j in range(2*self.N):                        
                        f[j, 0] = numpy.log(numpy.dot(numpy.dot(F[:,j].reshape(1, self.DataLength),Cov2[:,:,randGroup[i]]),F[:,j]))
                    y = numpy.dot(w, f)+b
                    if y*TypeOneSign <= 0:
                        right +=1
                acc[fre, cross] = right/(2*testGroups)
        meanAcc = numpy.mean(acc, axis=1)
        meanaccList = meanAcc.tolist()
        frequencyIndex = meanaccList.index(max(meanaccList))
        return meanaccList, frequencyIndex