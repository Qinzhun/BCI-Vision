# -*- coding: utf-8 -*-
# Developed By QinZhun on 12/6/2018
#bbbbbbbbb

import sys, random
from PyQt5.QtWidgets import QMainWindow, QFrame, QDesktopWidget
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt, QBasicTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QFont
import time


class mainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):

        self.tboard = Board(self)
        self.setCentralWidget(self.tboard)
        self.tboard.commandStart.connect(self.tboard.start)
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

    speed = 500  # 计时器计时间隔，后面需要验证是否产生累积误差---------------------------------------------------------------------
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
        self.sign = -1  # 标志位-0代表空白；1和2代表左右红色矩形块出现；3代表只有白色十字架
        self.timeComulation = 0  # 计时器响应次数。如果调整时间间隔、调整计时器最小时间，程序中所有判断该值的地方，均需要调整
        self.finishedTrials = 0  # 已完成trials数量-1
        a = [1] * 10
        b = [2] * 10
        self.trials = a + b
        random.shuffle(self.trials)  # 生成随机数，随机产生左右手运动

        self.timer = QBasicTimer()  # 定时器
        self.isStarted = False  # 由按钮点击开始
        self.setFocusPolicy(Qt.StrongFocus)

    # 点击按钮，程序开始运行
    def start(self):
        self.isStarted = True
        self.timer.start(Board.speed, self)

    # 定时器事件
    def timerEvent(self, event):
        if event.timerId() == self.timer.timerId():
            if self.finishedTrials == 0 and self.timeComulation == 0:
                self.sign = 0 
            self.timeComulation += 1  # 计时器响应次数

            if self.timeComulation == 24:  # 时间=24*500ms，下面类似
                self.timeComulation = 0
                if self.finishedTrials == 20:  # 单组实验结束，此处需添加文字提示
                    self.timer.stop()
                    self.sign = 5


            elif self.timeComulation == 4:
                if self.trials[self.finishedTrials] == 1:  # 随机产生左右手运动
                    self.sign = 1
                else:
                    self.sign = 2
                self.finishedTrials += 1

            elif self.timeComulation == 6:  # 显示白色十字架
                self.sign = 3

            elif self.timeComulation == 12:
                self.sign = 0

            self.update()

        else:
            super(Board, self).timerEvent(event)

    # 改变窗口尺寸时，自动调用该函数。通过读取窗口尺寸值，保证显示的图形不变形
    def resizeEvent(self, e):
        self.widthWindow = e.size().width()  # 窗口宽度
        self.heightWindow = e.size().height()  # 窗口高度

    # 响应按键事件，需要补充其他按键值及需要-------------------------------------------------------------------------------------------------------------------
    def keyPressEvent(self, event):
        key = event.key()

        if key == Qt.Key_Space:
            self.timer.stop()

        elif key == Qt.Key_S:
            self.commandStart.emit()
        else:
            super(Board, self).keyPressEvent(event)

    # 调用update()函数时，自动调用该函数。所有绘图操作均在此处进行
    def paintEvent(self, event):

        if self.sign == -1:
            painter = QPainter(self)
            painter.begin(self)
            self.drawText(painter, 0.25, 0.5, 30, "实验马上开始，请做好准备--点击按键S开始实验")
        #    self.drawText(painter, 0.29, 0.55, 30, "点击按键 S 开始实验")
            painter.end()
            
        elif self.sign == 0:
            return
            
        elif self.sign == 1:
            painter = QPainter(self)
            painter.begin(self)
            self.drawRectangles(painter, Board.placeRatioRectangleW,
                                Board.placeRatioRectangleH,
                                self.widthRatioRectangle,
                                self.heightRatioRectangle)
            painter.end()

        elif self.sign == 2:
            painter = QPainter(self)
            painter.begin(self)
            self.drawRectangles(painter, 1 - Board.placeRatioRectangleW,
                                Board.placeRatioRectangleH,
                                self.widthRatioRectangle,
                                self.heightRatioRectangle)
            painter.end()

        elif self.sign == 3:
            painter = QPainter(self)
            painter.begin(self)
            self.drawCrossRoad(painter, Board.placeRatioCrossW,
                               Board.placeRatioCrossH, Board.sizeRatioCross)
            painter.end()
        
        elif self.sign == 5:
            painter = QPainter(self)
            painter.begin(self)
            self.drawText(painter, 0.3, 0.5, 30, "本组实验结束，您辛苦啦")
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
        painter.drawText(x*self.widthWindow, y*self.heightWindow, textString)




if __name__ == '__main__':
    app = QApplication([])
    MW = mainWindow()
    sys.exit(app.exec_())