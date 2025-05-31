import os
import time
import sqlite3
import threading
import requests
import math
from PIL import Image, UnidentifiedImageError
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QPushButton, 
                            QLabel, QWidget, QProgressBar, QHBoxLayout, QDialog, 
                            QGridLayout, QSizePolicy)
from PyQt5.QtGui import QIcon, QFont
from requests.exceptions import ConnectionError

class Windows10ProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Загрузка карт")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowModality(Qt.WindowModal)
        self.setFixedSize(450, 220)
        
        self.setWindowIcon(QIcon.fromTheme("folder"))
        self.setFont(QFont("Segoe UI", 9))
        
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("Загрузка тайлов карты")
        font = self.title_label.font()
        font.setPointSize(10)
        font.setBold(True)
        self.title_label.setFont(font)
        header_layout.addWidget(self.title_label, 1)
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.setFixedSize(90, 28)
        header_layout.addWidget(self.cancel_button)
        
        layout.addLayout(header_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        layout.addWidget(self.progress_bar)
        
        progress_info_layout = QGridLayout()
        progress_info_layout.setHorizontalSpacing(25)
        
        self.status_label = QLabel("Подготовка...")
        self.status_label.setStyleSheet("color: #666666; font-size: 9pt;")
        progress_info_layout.addWidget(self.status_label, 0, 0, 1, 2)
        
        self.speed_label = QLabel("Скорость: -")
        self.speed_label.setStyleSheet("color: #666666; font-size: 9pt;")
        progress_info_layout.addWidget(self.speed_label, 1, 0)
        
        self.remaining_label = QLabel("Осталось: -")
        self.remaining_label.setStyleSheet("color: #666666; font-size: 9pt;")
        progress_info_layout.addWidget(self.remaining_label, 1, 1)
        
        layout.addLayout(progress_info_layout)
        
        self.details_button = QPushButton("Подробности ▼")
        self.details_button.setFlat(True)
        self.details_button.setStyleSheet("text-align: left; color: #0066CC; font-size: 9pt;")
        self.details_button.clicked.connect(self.toggle_details)
        layout.addWidget(self.details_button)
        
        self.details_widget = QWidget()
        details_layout = QVBoxLayout()
        details_layout.setContentsMargins(0, 5, 0, 0)
        details_layout.setSpacing(8)
        
        self.zoom_label = QLabel("Уровень масштабирования: -")
        self.zoom_label.setStyleSheet("font-size: 9pt;")
        details_layout.addWidget(self.zoom_label)
        
        self.tiles_label = QLabel("Тайлов: 0 из 0")
        self.tiles_label.setStyleSheet("font-size: 9pt;")
        details_layout.addWidget(self.tiles_label)
        
        self.details_widget.setLayout(details_layout)
        self.details_widget.hide()
        layout.addWidget(self.details_widget)
        
        self.setLayout(layout)
        
        self.start_time = time.time()
        self.last_update_time = self.start_time
        self.last_downloaded = 0
        self.download_speed = 0
    
    def toggle_details(self):
        if self.details_widget.isVisible():
            self.details_widget.hide()
            self.details_button.setText("Подробности ▼")
            self.setFixedHeight(220)
        else:
            self.details_widget.show()
            self.details_button.setText("Подробности ▲")
            self.setFixedHeight(270)
    
    def update_progress(self, downloaded, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(downloaded)
        self.tiles_label.setText(f"Тайлов: {downloaded} из {total}")
        
        current_time = time.time()
        time_diff = current_time - self.last_update_time
        
        if time_diff > 0.5:
            downloaded_diff = downloaded - self.last_downloaded
            self.download_speed = downloaded_diff / time_diff
            self.last_update_time = current_time
            self.last_downloaded = downloaded
            
            if self.download_speed > 0:
                self.speed_label.setText(f"Скорость: {self.download_speed:.1f} тайлов/сек")
                remaining = total - downloaded
                if remaining > 0 and self.download_speed > 0:
                    remaining_time = remaining / self.download_speed
                    self.remaining_label.setText(f"Осталось: {self.format_time(remaining_time)}")
                else:
                    self.remaining_label.setText("Осталось: -")
            else:
                self.speed_label.setText("Скорость: -")
                self.remaining_label.setText("Осталось: -")
    
    def format_time(self, seconds):
        if seconds < 60:
            return f"{int(seconds)} сек"
        elif seconds < 3600:
            return f"{int(seconds // 60)} мин {int(seconds % 60)} сек"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours} ч {minutes} мин"
    
    def closeEvent(self, event):
        # При закрытии окна отправляем сигнал для остановки загрузки
        if hasattr(self.parent(), 'stop_download'):
            self.parent().stop_download()
        event.accept()

class MapDownloaderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Offline Map Downloader")
        self.setGeometry(100, 100, 400, 200)
        
        font = self.font()
        font.setPointSize(10)
        self.setFont(font)
        
        self.initUI()
        self.downloader = None
        self.total_tiles = 0
        self.downloaded_tiles = 0
        self.progress_dialog = None
    
    def initUI(self):
        central_widget = QWidget()
        layout = QVBoxLayout()
        
        self.download_btn = QPushButton("Начать загрузку")
        self.download_btn.setFixedHeight(35)
        font = self.download_btn.font()
        font.setPointSize(10)
        self.download_btn.setFont(font)
        self.download_btn.clicked.connect(self.start_download)
        layout.addWidget(self.download_btn)
        
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
    
    def start_download(self):
        position_a = (51.686, -0.510)
        position_b = (51.381, 0.148)
        
        self.downloader = OfflineLoader()
        self.downloader.setDownloadArea(position_a, position_b, 0, 16)
        
        self.total_tiles = 0
        self.downloaded_tiles = 0
        
        self.progress_dialog = Windows10ProgressDialog(self)
        self.progress_dialog.cancel_button.clicked.connect(self.stop_download)
        
        self.downloader.signalZoom.connect(self.update_zoom_level)
        self.downloader.signalDownloadCount.connect(self.set_total_tiles)
        self.downloader.signalDownloadCountTile.connect(self.update_downloaded_tiles)
        self.downloader.signalFinished.connect(self.download_finished)
        self.downloader.signalInternetError.connect(self.show_internet_error)
        
        self.progress_dialog.status_label.setText("Загрузка начата...")
        self.progress_dialog.show()
        
        self.downloader.start()
    
    def set_total_tiles(self, count):
        self.total_tiles += count
        self.progress_dialog.update_progress(self.downloaded_tiles, self.total_tiles)
    
    def update_downloaded_tiles(self, count):
        self.downloaded_tiles += 1
        self.progress_dialog.update_progress(self.downloaded_tiles, self.total_tiles)
    
    def update_zoom_level(self, zoom):
        self.progress_dialog.zoom_label.setText(f"Уровень масштабирования: {zoom}")
    
    def stop_download(self):
        if self.downloader:
            self.downloader.stop_download()
            self.progress_dialog.status_label.setText("Загрузка отменена")
            QTimer.singleShot(1000, self.progress_dialog.close)
            self.downloader = None
    
    def download_finished(self):
        if self.progress_dialog:
            self.progress_dialog.status_label.setText("Загрузка завершена")
            QTimer.singleShot(2000, self.progress_dialog.close)
    
    def show_internet_error(self):
        if self.progress_dialog:
            self.progress_dialog.status_label.setText("Ошибка: Нет подключения к интернету")
            QTimer.singleShot(2000, self.progress_dialog.close)


class OfflineLoader(QThread):
    signalDownloadCountTile = pyqtSignal(int)
    signalDownloadCount = pyqtSignal(int)
    signalZoom = pyqtSignal(int)
    signalFinished = pyqtSignal()
    signalInternetError = pyqtSignal()
    
    def __init__(self, path=None, tileServer=None, name_server=None, maxZoom=19, parent=None):
        super().__init__(parent)
        self.tileServer = tileServer or "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"
        self.name_server = name_server or "OpenStreetMap"
        self.maxZoom = maxZoom
        
        # Database setup
        db_name = f"{self.name_server}.db"
        self.db_path = os.path.join(path or os.getcwd(), db_name)
        
        # Threading setup
        self.task_queue = []
        self.result_queue = []
        self.thread_pool = []
        self.lock = threading.Lock()
        self.number_of_threads = 50
        self.running = True
        self.force_stop = False
        self.position_a = None
        self.position_b = None
        self.zoom_a = 0
        self.zoom_b = 12
    
    def setDownloadArea(self, position_a, position_b, zoom_a=0, zoom_b=12):
        self.position_a = position_a
        self.position_b = position_b
        self.zoom_a = zoom_a
        self.zoom_b = zoom_b
    
    def save_offline_tiles_thread(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        cursor = conn.cursor()
        last_request_time = 0
        REQUEST_DELAY = 0.5

        while self.running and not self.force_stop:
            task = None
            with self.lock:
                if self.task_queue:
                    task = self.task_queue.pop()

            if not task:
                time.sleep(0.01)
                continue

            zoom, x, y = task
            try:
                # Проверяем, не скачан ли уже тайл
                cursor.execute(
                    "SELECT 1 FROM tiles WHERE zoom=? AND x=? AND y=? AND server=? LIMIT 1",
                    (zoom, x, y, self.tileServer))

                if not cursor.fetchone():
                    time_since_last = time.time() - last_request_time
                    if time_since_last < REQUEST_DELAY:
                        time.sleep(REQUEST_DELAY - time_since_last)

                    if self.force_stop:
                        break

                    url = self.tileServer.replace("{x}", str(x)).replace("{y}", str(y)).replace("{z}", str(zoom))
                    try:
                        response = requests.get(
                            url,
                            stream=True,
                            headers={"User-Agent": "PyQtMapView"},
                            timeout=20
                        )
                        response.raise_for_status()
                        image_data = response.content

                        with self.lock:
                            self.result_queue.append((zoom, x, y, self.tileServer, image_data))
                    except requests.exceptions.RequestException as e:
                        print(f"Failed to download tile {zoom}/{x}/{y}: {str(e)}")
                        with self.lock:
                            self.task_queue.append(task)
                        continue
                    
                    last_request_time = time.time()
                else:
                    with self.lock:
                        self.result_queue.append((zoom, x, y, self.tileServer, None))

            except (sqlite3.OperationalError, UnidentifiedImageError) as e:
                print(f"Database/Image error: {str(e)}")
                with self.lock:
                    self.task_queue.append(task)
            except Exception as e:
                print(f"Unexpected error: {str(e)}")
                with self.lock:
                    self.task_queue.append(task)

        conn.close()
    
    def load_task_queue(self, position_a, position_b, zoom=0):
        if self.force_stop:
            return

        try:
            upperLeftTilePos = decimal_to_osm(*position_a, zoom)
            lowerRightTilePos = decimal_to_osm(*position_b, zoom)
            
            if zoom == 0:
                tasks = [(0, 0, 0)]
            else:
                tasks = []
                x_start = max(0, math.floor(upperLeftTilePos[0]))
                x_end = min(2**zoom - 1, math.ceil(lowerRightTilePos[0]))
                y_start = max(0, math.floor(upperLeftTilePos[1]))
                y_end = min(2**zoom - 1, math.ceil(lowerRightTilePos[1]))
                
                for x in range(x_start, x_end + 1):
                    for y in range(y_start, y_end + 1):
                        tasks.append((zoom, x, y))
            
            with self.lock:
                self.task_queue.extend(tasks)
                self.number_of_tasks = len(self.task_queue)
            
            self.signalZoom.emit(zoom)
            self.signalDownloadCount.emit(self.number_of_tasks)
        except Exception as e:
            print(f"Error in load_task_queue: {str(e)}")

    def run(self):
        if self.position_b is None:
            print("position_b is None")
            return
        
        # Проверка интернета перед началом загрузки
        try:
            requests.get("https://www.google.com", timeout=5)
        except ConnectionError:
            self.signalInternetError.emit()
            return
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS server (
                        url VARCHAR(300) PRIMARY KEY NOT NULL,
                        maxZoom INTEGER NOT NULL
                    )""")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tiles (
                        zoom INTEGER NOT NULL,
                        x INTEGER NOT NULL,
                        y INTEGER NOT NULL,
                        server VARCHAR(300) NOT NULL,
                        tile_image BLOB NOT NULL,
                        PRIMARY KEY (zoom, x, y, server),
                        FOREIGN KEY (server) REFERENCES server (url)
                    )""")
                
                cursor.execute("SELECT 1 FROM server WHERE url=? LIMIT 1", (self.tileServer,))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO server (url, maxZoom) VALUES (?, ?)", 
                                 (self.tileServer, self.maxZoom))
                conn.commit()
        except Exception as e:
            print(f"Database initialization error: {str(e)}")
            return
        
        self.thread_pool = [
            threading.Thread(daemon=True, target=self.save_offline_tiles_thread)
            for _ in range(self.number_of_threads)
        ]
        
        for thread in self.thread_pool:
            thread.start()
        
        self.running = True
        self.force_stop = False
        
        try:
            for zoom in range(round(self.zoom_a), round(self.zoom_b + 1)):
                if self.force_stop:
                    break
                    
                self.load_task_queue(self.position_a, self.position_b, zoom)
                
                result_counter = 0
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    while result_counter < self.number_of_tasks and self.running and not self.force_stop:
                        result = None
                        
                        with self.lock:
                            if self.result_queue:
                                result = self.result_queue.pop()
                        
                        if result:
                            result_counter += 1
                            if result[-1] is not None:
                                cursor.execute(
                                    "INSERT INTO tiles (zoom, x, y, server, tile_image) VALUES (?, ?, ?, ?, ?)",
                                    result)
                                conn.commit()
                            
                            self.signalDownloadCountTile.emit(result_counter)
                        else:
                            time.sleep(0.01)
                
                if self.force_stop:
                    break
        
        except Exception as e:
            print(f"Download error: {str(e)}")
        finally:
            self.running = False
            if not self.force_stop:
                self.signalFinished.emit()
    
    def stop_download(self):
        print("stop")
        self.force_stop = True
        self.running = False



def decimal_to_osm(lat_deg: float, lon_deg: float, zoom: int) -> tuple:
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = (lon_deg + 180.0) / 360.0 * n
    ytile = (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n
    return xtile, ytile


if __name__ == "__main__":
    app = QApplication([])
    window = MapDownloaderApp()
    window.show()
    app.exec_()