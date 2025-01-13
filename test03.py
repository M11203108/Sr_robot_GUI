import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QSpacerItem, QFrame, QDesktopWidget
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QPainter, QColor

class MapWidget(QLabel):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 400)
        self.setFrameShape(QFrame.Box)
        self.setLineWidth(3)
        self.setStyleSheet("QFrame { border: 8px solid black; }")
        self.setText("地圖顯示區域")
        self.setAlignment(Qt.AlignCenter)
        self.robot_pose = None  # 保存機器人位置

    def update_map(self, robot_pose):
        self.robot_pose = robot_pose
        self.update()  # 重新繪製

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.robot_pose is not None:
            painter = QPainter(self)
            painter.setPen(QColor("red"))
            painter.drawEllipse(190, 190, 20, 20)  # 繪製紅色圓圈表示機器人位置
            painter.end()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("簡化的控制界面")

        # 創建地圖顯示元件
        self.map_widget = MapWidget()

        # 創建按鈕
        self.start_button = QPushButton("START\n啟動")
        self.stop_button = QPushButton("STOP\n停止")
        home_button = QPushButton("HOME\n回原點")

        # 設定按鈕大小和樣式
        self.start_button.setFixedSize(250, 300)
        self.stop_button.setFixedSize(250, 300)
        home_button.setFixedSize(250, 300)
        self.start_button.setStyleSheet("background-color: green; color: white; font-size: 30px;")
        self.stop_button.setStyleSheet("background-color: red; color: white; font-size: 30px;")
        home_button.setStyleSheet("background-color: blue; color: white; font-size: 30px;")

        # 綁定按鈕事件
        self.start_button.clicked.connect(self.start_process)
        self.stop_button.clicked.connect(self.stop_process)

        # 創建垂直佈局來控制按鈕位置，並均勻分配空間
        button_layout = QVBoxLayout()
        button_layout.setContentsMargins(10, 10, 10, 10)
        button_layout.setSpacing(20)
        button_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        button_layout.addWidget(self.start_button)
        button_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        button_layout.addWidget(self.stop_button)
        button_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        button_layout.addWidget(home_button)
        button_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # 創建水平佈局
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(30)
        main_layout.addLayout(button_layout)
        
        # 讓 map_widget 填充剩餘空間
        map_layout = QVBoxLayout()
        map_layout.setContentsMargins(0, 0, 0, 0)
        map_layout.addWidget(self.map_widget)
        
        map_label = QLabel("地圖畫面")
        map_label.setAlignment(Qt.AlignCenter)
        map_label.setStyleSheet("font-size: 24px; padding: 5px;")
        
        map_layout.addWidget(map_label)

        map_container = QWidget()
        map_container.setLayout(map_layout)
        map_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main_layout.addWidget(map_container)

        # 創建主窗口 widget
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # 調整窗口大小為螢幕大小
        screen_geometry = QDesktopWidget().screenGeometry()
        self.setGeometry(screen_geometry)

    @pyqtSlot()
    def start_process(self):
        print("START 按鈕被點擊")

    @pyqtSlot()
    def stop_process(self):
        print("STOP 按鈕被點擊")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
