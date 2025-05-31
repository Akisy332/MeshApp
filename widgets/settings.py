import sys
import json
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QDialog, 
                             QFormLayout, QDoubleSpinBox, QSpinBox, 
                             QMessageBox, QGroupBox, QCheckBox, QHBoxLayout,
                             QToolButton)
from PyQt5.QtCore import QRegExp, Qt, pyqtSignal
from PyQt5.QtGui import QRegExpValidator, QIcon

class SettingsManager:
    def __init__(self, filename='settings.json'):
        self.filename = filename
        self.default_settings = {
            'ip_address': '192.168.0.1',
            'home_latitude': 56.452018,
            'home_longitude': 84.961598,
            'zoom': 13,
            'use_internet_for_map': False
        }
    
    def load_settings(self):
        """Загружает настройки из файла, если файла нет - возвращает настройки по умолчанию"""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r') as f:
                    return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Ошибка загрузки настроек: {e}")
        
        return self.default_settings.copy()
    
    def save_settings(self, settings):
        """Сохраняет настройки в файл"""
        try:
            with open(self.filename, 'w') as f:
                json.dump(settings, f, indent=4)
            return True
        except IOError as e:
            print(f"Ошибка сохранения настроек: {e}")
            return False

class SettingsDialog(QDialog):   
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setWindowTitle("Настройки")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        # Создаем элементы управления
        self.ip_edit = QLineEdit()
        self.setup_ip_validation()
        
        self.wifi_ssid_edit = QLineEdit()
        
        self.latitude_edit = QDoubleSpinBox()
        self.latitude_edit.setRange(-90, 90)
        self.latitude_edit.setDecimals(6)
        
        self.longitude_edit = QDoubleSpinBox()
        self.longitude_edit.setRange(-180, 180)
        self.longitude_edit.setDecimals(6)
        
        self.zoom_edit = QSpinBox()
        self.zoom_edit.setRange(0, 20)
        
        self.use_internet_checkbox = QCheckBox("Не использовать интернет для загрузки карт")
        self.use_internet_checkbox.setChecked(True)
        
        # Основные кнопки
        self.save_button = QPushButton("Сохранить")
        self.cancel_button = QPushButton("Отмена")
        
        # Настройка layout
        main_layout = QVBoxLayout()
        
        # Группа для настроек конечного модуля
        endpoint_group = QGroupBox("Конечный модуль")
        endpoint_layout = QFormLayout()
        endpoint_layout.addRow("IP адрес:", self.ip_edit)
                
        endpoint_group.setLayout(endpoint_layout)
        
        # Группа для настроек карты
        map_group = QGroupBox("Настройки карты")
        map_layout = QFormLayout()
        map_layout.addRow("Широта дома:", self.latitude_edit)
        map_layout.addRow("Долгота дома:", self.longitude_edit)
        map_layout.addRow("Масштабирование:", self.zoom_edit)
        map_layout.addRow(self.use_internet_checkbox)
        map_group.setLayout(map_layout)
        
        # Группа для основных кнопок
        buttons_group = QGroupBox()
        buttons_layout = QVBoxLayout()
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)
        buttons_group.setLayout(buttons_layout)
        buttons_group.setFlat(True)
        
        # Собираем все вместе
        main_layout.addWidget(endpoint_group)
        main_layout.addWidget(map_group)
        main_layout.addWidget(buttons_group)
        main_layout.addStretch()
        
        self.setLayout(main_layout)
        
        # Подключаем сигналы
        self.save_button.clicked.connect(self.save_and_close)
        self.cancel_button.clicked.connect(self.reject)
    
    def setup_ip_validation(self):
        ip_range = "(?:[0-1]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])"
        ip_regex = QRegExp(f"^{ip_range}\\.{ip_range}\\.{ip_range}\\.{ip_range}$")
        ip_validator = QRegExpValidator(ip_regex, self.ip_edit)
        self.ip_edit.setValidator(ip_validator)
    
    def get_settings(self):
        """Возвращает текущие настройки в виде словаря"""
        return {
            'ip_address': self.ip_edit.text(),
            'home_latitude': self.latitude_edit.value(),
            'home_longitude': self.longitude_edit.value(),
            'zoom': self.zoom_edit.value(),
            'use_internet_for_map': self.use_internet_checkbox.isChecked()
        }
    
    def set_settings(self, settings):
        """Устанавливает настройки из словаря"""
        self.ip_edit.setText(settings.get('ip_address', ''))
        self.latitude_edit.setValue(settings.get('home_latitude', 0))
        self.longitude_edit.setValue(settings.get('home_longitude', 0))
        self.zoom_edit.setValue(settings.get('zoom', 10))
        self.use_internet_checkbox.setChecked(settings.get('use_internet_for_map', False))
    
    def save_and_close(self):
        """Сохраняет настройки и закрывает диалог"""
        if not self.ip_edit.hasAcceptableInput():
            QMessageBox.warning(self, "Ошибка", "Введите корректный IP адрес")
            return
        
        settings = self.get_settings()
        if self.settings_manager.save_settings(settings):
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось сохранить настройки")