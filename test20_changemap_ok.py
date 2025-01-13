import sys
import yaml
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QComboBox
from PyQt5.QtGui import QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt, pyqtSlot
from PIL import Image
import subprocess

class MapWindow(QMainWindow):
    def __init__(self, yaml_files, pgm_files):
        super().__init__()

        # 保存 YAML 和 PGM 文件路徑
        self.yaml_files = yaml_files
        self.pgm_files = pgm_files

        # 設置窗口標題
        self.setWindowTitle('Map with Control Buttons and Image Selector')
        self.setFixedSize(1300, 1000)  # 設置固定窗口大小

        # 設置主窗口佈局
        main_layout = QVBoxLayout()

        # 創建下拉式選單
        self.combo_box = QComboBox(self)
        self.combo_box.addItem("Select a map")  # 添加空白選項
        self.combo_box.addItems([f"Map {i + 1}" for i in range(len(pgm_files))])
        self.combo_box.currentIndexChanged.connect(self.update_map)  # 連接選單變更事件
        main_layout.addWidget(self.combo_box)

        # 創建按鈕並設置其樣式
        self.start_button = QPushButton("START\n啟動")
        self.stop_button = QPushButton("STOP\n停止")
        self.home_button = QPushButton("HOME\n回原點")

        # 綁定按鈕事件
        self.start_button.clicked.connect(self.start_process)
        self.stop_button.clicked.connect(self.stop_process)
        self.home_button.clicked.connect(self.home_process)

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
        self.label = MapLabel(self)  # 初始時不顯示地圖
        
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

    def load_map_metadata(self, index):
        """根據選擇的地圖讀取 YAML 文件中的元數據"""
        with open(self.yaml_files[index], 'r') as file:
            map_info = yaml.safe_load(file)

        self.resolution = map_info['resolution']
        self.origin = map_info['origin']

    @pyqtSlot()
    def start_process(self):
        print("START 按鈕被點擊")
        subprocess.Popen([
            "xterm", "-e", "bash -c 'cd ~/wheeltec_ros2 && source install/setup.bash && ros2 launch wheeltec_nav2 wheeltec_nav2.launch.py; exec bash'"
        ])

    @pyqtSlot()
    def stop_process(self):
        print("STOP 按鈕被點擊")
        subprocess.Popen([
            "xterm", "-e", "bash -c 'pkill -f ros2; exec bash'"
        ])

    @pyqtSlot()
    def home_process(self):
        print("HOME 按鈕被點擊")

    def load_image_height(self, pgm_file):
        """獲取圖片的實際高度（以像素為單位）"""
        image = Image.open(pgm_file)
        return image.height

    def update_map(self, index):
        """更新顯示的地圖圖像和元數據"""
        if index == 0:
            # 空白選項，隱藏地圖
            self.label.clear()
            return
        
        selected_index = index - 1  # 因為選單中添加了一個空白選項
        self.load_map_metadata(selected_index)
        selected_pgm_file = self.pgm_files[selected_index]
        self.label.update_image(selected_pgm_file, self.load_image_height(selected_pgm_file), self.origin, self.resolution)

    def get_pixel_position(self, event):
        # 獲取鼠標點擊的位置（像素坐標）
        px = event.pos().x()
        py = event.pos().y()

        # 將像素坐標轉換為世界坐標
        world_x, world_y = self.pixel_to_world(px, py)
        print(f"世界座標: ({world_x:.2f}, {world_y:.2f})")

    def pixel_to_world(self, px, py):
        """將像素位置轉換為地圖中的世界坐標"""
        scaled_px = px / self.label.scale_factor
        scaled_py = py / self.label.scale_factor
        x = self.origin[0] + (scaled_px * self.resolution)
        y = self.origin[1] + ((self.label.image_height - scaled_py) * self.resolution)
        return x, y

class MapLabel(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.origin = (0, 0)
        self.resolution = 1
        self.image_height = 1
        self.scale_factor = 1.0  # 初始比例設為 1.0

    def update_image(self, pgm_file, image_height, origin, resolution):
        """更新顯示的地圖圖像，並自動縮放以適應視窗"""
        self.image_height = image_height
        self.origin = origin
        self.resolution = resolution
        pixmap = QPixmap(pgm_file)

        # 自動縮放以適應 QLabel 大小
        scaled_pixmap = pixmap.scaled(
            self.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.scale_factor = scaled_pixmap.width() / pixmap.width()  # 更新縮放比例
        self.setPixmap(scaled_pixmap)
        self.update()

    def clear(self):
        """清除顯示的地圖圖像"""
        self.setPixmap(QPixmap())
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setPen(QColor("red"))

        # 計算 (0, 0) 點在地圖上的像素位置
        zero_px_x = (-self.origin[0]) / self.resolution * self.scale_factor
        zero_px_y = (self.image_height - (-self.origin[1]) / self.resolution) * self.scale_factor

        # 繪製紅點表示原點
        painter.drawEllipse(int(zero_px_x), int(zero_px_y), 5, 5)  # 5x5 像素的圓點

        painter.end()

    def resizeEvent(self, event):
        """在窗口大小改變時，自動重新縮放地圖"""
        if self.pixmap():
            self.update_image(self.pixmap().toImage(), self.image_height, self.origin, self.resolution)
        super().resizeEvent(event)

if __name__ == '__main__':
    # 地圖文件路徑
    yaml_files = [
        '/home/sr/wheeltec_ros2/src/wheeltec_robot_nav2/map/WHEELTEC.yaml',
        '/home/sr/wheeltec_ros2/src/wheeltec_robot_nav2/map/WHEELTEC1.yaml'
    ]
    pgm_files = [
        '/home/sr/wheeltec_ros2/src/wheeltec_robot_nav2/map/WHEELTEC.pgm',
        '/home/sr/wheeltec_ros2/src/wheeltec_robot_nav2/map/WHEELTEC1.pgm'
    ]

    app = QApplication(sys.argv)
    window = MapWindow(yaml_files, pgm_files)
    window.show()
    sys.exit(app.exec_())
