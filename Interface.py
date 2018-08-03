import sys, random
from PyQt5.QtWidgets import QMainWindow, QFrame, QDesktopWidget, QApplication, QMessageBox
from PyQt5.QtWidgets import QAction, QDialog, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout
from PyQt5.QtWidgets import QWidget, QDialogButtonBox, QCheckBox, QPushButton, QRadioButton
from PyQt5.QtWidgets import QLineEdit, QComboBox
from PyQt5.QtCore import Qt, QBasicTimer, pyqtSignal, QTimer
from PyQt5.QtGui import QPainter, QColor, QFont
import pyqtgraph as pg
import numpy as np

channels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]


class mainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        screen = QDesktopWidget().screenGeometry()
        self.resize(screen.width() - 10, screen.height() - 20)  # 全屏显示
        self.center()
        self.setWindowTitle('BCIVision')

        menubar = self.menuBar()

        fileMenu = menubar.addMenu('&File')
        toolsMenu = menubar.addMenu('&Tools')

        Channel = QAction("Channel", self)
        toolsMenu.addAction(Channel)
        Channel.triggered.connect(self.openChannelManagerDialog)

        self.labelChannel = QLabel(self)
        self.labelChannel.setText("Channels:")
        self.labelChannel.move(5, 25)
        self.labelChannel.setFont(QFont("Roman times", 10, QFont.Bold))
        channelsStr = [str(i) for i in channels]
        channelsText = " ".join(channelsStr)
        self.labelChannelDisplay = QLabel(self)
        self.labelChannelDisplay.setText(channelsText)
        self.labelChannelDisplay.move(90, 35)
        self.labelChannelDisplay.adjustSize()
        self.labelChannelDisplay.setFont(QFont("Roman times"))

        #   hlayoutchannel = QHBoxLayout()
        #   hlayoutchannel.addWidget(self.labelChannel)
        #   hlayoutchannel.addWidget(self.labelChannelDisplay)
        #   self.setLayout(hlayoutchannel)

        self.labelSubjectName = QLabel(self)
        self.labelSubjectName.setText("Subject:")
        self.labelSubjectName.setFont(QFont("Roman times", 10, QFont.Bold))
        self.nameEdit = QLineEdit(self)
        self.labelSubjectName.move(5, 60)
        self.nameEdit.move(120, 60)

        self.testGroups = QLabel(self)
        self.testGroups.setText("testGroups:")
        self.testGroups.setFont(QFont("Roman times", 10, QFont.Bold))
        self.testGroupsChoose = QComboBox(self)
        self.testGroupsChoose.addItems(["2", "3", "4"])
        self.testGroups.move(5, 100)
        self.testGroupsChoose.move(120, 100)

        self.trainTrialsNum = QLabel(self)
        self.trainTrialsNum.setText("trainTrials:")
        self.trainTrialsNum.setFont(QFont("Roman times", 10, QFont.Bold))
        self.trainTrialsNumChoose = QComboBox(self)
        self.trainTrialsNumChoose.addItems(["10", "15", "20"])
        self.trainTrialsNum.move(5, 140)
        self.trainTrialsNumChoose.move(120, 140)

        self.buttonOffline = QPushButton("Training", self)
        self.buttonOffline.setCheckable(True)
        self.buttonOffline.clicked.connect(self.training)
        self.buttonOnline = QPushButton("Online", self)
        self.buttonOnline.setCheckable(True)
        self.buttonOnline.clicked.connect(self.online)
        self.buttonOffline.move(5, 190)
        self.buttonOnline.move(120, 190)
        #####################################################
        self.signalGraphic = pg.PlotWidget(self)
        self.signalGraphic.resize(1000, 500)
        self.signalGraphic.move(400, 60)
        self.signalGraphic.setXRange(0, 500)
        self.signalGraphic.setYRange(0, 60)
        self.nPlots = 10
        self.nSamples = 500
        self.curve = []
        for i in range(self.nPlots):
            c = pg.PlotCurveItem(pen=(i, self.nPlots * 1.3))
            self.signalGraphic.addItem(c)
            c.setPos(0, i * 6)
            self.curve.append(c)
        self.data = np.random.normal(size=(self.nPlots, self.nSamples))
        self.ptr = 0
        self.count = 0

        # self.signalGraphic
        # y = np.random.normal(size = 1000)
        # self.signalGraphic.plot(y)
        # self.signalGraphic

        #grid = QGridLayout()
        #grid.setSpacing(100)
        #grid.addWidget(self.labelChannel, 1, 0)
        #grid.addWidget(self.labelChannelDisplay, 1, 1)
        #grid.addWidget(self.labelSubjectName, 2, 0)
        #grid.addWidget(self.nameEdit, 2, 1)
        #grid.addWidget(self.testGroups, 3, 0)
        #grid.addWidget(self.testGroupsChoose, 3, 1)
        #self.setLayout(grid)

        self.show()

    def training(self):
        # testGroups = int(self.testGroupsChoose.currentText())
        # trainTrialsNum = int(self.trainTrialsNumChoose.currentText())
        print("training")
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(100)

    #  print(testGroups)
    #  print(trainTrialsNum)

    def online(self):
        print("online")

    def update(self):
       # print("update")
        self.count += 1
        self.data[:, :-1] = self.data[:, 1:]
        self.data[:, -1] = np.random.normal(size=(self.nPlots))

        for i in range(self.nPlots):
            self.curve[i].setData(self.data[i])
        # self.ptr += self.nPlots

    # Channel manager Dialog
    def openChannelManagerDialog(self):
        dialog = channelManagerDialog(self)
        dialog.Signal_Channels.connect(self.channelsDisplay)
        dialog.show()

    def channelsDisplay(self):
        channelsStr = [str(i) for i in channels]
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
        global channels
        channels = self.channel
        self.Signal_Channels.emit()
        #  print(channels)
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    MW = mainWindow()
    sys.exit(app.exec_())