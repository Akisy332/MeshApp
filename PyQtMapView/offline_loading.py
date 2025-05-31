import os
import time
import sqlite3
import threading
import requests
import sys
import math
from PIL import Image, UnidentifiedImageError
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from .utility_functions import decimal_to_osm


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
        # print(self.db_path)
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