import sys
import yaml
import json
import math
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QComboBox, QLineEdit, QFileDialog, QSpinBox
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPolygonF
from PyQt5.QtCore import Qt, QPointF
from PIL import Image
import os


def calculate_quaternion_from_angle(angle):
    """根據 z 軸旋轉角度計算四元數"""
    qw = math.cos(angle / 2)
    qz = math.sin(angle / 2)
    return 0.0, 0.0, qz, qw


class MapWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 設定地圖與點位檔案目錄
        self.map_directory = "/home/sr/wheeltec_ros2/src/wheeltec_robot_nav2/map"
        self.default_point_file = "/home/sr/gui_ws/saved_points.json"
        self.point_file_path = self.default_point_file

        # 掃描目錄中的地圖檔案
        self.yaml_files, self.pgm_files = self.scan_map_files(self.map_directory)

        # 設定視窗標題與大小
        self.setWindowTitle("Map and Waypoint Manager")
        self.setGeometry(100, 100, 1200, 700)

        # 設定主佈局
        main_layout = QVBoxLayout()

        # 上方選單：選擇地圖和輸入檔案名稱
        self.map_combo_box = QComboBox(self)
        self.map_combo_box.addItem("Select a map")
        self.map_combo_box.addItems([os.path.splitext(os.path.basename(yaml))[0] for yaml in self.yaml_files])
        self.map_combo_box.currentIndexChanged.connect(self.update_map)

        self.file_name_input = QLineEdit(self)
        self.file_name_input.setPlaceholderText("Enter filename for saving points...")

        selection_layout = QHBoxLayout()
        selection_layout.addWidget(self.map_combo_box)
        selection_layout.addWidget(self.file_name_input)
        main_layout.addLayout(selection_layout)

        # 地圖顯示區
        self.label = MapLabel(self)
        map_layout = QVBoxLayout()
        map_layout.addWidget(self.label)

        # 按鈕區域
        self.start_button = QPushButton("START\n啟用")
        self.stop_button = QPushButton("STOP\n停止")
        self.home_button = QPushButton("HOME\n回原點")
        self.set_point_button = QPushButton("SET POINT\n設定點位")
        self.clear_button = QPushButton("CLEAR\n清除點位")
        self.save_as_button = QPushButton("SAVE AS\n另存為")
        self.load_button = QPushButton("LOAD\n載入檔案")

        self.start_button.clicked.connect(self.start_process)
        self.stop_button.clicked.connect(self.stop_process)
        self.home_button.clicked.connect(self.home_process)
        self.set_point_button.clicked.connect(self.toggle_set_point_mode)
        self.clear_button.clicked.connect(self.clear_points)
        self.save_as_button.clicked.connect(self.save_points_as)
        self.load_button.clicked.connect(self.load_points_from_file)

        self.set_button_style(self.start_button, "green")
        self.set_button_style(self.stop_button, "red")
        self.set_button_style(self.home_button, "blue")
        self.set_button_style(self.set_point_button, "gray")
        self.set_button_style(self.clear_button, "orange")

        button_layout = QVBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.home_button)
        button_layout.addWidget(self.set_point_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.save_as_button)
        button_layout.addWidget(self.load_button)
        button_layout.addStretch()

        # 停留時間設定
        time_layout = QHBoxLayout()
        self.stay_duration_hours = QSpinBox(self)
        self.stay_duration_minutes = QSpinBox(self)
        self.stay_duration_seconds = QSpinBox(self)
        self.stay_duration_hours.setRange(0, 23)
        self.stay_duration_minutes.setRange(0, 59)
        self.stay_duration_seconds.setRange(0, 59)
        self.stay_duration_seconds.setValue(10)
        time_layout.addWidget(self.stay_duration_hours)
        time_layout.addWidget(self.stay_duration_minutes)
        time_layout.addWidget(self.stay_duration_seconds)
        button_layout.addLayout(time_layout)

        # 主佈局組合
        content_layout = QHBoxLayout()
        content_layout.addLayout(button_layout)
        content_layout.addLayout(map_layout, 1)  # 地圖佔據剩餘空間
        main_layout.addLayout(content_layout)

        # 設定中心視窗
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # 初始化狀態
        self.recording_mode = False
        self.recorded_points = []
        self.load_saved_points()

    def set_button_style(self, button, color):
        """設置按鈕樣式"""
        button.setFixedSize(120, 80)
        button.setStyleSheet(f"background-color: {color}; color: white; font-size: 18px;")

    def scan_map_files(self, map_directory):
        """掃描目錄中的地圖檔案"""
        yaml_files, pgm_files = [], []
        if os.path.exists(map_directory):
            for file_name in sorted(os.listdir(map_directory)):
                if file_name.endswith('.yaml'):
                    yaml_files.append(os.path.join(map_directory, file_name))
                    pgm_files.append(os.path.join(map_directory, file_name.replace('.yaml', '.pgm')))
        return yaml_files, pgm_files

    def update_map(self, index):
        """更新地圖"""
        if index > 0:
            yaml_path = self.yaml_files[index - 1]
            pgm_file = self.pgm_files[index - 1]

            # 從 YAML 檔案中載入元數據
            with open(yaml_path, 'r') as file:
                map_info = yaml.safe_load(file)
                self.label.update_metadata(map_info['origin'], map_info['resolution'])

            # 更新地圖顯示
            image_height = self.label.load_image_height(pgm_file)
            self.label.update_image(pgm_file, image_height, map_info['origin'], map_info['resolution'])
            print(f"切換到地圖: {pgm_file}")

    def load_saved_points(self):
        """載入預設點位檔案"""
        try:
            with open(self.point_file_path, 'r') as file:
                data = json.load(file)
                self.recorded_points = data.get('points', [])
                self.label.set_points(self.recorded_points)
                print(f"已載入點位檔案: {self.point_file_path}")
        except FileNotFoundError:
            self.recorded_points = []
            print(f"未找到檔案: {self.point_file_path}")

    def save_points_as(self):
        """另存為功能"""
        file_name = self.file_name_input.text().strip()
        if file_name:
            self.point_file_path = os.path.join("/home/sr/gui_ws/", f"{file_name}.json")
            self.save_points()

    def save_points(self):
        """儲存點位檔案"""
        points_data = {'points': self.recorded_points}
        with open(self.point_file_path, 'w') as file:
            json.dump(points_data, file, indent=4)
        print(f"已儲存點位到檔案: {self.point_file_path}")

    def load_points_from_file(self):
        """選擇檔案並載入點位"""
        file_path, _ = QFileDialog.getOpenFileName(self, "選擇點位檔案", "", "JSON Files (*.json)")
        if file_path:
            self.point_file_path = file_path
            self.load_saved_points()

    def toggle_set_point_mode(self):
        """切換點位記錄模式"""
        self.recording_mode = not self.recording_mode
        self.label.recording_mode = self.recording_mode
        self.set_point_button.setStyleSheet("background-color: orange;" if self.recording_mode else "background-color: gray;")
        print("記錄模式" + ("啟用" if self.recording_mode else "停用"))

    def clear_points(self):
        """清除所有點位"""
        self.recorded_points = []
        self.label.set_points([])
        print("清除所有點位")

    def start_process(self):
        print("啟動導航")

    def stop_process(self):
        print("停止導航")

    def home_process(self):
        print("導航回原點")
        self.clear_points()
        self.recorded_points.append({"x": 0.0, "y": 0.0, "z": 0.0, "qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0, "stay_duration": 10})
        self.label.set_points(self.recorded_points)


class MapLabel(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.origin = (0, 0)
        self.resolution = 1
        self.image_height = 1
        self.scale_factor = 1.0
        self.points = []
        self.recording_mode = False

    def load_image_height(self, pgm_file):
        image = Image.open(pgm_file)
        return image.height

    def update_metadata(self, origin, resolution):
        self.origin = origin
        self.resolution = resolution

    def update_image(self, pgm_file, image_height, origin, resolution):
        self.image_height = image_height
        self.origin = origin
        self.resolution = resolution
        pixmap = QPixmap(pgm_file)
        scaled_pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.scale_factor = scaled_pixmap.width() / pixmap.width()
        self.setPixmap(scaled_pixmap)
        self.update()

    def set_points(self, points):
        self.points = points
        self.update()

    def mousePressEvent(self, event):
        if self.recording_mode:
            px, py = event.pos().x(), event.pos().y()
            world_x = self.origin[0] + px / self.scale_factor * self.resolution
            world_y = self.origin[1] + (self.image_height - py / self.scale_factor) * self.resolution

            if len(self.points) % 2 == 0:
                # 偶數次點擊，新增點
                point = {"x": world_x, "y": world_y, "z": 0.0, "qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0, "stay_duration": 10}
                self.points.append(point)
            else:
                # 奇數次點擊，計算方向
                last_point = self.points[-1]
                dx, dy = world_x - last_point["x"], world_y - last_point["y"]
                angle = math.atan2(dy, dx)
                qx, qy, qz, qw = calculate_quaternion_from_angle(angle)
                last_point.update({"qx": qx, "qy": qy, "qz": qz, "qw": qw})

            self.parent().recorded_points = self.points
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)

        # 繪製輔助格線
        self.draw_grid(painter)

        # 繪製地圖原點
        self.draw_origin(painter)

        # 繪製點位和方向
        for i, point in enumerate(self.points):
            px = int((point["x"] - self.origin[0]) / self.resolution * self.scale_factor)
            py = int((self.image_height - (point["y"] - self.origin[1])) / self.resolution * self.scale_factor)
            painter.setBrush(QColor("red"))
            painter.drawEllipse(px - 5, py - 5, 10, 10)
            if i > 0:
                prev_point = self.points[i - 1]
                prev_px = int((prev_point["x"] - self.origin[0]) / self.resolution * self.scale_factor)
                prev_py = int((self.image_height - (prev_point["y"] - self.origin[1])) / self.resolution * self.scale_factor)
                painter.setPen(QColor("blue"))
                painter.drawLine(prev_px, prev_py, px, py)
                self.draw_arrow(painter, prev_px, prev_py, px, py)

    def draw_grid(self, painter):
        grid_spacing = 50
        painter.setPen(QColor(200, 200, 200))
        for x in range(0, self.width(), grid_spacing):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), grid_spacing):
            painter.drawLine(0, y, self.width(), y)

    def draw_origin(self, painter):
        painter.setBrush(QColor("red"))
        px = int((-self.origin[0]) / self.resolution * self.scale_factor)
        py = int((self.image_height - (-self.origin[1]) / self.resolution) * self.scale_factor)
        painter.drawEllipse(px - 5, py - 5, 10, 10)

    def draw_arrow(self, painter, x1, y1, x2, y2):
        angle = math.atan2(y2 - y1, x2 - x1)
        arrow_size = 10
        painter.setPen(QColor("blue"))
        painter.setBrush(QColor("blue"))
        arrow_p1 = QPointF(x2 - arrow_size * math.cos(angle - math.pi / 6), y2 - arrow_size * math.sin(angle - math.pi / 6))
        arrow_p2 = QPointF(x2 - arrow_size * math.cos(angle + math.pi / 6), y2 - arrow_size * math.sin(angle + math.pi / 6))
        painter.drawPolygon(QPolygonF([QPointF(x2, y2), arrow_p1, arrow_p2]))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MapWindow()
    window.show()
    sys.exit(app.exec_())
