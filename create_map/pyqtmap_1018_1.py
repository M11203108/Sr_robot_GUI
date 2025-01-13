import sys
import os
import subprocess
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QPushButton, QWidget, QLineEdit, QMessageBox, QInputDialog, QScrollArea, QHBoxLayout
from PyQt5.QtGui import QPixmap, QTransform, QPainter, QColor, QPen
from PyQt5.QtCore import Qt

class MapBuilderWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.mapping_process = None
        self.save_map_process = None

        self.setWindowTitle('Map Builder')
        self.setFixedSize(800, 800)

        main_layout = QVBoxLayout()

        self.status_label = QLabel('點擊按鈕來建立地圖', self)
        main_layout.addWidget(self.status_label)

        self.save_name_input = QLineEdit(self)
        self.save_name_input.setPlaceholderText("輸入地圖名稱（例如：1F）")
        main_layout.addWidget(self.save_name_input)

        self.start_button = QPushButton('啟動建圖', self)
        self.start_button.clicked.connect(self.start_mapping)
        main_layout.addWidget(self.start_button)

        self.save_button = QPushButton('保存地圖', self)
        self.save_button.clicked.connect(self.save_map)
        main_layout.addWidget(self.save_button)

        self.view_maps_button = QPushButton('查看已有地圖', self)
        self.view_maps_button.clicked.connect(self.view_existing_maps)
        main_layout.addWidget(self.view_maps_button)

        self.delete_map_button = QPushButton('刪除地圖', self)
        self.delete_map_button.clicked.connect(self.delete_map)
        main_layout.addWidget(self.delete_map_button)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)

        self.map_label = QLabel(self)
        self.map_label.setAlignment(Qt.AlignCenter)
        self.scroll_area.setWidget(self.map_label)
        main_layout.addWidget(self.scroll_area)

        control_layout = QHBoxLayout()

        self.rotate_left_button = QPushButton('逆時針旋轉', self)
        self.rotate_left_button.clicked.connect(self.rotate_left)
        control_layout.addWidget(self.rotate_left_button)

        self.rotate_right_button = QPushButton('順時針旋轉', self)
        self.rotate_right_button.clicked.connect(self.rotate_right)
        control_layout.addWidget(self.rotate_right_button)

        self.zoom_in_button = QPushButton('放大', self)
        self.zoom_in_button.clicked.connect(self.zoom_in)
        control_layout.addWidget(self.zoom_in_button)

        self.zoom_out_button = QPushButton('縮小', self)
        self.zoom_out_button.clicked.connect(self.zoom_out)
        control_layout.addWidget(self.zoom_out_button)

        self.zoom_label = QLabel('縮放倍率: 100%', self)
        control_layout.addWidget(self.zoom_label)

        main_layout.addLayout(control_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.current_angle = 0
        self.current_scale = 1.0
        self.current_map_path = None

    def start_mapping(self):
        try:
            self.mapping_process = subprocess.Popen("bash -c 'cd ~/wheeltec_ros2 && source install/setup.bash && ros2 launch wheeltec_slam_toolbox online_async_launch.py'", shell=True, executable='/bin/bash')
            self.status_label.setText("建圖啟動中...")
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"啟動建圖失敗: {e}")

    def save_map(self):
        map_name = self.save_name_input.text().strip()
        if not map_name:
            QMessageBox.warning(self, 'Warning', "請輸入地圖名稱")
            return

        save_path = f"/home/sr/wheeltec_ros2/src/wheeltec_robot_nav2/map/{map_name}"

        try:
            self.save_map_process = subprocess.Popen(f"bash -c 'cd ~/wheeltec_ros2 && source install/setup.bash && ros2 run nav2_map_server map_saver_cli -f {save_path}'", shell=True, executable='/bin/bash')
            self.status_label.setText(f"地圖保存至 {save_path}")
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"保存地圖失敗: {e}")

    def view_existing_maps(self):
        map_directory = "/home/sr/wheeltec_ros2/src/wheeltec_robot_nav2/map"
        try:
            map_files = sorted([f for f in os.listdir(map_directory) if f.endswith('.pgm')])
            if map_files:
                map_file_names = [os.path.splitext(f)[0] for f in map_files]
                map_to_view, ok = QInputDialog.getItem(self, "選擇地圖", "選擇地圖：", map_file_names, 0, False)
                if ok and map_to_view:
                    self.show_map_image(map_directory, map_to_view + '.pgm')
            else:
                QMessageBox.information(self, "已有地圖", "目前沒有已保存的地圖檔案")
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"無法讀取地圖目錄: {e}")

    def show_map_image(self, directory, map_file):
        map_path = os.path.join(directory, map_file)
        self.current_map_path = map_path
        self.update_map_transform()

    def rotate_left(self):
        self.current_angle -= 10
        self.update_map_transform()

    def rotate_right(self):
        self.current_angle += 10
        self.update_map_transform()

    def zoom_in(self):
        self.current_scale += 0.1
        self.update_map_transform()

    def zoom_out(self):
        if self.current_scale > 0.1:
            self.current_scale -= 0.1
            self.update_map_transform()

    def update_map_transform(self):
        if self.current_map_path:
            pixmap = QPixmap(self.current_map_path)
            transform = QTransform()
            transform.rotate(self.current_angle)
            transformed_pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)
            scaled_pixmap = transformed_pixmap.scaled(int(pixmap.width() * self.current_scale),
                                                      int(pixmap.height() * self.current_scale),
                                                      Qt.KeepAspectRatio)

            # 在地圖上繪製比例尺和格線
            painter = QPainter(scaled_pixmap)
            self.draw_grid(painter)
            self.draw_scale(painter)
            painter.end()

            self.map_label.setPixmap(scaled_pixmap)
            self.zoom_label.setText(f'縮放倍率: {int(self.current_scale * 100)}%')

    def draw_grid(self, painter):
        pen = QPen(QColor(200, 200, 200), 1, Qt.DotLine)
        painter.setPen(pen)
        
        for x in range(0, self.map_label.width(), 50):
            painter.drawLine(x, 0, x, self.map_label.height())
        for y in range(0, self.map_label.height(), 50):
            painter.drawLine(0, y, self.map_label.width(), y)

    def draw_scale(self, painter):
        pen = QPen(QColor(0, 0, 0), 2)
        painter.setPen(pen)

        # 假設每個格子的實際長度為 10 公分
        scale_length = 50 * self.current_scale  # 將像素轉換為縮放後的長度
        if scale_length < 100:
            units = '公分'
            display_length = int(scale_length)
        else:
            units = '公尺'
            display_length = scale_length / 100

        painter.drawLine(10, self.map_label.height() - 30, 10 + 50, self.map_label.height() - 30)
        painter.drawText(10, self.map_label.height() - 35, f"{display_length:.1f} {units}")

    def delete_map(self):
        map_directory = "/home/sr/wheeltec_ros2/src/wheeltec_robot_nav2/map"
        try:
            map_files = [f for f in os.listdir(map_directory) if f.endswith('.yaml') or f.endswith('.pgm')]
            if not map_files:
                QMessageBox.information(self, "刪除地圖", "目前沒有可刪除的地圖檔案")
                return

            map_file_names = [os.path.splitext(f)[0] for f in map_files]
            map_to_delete, ok = QInputDialog.getItem(self, "選擇要刪除的檔案", "選擇檔案：", sorted(set(map_file_names)), 0, False)
            if ok and map_to_delete:
                yaml_file_path = os.path.join(map_directory, f"{map_to_delete}.yaml")
                pgm_file_path = os.path.join(map_directory, f"{map_to_delete}.pgm")
                if os.path.exists(yaml_file_path):
                    os.remove(yaml_file_path)
                if os.path.exists(pgm_file_path):
                    os.remove(pgm_file_path)
                QMessageBox.information(self, "刪除地圖", f"已刪除地圖：{map_to_delete}")
            else:
                QMessageBox.information(self, "刪除地圖", "未選擇任何檔案")
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"無法刪除地圖檔案: {e}")

    def closeEvent(self, event):
        reply = QMessageBox.question(self, '退出', "確定要退出並停止建圖進程嗎?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.stop_mapping()
            event.accept()
        else:
            event.ignore()

    def stop_mapping(self):
        if self.mapping_process:
            self.mapping_process.terminate()
            self.mapping_process.wait()
            self.mapping_process = None
        if self.save_map_process:
            self.save_map_process.terminate()
            self.save_map_process.wait()
            self.save_map_process = None
        self.status_label.setText("建圖進程已停止")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MapBuilderWindow()
    window.show()
    sys.exit(app.exec_())
