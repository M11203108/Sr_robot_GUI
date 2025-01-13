import sys
import yaml
import json
import math
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QComboBox
from PyQt5.QtGui import QPixmap, QPainter, QColor, QMouseEvent, QPolygonF
from PyQt5.QtCore import Qt, pyqtSlot, QPointF
from PIL import Image
import subprocess

class MapWindow(QMainWindow):
    def __init__(self, yaml_files, pgm_files):
        super().__init__()

        # 保存 YAML 和 PGM 檔案路徑
        self.yaml_files = yaml_files
        self.pgm_files = pgm_files

        # 初始化時加載已保存的點位和方向
        self.load_saved_points()

        # 設定視窗標題
        self.setWindowTitle('保全機器人控制界面')
        self.setFixedSize(1300, 1000)  # 設定固定視窗大小

        # 設定主視窗佈局
        main_layout = QVBoxLayout()

        # 創建下拉式選單
        self.combo_box = QComboBox(self)
        self.combo_box.addItem("選擇地圖")  # 添加空白選項
        self.combo_box.addItems([f"地圖 {i + 1}" for i in range(len(pgm_files))])
        self.combo_box.currentIndexChanged.connect(self.update_map)  # 連接選單變更事件
        main_layout.addWidget(self.combo_box)

        # 創建按鈕並設定其樣式
        self.start_button = QPushButton("啟動\nSTART")
        self.stop_button = QPushButton("停止\nSTOP")
        self.home_button = QPushButton("回原點\nHOME")
        self.set_point_button = QPushButton("設定點位\nSET POINT")
        self.clear_button = QPushButton("清除點位\nCLEAR")

        # 綁定按鈕事件
        self.start_button.clicked.connect(self.start_process)
        self.stop_button.clicked.connect(self.stop_process)
        self.home_button.clicked.connect(self.home_process)
        self.set_point_button.clicked.connect(self.toggle_set_point_mode)
        self.clear_button.clicked.connect(self.clear_points)

        # 設定按鈕大小和顏色
        self.start_button.setFixedSize(120, 150)
        self.start_button.setStyleSheet("background-color: green; color: white; font-size: 18px;")
        self.stop_button.setFixedSize(120, 150)
        self.stop_button.setStyleSheet("background-color: red; color: white; font-size: 18px;")
        self.home_button.setFixedSize(120, 150)
        self.home_button.setStyleSheet("background-color: blue; color: white; font-size: 18px;")
        self.set_point_button.setFixedSize(120, 150)
        self.set_point_button.setStyleSheet("background-color: gray; color: white; font-size: 18px;")
        self.clear_button.setFixedSize(120, 150)
        self.clear_button.setStyleSheet("background-color: orange; color: white; font-size: 18px;")

        # 創建按鈕佈局
        button_layout = QVBoxLayout()
        button_layout.setContentsMargins(20, 20, 20, 20)
        button_layout.setSpacing(20)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.home_button)
        button_layout.addWidget(self.set_point_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()  # 添加彈性空間，確保按鈕在頂部

        # 創建地圖顯示區域
        self.label = MapLabel(self)  # 初始時不顯示地圖

        # 創建數值顯示區域
        self.value_label = QLabel(self)
        self.value_label.setFixedSize(200, 50)
        self.value_label.setStyleSheet("background-color: white; border: 1px solid black;")

        # 創建地圖佈局
        map_layout = QVBoxLayout()
        map_layout.addWidget(self.label)
        map_layout.setContentsMargins(0, 0, 0, 0)

        # 將按鈕佈局和地圖佈局添加到主佈局
        content_layout = QHBoxLayout()
        content_layout.addLayout(button_layout)
        content_layout.addLayout(map_layout)
        main_layout.addLayout(content_layout)
        main_layout.addWidget(self.value_label)

        # 設定中心視窗
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # 綁定滑鼠點擊事件
        self.label.mousePressEvent = self.get_pixel_position

        # 記錄模式狀態
        self.recording_mode = False
        self.current_waypoint = None

    def load_map_metadata(self, index):
        """根據選擇的地圖讀取 YAML 檔案中的元數據"""
        with open(self.yaml_files[index], 'r') as file:
            map_info = yaml.safe_load(file)

        self.resolution = map_info['resolution']
        self.origin = map_info['origin']

    @pyqtSlot()
    def start_process(self):
        print("啟動按鈕被點擊")
        subprocess.Popen([
            "xterm", "-e", "bash -c 'cd ~/wheeltec_ros2 && source install/setup.bash && ros2 launch wheeltec_nav2 wheeltec_nav2.launch.py; exec bash'"
        ])

    @pyqtSlot()
    def stop_process(self):
        print("停止按鈕被點擊")
        subprocess.Popen([
            "xterm", "-e", "bash -c 'pkill -f ros2; exec bash'"
        ])

    @pyqtSlot()
    def home_process(self):
        print("回原點按鈕被點擊")

    @pyqtSlot()
    def toggle_set_point_mode(self):
        """切換點位記錄模式"""
        self.recording_mode = not self.recording_mode
        if self.recording_mode:
            self.set_point_button.setStyleSheet("background-color: orange; color: white; font-size: 18px;")
            self.recorded_points = []  # 清空之前的點位
            self.directions = []  # 清空之前的方向
            print("已進入點位記錄模式")
        else:
            self.set_point_button.setStyleSheet("background-color: gray; color: white; font-size: 18px;")
            self.save_points()  # 保存記錄的點位
            print("已退出點位記錄模式")

    @pyqtSlot()
    def clear_points(self):
        """清除所有記錄的點位"""
        self.recorded_points = []
        self.directions = []
        self.label.update()
        print("所有記錄的點位已清除")

    def save_points(self):
        """保存記錄的點位到檔案"""
        with open('saved_points.json', 'w') as file:
            json.dump({'points': self.recorded_points, 'directions': self.directions}, file)
        print("點位和方向已保存")

    def load_saved_points(self):
        """加載已保存的點位"""
        try:
            with open('saved_points.json', 'r') as file:
                data = json.load(file)
                self.recorded_points = data['points']
                self.directions = data['directions']
                print("已加載保存的點位和方向")
        except FileNotFoundError:
            self.recorded_points = []
            self.directions = []
            print("沒有找到已保存的點位檔案")

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
        # 獲取滑鼠點擊的位置（像素座標）
        px = event.pos().x()
        py = event.pos().y()

        if self.recording_mode:
            if not self.current_waypoint:
                # 記錄點位
                world_x, world_y = self.pixel_to_world(px, py)
                self.current_waypoint = (world_x, world_y)
                print(f"記錄點位: ({world_x:.2f}, {world_y:.2f})")
            else:
                # 計算方向
                waypoint_x, waypoint_y = self.current_waypoint
                robot_x, robot_y = self.pixel_to_world(px, py)
                angle = self.calculate_angle(waypoint_x, waypoint_y, robot_x, robot_y)
                print(f"機器人方向: {angle:.2f} 度")

                # 記錄並顯示點位
                self.recorded_points.append(self.current_waypoint)
                self.directions.append(angle)
                self.current_waypoint = None
                self.label.update()
                print(f"確定機器人朝向: ({robot_x:.2f}, {robot_y:.2f})")
        else:
            # 非記錄模式下顯示座標
            world_x, world_y = self.pixel_to_world(px, py)
            self.value_label.setText(f"世界座標: ({world_x:.2f}, {world_y:.2f})")

    def pixel_to_world(self, px, py):
        """將像素位置轉換為地圖中的世界座標"""
        scaled_px = px / self.label.scale_factor
        scaled_py = py / self.label.scale_factor
        x = self.origin[0] + (scaled_px * self.resolution)
        y = self.origin[1] + ((self.label.image_height - scaled_py) * self.resolution)
        return x, y

    def calculate_angle(self, x1, y1, x2, y2):
        """計算兩點之間的角度"""
        return math.degrees(math.atan2(y2 - y1, x2 - x1))

class MapLabel(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.origin = (0, 0)
        self.resolution = 1
        self.image_height = 1
        self.scale_factor = 1.0  # 初始比例設為 1.0
        self.points = []  # 存儲所有點擊的位置
        self.directions = []  # 存儲所有的方向箭頭

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

    def mousePressEvent(self, event: QMouseEvent):
        # 獲取滑鼠點擊的位置
        if len(self.points) % 2 == 0:
            # 偶數次點擊，添加新點
            self.points.append(event.pos())
        else:
            # 奇數次點擊，計算方向並添加方向箭頭
            start_point = self.points[-1]
            end_point = event.pos()
            self.directions.append((start_point, end_point))  # 存儲方向
            self.points.pop()  # 移除最後一個點（第二次點擊不顯示紅點）
        
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)

        # 繪製輔助格線
        self.draw_grid(painter)

        # 繪製地圖原點
        self.draw_origin(painter)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("red"))

        # 繪製所有點擊位置的點
        for i, point in enumerate(self.points):
            if i % 2 == 0:  # 只在第一次點擊時繪製紅色圓點
                painter.drawEllipse(QPointF(point), 10, 10)  # 10x10 像素的紅色圓點

        # 繪製所有方向
        painter.setPen(QColor("blue"))
        painter.setBrush(Qt.NoBrush)
        for start_point, end_point in self.directions:
            painter.drawLine(start_point, end_point)
            self.draw_direction(painter, start_point, end_point)

    def draw_grid(self, painter):
        """在地圖上繪製輔助格線"""
        grid_spacing = 50  # 格線間距為50像素
        painter.setPen(QColor(200, 200, 200))  # 灰色的格線顏色

        # 繪製垂直格線
        for x in range(0, self.width(), grid_spacing):
            painter.drawLine(x, 0, x, self.height())

        # 繪製水平格線
        for y in range(0, self.height(), grid_spacing):
            painter.drawLine(0, y, self.width(), y)

    def draw_origin(self, painter):
        """繪製地圖原點"""
        painter.setPen(QColor("red"))
        painter.setBrush(QColor("red"))

        # 計算 (0, 0) 點在地圖上的像素位置
        zero_px_x = (-self.origin[0]) / self.resolution * self.scale_factor
        zero_px_y = (self.image_height - (-self.origin[1]) / self.resolution) * self.scale_factor

        # 圓點的半徑
        radius = 5  # 設定為5像素半徑，總大小為10x10像素

        # 繪製圓點，確保圓心在原點位置
        painter.drawEllipse(int(zero_px_x) - radius, int(zero_px_y) - radius, radius * 2, radius * 2)

    def draw_direction(self, painter, start_point, end_point):
        """繪製方向箭頭"""
        arrow_size = 10  # 箭頭的大小
        angle = math.atan2(start_point.y() - end_point.y(), start_point.x() - end_point.x())

        # 箭頭的兩個邊角
        arrow_p1 = end_point + QPointF(arrow_size * math.cos(angle + math.pi / 6),
                                       arrow_size * math.sin(angle + math.pi / 6))
        arrow_p2 = end_point + QPointF(arrow_size * math.cos(angle - math.pi / 6),
                                       arrow_size * math.sin(angle - math.pi / 6))

        # 畫箭頭
        arrow_head = QPolygonF([end_point, arrow_p1, arrow_p2])
        painter.drawPolygon(arrow_head)

    def resizeEvent(self, event):
        """在視窗大小改變時，自動重新縮放地圖"""
        if self.pixmap():
            self.update_image(self.pixmap().toImage(), self.image_height, self.origin, self.resolution)
        super().resizeEvent(event)

    def world_to_pixel(self, x, y):
        """將世界座標轉換為像素位置"""
        px = (x - self.origin[0]) / self.resolution * self.scale_factor
        py = (self.image_height - (y - self.origin[1]) / self.resolution) * self.scale_factor
        return px, py

if __name__ == '__main__':
    # 地圖檔案路徑
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
