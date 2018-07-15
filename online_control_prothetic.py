


import serial,time 
t = serial.Serial('com20',115200,timeout=0.001)      # initial the serial
print("Open serial for bluetooth!")

t.write('A'.encode())
t.close()