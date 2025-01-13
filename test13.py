import sys
import yaml
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton
from PyQt5.QtGui import QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt
from PIL import Image

class MapWindow(QMainWindow):
    def __init__(self, yaml_file, pgm_file):
        super().__init__()

        # 讀取地圖的元數據
        with open(yaml_file, 'r') as file:
            self.map_info = yaml.safe_load(file)

        self.resolution = self.map_info['resolution']
        self.origin = self.map_info['origin']

        # 獲取圖片的實際高度（以像素為單位）
        image = Image.open(pgm_file)
        self.image_height = image.height

        # 設置窗口標題
        self.setWindowTitle('Map with Control Buttons')

        # 設置主窗口佈局
        main_layout = QHBoxLayout()

        # 創建按鈕並設置其樣式
        self.start_button = QPushButton("START")
        self.stop_button = QPushButton("STOP")
        self.home_button = QPushButton("HOME")

        # 設置按鈕大小和顏色
        self.start_button.setFixedSize(120, 50)
        self.start_button.setStyleSheet("background-color: green; color: white; font-size: 18px;")
        self.stop_button.setFixedSize(120, 50)
        self.stop_button.setStyleSheet("background-color: red; color: white; font-size: 18px;")
        self.home_button.setFixedSize(120, 50)
        self.home_button.setStyleSheet("background-color: blue; color: white; font-size: 18px;")

        # 創建按鈕佈局
        button_layout = QVBoxLayout()
        button_layout.setContentsMargins(20, 20, 20, 20)
        button_layout.setSpacing(20)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.home_button)
        button_layout.addStretch()  # 添加伸縮空間，確保按鈕在頂部

        # 創建地圖顯示區域
        self.label = MapLabel(self.origin, self.resolution, self.image_height, pgm_file)
        
        # 創建地圖佈局
        map_layout = QVBoxLayout()
        map_layout.addWidget(self.label)
        map_layout.setContentsMargins(0, 0, 0, 0)

        # 將按鈕佈局和地圖佈局添加到主佈局
        main_layout.addLayout(button_layout)
        main_layout.addLayout(map_layout)

        # 設置中心窗口
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # 綁定鼠標點擊事件
        self.label.mousePressEvent = self.get_pixel_position

    def get_pixel_position(self, event):
        # 獲取鼠標點擊的位置（像素座標）
        px = event.pos().x()
        py = event.pos().y()

        # 將像素坐標轉換為世界座標
        world_x, world_y = self.pixel_to_world(px, py)
        print(f"世界座標: ({world_x:.2f}, {world_y:.2f})")

    def pixel_to_world(self, px, py):
        """將像素位置轉換為地圖中的世界坐標"""
        x = self.origin[0] + (px * self.resolution)
        y = self.origin[1] + ((self.image_height - py) * self.resolution)
        return x, y

class MapLabel(QLabel):
    def __init__(self, origin, resolution, image_height, pgm_file):
        super().__init__()
        self.origin = origin
        self.resolution = resolution
        self.image_height = image_height

        # 加載地圖圖像
        pixmap = QPixmap(pgm_file)
        self.setPixmap(pixmap)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setPen(QColor("red"))

        # 計算原點在像素座標系中的位置
        origin_px_x = -self.origin[0] / self.resolution
        origin_px_y = self.image_height + (self.origin[1] / self.resolution)

        # 在地圖上繪製一個小紅色圓點表示原點
        painter.drawEllipse(int(origin_px_x), int(origin_px_y), 5, 5)  # 5x5 像素的圓點
        painter.end()

if __name__ == '__main__':
    # 地圖文件路徑
    yaml_file = '/home/sr/wheeltec_ros2/src/wheeltec_robot_nav2/map/WHEELTEC.yaml'
    pgm_file = '/home/sr/wheeltec_ros2/src/wheeltec_robot_nav2/map/WHEELTEC.pgm'

    app = QApplication(sys.argv)
    window = MapWindow(yaml_file, pgm_file)
    window.show()
    sys.exit(app.exec_())
