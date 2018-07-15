# -*- coding: utf-8 -*-
# Developed By QinZhun on 12/6/2018
# pip install 插件名字 -i https://pypi.tuna.tsinghua.edu.cn/simple
# http://pypi.douban.com/simple/

# 功能：界面提示+离线采集数据(训练参数按键P) + 在线解码 (标签为脉冲，标志动作开始)
# 修改：训练参数 + 在线解码 + 字体显示位置优化
# Developped by QinZhun on 15/6/2018

import random
import sys
import time
import argparse
import datetime
import io
import os
import queue
import socket
import struct
import threading
import matlab
import matlab.engine

from PyQt5.QtCore import QBasicTimer, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QPainter
from PyQt5.QtWidgets import (QApplication, QDesktopWidget, QFrame, QMainWindow,
                             QMessageBox)

# if platform.system() == 'Darwin':  # OSX

# Global queues
queues = []  # Per-thread working queue.
message_queue = queue.Queue()  # construct a queue for printing messages
Data_queue = queue.Queue()
run_flag = True
symbol = -1  # 全局标志位


class mainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):

        self.tboard = Board(self)
        self.setCentralWidget(self.tboard)
        self.tboard.commandStart.connect(self.tboard.start)
        self.tboard.paramTrain.connect(self.tboard.param)
        #  self.tboard.start()

        screen = QDesktopWidget().screenGeometry()
        self.resize(screen.width() - 10, screen.height() - 20)  # 全屏显示
        self.center()
        self.setWindowTitle('BCIVision')
        self.setObjectName("MainWindow")
        self.setStyleSheet("#MainWindow{background-color: black}")  # 设置背景为黑色
        self.show()

    # 界面居中显示
    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)

    # 关屏提示
    def closeEvent(self, event):

        reply = QMessageBox.question(self, 'Message', "Are you sure to quit?",
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


class Board(QFrame):
    commandStart = pyqtSignal()
    paramTrain = pyqtSignal()

    numTestTrials = 40
    #  Groups = [1,1]

    speed = 500  # 计时器计时间隔，后面需要验证是否产生累积误差
    widthRatioRectangle = 0.1
    heightRatioRectangle = 0.1  # 矩形相对于屏幕的尺寸
    placeRatioRectangleW = 0.25  # 矩形相对于屏幕的位置
    placeRatioRectangleH = 0.5

    sizeRatioCross = 0.05  # 十字架相对于屏幕的尺寸
    placeRatioCrossH = 0.5  # 十字架相对于屏幕的位置   注意：参考坐标系原点在屏幕左上方
    placeRatioCrossW = 0.5

    def __init__(self, parent):
        super().__init__(parent)

        self.initBoard()

    def initBoard(self):
        self.sign = -1  # 标志位-1代表实验未开始；0代表开始的空白；1和2代表左右红色矩形块出现；3代表只有白色十字架；4表示大段空白休息；5表示训练结束；6表示居中显示文字；8表示参数训练完成；9给出识别结果；10表示测试结束
        self.timeComulation = 0  # 计时器响应次数。如果调整时间间隔、调整计时器最小时间，程序中所有判断该值的地方，均需要调整
        self.finishedTrials = 0  # 已完成trials数量-1
        self.finishedTestTrials = 0

        a = [1] * 5
        b = [2] * 5
        self.trials = a + b
        self.numTrainTrials = len(self.trials)
        random.shuffle(self.trials)  # 生成随机数，随机产生左右手运动

        self.timer = QBasicTimer()  # 训练组定时器
        self.timerTest = QBasicTimer()  # 测试组计时器

        self.isStarted = False  # 由按钮点击开始
        self.setFocusPolicy(Qt.StrongFocus)
        #   self.trainGroupsFinished = 0
        #   self.testGroupsFinished = 0
        self.Groups = 0

    # 点击按钮，程序开始运行
    def start(self):
        if self.Groups == 0:
            self.isStarted = True
            self.timer.start(Board.speed, self)
            self.Groups += 1
        elif self.Groups == 1:
            self.isStarted = True
            self.timerTest.start(Board.speed, self)

    # 训练参数
    def param(self):
        print("Start Train Params")  # start matlab engine
        window = eng.paramTrain(filename, self.numTrainTrials / 2)
        print("Finish Train Params")

    #    symbol = 8   # 代表训练参数完成

    # 定时器事件
    def timerEvent(self, event):
        if event.timerId() == self.timer.timerId():
            if self.finishedTrials == 0 and self.timeComulation == 0:
                self.sign = 0
            self.timeComulation += 1  # 计时器响应次数

            if self.timeComulation == 24:  # 时间=24*500ms，下面类似
                self.timeComulation = 0
                if self.finishedTrials == self.numTrainTrials:  # 单组实验结束
                    self.timer.stop()
                    self.sign = 5

            elif self.timeComulation == 4:
                self.sign = 3

            elif self.timeComulation == 6:
                if self.trials[self.finishedTrials] == 1:  # 随机产生左右手运动
                    self.sign = 1
                else:
                    self.sign = 2
                self.finishedTrials += 1

            elif self.timeComulation == 8:  # 显示白色十字架
                self.sign = 3

            elif self.timeComulation == 14:
                self.sign = 4

            global symbol
            symbol = self.sign
            #    print('sign: ' + str(self.sign))
            self.update()

        elif event.timerId() == self.timerTest.timerId():
            if self.finishedTestTrials == 0 and self.timeComulation == 0:
                self.sign = 0
            self.timeComulation += 1  # 计时器响应次数

            if self.timeComulation == 24:  # 时间=24*500ms，下面类似
                self.timeComulation = 0
                if self.finishedTestTrials == Board.numTestTrials:  # 单组测试结束
                    self.timerTest.stop()
                    self.sign = 10

            elif self.timeComulation == 4:
                self.sign = 3

            elif self.timeComulation == 6:  # 显示提示文字
                self.sign = 6
                self.finishedTestTrials += 1

            elif self.timeComulation == 14:
                self.sign = 4

            elif self.timeComulation == 16:
                self.sign = 9

            elif self.timeComulation == 23:
                self.sign = 4

            symbol = self.sign
            self.update()

        else:
            super(Board, self).timerEvent(event)

    # 改变窗口尺寸时，自动调用该函数。通过读取窗口尺寸值，保证显示的图形不变形
    def resizeEvent(self, e):
        self.widthWindow = e.size().width()  # 窗口宽度
        self.heightWindow = e.size().height()  # 窗口高度
        self.update()

    # 响应按键事件，需要补充其他按键值及需要-------------------------------------------------------------------------------------------------------------------
    def keyPressEvent(self, event):
        key = event.key()

        if key == Qt.Key_Space:
            self.timer.stop()

        elif key == Qt.Key_S:
            self.commandStart.emit()

        elif key == Qt.Key_P:
            self.paramTrain.emit()

        else:
            super(Board, self).keyPressEvent(event)

    # 调用update()函数时，自动调用该函数。所有绘图操作均在此处进行
    def paintEvent(self, event):

        if self.sign == -1:
            painter = QPainter(self)
            painter.begin(self)
            self.drawText(painter, 0.5, 0.5, 30, "实验马上开始-请做好准备")
            painter.end()

        elif self.sign == 0 or self.sign == 4:
            return

        elif self.sign == 1:
            painter = QPainter(self)
            painter.begin(self)
            # self.drawRectangles(painter, Board.placeRatioRectangleW, Board.placeRatioRectangleH, self.widthRatioRectangle,self.heightRatioRectangle)   
            self.drawText(painter, 0.25, 0.5, 30, "左手握拳")
            painter.end()

        elif self.sign == 2:
            painter = QPainter(self)
            painter.begin(self)
            # self.drawRectangles(painter, 1 - Board.placeRatioRectangleW, Board.placeRatioRectangleH, self.widthRatioRectangle, self.heightRatioRectangle)
            self.drawText(painter, 0.5, 0.5, 30, "左手休息")
            painter.end()

        elif self.sign == 3:
            painter = QPainter(self)
            painter.begin(self)
            self.drawCrossRoad(painter, Board.placeRatioCrossW,
                               Board.placeRatioCrossH, Board.sizeRatioCross)
            painter.end()

        elif self.sign == 5 or self.sign == 10:
            painter = QPainter(self)
            painter.begin(self)
            self.drawText(painter, 0.5, 0.5, 30, "本组实验结束-您辛苦啦")
            painter.end()

        elif self.sign == 6:
            painter = QPainter(self)
            painter.begin(self)
            self.drawText(painter, 0.5, 0.5, 30, "请任意选择握拳或者保持休息")
            painter.end()

        elif self.sign == 9:
            painter = QPainter(self)
            painter.begin(self)
            if feed == 1.5:
                self.drawText(painter, 0.5, 0.2, 30, "您被识别的动作为握拳")
            elif feed == 0.5:
                self.drawText(painter, 0.5, 0.2, 30, "您被识别的动作为休息")
            painter.end()

    # 绘制矩形块函数。参数x表示矩形块中心相对于窗口的位置，如0.25表示矩形块出现在窗口左侧25%的位置；y相对于窗口上侧；
    # w表示矩形块宽度相对于窗口宽度比值；h表示矩形块高度相对于窗口高度比值；
    def drawRectangles(self, painter, x, y, w, h):

        self.widthPlaceRectangle = w * self.widthWindow
        self.heightPlaceRectangle = h * self.heightWindow
        recX = x * self.widthWindow - 0.5 * self.widthPlaceRectangle
        recY = y * self.heightWindow - 0.5 * self.heightPlaceRectangle
        color = QColor(Qt.red)
        painter.fillRect(recX, recY, self.widthPlaceRectangle,
                         self.heightPlaceRectangle, color)

    # 绘制十字架函数。参数x表示十字架中心相对于窗口的位置，如0.25表示十字架出现在窗口左侧25%的位置；y相对于窗口上侧；
    # Cross表示十字架最长边相对于窗口高度比值（默认屏幕为横屏，宽>高）
    def drawCrossRoad(self, painter, x, y, Cross):
        color = QColor(Qt.white)
        sizeCross = Cross * self.heightWindow
        wid = sizeCross * 0.25
        hei = sizeCross * 1
        painter.fillRect(x * self.widthWindow - 0.5 * wid,
                         y * self.heightWindow - 0.5 * hei, wid, hei, color)
        painter.fillRect(x * self.widthWindow - 0.5 * hei,
                         y * self.heightWindow - 0.5 * wid, hei, wid, color)

    # 绘制文字。可设置 文字相对位置、文字大小、文字内容
    def drawText(self, painter, x, y, size, textString):
        painter.setPen(QColor(0, 160, 230))
        font = QFont()
        font.setFamily("Microsoft YaHei")
        font.setPointSize(size)
        painter.setFont(font)
        halfLengthText = len(textString) / 2
        painter.drawText(x * self.widthWindow - halfLengthText * size * 1.2,
                         y * self.heightWindow, textString)


# class used inside "JagaMultiDisplay" for threading data stream
class CaptureThread(threading.Thread):
    def __init__(self, bind_port, length, label, data_dir, file_name, queue_length):
        
        threading.Thread.__init__(self)

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
        self.outtfile.close()

    def run(self):
        """
        connects to the IP client "JAGA" and continuously receives data
        packets via the UDP framework (through the python "socket" class)

        If we are only streaming to disk without need for real-time control,
        it may be advantageous to use TCP vs. UDP data streaming to minimize
        packet drop / reordering. - JMS
        """

        # Initiate the socket to connect to client JAGA
        self.sock = socket.socket(
            type=socket.SOCK_DGRAM)  # DGRAM = connectionless?
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('0.0.0.0', self.bind_port))

        # print the port number and generate a file name with the date-time appended
        message_queue.put('Listening to port {}\n'.format(self.bind_port))
        global filename
        filename = self.generate_filename()
        message_queue.put('Writing to file {}\n'.format(filename))
        self.outtfile = open(filename, 'wb')

        # packets_left = 0
        formsymbol = -1
        currentsymbol = -1
        trigger = 0
        llen = 0
        testGroupsStarted = False
        testGroupsStartedTimes = 0
        #  classifyThreadstarted = 0

        while run_flag:
            if symbol == 5 and testGroupsStartedTimes == 0:
                self.outtfile.close()
                testGroupsStarted = True
                testGroupsStartedTimes = 1
                #   if symbol == 8 and classifyThreadstarted == 0:
                #  classifyThreadstarted = 1
                self.classify_thread = ClassifyThread()
                self.classify_thread.start()

            if testGroupsStarted is False:
                #    start=time.time()
                currentsymbol = symbol
                if formsymbol != currentsymbol and currentsymbol == 1:
                    trigger = 1
                    llen = 0
                    print(trigger)
                elif formsymbol != currentsymbol and currentsymbol == 2:
                    trigger = 2
                    llen = 0
                    print(trigger)
                else:
                    trigger = 0
                    llen+=1
                    # print(trigger)

                formsymbol = currentsymbol
                data, address = self.sock.recvfrom(self.length)
                # timestamp = time.time() # get the time-stamp of the data packet read
                self.outtfile.write(struct.pack("<h", trigger) + data)
                print(llen)
                # print("数据写入完成")

            else:
                data, address = self.sock.recvfrom(self.length)
                Data_queue.put(data)

    def generate_filename(self):
        """
        Generate the file name for the streamed data based on operating system.
        If the file name is not provided at terminal prompt, default to "jaga.dat"
        Automatically append date-time information to the file name.
        """

        if os.name == 'nt':
            return os.path.join(
                self.data_dir,
                datetime.datetime.fromtimestamp(
                    time.time()).strftime('%Y-%m-%d_%H-%M-%S_') + "{}_".format(
                        self.label) + self.file_name + '.dat')
        else:
            return os.path.join(
                self.data_dir,
                time.strftime('%Y-%m-%d_%H-%M-%S_', time.localtime()) +
                "{}_".format(self.label) + self.file_name + '.dat')


# ========================================
class MessageThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while run_flag:
            if not message_queue.empty():
                sys.stderr.write(message_queue.get() + "\n")
            time.sleep(3)


# ========================================================================================
class ClassifyThread(threading.Thread):
    def __init__(self):
        print("Initial ClassifyThread")
        threading.Thread.__init__(self)

    def run(self):

        print("Initializing Matlab Engine")  # start matlab engine
        global eng
        eng = matlab.engine.start_matlab()
        print("Initializing Complete!")

        #    filenameOnline = CaptureThread.generate_filename()
        #    self.outfileOnline = open(filenameOnline, 'wb')
        self.outtfileOnline = open('E:\Python\BCI-Vision\JAGA_data\online.dat',
                                   'wb')

        self.num = 0
        self.formsymbol = -1
        self.currentsymbol = -1
        self.trigger = 0
        self.testTrialsStart = False
        self.testTrialsContinue = False
        global feed

        while run_flag:
            #  start=time.time()

            if not Data_queue.empty():
                data = Data_queue.get()

                self.currentsymbol = symbol
                if self.formsymbol != self.currentsymbol and self.currentsymbol == 6:
                    self.testTrialsStart = True
                    print("Start A Test Trial")
                self.formsymbol = self.currentsymbol

                if self.testTrialsStart:  
                    self.testTrialsContinue = True
                    self.testTrialsStart = False
                    self.outtfileOnline.seek(0)
                    self.outtfileOnline.truncate()
                    self.num = 0

                if self.testTrialsContinue and self.num == 100:
                 #   print("开始识别ing")
                    #   self.outtfileOnline.close()
                    ifinal = self.num - 3
                 #   start = time.time()
                    feed = eng.online_LDA(ifinal)  # 修改函数
                 #   print("花费时间为："+str(time.time()-start))

                    print("识别结果为：" + str(feed))
                    #   self.outtfileOnline = open('E:\Python\BCI-Vision\JAGA_data\online.dat', 'wb')
                    self.testTrialsContinue = False
                    self.num = 0

                self.num = self.num + 1
                self.outtfileOnline.write(data)
                self.outtfileOnline.flush()
                # print(time.time()-start)


# ========================================
class JagaMultiDisplay(object):
    """Receive data from one or more JAGA devices and display."""

    def __init__(self, data_dir, file_name, num_devices, starting_port,
                 plot_memory, color_map):
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
        self.message_thread = MessageThread(
        )  # instance of the MessageThread class above
        self.message_thread.start()
        self.channels = 16  # Need a default until we've read the first packet.
        self.length = 1500  # data packet byte size?
        self.first_packet = True
        self.fh = io.BytesIO(
        )  # instance of the BytesIO class from the io package. Provides interface for buffered I/O data
        self.axes = []
        self.lines = []

    def start(self):
        """Start capturing data on the bound ports, and display."""

        # Make the output folder if it doesn't already exist
        if os.path.exists(self.data_dir):
            if not os.path.isdir(self.data_dir):
                sys.stderr.write(
                    "ERROR: Path {} exists, but is not a directory\n".format(
                        self.data_dir))
                return
        else:
            os.makedirs(self.data_dir)

        # Check the number of clients (devices) discovered over the JAGA network
        for dev in range(self.num_devices):
            sys.stderr.write("Starting capture for device {}\n".format(dev))
            queues.append(
                queue.Queue()
            )  # append a new queue instance to the "queues" list for each device

            # create an instance of the CaptureThread object to connect to this device
            self.threads.append(
                CaptureThread(
                    self.starting_port + dev,  # bind_port
                    self.length,  # length
                    dev,  # label (device number)
                    self.data_dir,  # data directory
                    self.file_name,  # file name
                    self.plot_memory))  # packets to queue

            # initiate data streaming for this device
            self.threads[dev].start()


if __name__ == '__main__':
    app = QApplication([])
    MW = mainWindow()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--starting_port',
        type=int,
        help='First port number to listen to for data.',
        default=55000)
    parser.add_argument(
        '--num_devices',
        type=int,
        help='Number of devices to listen for.',
        default=1)
    parser.add_argument(
        '--data_dir',
        type=str,
        help='Directory to write data files to.',
        default='JAGA_data')
    parser.add_argument(
        '--file_name',
        type=str,
        help='Name of file to write data into.',
        default='jaga')
    parser.add_argument(
        '--plot_memory',
        type=int,
        help=
        'Number of packets to display. More packets results in smoother but slower plotting',
        default=10)
    parser.add_argument(
        '--color_map',
        type=str,
        help=
        'Color map for drawing the data. See matplotlib documentation for details',
        default='Set2')
    args = parser.parse_args()  # parse the optionals
    md = JagaMultiDisplay(
        args.data_dir, args.file_name, args.num_devices, args.starting_port,
        args.plot_memory,
        args.color_map)  # create an instance of the main runtime class

    try:
        run_flag = True
        md.start()  # start the runtime
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        print("Received interrupt, exiting.")
        run_flag = False
