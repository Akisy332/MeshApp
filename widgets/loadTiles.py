from PyQt5.QtWidgets import  QPushButton, QDialog, QVBoxLayout, QLabel, QWidget, QProgressBar, QDialog, QMessageBox, QHBoxLayout
from PyQt5.QtCore import QThread, pyqtSignal,  pyqtSlot
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5 import uic

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

import os
import time
import sys

from PyQtMapView import MapView, Marker
from PyQtMapView import OfflineLoader

from typing import TYPE_CHECKING

from ui.uiLoadTiles import Ui_Form


if TYPE_CHECKING:
    from gui import MainWindow

class loadTiles(QDialog):
    def __init__(self, gui: "MainWindow", lat, lon, zoom, dataPath: str = None):
        super().__init__()
        self.setWindowTitle("Offline Map Downloader")
        self.setGeometry(100, 100, 400, 200)
        
        font = self.font()
        font.setPointSize(10)
        self.setFont(font)
    
        self.downloader = None
        self.total_tiles = 0
        self.downloaded_tiles = 0
        self.progress_dialog = None
        
        
        self.gui = gui
        self.dataPath = dataPath
        
        self.ui = Ui_Form()  # Создаем экземпляр
        self.ui.setupUi(self) 
        
        # Validation of input fields
        self.validate()
        
        # Map
        layout = QVBoxLayout()
        self.ui.widgetMapDownload.setLayout(layout) # load widgetMap from .ui file
        self.map = MapView(homeCoord=(lat, lon))
        self.map.setZoom(zoom)
        self.map.add_right_click_menu_command("Левый верхний угол", self.setLeftUpCorner, True)
        self.map.add_right_click_menu_command("Правый нижний угол", self.setRightBottomCorner, True)
        layout.addWidget(self.map)
        
        self.ui.pushButtonDownload.clicked.connect(self.start_download)
                
        self.ui.lineEditBottomRightLat.textChanged.connect(self.update_markers)
        self.ui.lineEditBottomRightLon.textChanged.connect(self.update_markers)
        self.ui.lineEditTopLeftLat.textChanged.connect(self.update_markers)
        self.ui.lineEditTopLeftLon.textChanged.connect(self.update_markers)
        
        self.update_markers()
    
    def update_markers(self):
        # Получаем координаты из полей ввода
        pos1 = (float(self.ui.lineEditBottomRightLat.text()), 
                float(self.ui.lineEditBottomRightLon.text()))
        pos2 = (float(self.ui.lineEditTopLeftLat.text()), 
                float(self.ui.lineEditTopLeftLon.text()))
        
        # Если маркеры уже существуют - обновляем их позиции
        if hasattr(self, 'marker1') and self.marker1:
            self.marker1.setPosition(*pos1)
        else:
            self.marker1 = Marker(pos1, "Нижний правый")
            self.map.addElement(self.marker1)
            
        if hasattr(self, 'marker2') and self.marker2:
            self.marker2.setPosition(*pos2)
        else:
            self.marker2 = Marker(pos2, "Левый верхний")
            self.map.addElement(self.marker2)
            
    def setLeftUpCorner(self, coords):
        self.ui.lineEditTopLeftLat.setText(str(coords[0])[:10])
        self.ui.lineEditTopLeftLon.setText(str(coords[1])[:10])
        self.marker2.setPosition(coords[0],coords[1])
        
    def setRightBottomCorner(self, coords):
        self.ui.lineEditBottomRightLat.setText(str(coords[0])[:10])
        self.ui.lineEditBottomRightLon.setText(str(coords[1])[:10])
        self.marker1.setPosition(coords[0],coords[1])
    
    def validate(self):
        self.ui.lineEditTopLeftLat.setValidator(DoubleValidator(-90, 90, 8))
        self.ui.lineEditTopLeftLon.setValidator(DoubleValidator(-180, 180, 8))

        self.ui.lineEditBottomRightLat.setValidator(DoubleValidator(-90, 90, 8))
        self.ui.lineEditBottomRightLon.setValidator(DoubleValidator(-180, 180, 8))
        
        self.ui.lineEditZoomMin.setValidator(IntValidator(0, 22, self))
        self.ui.lineEditZoomMax.setValidator(IntValidator(0, 22, self))
        
    def checkConditions(self):
        self.TopLeftLat = self.ui.lineEditTopLeftLat.text().strip().replace(',', '.')
        self.TopLeftLon = self.ui.lineEditTopLeftLon.text().strip().replace(',', '.')
        self.BottomRightLat = self.ui.lineEditBottomRightLat.text().strip().replace(',', '.')
        self.BottomRightLon = self.ui.lineEditBottomRightLon.text().strip().replace(',', '.')
        
        self.zoomMin = self.ui.lineEditZoomMin.text().strip()
        self.zoomMax = self.ui.lineEditZoomMax.text().strip()
        
        if not self.TopLeftLat:
            QMessageBox.warning(self, "Ошибка", "Поле не должно быть пустым!")
            return False
        if not self.TopLeftLon:
            QMessageBox.warning(self, "Ошибка", "Поле не должно быть пустым!")
            return False
        if not self.BottomRightLat:
            QMessageBox.warning(self, "Ошибка", "Поле не должно быть пустым!")
            return False
        if not self.BottomRightLon:
            QMessageBox.warning(self, "Ошибка", "Поле не должно быть пустым!")
            return False
        
        self.TopLeftLat = float(self.TopLeftLat)
        self.TopLeftLon = float(self.TopLeftLon)
        self.BottomRightLat = float(self.BottomRightLat)
        self.BottomRightLon = float(self.BottomRightLon)
        
        # print(self.TopLeftLat,
        #     self.TopLeftLon,
        #     self.BottomRightLat,
        #     self.BottomRightLon)
                
        if not self.zoomMin:
            QMessageBox.warning(self, "Ошибка", "Поле не должно быть пустым!")
            return False
        if not self.zoomMax:
            QMessageBox.warning(self, "Ошибка", "Поле не должно быть пустым!")
            return False
        
        self.zoomMin = int(self.zoomMin)
        self.zoomMax = int(self.zoomMax)

        return True
    
    def start_download(self):     
        if self.checkConditions():  
            mapLayers = self.map.getTileServer()
            
            if self.dataPath is None:
                self.dataPath = "dataBase"
            if not os.path.exists(self.dataPath):
                os.makedirs(self.dataPath)
                
            self.downloader = OfflineLoader(path=self.dataPath, 
                                tileServer=mapLayers.get("tileServer"),
                                name_server=mapLayers.get("nameDir"))

            self.downloader.setDownloadArea((self.TopLeftLat, self.TopLeftLon), (self.BottomRightLat, self.BottomRightLon), self.zoomMin, self.zoomMax)

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
        
        # Добавлено поле "Прошло:"
        self.elapsed_label = QLabel("Прошло: -")
        self.elapsed_label.setStyleSheet("color: #666666; font-size: 9pt;")
        progress_info_layout.addWidget(self.elapsed_label, 2, 0)
        
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
        
        # Таймер для обновления времени "Прошло:"
        self.elapsed_timer = QTimer(self)
        self.elapsed_timer.timeout.connect(self.update_elapsed_time)
        self.elapsed_timer.start(1000)  # Обновление каждую секунду
    
    def update_elapsed_time(self):
        elapsed_seconds = time.time() - self.start_time
        self.elapsed_label.setText(f"Прошло: {self.format_time(elapsed_seconds)}")
    
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
        # Останавливаем таймер при закрытии окна
        self.elapsed_timer.stop()
        # При закрытии окна отправляем сигнал для остановки загрузки
        if hasattr(self.parent(), 'stop_download'):
            self.parent().stop_download()
        event.accept()

        
class IntValidator(QIntValidator):
    def validate(self, a0: str, a1: int):
        """
        Overwrite this method to add better restriction
        when user type a value.
        It checks if the value user inserted is not in
        the boundaries, then prevent typing more than of
        the boundaries.
        """
        res = super().validate(a0, a1)
        try:
            if not self.bottom() <= int(a0) <= self.top():
                res = (0, a0, a1)
        except ValueError:
            return res
        return res

class DoubleValidator(QDoubleValidator):
    def validate(self, a0: str, a1: int):
        """
        Overwrite this method to add better restriction
        when user type a value.
        It checks if the value user inserted is not in
        the boundaries, then prevent typing more than of
        the boundaries.
        """
        res = super().validate(a0, a1)
        try:
            if not self.bottom() <= int(a0) <= self.top():
                res = (0, a0, a1)
        except ValueError:
            return res
        return res
