import sys
import yaml
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtGui import QPixmap
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
        self.setWindowTitle('Map Click Coordinate Converter')

        # 設置主窗口佈局
        layout = QVBoxLayout()

        # 加載並顯示地圖圖像
        self.label = QLabel(self)
        pixmap = QPixmap(pgm_file)
        self.label.setPixmap(pixmap)
        self.label.mousePressEvent = self.get_pixel_position  # 綁定鼠標點擊事件
        layout.addWidget(self.label)

        # 顯示轉換後的座標
        self.coord_label = QLabel(self)
        layout.addWidget(self.coord_label)

        # 設置中心窗口
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def get_pixel_position(self, event):
        # 獲取鼠標點擊的位置（像素坐標）
        px = event.pos().x()
        py = event.pos().y()

        # 將像素坐標轉換為世界座標
        world_x, world_y = self.pixel_to_world(px, py)
        self.coord_label.setText(f"世界座標: ({world_x:.2f}, {world_y:.2f})")

    def pixel_to_world(self, px, py):
        """將像素位置轉換為地圖中的世界坐標"""
        x = self.origin[0] + (px * self.resolution)
        y = self.origin[1] + ((self.image_height - py) * self.resolution)
        return x, y

if __name__ == '__main__':
    # 地圖文件路徑
    yaml_file = '/home/sr/wheeltec_ros2/src/wheeltec_robot_nav2/map/WHEELTEC.yaml'
    pgm_file = '/home/sr/wheeltec_ros2/src/wheeltec_robot_nav2/map/WHEELTEC.pgm'

    app = QApplication(sys.argv)
    window = MapWindow(yaml_file, pgm_file)
    window.show()
    sys.exit(app.exec_())
