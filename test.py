import trainParams
import onlineClass
import offlineParamOptimization
# test test

channel = [1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
# frequency = [8, 30]
num = 95
groups = 15

offline = offlineParamOptimization.offlineParamOpt(channel, num, groups)

meanacc = offline.offlineClass('./JAGA_data/2018-06-29_21-09-40_0_jaga_xuyao.dat')
meanaccList = meanacc.tolist()
frequencyIndex = meanaccList.index(max(meanaccList))
print(frequencyIndex)

# train = trainParams.trainParams(channel, [499, 3800], frequency, num, groups)
# F,w,b,Typeone= train.paramsTrain('./JAGA_data/2018-07-01_19-07-09_0_jaga.dat')
# para = [F,w,b,Typeone]
# onlineclass = onlineClass.ReadData(channel, [499,3800], frequency, para, 98)
# feed = onlineclass.onlineClassify()


nameSubject = "QinZhun"

fileName = []
file = []
for o in range(4):
    fileName.append( "./JAGA_data/"+ nameSubject + "_online_Group%d"%(o)+".dat")
    file.append("file%d"%(o))

for o in range(4):
    file[o] = open(fileName[o], 'wb')
