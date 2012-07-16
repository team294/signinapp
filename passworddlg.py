from PyQt4.QtCore import *
from PyQt4.QtGui import *

class PasswordDlg(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        passwordLabel = QLabel("&Password:")
        self.passwordEdit = QLineEdit()
        passwordLabel.setBuddy(self.passwordEdit)
        self.passwordEdit.setEchoMode(QLineEdit.Password)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok|
                                     QDialogButtonBox.Cancel)

        layout = QGridLayout()
        layout.addWidget(passwordLabel, 0, 0)
        layout.addWidget(self.passwordEdit, 0, 1)
        layout.addWidget(buttonBox, 1, 0, 1, 2)
        self.setLayout(layout)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        self.setWindowTitle("Set Server Password")

    def result(self):
        return self.passwordEdit.text()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    form = PasswordDlg()
    form.show()
    app.exec_()
