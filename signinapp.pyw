from PyQt4.QtCore import *
from PyQt4.QtGui import *
import datastore
import settings
from passworddlg import PasswordDlg

class SynchronizeThread(QThread):
    finished = pyqtSignal()

    def __init__(self, datastore, parent=None):
        super().__init__(parent)
        self.datastore = datastore

    def run(self):
        self.datastore.sync()
        self.finished.emit()

class ImageButton(QAbstractButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = None
        self.id = None

    @property
    def pixmap(self):
        return self._pixmap

    @pixmap.setter
    def pixmap(self, value):
        self._pixmap = value
        self.update()

    def minimumSizeHint(self):
        return QSize(60, 100)

    def sizeHint(self):
        return QSize(60, 100)

    def paintEvent(self, event=None):
        p = QPainter(self)
        if self._pixmap is not None:
            p.drawPixmap(0, 0, self._pixmap)
            return
        p.save()
        p.fillRect(p.viewport(), Qt.white)
        p.setPen(Qt.black)
        p.drawRect(p.viewport().adjusted(0, 0, -1, -1))
        p.restore()

    def clear(self):
        self._pixmap = None
        self.id = None
        self.update()

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.datastore = datastore.DataStore()
        self.datastore.statusUpdate.connect(
                lambda s: self.statusBar().showMessage(s))
        self.ids = {} # map from id to widget displaying that id

        # Synchronizer thread
        self.syncThread = SynchronizeThread(self.datastore, parent=self)
        self.syncThread.finished.connect(self.syncDone)

        # Center widget
        center = QWidget()
        self.setCentralWidget(center)

        self.studentpics = [ImageButton() for i in range(7*4)]
        self.adultpics = [ImageButton() for i in range(3*4)]
        self.overflow = [QLabel() for i in range(20)]

        # Student photos (grid)
        studentgrid = QGridLayout()
        studentgrid.setSpacing(4)
        studentgrid.setRowStretch(5, 1) # empty row to handle stretching

        studentlabel = QLabel("Students")
        studentlabel.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        studentlabel.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        studentlabel.setObjectName("student")
        studentgrid.addWidget(studentlabel, 0, 0, 1, -1)

        for row in range(4):
            for col in range(7):
                studentgrid.addWidget(self.studentpics[row*7+col], row+1, col)

        # Adult photos (grid)
        adultgrid = QGridLayout()
        adultgrid.setSpacing(4)
        adultgrid.setRowStretch(5, 1) # empty row to handle stretching

        adultlabel = QLabel("Mentors & Parents")
        adultlabel.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        adultlabel.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        adultlabel.setObjectName("adult")
        adultgrid.addWidget(adultlabel, 0, 0, 1, -1)

        for row in range(4):
            for col in range(3):
                adultgrid.addWidget(self.adultpics[row*3+col], row+1, col)

        # Overflow (including entry text box)
        self.idedit = QLineEdit()
        self.idedit.setValidator(QIntValidator())
        self.idedit.returnPressed.connect(self.idEntered)

        overflowlayout = QVBoxLayout()
        overflowlayout.addWidget(self.idedit)
        for widget in self.overflow:
            overflowlayout.addWidget(widget)
        overflowlayout.addStretch(1)
        overflowlayout.addStrut(60)

        # Overall layout
        layout = QHBoxLayout()
        layout.addLayout(studentgrid)
        layout.addLayout(overflowlayout)
        layout.addLayout(adultgrid)

        center.setLayout(layout)

        # Create actions
        usersSignOutAllAction = self.createAction("Sign &Out All",
                tip="Sign out all users")
        usersSignOutAllAction.triggered.connect(self.signOutAll)

        usersClearAllAction = self.createAction("&Clear All",
                tip="Clear all users (no hours credit given)")
        usersClearAllAction.triggered.connect(self.clearAll)

        serverPasswordAction = self.createAction("Set &Password",
                tip="Set server password")
        serverPasswordAction.triggered.connect(self.setServerPassword)

        self.serverSyncAction = self.createAction("&Synchronize",
                tip="Synchronize with server")
        self.serverSyncAction.triggered.connect(self.sync)
        self.serverSyncAction.setEnabled(False)

        # Create menu bar
        userMenu = self.menuBar().addMenu("&Users")
        userMenu.addAction(usersSignOutAllAction)
        userMenu.addAction(usersClearAllAction)

        serverMenu = self.menuBar().addMenu("&Server")
        serverMenu.addAction(serverPasswordAction)
        serverMenu.addAction(self.serverSyncAction)

        # Status bar
        status = self.statusBar()

        self.setWindowTitle("Sign In Application")
        self.idedit.setFocus()

        # Load file
        QTimer.singleShot(0, self.datastore.load)

        for widget in self.studentpics:
            widget.clicked.connect(self.pic_clicked)
        for widget in self.adultpics:
            widget.clicked.connect(self.pic_clicked)

    def createAction(self, text, shortcut=None, icon=None, tip=None):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        return action

    def idEntered(self):
        id = int(self.idedit.text())
        self.idedit.clear()

    def signOutAll(self):
        self.datastore.signOutAll()

    def clearAll(self):
        self.datastore.clearAll()
        for widget in self.ids:
            widget.clear()
        self.ids.clear()

    def setServerPassword(self):
        form = PasswordDlg(self)
        if form.exec_():
            oldpass = settings.LOGIN_PASSWORD
            settings.LOGIN_PASSWORD = form.result()
            if not oldpass:
                self.serverSyncAction.setEnabled(True)

    def sync(self):
        self.statusBar().showMessage("Synchronizing...")
        self.serverSyncAction.setEnabled(False)
        self.syncThread.start()

    def syncDone(self):
        self.serverSyncAction.setEnabled(True)

    def pic_clicked(self):
        self.signout(self.sender().id)
        self.idedit.setFocus()

    def signout(self, id):
        if id not in self.ids:
            return
        self.ids[id].clear()
        del self.ids[id]

    def closeEvent(self, event):
        self.datastore.save()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    with open("signinapp.css") as f:
        app.setStyleSheet(f.read())
    form = MainWindow()
    form.show()
    app.exec_()
