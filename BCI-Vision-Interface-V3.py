# interface
# Developped by QinZhun on 7.31/2018

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
import pyqtgraph as pg
import numpy
from struct_methods import read_uint16le
import onlineClass
import trainParams
import offlineParamOptimization
from PyQt5.QtWidgets import QMainWindow, QFrame, QDesktopWidget, QApplication, QMessageBox
from PyQt5.QtWidgets import QAction, QDialog, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout
from PyQt5.QtWidgets import QWidget, QDialogButtonBox, QCheckBox, QPushButton, QRadioButton
from PyQt5.QtWidgets import QLineEdit, QComboBox
from PyQt5.QtCore import Qt, QBasicTimer, pyqtSignal, QTimer
from PyQt5.QtGui import QPainter, QColor, QFont

# if platform.system() == 'Darwin':  # OSX

queues = []  # Per-thread working queue.
message_queue = queue.Queue()  # construct a queue for printing messages
Data_queue = queue.Queue()
run_flag = True
symbol = -1  # 全局标志位
frequency = [[8, 30], [8, 13], [13, 20], [20, 30]]
freindex = 0
timePoint = [999, 4000]
timeNum = 96
groups = 15
TrainTestRuns = [1, 3]
params = []
OnlineGroups = 0
TestTrialsNum = 20
nameSubject = ""
channel = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
allGroups = 0
onlineStarted = 0
offlineStarted = 0
dataDisplay = numpy.zeros(shape=(16, 5160))
currentPackets = 0


class mainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        screen = QDesktopWidget().screenGeometry()
        self.resize(screen.width() - 10, screen.height() - 20)  # 全屏显示
        self.center()
        self.setWindowTitle('BCIVision')
        self.yRange = 5

        menubar = self.menuBar()

        fileMenu = menubar.addMenu('&File')
        toolsMenu = menubar.addMenu('&Tools')

        Channel = QAction("Channel", self)
        toolsMenu.addAction(Channel)
        Channel.triggered.connect(self.openChannelManagerDialog)

        self.labelChannel = QLabel(self)
        self.labelChannel.setText("Channels:")
        # self.labelChannel.move(5, 25)
        self.labelChannel.setFont(QFont("Roman times", 10, QFont.Bold))
        channelsStr = [str(i) for i in channel]
        channelsText = " ".join(channelsStr)
        self.labelChannelDisplay = QLabel(self)
        self.labelChannelDisplay.setText(channelsText)
        # self.labelChannelDisplay.move(90, 35)
        # self.labelChannelDisplay.adjustSize()
        self.labelChannelDisplay.setFont(QFont("Roman times"))

        #   hlayoutchannel = QHBoxLayout()
        #   hlayoutchannel.addWidget(self.labelChannel)
        #   hlayoutchannel.addWidget(self.labelChannelDisplay)
        #   self.setLayout(hlayoutchannel)

        self.labelSubjectName = QLabel(self)
        self.labelSubjectName.setText("Subject:")
        self.labelSubjectName.setFont(QFont("Roman times", 10, QFont.Bold))
        self.nameEdit = QLineEdit(self)
        #self.labelSubjectName.move(5, 60)
        #self.nameEdit.move(120, 60)

        self.testGroups = QLabel(self)
        self.testGroups.setText("testGroups:")
        self.testGroups.setFont(QFont("Roman times", 10, QFont.Bold))
        self.testGroupsChoose = QComboBox(self)
        self.testGroupsChoose.addItems(["2", "3", "4"])
        #self.testGroups.move(5, 100)
        #self.testGroupsChoose.move(120, 100)

        self.trainTrialsNum = QLabel(self)
        self.trainTrialsNum.setText("trainTrials:")
        self.trainTrialsNum.setFont(QFont("Roman times", 10, QFont.Bold))
        self.trainTrialsNumChoose = QComboBox(self)
        self.trainTrialsNumChoose.addItems(["5", "10", "15", "20"])
        #self.trainTrialsNum.move(5, 140)
        #self.trainTrialsNumChoose.move(120, 140)

        self.buttonOffline = QPushButton("Training", self)
        self.buttonOffline.setCheckable(True)
        self.buttonOffline.clicked.connect(self.training)
        self.buttonOnline = QPushButton("Online", self)
        self.buttonOnline.setCheckable(True)
        self.buttonOnline.clicked.connect(self.online)
        #self.buttonOffline.move(5, 190)
        #self.buttonOnline.move(120, 190)

        self.signalGraphic = pg.PlotWidget(self)
        self.signalGraphic.setTitle("All Channels")
        #self.signalGraphic.resize(1200, 800)
        #self.signalGraphic.move(400, 60)
        self.signalGraphic.setXRange(0, 5200)
        self.signalGraphic.setYRange(0, 16 * self.yRange)

        self.labelChannel.setFixedHeight(10)
        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(self.labelChannel, 1, 0)
        grid.addWidget(self.labelChannelDisplay, 1, 1)
        grid.addWidget(self.labelSubjectName, 2, 0)
        grid.addWidget(self.nameEdit, 2, 1)
        grid.addWidget(self.testGroups, 3, 0)
        grid.addWidget(self.testGroupsChoose, 3, 1)
        grid.addWidget(self.trainTrialsNum, 4, 0)
        grid.addWidget(self.trainTrialsNumChoose, 4, 1)
        grid.addWidget(self.buttonOffline, 5, 0)
        grid.addWidget(self.buttonOnline, 5, 1)
        grid.addWidget(self.signalGraphic, 1, 2, 8, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(2, 8)

        layout_widget = QWidget()
        layout_widget.setLayout(grid)
        self.setCentralWidget(layout_widget)

        self.nPlots = 16
        # self.nSamples = 500
        self.curve = []
        for i in range(self.nPlots):
            c = pg.PlotCurveItem(pen=(i, self.nPlots * 1.3))
            self.signalGraphic.addItem(c)
            c.setPos(0, i * self.yRange)
            self.curve.append(c)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(43)
        self.show()

        #  self.data = numpy.random.normal(size=(self.nPlots, self.nSamples))
        #  self.ptr = 0
        #  self.count = 0
        #grid = QGridLayout()
        #grid.setSpacing(100)
        #grid.addWidget(self.labelChannel, 1, 0)
        #grid.addWidget(self.labelChannelDisplay, 1, 1)
        #grid.addWidget(self.labelSubjectName, 2, 0)
        #grid.addWidget(self.nameEdit, 2, 1)
        #grid.addWidget(self.testGroups, 3, 0)
        #grid.addWidget(self.testGroupsChoose, 3, 1)
        #self.setLayout(grid)

    def training(self):
        testGroups = int(self.testGroupsChoose.currentText())
        trainTrialsNum = int(self.trainTrialsNumChoose.currentText())
        global TrainTestRuns
        TrainTestRuns[1] = testGroups
        global groups
        groups = trainTrialsNum
        # print(groups)
        global allGroups
        allGroups = 0
        global offlineStarted
        offlineStarted = 1
        self.experRemind = experiment()

    #   print(testGroups)
    #   print(trainTrialsNum)

    def online(self):
        global allGroups
        allGroups = 1
        global nameSubject
        nameSubject = self.nameEdit.text()
        global onlineStarted
        onlineStarted = 1
        # print(nameSubject)
        self.experRemindOnline = experiment()

    def update(self):
        #    print("update")
        #    self.count += 1
        #    self.data[:, :-1] = self.data[:, 1:]
        #    self.data[:, -1] = numpy.random.normal(size=(self.nPlots))
        self.signalGraphic.setYRange(0, 16 * self.yRange)
        for i in range(self.nPlots):
            self.curve[i].setPos(0, i * self.yRange)
            self.curve[i].setData(dataDisplay[i])

    # Channel manager Dialog
    def openChannelManagerDialog(self):
        dialog = channelManagerDialog(self)
        dialog.Signal_Channels.connect(self.channelsDisplay)
        dialog.show()

    def channelsDisplay(self):
        channelsStr = [str(i) for i in channel]
        channelsText = " ".join(channelsStr)
        self.labelChannelDisplay.setText(channelsText)

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

    def keyPressEvent(self, event):
        key = event.key()

        if key == Qt.Key_U:
            print("UUU")
            self.yRange = self.yRange / 2

        elif key == Qt.Key_D:
            self.yRange = self.yRange * 2

        else:
            super(Board, self).keyPressEvent(event)


class experiment(QMainWindow):
    def __init__(self):
        super().__init__()
        print(2000)
        self.initUI()

    def initUI(self):
        self.tboard = Board(self)
        self.setCentralWidget(self.tboard)
        self.tboard.commandStart.connect(self.tboard.start)
        self.tboard.paramTrain.connect(self.tboard.param)
        # print(11)
        screen = QDesktopWidget().screenGeometry()
        self.resize(screen.width() - 10, screen.height() - 20)  # 全屏显示
        self.center()
        self.setWindowTitle('BCIVision')
        self.setObjectName("MainWindow")
        self.setStyleSheet("#MainWindow{background-color: black}")  # 设置背景为黑色
        self.show()

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)

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

    numTestTrials = TestTrialsNum

    speed = 500  # 计时器计时间隔，后面需要验证是否产生累积误差

    sizeRatioCross = 0.1  # 十字架相对于屏幕的尺寸
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

        a = [1] * groups
        b = [2] * groups
        self.trials = a + b
        self.numTrainTrials = len(self.trials)
        random.shuffle(self.trials)  # 生成随机数，随机产生左右手运动

        self.timer = QBasicTimer()  # 训练组定时器
        self.timerTest = QBasicTimer()  # 测试组计时器

        self.isStarted = False  # 由按钮点击开始
        self.setFocusPolicy(Qt.StrongFocus)
        #   self.trainGroupsFinished = 0
        #   self.testGroupsFinished = 0
        # self.Groups = 0

    # 点击按钮，程序开始运行
    def start(self):
        global OnlineGroups
        global allGroups
        if allGroups == 0:
            self.isStarted = True
            self.timer.start(Board.speed, self)
        elif allGroups != TrainTestRuns[1] + 1:
            self.isStarted = True
            OnlineGroups = allGroups - 1
            allGroups += 1
            self.timerTest.start(Board.speed, self)

    # 训练参数
    def param(self):
        train = trainParams.trainParams(channel, timePoint,
                                        frequency[freindex], timeNum, groups)
        train.paramsTrain(filename)
        print("Finish training params")

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
                    self.finishedTestTrials = 0
                    self.timerTest.stop()
                    self.sign = 10

            elif self.timeComulation == 4:
                self.sign = 3

            elif self.timeComulation == 6:  # 显示提示文字
                self.sign = 6
                self.finishedTestTrials += 1

            elif self.timeComulation == 14:
                self.sign = 4

            elif self.timeComulation == 17:
                self.sign = 9  # 9

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
        self.textSize = self.heightWindow / 750 * 30
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
            self.drawText(painter, 0.5, 0.5, self.textSize, "实验马上开始-请做好准备")
            painter.end()

        elif self.sign == 0 or self.sign == 4:
            return

        elif self.sign == 1:
            painter = QPainter(self)
            painter.begin(self)
            # self.drawRectangles(painter, Board.placeRatioRectangleW, Board.placeRatioRectangleH, self.widthRatioRectangle,self.heightRatioRectangle)
            self.drawText(painter, 0.75, 0.5, self.textSize, "右手握拳")
            painter.end()

        elif self.sign == 2:
            painter = QPainter(self)
            painter.begin(self)
            # self.drawRectangles(painter, 1 - Board.placeRatioRectangleW, Board.placeRatioRectangleH, self.widthRatioRectangle, self.heightRatioRectangle)
            self.drawText(painter, 0.5, 0.5, self.textSize, "右手休息")
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
            self.drawText(painter, 0.5, 0.5, self.textSize, "本组实验结束-您辛苦啦")
            painter.end()

        elif self.sign == 6:
            painter = QPainter(self)
            painter.begin(self)
            self.drawText(painter, 0.5, 0.5, self.textSize, "请任意选择握拳或者保持休息")
            painter.end()

        elif self.sign == 9:
            painter = QPainter(self)
            painter.begin(self)
            if feed == 1.5:
                self.drawText(painter, 0.5, 0.2, self.textSize, "您被识别的动作为握拳")
            elif feed == 0.5:
                self.drawText(painter, 0.5, 0.2, self.textSize, "您被识别的动作为休息")
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
    def __init__(self, bind_port, length, label, data_dir, file_name,
                 queue_length):

        threading.Thread.__init__(self)

        self.bind_port = bind_port
        self.length = length
        self.label = label
        self.packet_count = 0
        self.data_dir = data_dir
        self.file_name = file_name
        self.queue_length = queue_length
        self.num = 0
        self.fh = io.BytesIO()
        self.samples_per_packet = 43
        self.allChannels = 16

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
        testGroupsStarted = 0
        testGroupsStartedTimes = 0
        global offlineStarted
        global onlineStarted

        #  classifyThreadstarted = 0

        while run_flag:
            # print("run_flag")

            if offlineStarted == 1:
                print("OFFLINESTARTEd")
                offline = offlineParamOptimization.offlineParamOpt(
                    channel, timeNum, groups)
                print("离线初始化完成")
                offlineStarted = 0

            if symbol == 5 and testGroupsStartedTimes == 0:
                self.outtfile.close()
                testGroupsStarted = 1
                testGroupsStartedTimes = 1
                global freindex
                meanacc, freindex = offline.offlineClass(filename)
                print("meanacc=", meanacc)
                print("freindex=", freindex)
                print("离线识别率计算")
                train = trainParams.trainParams(
                    channel, timePoint, frequency[freindex], timeNum, groups)
                train.paramsTrain(filename)
                print("Finish training params")
                # 训练参数
                #   if symbol == 8 and classifyThreadstarted == 0:
                #  classifyThreadstarted = 1

            if onlineStarted == 1:
                print("onlineStartttt")
                onlineStarted = 0
                testGroupsStarted = 2
                self.classify_thread = ClassifyThread()
                self.classify_thread.start()

            if testGroupsStarted == 0:
                #print("testGroupsStart")
                #    start=time.time()
                currentsymbol = symbol
                if formsymbol != currentsymbol and currentsymbol == 1:
                    trigger = 1
                    print(trigger)
                elif formsymbol != currentsymbol and currentsymbol == 2:
                    trigger = 2
                    print(trigger)
                else:
                    trigger = 0
                    # print(trigger)
                formsymbol = currentsymbol
                data, address = self.sock.recvfrom(self.length)
                # print("data")
                # timestamp = time.time() # get the time-stamp of the data packet read
                self.outtfile.write(struct.pack("<h", trigger) + data)
                # print("数据写入完成")

            elif testGroupsStarted == 1:
                data, address = self.sock.recvfrom(self.length)

            elif testGroupsStarted == 2:
                data, address = self.sock.recvfrom(self.length)
                Data_queue.put(data)
            self.readPacketData(data)

    def readPacketData(self, data):
        # print("readdata")
        self.fh.seek(0)
        self.fh.write(data)
        self.fh.seek(0)
        # trigger = read_uint16le(self.fh)
        self.fh.seek(12, 1)
        all_samples = []
        for i in range(self.samples_per_packet):
            samples = []
            for j in range(self.allChannels):
                sample = read_uint16le(self.fh)
                samples.append(sample)
            all_samples.append(samples)
        first_Packet = numpy.array(all_samples)
        firstPacketMatrics = first_Packet.reshape((self.samples_per_packet,
                                                   self.allChannels))
        firstPacketMatrics = (firstPacketMatrics - 32768) * 0.17 * 0.001
        global currentPackets
        currentPackets += 1
        global dataDisplay
        if currentPackets < 120:
            dataDisplay[:, 43 * currentPackets -
                        43:43 * currentPackets] = firstPacketMatrics.T
        else:
            dataDisplay[:, 0:5117] = dataDisplay[:, 43:5160]
            dataDisplay[:, 5117:5160] = firstPacketMatrics.T

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

        #  print("Initializing Matlab Engine")  # start matlab engine
        #  global eng
        #  eng = matlab.engine.start_matlab()
        #  print("Initializing Complete!")
        print("run classifyThread")

        #    filenameOnline = CaptureThread.generate_filename()
        #    self.outfileOnline = open(filenameOnline, 'wb')
        self.outtfileOnline = open('./JAGA_data/online.dat', 'wb')
        self.num = 0
        self.formsymbol = -1
        self.currentsymbol = -1
        self.trigger = 0
        self.testTrialsStart = False
        self.testTrialsContinue = False
        self.readOnlineData = onlineClass.ReadData(
            channel, timePoint, frequency[freindex], timeNum)
        global feed
        fileName = []
        fileOnline = []
        for o in range(TrainTestRuns[1]):
            fileName.append("./JAGA_data/" + nameSubject +
                            "_online_Group%d" % (o) + ".dat")
            fileOnline.append("file%d" % (o))
        for o in range(TrainTestRuns[1]):
            fileOnline[o] = open(fileName[o], 'wb')

        while run_flag:
            #  start=time.time()
            if not Data_queue.empty():
                data = Data_queue.get()
                triggerOnline = 0

                self.currentsymbol = symbol
                if self.formsymbol != self.currentsymbol and self.currentsymbol == 6:
                    self.testTrialsStart = True
                    triggerOnline = 4  # 在线数据开始标签
                    print("Start A Test Trial")
                self.formsymbol = self.currentsymbol

                if self.testTrialsStart:
                    self.testTrialsContinue = True
                    self.testTrialsStart = False
                    self.outtfileOnline.seek(0)
                    self.outtfileOnline.truncate()
                    self.num = 0

                if self.testTrialsContinue and self.num == timeNum + 1:
                    # ifinal = self.num - 3
                    # feed = eng.online_LDA(ifinal)  # 修改函数
                    # start = time.time()
                    feed = self.readOnlineData.onlineClassify()
                    # print(time.time()-start)
                    print("识别结果为：" + str(feed))
                    #   self.outtfileOnline = open('E:\Python\BCI-Vision\JAGA_data\online.dat', 'wb')
                    self.testTrialsContinue = False
                    self.num = 0

                self.num = self.num + 1
                self.outtfileOnline.write(data)
                self.outtfileOnline.flush()
                fileOnline[OnlineGroups].write(
                    struct.pack("<h", triggerOnline) + data)

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


class channelManagerDialog(QDialog):
    Signal_Channels = pyqtSignal()

    def __init__(self, parent=None):
        super(channelManagerDialog, self).__init__(parent)

        self.initUI()

    def initUI(self):
        self.setWindowTitle("ChannelManager")
        self.move(100, 0)
        self.resize(200, 600)

        wwg = QWidget(self)
        wlayout = QVBoxLayout(wwg)
        hlayout = QHBoxLayout()
        grid = QGridLayout()
        grid.setSpacing(10)

        self.label = QLabel(self)
        self.label.setText("")
        grid.addWidget(self.label, 0, 0)
        self.check = []

        self.all = QRadioButton("All")
        self.all.setChecked(True)
        self.all.toggled.connect(self.btnstate)
        grid.addWidget(self.all, 0, 1)

        for i in range(16):
            name = "Channel " + str(i + 1)
            self.label = QLabel(self)
            self.label.setText(name)
            grid.addWidget(self.label, i + 1, 0)

            self.check.append(QCheckBox("", self))
            self.check[i].setChecked(True)
            grid.addWidget(self.check[i], i + 1, 1)

        # 使用两个button(ok和cancel)分别连接accept()和reject()槽函数
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        hlayout.addWidget(buttons)

        wlayout.addLayout(grid)
        wlayout.addLayout(hlayout)

        self.setLayout(wlayout)

    def btnstate(self):
        if self.all.isChecked():
            for i in range(16):
                self.check[i].setChecked(True)
        else:
            for i in range(16):
                self.check[i].setChecked(False)

    def accept(self):
        self.channel = []
        for i in range(16):
            if self.check[i].isChecked():
                self.channel.append(i + 1)
        global channel
        channel = self.channel
        self.Signal_Channels.emit()
        #  print(channels)
        self.close()


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
