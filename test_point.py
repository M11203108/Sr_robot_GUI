import sys
import math
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtGui import QPixmap, QPainter, QColor, QMouseEvent, QPolygonF
from PyQt5.QtCore import Qt, QPointF

class SimpleMapWindow(QMainWindow):
    def __init__(self, map_image_path):
        super().__init__()

        # 设置窗口标题和尺寸
        self.setWindowTitle('Simple Map Viewer with Grid and Direction')
        self.setFixedSize(800, 600)

        # 加载地图图像
        self.label = MapLabel(map_image_path, self)
        layout = QVBoxLayout()
        layout.addWidget(self.label)

        # 设置中心窗口
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

class MapLabel(QLabel):
    def __init__(self, map_image_path, parent):
        super().__init__(parent)
        self.map_image_path = map_image_path
        self.pixmap = QPixmap(self.map_image_path)
        self.points = []  # 存储所有点击的位置
        self.directions = []  # 存储所有的方向箭头

        # 设置图像
        self.setPixmap(self.pixmap)
        self.setFixedSize(self.pixmap.size())

    def mousePressEvent(self, event: QMouseEvent):
        # 获取鼠标点击的位置
        if len(self.points) % 2 == 0:
            # 偶数次点击，添加新点
            self.points.append(event.pos())
        else:
            # 奇数次点击，计算方向并添加方向箭头
            start_point = self.points[-1]
            end_point = event.pos()
            self.directions.append((start_point, end_point))  # 存储方向
            self.points.pop()  # 移除最后一个点（第二次点击不显示红点）
        
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)

        # 绘制辅助格线
        self.draw_grid(painter)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("red"))

        # 绘制所有点击位置的点
        for i, point in enumerate(self.points):
            if i % 2 == 0:  # 只在第一次点击时绘制红色圆点
                painter.drawEllipse(QPointF(point), 10, 10)  # 10x10 像素的红色圆点

        # 绘制所有方向
        painter.setPen(QColor("blue"))
        painter.setBrush(Qt.NoBrush)
        for start_point, end_point in self.directions:
            painter.drawLine(start_point, end_point)
            self.draw_direction(painter, start_point, end_point)

    def draw_grid(self, painter):
        """在地图上绘制辅助格线"""
        grid_spacing = 50  # 格线间距为50像素
        painter.setPen(QColor(200, 200, 200))  # 灰色的格线颜色

        # 绘制垂直格线
        for x in range(0, self.width(), grid_spacing):
            painter.drawLine(x, 0, x, self.height())

        # 绘制水平格线
        for y in range(0, self.height(), grid_spacing):
            painter.drawLine(0, y, self.width(), y)

    def draw_direction(self, painter, start_point, end_point):
        """绘制方向箭头"""
        arrow_size = 10  # 箭头的大小
        angle = math.atan2(start_point.y() - end_point.y(), start_point.x() - end_point.x())

        # 箭头的两个边角
        arrow_p1 = end_point + QPointF(arrow_size * math.cos(angle + math.pi / 6),
                                       arrow_size * math.sin(angle + math.pi / 6))
        arrow_p2 = end_point + QPointF(arrow_size * math.cos(angle - math.pi / 6),
                                       arrow_size * math.sin(angle - math.pi / 6))

        # 画箭头
        arrow_head = QPolygonF([end_point, arrow_p1, arrow_p2])
        painter.drawPolygon(arrow_head)

if __name__ == '__main__':
    # 地图图像路径
    map_image_path = '/home/sr/wheeltec_ros2/src/wheeltec_robot_nav2/map/WHEELTEC.pgm'

    app = QApplication(sys.argv)
    window = SimpleMapWindow(map_image_path)
    window.show()
    sys.exit(app.exec_())
