nameSubject = "QinZhun"

fileName = []
file = []
for o in range(4):
    fileName.append( "./JAGA_data/"+ nameSubject + "_online_Group%d"%(o)+".dat")
    file.append("file%d"%(o))

for o in range(4):
    file[o] = open(fileName[o], 'wb')