from __future__ import print_function
from PyQt4.QtCore import *
from PyQt4.QtGui import *

MAC = "qt_mac_set_native_menubar" in dir()

class FindDlg(QDialog):
    personInOut = pyqtSignal([int])

    def __init__(self, datastore, parent=None):
        super(FindDlg, self).__init__(parent)
        self.datastore = datastore

        findLabel = QLabel("&Name:")
        self.findLineEdit = QLineEdit()
        findLabel.setBuddy(self.findLineEdit)

        self.results = QTableWidget()
        self.results.setColumnCount(2)
        self.results.setHorizontalHeaderLabels(["Name", "Badge"])

        findButton = QPushButton("&Find")
        closeButton = QPushButton("&Close")
        if not MAC:
            findButton.setFocusPolicy(Qt.NoFocus)
            closeButton.setFocusPolicy(Qt.NoFocus)

        gridLayout = QGridLayout()
        gridLayout.addWidget(findLabel, 0, 0)
        gridLayout.addWidget(self.findLineEdit, 0, 1)
        gridLayout.addWidget(findButton, 0, 2)
        gridLayout.addWidget(closeButton, 0, 3)
        gridLayout.addWidget(self.results, 1, 0, 1, -1)
        self.setLayout(gridLayout)

        findButton.clicked.connect(self.find)
        self.findLineEdit.returnPressed.connect(self.find)
        closeButton.clicked.connect(self.close)
        self.results.cellDoubleClicked.connect(self.resultDoubleClicked)

        self.setWindowTitle("Find User")

    def find(self):
        text = str(self.findLineEdit.text()).lower()
        people = [p for p in self.datastore.people.values() if
                text in p.name.lower()]
        print("found %d results for '%s'" % (len(people), text))
        self.results.clearContents()
        self.results.setSortingEnabled(False)
        self.results.setRowCount(len(people))
        for row, person in enumerate(people):
            item = QTableWidgetItem(person.name)
            item.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
            self.results.setItem(row, 0, item)

            item = QTableWidgetItem(str(person.badge))
            item.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
            self.results.setItem(row, 1, item)
        self.results.sortItems(0)

    def resultDoubleClicked(self, row, column):
        item = self.results.item(row, 1)
        self.personInOut.emit(int(item.text()))

if __name__ == "__main__":
    import sys
    import datastore
    store = datastore.DataStore()
    store.load()
    app = QApplication(sys.argv)
    form = FindDlg(store)
    form.show()
    app.exec_()
