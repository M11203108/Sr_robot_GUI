import sys
from PyQt5.QtWidgets import QApplication, QMainWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Hello PyQt5')
        self.setGeometry(100, 100, 600, 400)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())
