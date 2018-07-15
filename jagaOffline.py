# pip install 插件名字 -i https://pypi.tuna.tsinghua.edu.cn/simple
# http://pypi.douban.com/simple/ 


# !env python
import argparse
import datetime
import io
import os
import queue
import socket
import struct
import sys
import threading
import time

# if platform.system() == 'Darwin':  # OSX

# Global queues
queues = []  # Per-thread working queue.
message_queue = queue.Queue()  # construct a queue object simply for printing messages 
run_flag = True  # <-- might be more efficient to avoid global variable?


# class used inside "JagaMultiDisplay" for threading data stream
class CaptureThread(threading.Thread):

  def __init__(self, bind_port, length, label, data_dir, file_name, queue_length):
    threading.Thread.__init__(self)         # are we appending an instance of the threading class here?
    self.bind_port = bind_port
    self.length = length
    self.label = label
    self.packet_count = 0
    self.data_dir = data_dir
    self.file_name = file_name
    self.queue_length = queue_length
    self.num = 0
  
  # closes the output file to stop the writing process
  def __del__(self):
 
    message_queue.put("Received {} packets from device {}.\n".format(
        self.packet_count, self.label))
    self.outfile.close()    

  def run(self):
    """
    connects to the IP client "JAGA" and continuously receives data
    packets via the UDP framework (through the python "socket" class)

    If we are only streaming to disk without need for real-time control,
    it may be advantageous to use TCP vs. UDP data streaming to minimize
    packet drop / reordering. - JMS
    """

    # Initiate the socket to connect to client JAGA 
    self.sock = socket.socket(type=socket.SOCK_DGRAM) # DGRAM = connectionless?
    self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.sock.bind(('0.0.0.0', self.bind_port))

    # print the port number and generate a file name with the date-time appended
    message_queue.put('Listening to port {}\n'.format(self.bind_port))
    filename = self.generate_filename()
    message_queue.put('Writing to file {}\n'.format(filename))
    self.outtfile = open(filename, 'wb') #  open the file for writing binary data ("wb") since not writing text files
    # self.outtfile = open('E:\Matlab\Actual_Rest_For_Classification\Data_four_seconds\OFFLINE.dat','wb')

    packets_left = 0
    
    while run_flag:
  #    print("ppppppppppppppppp")
      print('symbol: ' + str(main.Board.symbol))

      self.num=self.num+1
      data, address = self.sock.recvfrom(self.length) # read the data packet. Could split data from here too
#      timestamp = time.time() # get the time-stamp of the data packet read
      self.outtfile.write(struct.pack("<h", main.Board.symbol) + data) # write to the output file...saves us from over-riding data
#      self.outfile.write( serial_value + data) # write to the output file...saves us from over-riding data
      self.packet_count += 1

  def generate_filename(self):
    """
    Generate the file name for the streamed data based on operating system.

    If the file name is not provided at terminal prompt, default to "jaga.dat"
    Automatically append date-time information to the file name.
    """
    if os.name == 'nt':
      return os.path.join(self.data_dir, datetime.datetime.fromtimestamp(
          time.time()).strftime('%Y-%m-%d_%H-%M-%S_') + "{}_".format(self.label)
	  + self.file_name + '.dat')
    else:
      return os.path.join(self.data_dir, time.strftime('%Y-%m-%d_%H-%M-%S_',
          time.localtime()) + "{}_".format(self.label) + self.file_name
	  + '.dat')


# ========================================
class MessageThread(threading.Thread):

  def __init__(self):
    threading.Thread.__init__(self)

  def run(self):
    while run_flag:
      if not message_queue.empty():
        sys.stderr.write(message_queue.get() + "\n") 
      time.sleep(3) # could just put the timeout into the message_que.get() method? 

# ========================================
class JagaMultiDisplay(object):
  """Receive data from one or more JAGA devices and display."""

  def __init__(self, data_dir, file_name, num_devices, starting_port, plot_memory, color_map):
    # Passed variables.
    self.num_devices = num_devices
    self.starting_port = starting_port
    self.data_dir = data_dir
    self.file_name = file_name
    self.plot_memory = plot_memory
    self.color_map = color_map

    # Internal variables.
    self.plotData = None
    self.packets_to_plot = 0
    self.threads = []
    self.message_thread = MessageThread() # instance of the MessageThread class above
    self.message_thread.start()
    self.channels = 16  # Need a default until we've read the first packet.
    self.length = 1500 # data packet byte size? 
    self.first_packet = True
    self.fh = io.BytesIO() # instance of the BytesIO class from the io package. Provides interface for buffered I/O data
    self.axes = []
    self.lines = []

  def start(self):
    """Start capturing data on the bound ports, and display."""

    # Make the output folder if it doesn't already exist
    if os.path.exists(self.data_dir):
      if not os.path.isdir(self.data_dir):
        sys.stderr.write(
            "ERROR: Path {} exists, but is not a directory\n".format(self.data_dir))
        return
    else:
      os.makedirs(self.data_dir)

    # Check the number of clients (devices) discovered over the JAGA network  
    for dev in range(self.num_devices):
      sys.stderr.write("Starting capture for device {}\n".format(dev))
      queues.append(queue.Queue()) # append a new queue instance to the "queues" list for each device
      
      # create an instance of the CaptureThread object to connect to this device 
      self.threads.append(CaptureThread(
          self.starting_port + dev,  # bind_port
          self.length,               # length
          dev,                       # label (device number)
          self.data_dir,             # data directory
          self.file_name,            # file name
          self.plot_memory))         # packets to queue
      
      # initiate data streaming for this device
      self.threads[dev].start()
