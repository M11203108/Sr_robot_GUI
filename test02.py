import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QSpacerItem, QFrame, QDesktopWidget
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QPixmap, QPainter, QColor

import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid
from geometry_msgs.msg import PoseWithCovarianceStamped

# 定義一個 ROS 2 節點，用於處理地圖和機器人姿態的訊息
class RobotStateNode(Node):
    def __init__(self):
        super().__init__('robot_state_node')
        # 訂閱地圖的主題
        self.map_subscriber = self.create_subscription(OccupancyGrid, '/map', self.map_callback, 10)
        # 訂閱機器人姿態的主題
        self.pose_subscriber = self.create_subscription(PoseWithCovarianceStamped, '/amcl_pose', self.pose_callback, 10)
        # 保存當前的地圖和機器人姿態
        self.current_pose = None
        self.current_map = None

    # 地圖的回調函數
    def map_callback(self, msg):
        self.get_logger().info('地圖已接收')
        self.current_map = msg

    # 姿態的回調函數
    def pose_callback(self, msg):
        self.get_logger().info('姿態已接收')
        self.current_pose = msg.pose.pose

    # 返回當前的機器人姿態
    def get_current_pose(self):
        return self.current_pose

    # 返回當前的地圖
    def get_current_map(self):
        return self.current_map

# 自定義的地圖顯示元件，用於在 GUI 中顯示地圖和機器人位置
class MapWidget(QLabel):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(800, 800)
        self.setFrameShape(QFrame.Box)
        self.setLineWidth(3)
        self.setStyleSheet("QFrame { border: 8px solid black; }")
        self.map_image = None  # 保存地圖圖像
        self.robot_pose = None  # 保存機器人位置

    # 從 .pgm 文件加載地圖圖像
    def load_map(self, image_path):
        self.map_image = QPixmap(image_path)
        self.update()  # 更新顯示

    # 更新地圖和機器人位置
    def update_map(self, map_data, robot_pose):
        self.robot_pose = robot_pose
        self.update()  # 重新繪製地圖和機器人位置

    # 重寫 paintEvent 方法，繪製地圖和機器人位置
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.map_image is None:
            return

        # 獲取 QLabel 的大小
        widget_width = self.width()
        widget_height = self.height()

        # 獲取圖像的大小
        image_width = self.map_image.width()
        image_height = self.map_image.height()

        # 計算圖像縮放比例
        scale_x = widget_width / image_width
        scale_y = widget_height / image_height
        scale = min(scale_x, scale_y)

        # 計算縮放後的圖像大小
        scaled_width = int(image_width * scale)
        scaled_height = int(image_height * scale)

        # 計算圖像在 QLabel 中居中的位置
        x = (widget_width - scaled_width) // 2
        y = (widget_height - scaled_height) // 2

        # 繪製縮放後的圖像
        painter = QPainter(self)
        painter.drawPixmap(x, y, scaled_width, scaled_height, self.map_image)

        # 如果有機器人位置數據，則在地圖上繪製機器人位置
        if self.robot_pose is not None:
            # 將機器人位置轉換為圖像坐標
            map_resolution = 1.0  # 預設分辨率（像素/米）
            origin_x = 0.0  # 預設原點
            origin_y = 0.0  # 預設原點

            # 計算機器人的像素位置
            robot_x = int((self.robot_pose.position.x - origin_x) / map_resolution) * scale + x
            robot_y = (self.map_image.height() - int((self.robot_pose.position.y - origin_y) / map_resolution)) * scale + y

            painter.setPen(QColor("red"))
            painter.drawEllipse(robot_x - 5, robot_y - 5, 10, 10)  # 繪製紅色圓圈表示機器人位置

        painter.end()  # 結束繪製

# 主窗口類，包含地圖顯示元件和控制按鈕
class MainWindow(QMainWindow):
    def __init__(self, node):
        super().__init__()

        self.node = node
        self.setWindowTitle("控制界面")

        # 創建地圖顯示元件
        self.map_widget = MapWidget()
        self.map_widget.load_map('/home/sr/wheeltec_ros2/src/wheeltec_robot_nav2/map/WHEELTEC.pgm')

        # 創建按鈕
        self.start_button = QPushButton("START\n啟動")
        self.stop_button = QPushButton("STOP\n停止")
        home_button = QPushButton("HOME\n回原點")

        # 設定按鈕大小
        self.start_button.setFixedSize(250, 300)
        self.stop_button.setFixedSize(250, 300)
        home_button.setFixedSize(250, 300)

        # 設定按鈕顏色和字體大小
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
        
        # 創建一個垂直佈局包含地圖畫面和標籤
        map_layout = QVBoxLayout()
        map_layout.setContentsMargins(0, 0, 0, 0)
        map_layout.addWidget(self.map_widget)
        
        map_label = QLabel("地圖畫面")
        map_label.setAlignment(Qt.AlignCenter)
        map_label.setStyleSheet("font-size: 24px; padding: 5px;")
        
        map_layout.addWidget(map_label)

        # 讓 map_widget 填充剩餘空間
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

        # 創建定時器來更新機器人位置
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_map)
        self.timer.start(1000)

        self.process = None  # 保存啟動的進程

    @pyqtSlot()
    def start_process(self):
        if self.process is None or self.process.poll() is not None:
            # 啟動 ROS2 程式
            self.process = subprocess.Popen(
                [
                    "bash", "-c",
                    "cd /home/sr/wheeltec_ros2/ && source install/setup.bash && ros2 launch wheeltec_nav2 wheeltec_nav2.launch.py"
                ]
            )
            subprocess.Popen(
                [
                    "bash", "-c",
                    "cd /home/sr/wheeltec_ros2/ && source install/setup.bash && ros2 launch wheeltec_nav2 waypoint_2point.py"
                ]
            )

    @pyqtSlot()
    def stop_process(self):
        if self.process is not None:
            self.process.terminate()
            self.process.wait()
            self.process = None

    @pyqtSlot()
    def update_map(self):
        map_data = self.node.get_current_map()
        pose = self.node.get_current_pose()
        self.map_widget.update_map(map_data, pose)

    def closeEvent(self, event):
        if self.process is not None:
            self.process.terminate()
            self.process.wait()
        rclpy.shutdown()
        super().closeEvent(event)

if __name__ == "__main__":
    rclpy.init()
    node = RobotStateNode()

    app = QApplication(sys.argv)
    window = MainWindow(node)
    window.show()

    # 使用 QTimer 來調用 rclpy.spin_once
    def ros_spin():
        rclpy.spin_once(node, timeout_sec=0.1)

    timer = QTimer()
    timer.timeout.connect(ros_spin)
    timer.start(100)

    sys.exit(app.exec_())
