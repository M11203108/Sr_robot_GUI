import sys
import yaml
import json
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QComboBox
from PyQt5.QtGui import QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt, pyqtSlot, QPointF
from PIL import Image
import subprocess
import math

class MapWindow(QMainWindow):
    def __init__(self, yaml_files, pgm_files):
        super().__init__()

        # 保存 YAML 和 PGM 文件路径
        self.yaml_files = yaml_files
        self.pgm_files = pgm_files

        # 初始化時加載已保存的點位和方向
        self.load_saved_points()

        # 设置窗口标题
        self.setWindowTitle('Map with Control Buttons and Image Selector')
        self.setFixedSize(1300, 1000)  # 设置固定窗口大小

        # 设置主窗口布局
        main_layout = QVBoxLayout()

        # 创建下拉式选单
        self.combo_box = QComboBox(self)
        self.combo_box.addItem("Select a map")  # 添加空白选项
        self.combo_box.addItems([f"Map {i + 1}" for i in range(len(pgm_files))])
        self.combo_box.currentIndexChanged.connect(self.update_map)  # 连接选单变更事件
        main_layout.addWidget(self.combo_box)

        # 创建按钮并设置其样式
        self.start_button = QPushButton("START\n启用")
        self.stop_button = QPushButton("STOP\n停止")
        self.home_button = QPushButton("HOME\n回原点")
        self.set_point_button = QPushButton("SET POINT\n设置点位")
        self.clear_button = QPushButton("CLEAR\n清除点位")

        # 绑定按钮事件
        self.start_button.clicked.connect(self.start_process)
        self.stop_button.clicked.connect(self.stop_process)
        self.home_button.clicked.connect(self.home_process)
        self.set_point_button.clicked.connect(self.toggle_set_point_mode)
        self.clear_button.clicked.connect(self.clear_points)

        # 设置按钮大小和颜色
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

        # 创建按钮布局
        button_layout = QVBoxLayout()
        button_layout.setContentsMargins(20, 20, 20, 20)
        button_layout.setSpacing(20)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.home_button)
        button_layout.addWidget(self.set_point_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()  # 添加伸缩空间，确保按钮在顶部

        # 创建地图显示区域
        self.label = MapLabel(self)  # 初始时不显示地图

        # 创建数值显示区域
        self.value_label = QLabel(self)
        self.value_label.setFixedSize(200, 50)
        self.value_label.setStyleSheet("background-color: white; border: 1px solid black;")

        # 创建地图布局
        map_layout = QVBoxLayout()
        map_layout.addWidget(self.label)
        map_layout.setContentsMargins(0, 0, 0, 0)

        # 将按钮布局和地图布局添加到主布局
        content_layout = QHBoxLayout()
        content_layout.addLayout(button_layout)
        content_layout.addLayout(map_layout)
        main_layout.addLayout(content_layout)
        main_layout.addWidget(self.value_label)

        # 设置中心窗口
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # 绑定鼠标点击事件
        self.label.mousePressEvent = self.get_pixel_position

        # 记录模式状态
        self.recording_mode = False
        self.current_waypoint = None

    def load_map_metadata(self, index):
        """根据选择的地图读取 YAML 文件中的元数据"""
        with open(self.yaml_files[index], 'r') as file:
            map_info = yaml.safe_load(file)

        self.resolution = map_info['resolution']
        self.origin = map_info['origin']

    @pyqtSlot()
    def start_process(self):
        print("START 按钮被点击")
        subprocess.Popen([
            "xterm", "-e", "bash -c 'cd ~/wheeltec_ros2 && source install/setup.bash && ros2 launch wheeltec_nav2 wheeltec_nav2.launch.py; exec bash'"
        ])

    @pyqtSlot()
    def stop_process(self):
        print("STOP 按钮被点击")
        subprocess.Popen([
            "xterm", "-e", "bash -c 'pkill -f ros2; exec bash'"
        ])

    @pyqtSlot()
    def home_process(self):
        print("HOME 按钮被点击")

    @pyqtSlot()
    def toggle_set_point_mode(self):
        """切换点位记录模式"""
        self.recording_mode = not self.recording_mode
        if self.recording_mode:
            self.set_point_button.setStyleSheet("background-color: orange; color: white; font-size: 18px;")
            self.recorded_points = []  # 清空之前的点位
            self.directions = []  # 清空之前的方向
            print("已进入点位记录模式")
        else:
            self.set_point_button.setStyleSheet("background-color: gray; color: white; font-size: 18px;")
            self.save_points()  # 保存记录的点位
            print("已退出点位记录模式")

    @pyqtSlot()
    def clear_points(self):
        """清除所有记录的点位"""
        self.recorded_points = []
        self.directions = []
        self.label.update()
        print("所有记录的点位已清除")

    def save_points(self):
        """保存记录的点位到文件"""
        with open('saved_points.json', 'w') as file:
            json.dump({'points': self.recorded_points, 'directions': self.directions}, file)
        print("点位和方向已保存")

    def load_saved_points(self):
        """加载已保存的点位"""
        try:
            with open('saved_points.json', 'r') as file:
                data = json.load(file)
                self.recorded_points = data['points']
                self.directions = data['directions']
                print("已加载保存的点位和方向")
        except FileNotFoundError:
            self.recorded_points = []
            self.directions = []
            print("没有找到已保存的点位文件")

    def load_image_height(self, pgm_file):
        """获取图片的实际高度（以像素为单位）"""
        image = Image.open(pgm_file)
        return image.height

    def update_map(self, index):
        """更新显示的地图图像和元数据"""
        if index == 0:
            # 空白选项，隐藏地图
            self.label.clear()
            return
        
        selected_index = index - 1  # 因为选单中添加了一个空白选项
        self.load_map_metadata(selected_index)
        selected_pgm_file = self.pgm_files[selected_index]
        self.label.update_image(selected_pgm_file, self.load_image_height(selected_pgm_file), self.origin, self.resolution)

    def get_pixel_position(self, event):
        # 获取鼠标点击的位置（像素坐标）
        px = event.pos().x()
        py = event.pos().y()

        if self.recording_mode:
            if not self.current_waypoint:
                # 记录点位
                world_x, world_y = self.pixel_to_world(px, py)
                self.current_waypoint = (world_x, world_y)
                print(f"记录点位: ({world_x:.2f}, {world_y:.2f})")
            else:
                # 计算方向
                waypoint_x, waypoint_y = self.current_waypoint
                robot_x, robot_y = self.pixel_to_world(px, py)
                angle = self.calculate_angle(waypoint_x, waypoint_y, robot_x, robot_y)
                print(f"机器人方向: {angle:.2f} 度")

                # 记录并显示点位
                self.recorded_points.append(self.current_waypoint)
                self.directions.append(angle)
                self.current_waypoint = None
                self.label.update_image(self.pgm_files[self.combo_box.currentIndex() - 1], self.load_image_height(self.pgm_files[self.combo_box.currentIndex() - 1]), self.origin, self.resolution)
                print(f"确定机器人朝向: ({robot_x:.2f}, {robot_y:.2f})")
        else:
            # 非记录模式下显示坐标
            world_x, world_y = self.pixel_to_world(px, py)
            self.value_label.setText(f"世界坐标: ({world_x:.2f}, {world_y:.2f})")

    def pixel_to_world(self, px, py):
        """将像素位置转换为地图中的世界坐标"""
        scaled_px = px / self.label.scale_factor
        scaled_py = py / self.label.scale_factor
        x = self.origin[0] + (scaled_px * self.resolution)
        y = self.origin[1] + ((self.label.image_height - scaled_py) * self.resolution)
        return x, y

    def calculate_angle(self, x1, y1, x2, y2):
        """计算两点之间的角度"""
        return math.degrees(math.atan2(y2 - y1, x2 - x1))

class MapLabel(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.origin = (0, 0)
        self.resolution = 1
        self.image_height = 1
        self.scale_factor = 1.0  # 初始比例设为 1.0

    def update_image(self, pgm_file, image_height, origin, resolution):
        """更新显示的地图图像，并自动缩放以适应窗口"""
        self.image_height = image_height
        self.origin = origin
        self.resolution = resolution
        pixmap = QPixmap(pgm_file)

        # 自动缩放以适应 QLabel 大小
        scaled_pixmap = pixmap.scaled(
            self.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.scale_factor = scaled_pixmap.width() / pixmap.width()  # 更新缩放比例
        self.setPixmap(scaled_pixmap)
        self.update()

    def clear(self):
        """清除显示的地图图像"""
        self.setPixmap(QPixmap())
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setPen(QColor("red"))

        # 计算 (0, 0) 点在地图上的像素位置
        zero_px_x = (-self.origin[0]) / self.resolution * self.scale_factor
        zero_px_y = (self.image_height - (-self.origin[1]) / self.resolution) * self.scale_factor

        # 绘制红点表示原点
        painter.drawEllipse(int(zero_px_x), int(zero_px_y), 5, 5)  # 5x5 像素的圆点

        # 绘制记录的点位
        if hasattr(self.parent(), 'recorded_points'):
            for idx, point in enumerate(self.parent().recorded_points):
                world_x, world_y = point
                px, py = self.world_to_pixel(world_x, world_y)
                painter.drawEllipse(int(px), int(py), 10, 10)  # 10x10 像素的圆点
                painter.drawText(int(px + 10), int(py + 10), str(idx + 1))  # 显示序号
                
                # 绘制方向
                if idx < len(self.parent().directions):
                    angle = self.parent().directions[idx]
                    self.draw_direction(painter, px, py, angle)

        painter.end()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setPen(QColor("red"))

        # 计算 (0, 0) 点在地图上的像素位置
        zero_px_x = (-self.origin[0]) / self.resolution * self.scale_factor
        zero_px_y = (self.image_height - (-self.origin[1]) / self.resolution) * self.scale_factor

        # 绘制红点表示原点
        painter.drawEllipse(int(zero_px_x), int(zero_px_y), 5, 5)  # 5x5 像素的圆点

        # 绘制记录的点位及其方向
        if hasattr(self.parent(), 'recorded_points'):
            for idx, point in enumerate(self.parent().recorded_points):
                world_x, world_y = point
                px_x, px_y = self.world_to_pixel(world_x, world_y)

                # 绘制点位
                painter.setBrush(QColor("yellow"))
                painter.drawEllipse(QPointF(px_x, px_y), 8, 8)  # 8x8 像素的圆点

                # 计算并绘制方向
                if idx < len(self.parent().directions):
                    angle = math.radians(self.parent().directions[idx])
                    arrow_length = 20  # 箭头长度
                    dx = arrow_length * math.cos(angle)
                    dy = -arrow_length * math.sin(angle)  # Y轴像素是反的

                    arrow = QPolygonF([
                        QPointF(px_x, px_y),
                        QPointF(px_x + dx, px_y + dy)
                    ])

                    painter.setPen(QColor("blue"))
                    painter.drawPolyline(arrow)


    def resizeEvent(self, event):
        """在窗口大小改变时，自动重新缩放地图"""
        if self.pixmap():
            self.update_image(self.pixmap().toImage(), self.image_height, self.origin, self.resolution)
        super().resizeEvent(event)

    def world_to_pixel(self, x, y):
        """将世界坐标转换为像素位置"""
        px = (x - self.origin[0]) / self.resolution * self.scale_factor
        py = (self.image_height - (y - self.origin[1]) / self.resolution) * self.scale_factor
        return px, py

if __name__ == '__main__':
    # 地图文件路径
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
