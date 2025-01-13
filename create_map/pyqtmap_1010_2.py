import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QPushButton, QWidget, QLineEdit, QMessageBox

class MapBuilderWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 儲存啟動的進程 ID 方便關閉時進行處理
        self.mapping_process = None
        self.save_map_process = None

        # 設定視窗標題和大小
        self.setWindowTitle('Map Builder')
        self.setFixedSize(400, 300)

        # 建立主佈局
        main_layout = QVBoxLayout()

        # 建立顯示訊息的標籤
        self.status_label = QLabel('點擊按鈕來建立地圖', self)
        main_layout.addWidget(self.status_label)

        # 建立保存名稱輸入框
        self.save_name_input = QLineEdit(self)
        self.save_name_input.setPlaceholderText("輸入地圖名稱（例如：WHEELTEC1）")
        main_layout.addWidget(self.save_name_input)

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
            # 啟動建圖的命令，使用 subprocess 啟動新進程
            self.mapping_process = subprocess.Popen("bash -c 'cd ~/wheeltec_ros2 && source install/setup.bash && ros2 launch wheeltec_slam_toolbox online_async_launch.py'", shell=True, executable='/bin/bash')
            self.status_label.setText("建圖啟動中...")
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"啟動建圖失敗: {e}")

    def save_map(self):
        """保存地圖"""
        map_name = self.save_name_input.text().strip()
        if not map_name:
            QMessageBox.warning(self, 'Warning', "請輸入地圖名稱")
            return

        # 設定保存路徑的格式
        save_path = f"/home/sr/wheeltec_ros2/src/wheeltec_robot_nav2/map/{map_name}"

        try:
            # 執行保存地圖的命令
            self.save_map_process = subprocess.Popen(f"bash -c 'cd ~/wheeltec_ros2 && source install/setup.bash && ros2 run nav2_map_server map_saver_cli -f {save_path}'", shell=True, executable='/bin/bash')
            self.status_label.setText(f"地圖保存至 {save_path}")
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"保存地圖失敗: {e}")

    def closeEvent(self, event):
        """視窗關閉事件觸發，執行停止操作"""
        reply = QMessageBox.question(self, '退出', "確定要退出並停止建圖進程嗎?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # 當用戶選擇 Yes 時，關閉視窗並停止建圖進程
            self.stop_mapping()
            event.accept()
        else:
            # 用戶選擇 No 時，取消關閉事件
            event.ignore()

    def stop_mapping(self):
        """停止建圖進程"""
        if self.mapping_process:
            self.mapping_process.terminate()  # 終止建圖進程
            self.mapping_process.wait()  # 等待進程結束
            self.mapping_process = None
            print("建圖進程已停止")

        if self.save_map_process:
            self.save_map_process.terminate()  # 終止保存地圖的進程
            self.save_map_process.wait()
            self.save_map_process = None
            print("保存地圖進程已停止")

        self.status_label.setText("建圖進程已停止")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MapBuilderWindow()
    window.show()
    sys.exit(app.exec_())
