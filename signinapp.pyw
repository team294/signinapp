#!/usr/bin/env python3
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import datastore
import settings
from passworddlg import PasswordDlg
from finddlg import FindDlg

class SynchronizeThread(QThread):
    finished = pyqtSignal()

    def __init__(self, datastore, parent=None):
        super().__init__(parent)
        self.datastore = datastore

    def run(self):
        self.datastore.sync()
        self.datastore.save()
        self.finished.emit()

class PersonImage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = None
        self.pixmap = None
        self.record = None
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.labelHeight = self.label.minimumSizeHint().height() * 1.25

    def minimumSizeHint(self):
        return QSize(60, 100)

    def updatePixmap(self):
        if self.image is not None:
            width = self.size().width()
            height = self.size().height() - self.labelHeight
            self.pixmap = QPixmap.fromImage(self.image.scaled(width, height,
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation))

    def resizeEvent(self, event=None):
        self.updatePixmap()
        self.label.move(0, self.size().height()-self.labelHeight)
        self.label.resize(self.size().width(), self.labelHeight)

    def paintEvent(self, event=None):
        p = QPainter(self)
        p.save()
        p.fillRect(p.viewport(), Qt.white)
        p.setPen(Qt.black)
        p.drawRect(p.viewport().adjusted(0, 0, -1, -1))
        p.restore()

        if self.pixmap is not None:
            width = p.viewport().width()
            height = p.viewport().height() - self.labelHeight
            p.drawPixmap(0, 0, self.pixmap,
                    abs(width - self.pixmap.width()) / 2,
                    abs(height - self.pixmap.height()) / 2,
                    width, height)

    def set(self, record):
        self.record = record
        image = QImage(record.person.photo)
        if image.isNull():
            raise IOError
        self.image = image
        self.updatePixmap()
        self.label.setText("%s (%d)" % (
            record.person.name.partition(' ')[0], record.person.badge))
        self.update()

    def clear(self):
        self.record = None
        self.image = None
        self.pixmap = None
        self.label.clear()
        self.update()

class PersonLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.record = None

    def set(self, record):
        self.record = record
        self.setText(str(record.person))

    def clear(self):
        super().clear()
        self.record = None

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
        layout = QGridLayout()
        layout.setSpacing(4)

        self.studentpics = [PersonImage() for i in range(7*4)]
        self.adultpics = [PersonImage() for i in range(3*4)]
        self.overflow = [PersonLabel() for i in range(20)]

        # Photos
        studentlabel = QLabel("Students")
        studentlabel.setAlignment(Qt.AlignCenter)
        studentlabel.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        studentlabel.setObjectName("student")
        layout.addWidget(studentlabel, 0, 0, 1, 7)

        adultlabel = QLabel("Mentors & Parents")
        adultlabel.setAlignment(Qt.AlignCenter)
        adultlabel.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        adultlabel.setObjectName("adult")
        layout.addWidget(adultlabel, 0, 8, 1, 3)

        for row in range(4):
            for col in range(7):
                layout.addWidget(self.studentpics[row*7+col], row+1, col)
                layout.setColumnStretch(col, 1)
            for col in range(3):
                layout.addWidget(self.adultpics[row*3+col], row+1, col+8)
                layout.setColumnStretch(col+8, 1)
            layout.setRowStretch(row+1, 1)

        # Overflow (including entry text box)
        self.badgeEdit = QLineEdit()
        self.badgeEdit.returnPressed.connect(self.badgeEntered)
        layout.addWidget(self.badgeEdit, 0, 7)

        overflowwidget = QWidget()
        overflowlayout = QVBoxLayout()
        for widget in self.overflow:
            overflowlayout.addWidget(widget)
        overflowlayout.addStretch(1)
        overflowlayout.addStrut(120)
        overflowwidget.setLayout(overflowlayout)
        layout.addWidget(overflowwidget, 1, 7, -1, 1)

        center.setLayout(layout)

        # Create actions
        usersFindAction = self.createAction("&Find...", tip="Find id for user")
        usersFindAction.triggered.connect(self.findUser)

        usersSignOutAllAction = self.createAction("Sign &Out All",
                tip="Sign out all users")
        usersSignOutAllAction.triggered.connect(self.signOutAll)

        usersClearAllAction = self.createAction("&Clear All",
                tip="Clear all users (no hours credit given)")
        usersClearAllAction.triggered.connect(self.clearAll)

        self.serverPasswordAction = self.createAction("Set &Password...",
                tip="Set server password")
        self.serverPasswordAction.triggered.connect(self.setServerPassword)

        self.serverSyncAction = self.createAction("&Synchronize Now",
                tip="Synchronize with server")
        self.serverSyncAction.triggered.connect(self.sync)

        self.autoSyncAction = self.createAction("&Auto Sync",
                tip="Enable auto-synchronization with server", checkable=True)
        self.autoSyncAction.toggled.connect(self.autoSyncToggled)

        # Create menu bar
        userMenu = self.menuBar().addMenu("&Users")
        userMenu.addAction(usersFindAction)

        actionMenu = self.menuBar().addMenu("&Actions")
        actionMenu.addAction(usersSignOutAllAction)
        actionMenu.addAction(usersClearAllAction)

        serverMenu = self.menuBar().addMenu("&Server")
        serverMenu.addAction(self.serverPasswordAction)
        serverMenu.addAction(self.serverSyncAction)
        serverMenu.addAction(self.autoSyncAction)

        # Status bar
        status = self.statusBar()
        self.numPeopleLabel = QLabel("0 total")
        status.addPermanentWidget(self.numPeopleLabel)
        self.numClockedInLabel = QLabel("0 in")
        status.addPermanentWidget(self.numClockedInLabel)
        self.numTimeEntriesLabel = QLabel("0 records")
        status.addPermanentWidget(self.numTimeEntriesLabel)
        self.datastore.statsChanged.connect(self.statsChanged)

        self.setWindowTitle("Sign In Application")
        self.badgeEdit.setFocus()

        # Load file
        QTimer.singleShot(0, self.load)

        # Try to autosync once a day
        self.autoSyncTimer = QTimer(self)
        self.autoSyncTimer.setInterval(24*60*60*1000)
        self.autoSyncTimer.timeout.connect(self.sync)
        self.autoSyncAction.setChecked(True)

    def createAction(self, text, shortcut=None, icon=None, tip=None,
            checkable=False):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if checkable:
            action.setCheckable(True)
        return action

    def load(self):
        self.datastore.load()
        for record in self.datastore.clockedIn.values():
            self.signin(record)

    def badgeEntered(self):
        badgestr = self.badgeEdit.text()
        self.badgeEdit.clear()

        if badgestr[0] == 'B':
            # Handle as Code39-encoded barcode "BxxxxC" (C=checksum)
            # Check checksum across all characters
            charset = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-. $/+%"
            checksum = charset[sum(charset.index(c) for c in badgestr[:-1]) % 43]
            if checksum != badgestr[-1]:
                self.statusBar().showMessage("Bad barcode checksum for '%s': expected %s" % (badgestr, checksum))
                return
            # Extract internal data (should be number)
            badgestr = badgestr[1:-1]

        try:
            badge = int(badgestr)
        except ValueError:
            self.statusBar().showMessage("Invalid data entry '%s'" % badgestr)
            return

        try:
            record = self.datastore.signInOut(badge)
        except KeyError:
            self.statusBar().showMessage("User %d does not exist" % badge)
            return

        self.statusBar().showMessage("%s signed %s" %
                (self.datastore.people[self.datastore.badgeToId[badge]],
                "out" if record is None else "in"))

        if record is not None:
            self.signin(record)

    def signin(self, record):
        # get notified when person signs out
        record.completed.connect(self.handle_signout)

        # figure out which widget to place person at..
        widget = None

        # if picture available, try to place in pics
        person = record.person
        if person.hasPhoto():
            if person.student:
                picwidgets = self.studentpics
            else:
                picwidgets = self.adultpics
            for w in picwidgets:
                if w.record is None:
                    widget = w
                    break
            if widget is not None:
                try:
                    widget.set(record)
                except IOError:
                    widget = None # file didn't load, place in overflow

        # otherwise place in overflow
        if widget is None:
            for w in self.overflow:
                if w.record is None:
                    widget = w
                    break
            if widget is not None:
                widget.set(record)

        # update widget
        self.ids[person.id] = widget

    def findUser(self):
        form = FindDlg(self.datastore, parent=self)
        form.exec_()

    def signOutAll(self):
        reply = QMessageBox.warning(self, "Confirm sign out",
                "Are you sure you want to sign out ALL users?",
                QMessageBox.Yes|QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.datastore.signOutAll()

    def clearAll(self):
        reply = QMessageBox.warning(self, "Confirm clear",
                "Are you sure you want to clear ALL users?\n"
                "They will not get any hours credit!",
                QMessageBox.Yes|QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.datastore.clearAll()

    def setServerPassword(self):
        form = PasswordDlg(self)
        if form.exec_():
            settings.LOGIN_PASSWORD = form.result()
            self.serverSyncAction.setEnabled(True)

    def sync(self):
        if self.syncThread.isRunning():
            return
        self.statusBar().showMessage("Synchronizing...")
        self.serverPasswordAction.setEnabled(False)
        self.serverSyncAction.setEnabled(False)
        self.syncThread.start()

    def syncDone(self):
        self.serverPasswordAction.setEnabled(True)
        self.serverSyncAction.setEnabled(True)
        # update all widgets
        for id in self.ids:
            self.ids[id].clear()
        self.ids.clear()
        for record in self.datastore.clockedIn.values():
            self.signin(record)

    def autoSyncToggled(self):
        if self.autoSyncAction.isChecked():
            self.autoSyncTimer.start()
        else:
            self.autoSyncTimer.stop()

    def statsChanged(self):
        self.numPeopleLabel.setText("%d total" % self.datastore.getNumPeople())
        self.numClockedInLabel.setText("%d in" % self.datastore.getNumClockedIn())
        self.numTimeEntriesLabel.setText("%d records" % self.datastore.getNumTimeEntries())

    def handle_signout(self):
        id = self.sender().person.id
        if id not in self.ids:
            return # shouldn't happen, but just in case..
        if self.ids[id] is not None:
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
