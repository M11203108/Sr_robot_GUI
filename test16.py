import sys
import yaml
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QComboBox
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPolygonF
from PyQt5.QtCore import Qt, QPointF
from PIL import Image
import math

class MapWindow(QMainWindow):
    def __init__(self, yaml_file, pgm_files, waypoints):
        super().__init__()

        # 讀取地圖的元數據
        with open(yaml_file, 'r') as file:
            self.map_info = yaml.safe_load(file)

        self.resolution = self.map_info['resolution']
        self.origin = self.map_info['origin']
        self.waypoints = waypoints

        # 設置窗口標題
        self.setWindowTitle('Map with Control Buttons and Image Selector')

        # 設置主窗口佈局
        main_layout = QVBoxLayout()
        self.pgm_files = pgm_files

        # 創建下拉式選單
        self.combo_box = QComboBox(self)
        self.combo_box.addItems([f"Map {i + 1}" for i in range(len(pgm_files))])
        self.combo_box.currentIndexChanged.connect(self.update_map)  # 連接選單變更事件
        main_layout.addWidget(self.combo_box)

        # 創建按鈕並設置其樣式
        self.start_button = QPushButton("START\n啟動")
        self.stop_button = QPushButton("STOP\n停止")
        self.home_button = QPushButton("HOME\n回原點")

        # 設置按鈕大小和顏色
        self.start_button.setFixedSize(120, 150)
        self.start_button.setStyleSheet("background-color: green; color: white; font-size: 18px;")
        self.stop_button.setFixedSize(120, 150)
        self.stop_button.setStyleSheet("background-color: red; color: white; font-size: 18px;")
        self.home_button.setFixedSize(120, 150)
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
        self.label = MapLabel(self.origin, self.resolution, self.load_image_height(pgm_files[0]), pgm_files[0], waypoints, scale_factor=1.5)
        
        # 創建地圖佈局
        map_layout = QVBoxLayout()
        map_layout.addWidget(self.label)
        map_layout.setContentsMargins(0, 0, 0, 0)

        # 將按鈕佈局和地圖佈局添加到主佈局
        content_layout = QHBoxLayout()
        content_layout.addLayout(button_layout)
        content_layout.addLayout(map_layout)
        main_layout.addLayout(content_layout)

        # 設置中心窗口
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # 綁定鼠標點擊事件
        self.label.mousePressEvent = self.get_pixel_position

    def load_image_height(self, pgm_file):
        """獲取圖片的實際高度（以像素為單位）"""
        image = Image.open(pgm_file)
        return image.height

    def update_map(self, index):
        """更新顯示的地圖圖像"""
        selected_pgm_file = self.pgm_files[index]
        self.label.update_image(selected_pgm_file, self.load_image_height(selected_pgm_file))

    def get_pixel_position(self, event):
        # 獲取鼠標點擊的位置（像素坐標）
        px = event.pos().x()
        py = event.pos().y()

        # 將像素坐標轉換為世界座標
        world_x, world_y = self.pixel_to_world(px, py)
        print(f"世界座標: ({world_x:.2f}, {world_y:.2f})")

    def pixel_to_world(self, px, py):
        """將像素位置轉換為地圖中的世界坐標"""
        x = self.origin[0] + (px * self.resolution)
        y = self.origin[1] + ((self.label.image_height - py) * self.resolution)
        return x, y

class MapLabel(QLabel):
    def __init__(self, origin, resolution, image_height, pgm_file, waypoints, scale_factor=1.0):
        super().__init__()
        self.origin = origin
        self.resolution = resolution
        self.image_height = image_height
        self.waypoints = waypoints
        self.scale_factor = scale_factor

        # 加載地圖圖像
        self.update_image(pgm_file, image_height)

    def update_image(self, pgm_file, image_height):
        """更新顯示的地圖圖像"""
        self.image_height = image_height
        pixmap = QPixmap(pgm_file)
        # 計算縮放後的寬度和高度
        scaled_width = int(pixmap.width() * self.scale_factor)
        scaled_height = int(pixmap.height() * self.scale_factor)
        scaled_pixmap = pixmap.scaled(
            scaled_width,
            scaled_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.setPixmap(scaled_pixmap)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setPen(QColor("red"))

        # 繪製原點
        origin_px_x = -self.origin[0] / self.resolution * self.scale_factor
        origin_px_y = self.image_height * self.scale_factor + (self.origin[1] / self.resolution * self.scale_factor)
        painter.drawEllipse(int(origin_px_x), int(origin_px_y), 5, 5)  # 5x5 像素的圓點

        # 繪製每個點位及其方向
        for waypoint in self.waypoints:
            # 將世界座標轉換為像素座標
            px_x = (waypoint['x'] - self.origin[0]) / self.resolution * self.scale_factor
            px_y = self.image_height * self.scale_factor - ((waypoint['y'] - self.origin[1]) / self.resolution * self.scale_factor)

            # 繪製點位
            painter.setBrush(QColor("yellow"))
            painter.drawEllipse(QPointF(px_x, px_y), 8, 8)  # 8x8 像素的圓點

            # 計算並繪製方向箭頭
            arrow_length = 20  # 箭頭長度
            angle = 2 * math.atan2(waypoint['qz'], waypoint['qw'])  # 計算旋轉角度
            dx = arrow_length * math.cos(angle)
            dy = -arrow_length * math.sin(angle)  # Y軸像素是反的

            arrow = QPolygonF([
                QPointF(px_x, px_y),
                QPointF(px_x + dx, px_y + dy)
            ])

            painter.setPen(QColor("blue"))
            painter.drawPolyline(arrow)

        painter.end()

if __name__ == '__main__':
    # 地圖文件路徑
    yaml_file = '/home/sr/wheeltec_ros2/src/wheeltec_robot_nav2/map/WHEELTEC.yaml'
    pgm_files = [
        '/home/sr/wheeltec_ros2/src/wheeltec_robot_nav2/map/WHEELTEC.pgm',
        '/home/sr/wheeltec_ros2/src/wheeltec_robot_nav2/map/OTHER_MAP.pgm'
    ]

    # 定義點位
    waypoints = [
        {"x": 5.4109198438036215, "y": 0.4012809838948602, "z": 0.0, "qx": 0.0, "qy": 0.0, "qz": 0.6977885684820497, "qw": 0.7163037859007669},
        {"x": 5.578655403644704, "y": 2.782073451495792, "z": 0.0, "qx": 0.0, "qy": 0.0, "qz": 0.9929940622784668, "qw": 0.11816425973918068},
        {"x": 3.1718655996877505, "y": 2.8979294892565557, "z": 0.0, "qx": 0.0, "qy": 0.0, "qz": -0.796202960047208, "qw": 0.6050296244086434},
        {"x": 2.959936223064883, "y": 0.49194696489205514, "z": 0.0, "qx": 0.0, "qy": 0.0, "qz": -0.11142263058050911, "qw": 0.9937731116278602}
    ]

    app = QApplication(sys.argv)
    window = MapWindow(yaml_file, pgm_files, waypoints)
    window.show()
    sys.exit(app.exec_())
