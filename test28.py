import sys
import math
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QComboBox
from PyQt5.QtGui import QPainter, QColor, QPolygonF, QMouseEvent
from PyQt5.QtCore import Qt, QPointF, pyqtSlot  # 添加 pyqtSlot 導入
from PIL import Image
import subprocess

class MapWindow(QMainWindow):
    def __init__(self, yaml_files, pgm_files):
        super().__init__()

        # 保存 YAML 和 PGM 文件路径
        self.yaml_files = yaml_files
        self.pgm_files = pgm_files

        # 设置窗口标题
        self.setWindowTitle('Map with Control Buttons, Image Selector, and Grid')
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

        # 记录模式状态
        self.recording_mode = False

    @pyqtSlot()
    def toggle_set_point_mode(self):
        """切换点位记录模式"""
        self.recording_mode = not self.recording_mode
        if self.recording_mode:
            self.set_point_button.setStyleSheet("background-color: orange")
            self.label.recording_mode = True
            print("已进入点位记录模式")
        else:
            self.set_point_button.setStyleSheet("")
            self.label.recording_mode = False
            print("已退出点位记录模式")

    def load_map_metadata(self, index):
        """根据选择的地图读取 YAML 文件中的元数据"""
        with open(self.yaml_files[index], 'r') as file:
            map_info = yaml.safe_load(file)

        self.resolution = map_info['resolution']
        self.origin = map_info['origin']

    def start_process(self):
        print("START 按钮被点击")
        subprocess.Popen([
            "xterm", "-e", "bash -c 'cd ~/wheeltec_ros2 && source install/setup.bash && ros2 launch wheeltec_nav2 wheeltec_nav2.launch.py; exec bash'"
        ])

    def stop_process(self):
        print("STOP 按钮被点击")
        subprocess.Popen([
            "xterm", "-e", "bash -c 'pkill -f ros2; exec bash'"
        ])

    def home_process(self):
        print("HOME 按钮被点击")

    def clear_points(self):
        """清除所有记录的点位和方向"""
        self.label.clear_points()

class MapLabel(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedSize(1000, 800)
        self.setStyleSheet("background-color: lightgray;")
        self.recording_mode = False
        self.points = []  # 存储所有点击的位置
        self.directions = []  # 存储所有的箭头

    def mousePressEvent(self, event: QMouseEvent):
        if self.recording_mode:
            if len(self.points) % 2 == 0:
                # 第一次点击，记录起点
                self.points.append(event.pos())
            else:
                # 第二次点击，记录终点并生成箭头
                start_point = self.points[-1]
                end_point = event.pos()
                self.directions.append((start_point, end_point))
                self.points.pop()  # 移除起点，不再显示红点
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)

        # 画箭头
        painter.setPen(QColor("blue"))
        for start_point, end_point in self.directions:
            painter.drawLine(start_point, end_point)
            self.draw_arrow_head(painter, start_point, end_point)

    def draw_arrow_head(self, painter, start_point, end_point):
        """绘制箭头"""
        arrow_size = 10
        angle = math.atan2(start_point.y() - end_point.y(), start_point.x() - end_point.x())

        arrow_p1 = end_point + QPointF(arrow_size * math.cos(angle + math.pi / 6),
                                       arrow_size * math.sin(angle + math.pi / 6))
        arrow_p2 = end_point + QPointF(arrow_size * math.cos(angle - math.pi / 6),
                                       arrow_size * math.sin(angle - math.pi / 6))

        arrow_head = QPolygonF([end_point, arrow_p1, arrow_p2])
        painter.drawPolygon(arrow_head)

    def clear_points(self):
        """清除所有记录的点位和方向"""
        self.points = []
        self.directions = []
        self.update()

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
