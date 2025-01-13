import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QPushButton, QWidget, QLineEdit, QMessageBox

class MapBuilderWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 設定視窗標題和大小
        self.setWindowTitle('Map Builder')
        self.setFixedSize(400, 300)

        # 建立主佈局
        main_layout = QVBoxLayout()

        # 建立顯示訊息的標籤
        self.status_label = QLabel('點擊按鈕來建立地圖', self)
        main_layout.addWidget(self.status_label)

        # 建立保存路徑輸入框
        self.save_path_input = QLineEdit(self)
        self.save_path_input.setPlaceholderText("輸入保存地圖的路徑")
        main_layout.addWidget(self.save_path_input)

        # 建立 "啟動建圖" 按鈕
        self.start_button = QPushButton('啟動建圖', self)
        self.start_button.clicked.connect(self.start_mapping)
        main_layout.addWidget(self.start_button)

        # 建立 "保存地圖" 按鈕
        self.save_button = QPushButton('保存地圖', self)
        self.save_button.clicked.connect(self.save_map)
        main_layout.addWidget(self.save_button)

        # 設定主視窗的佈局
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def start_mapping(self):
        """啟動建圖流程"""
        try:
            # 執行啟動建圖的命令
            subprocess.Popen("bash -c 'cd ~/wheeltec_ros2 && source install/setup.bash && ros2 launch wheeltec_slam_toolbox online_async_launch.py'", shell=True, executable='/bin/bash')
            self.status_label.setText("建圖啟動中...")
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"啟動建圖失敗: {e}")

    def save_map(self):
        """保存地圖"""
        save_path = self.save_path_input.text().strip()
        if not save_path:
            QMessageBox.warning(self, 'Warning', "請輸入保存地圖的路徑")
            return

        try:
            # 執行保存地圖的命令
            subprocess.Popen(f"bash -c 'cd ~/wheeltec_ros2 && source install/setup.bash && ros2 run nav2_map_server map_saver_cli -f {save_path}'", shell=True, executable='/bin/bash')
            self.status_label.setText(f"地圖保存至 {save_path}")
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"保存地圖失敗: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MapBuilderWindow()
    window.show()
    sys.exit(app.exec_())
