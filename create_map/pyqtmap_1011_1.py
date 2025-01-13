import sys
import os
import subprocess
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QPushButton, QWidget, QLineEdit, QMessageBox, QInputDialog

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
        self.save_name_input.setPlaceholderText("輸入地圖名稱（例如：1F）")
        main_layout.addWidget(self.save_name_input)

        # 建立 "啟動建圖" 按鈕
        self.start_button = QPushButton('啟動建圖', self)
        self.start_button.clicked.connect(self.start_mapping)
        main_layout.addWidget(self.start_button)

        # 建立 "保存地圖" 按鈕
        self.save_button = QPushButton('保存地圖', self)
        self.save_button.clicked.connect(self.save_map)
        main_layout.addWidget(self.save_button)

        # 新增 "查看已有地圖" 按鈕
        self.view_maps_button = QPushButton('查看已有地圖', self)
        self.view_maps_button.clicked.connect(self.view_existing_maps)
        main_layout.addWidget(self.view_maps_button)

        # 新增 "刪除地圖" 按鈕
        self.delete_map_button = QPushButton('刪除地圖', self)
        self.delete_map_button.clicked.connect(self.delete_map)
        main_layout.addWidget(self.delete_map_button)

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
        """保存地圖並執行編譯"""
        map_name = self.save_name_input.text().strip()
        if not map_name:
            QMessageBox.warning(self, 'Warning', "請輸入地圖名稱")
            return

        # 設定保存路徑的格式
        save_path = f"/home/sr/wheeltec_ros2/src/wheeltec_robot_nav2/map/{map_name}"

        try:
            # 執行保存地圖的命令
            self.save_map_process = subprocess.Popen(f"bash -c 'cd ~/wheeltec_ros2 && source install/setup.bash && ros2 run nav2_map_server map_saver_cli -f {save_path}'", shell=True, executable='/bin/bash')
            self.save_map_process.wait()  # 等待保存完成

            # 更新狀態標籤
            self.status_label.setText(f"地圖保存至 {save_path}")
            
            # 執行 colcon build
            build_process = subprocess.Popen("bash -c 'cd ~/wheeltec_ros2 && source install/setup.bash && colcon build'", shell=True, executable='/bin/bash')
            build_process.wait()  # 等待編譯完成

            # 更新狀態標籤
            self.status_label.setText("地圖已保存並已重新編譯")
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"保存地圖或編譯失敗: {e}")


    def view_existing_maps(self):
        """查看當前已有的地圖列表"""
        map_directory = "/home/sr/wheeltec_ros2/src/wheeltec_robot_nav2/map"
        try:
            # 列出地圖目錄中的檔案，過濾出 .yaml 和 .pgm 檔案
            map_files = sorted([f for f in os.listdir(map_directory) if f.endswith('.yaml') or f.endswith('.pgm')])
            
            if map_files:
                # 將地圖檔案逐行顯示
                maps_list = "\n".join(map_files)
                QMessageBox.information(self, "已有地圖", f"已找到以下地圖檔案：\n{maps_list}")
            else:
                QMessageBox.information(self, "已有地圖", "目前沒有已保存的地圖檔案")
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"無法讀取地圖目錄: {e}")

    def delete_map(self):
        """刪除選定的地圖"""
        map_directory = "/home/sr/wheeltec_ros2/src/wheeltec_robot_nav2/map"
        try:
            # 列出地圖目錄中的 .yaml 和 .pgm 檔案
            map_files = [f for f in os.listdir(map_directory) if f.endswith('.yaml') or f.endswith('.pgm')]
            
            if not map_files:
                QMessageBox.information(self, "刪除地圖", "目前沒有可刪除的地圖檔案")
                return

            # 隱藏副檔名，僅顯示檔案名稱
            map_file_names = [os.path.splitext(f)[0] for f in map_files]
            
            # 彈出選擇框讓使用者選擇要刪除的地圖檔案
            map_to_delete, ok = QInputDialog.getItem(self, "選擇要刪除的檔案", "選擇檔案：", sorted(set(map_file_names)), 0, False)
            
            if ok and map_to_delete:
                # 刪除選定的 .yaml 和 .pgm 檔案（如果存在）
                yaml_file_path = os.path.join(map_directory, f"{map_to_delete}.yaml")
                pgm_file_path = os.path.join(map_directory, f"{map_to_delete}.pgm")
                
                # 刪除 .yaml 檔案
                if os.path.exists(yaml_file_path):
                    os.remove(yaml_file_path)
                    print(f"已刪除檔案：{yaml_file_path}")
                
                # 刪除 .pgm 檔案
                if os.path.exists(pgm_file_path):
                    os.remove(pgm_file_path)
                    print(f"已刪除檔案：{pgm_file_path}")
                    
                QMessageBox.information(self, "刪除地圖", f"已刪除地圖：{map_to_delete}")
            else:
                QMessageBox.information(self, "刪除地圖", "未選擇任何檔案")
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"無法刪除地圖檔案: {e}")


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
