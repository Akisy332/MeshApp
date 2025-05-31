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
            'wifi_ssid': '',
            'wifi_password': '',
            'home_latitude': 55.7558,
            'home_longitude': 37.6173,
            'zoom': 10,
            'use_internet_for_map': True
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
    wifi_load_requested = pyqtSignal(str, str)  # Сигнал для загрузки WiFi настроек
    
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
        
        # Поле пароля с кнопкой показа/скрытия
        self.password_layout = QHBoxLayout()
        self.wifi_password_edit = QLineEdit()
        self.wifi_password_edit.setEchoMode(QLineEdit.Password)
        
        self.toggle_password_button = QToolButton()
        self.toggle_password_button.setCheckable(True)
        self.toggle_password_button.setChecked(False)
        self.toggle_password_button.setIcon(QIcon.fromTheme("visibility-off"))
        self.toggle_password_button.toggled.connect(self.toggle_password_visibility)
        
        self.password_layout.addWidget(self.wifi_password_edit)
        self.password_layout.addWidget(self.toggle_password_button)
        
        # Кнопка загрузки WiFi
        self.load_wifi_button = QPushButton("Загрузить")
        self.load_wifi_button.clicked.connect(self.emit_wifi_load_signal)
        
        self.latitude_edit = QDoubleSpinBox()
        self.latitude_edit.setRange(-90, 90)
        self.latitude_edit.setDecimals(6)
        
        self.longitude_edit = QDoubleSpinBox()
        self.longitude_edit.setRange(-180, 180)
        self.longitude_edit.setDecimals(6)
        
        self.zoom_edit = QSpinBox()
        self.zoom_edit.setRange(0, 20)
        
        self.use_internet_checkbox = QCheckBox("Использовать интернет для загрузки карт")
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
        
        # Подгруппа для WiFi настроек
        wifi_group = QGroupBox("WiFi подключение")
        wifi_layout = QFormLayout()
        wifi_layout.addRow("Имя сети (SSID):", self.wifi_ssid_edit)
        
        # Виджет для поля пароля с кнопкой
        password_widget = QWidget()
        password_widget.setLayout(self.password_layout)
        wifi_layout.addRow("Пароль:", password_widget)
        
        # Добавляем кнопку загрузки WiFi
        wifi_layout.addRow(self.load_wifi_button)
        
        wifi_group.setLayout(wifi_layout)
        endpoint_layout.addRow(wifi_group)
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
    
    def emit_wifi_load_signal(self):
        """Инициирует загрузку WiFi настроек"""
        ssid = self.wifi_ssid_edit.text()
        password = self.wifi_password_edit.text()
        self.wifi_load_requested.emit(ssid, password)
        QMessageBox.information(self, "WiFi", "Попытка подключения к WiFi...")
    
    def toggle_password_visibility(self, checked):
        """Переключает видимость пароля"""
        if checked:
            self.wifi_password_edit.setEchoMode(QLineEdit.Normal)
            self.toggle_password_button.setIcon(QIcon.fromTheme("visibility"))
        else:
            self.wifi_password_edit.setEchoMode(QLineEdit.Password)
            self.toggle_password_button.setIcon(QIcon.fromTheme("visibility-off"))
    
    def setup_ip_validation(self):
        ip_range = "(?:[0-1]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])"
        ip_regex = QRegExp(f"^{ip_range}\\.{ip_range}\\.{ip_range}\\.{ip_range}$")
        ip_validator = QRegExpValidator(ip_regex, self.ip_edit)
        self.ip_edit.setValidator(ip_validator)
    
    def get_settings(self):
        """Возвращает текущие настройки в виде словаря"""
        return {
            'ip_address': self.ip_edit.text(),
            'wifi_ssid': self.wifi_ssid_edit.text(),
            'wifi_password': self.wifi_password_edit.text(),
            'home_latitude': self.latitude_edit.value(),
            'home_longitude': self.longitude_edit.value(),
            'zoom': self.zoom_edit.value(),
            'use_internet_for_map': self.use_internet_checkbox.isChecked()
        }
    
    def set_settings(self, settings):
        """Устанавливает настройки из словаря"""
        self.ip_edit.setText(settings.get('ip_address', ''))
        self.wifi_ssid_edit.setText(settings.get('wifi_ssid', ''))
        self.wifi_password_edit.setText(settings.get('wifi_password', ''))
        self.latitude_edit.setValue(settings.get('home_latitude', 0))
        self.longitude_edit.setValue(settings.get('home_longitude', 0))
        self.zoom_edit.setValue(settings.get('zoom', 10))
        self.use_internet_checkbox.setChecked(settings.get('use_internet_for_map', True))
    
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Главное окно")
        self.setGeometry(100, 100, 600, 400)
        
        self.settings_manager = SettingsManager()
        self.current_settings = self.settings_manager.load_settings()
        
        self.settings_button = QPushButton("Открыть настройки", self)
        self.settings_button.clicked.connect(self.open_settings)
        
        self.settings_group = QGroupBox("Текущие настройки")
        self.settings_label = QLabel()
        self.update_settings_label()
        
        settings_layout = QVBoxLayout()
        settings_layout.addWidget(self.settings_label)
        self.settings_group.setLayout(settings_layout)
        
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.settings_button)
        layout.addWidget(self.settings_group)
        layout.addStretch()
        central_widget.setLayout(layout)
        
        self.setCentralWidget(central_widget)
    
    def open_settings(self):
        dialog = SettingsDialog(self.settings_manager, self)
        dialog.set_settings(self.current_settings)
        
        # Подключаем сигнал загрузки WiFi к нашему методу
        dialog.wifi_load_requested.connect(self.init_wifi_connection)
        
        if dialog.exec_() == QDialog.Accepted:
            self.current_settings = dialog.get_settings()
            self.update_settings_label()
            print("Настройки обновлены:", self.current_settings)
    
    def init_wifi_connection(self, ssid, password):
        """Метод для инициализации WiFi подключения"""
        print(f"Попытка подключения к WiFi: SSID={ssid}, Password={password}")
        # Здесь должна быть ваша логика подключения к WiFi
        # Например, вызов внешнего API или системных команд
        
        # Пример реализации:
        if ssid:
            QMessageBox.information(self, "WiFi", f"Подключаемся к сети {ssid}...")
            # Ваш код для подключения к WiFi
        else:
            QMessageBox.warning(self, "Ошибка", "Не указано имя сети WiFi")
    
    def update_settings_label(self):
        internet_status = "Да" if self.current_settings['use_internet_for_map'] else "Нет"
        wifi_password = "********" if self.current_settings['wifi_password'] else "не задан"
        text = f"""
        <b>IP адрес:</b> {self.current_settings['ip_address']}<br>
        <b>WiFi SSID:</b> {self.current_settings['wifi_ssid'] or "не задано"}<br>
        <b>WiFi пароль:</b> {wifi_password}<br>
        <b>Широта дома:</b> {self.current_settings['home_latitude']}<br>
        <b>Долгота дома:</b> {self.current_settings['home_longitude']}<br>
        <b>Масштаб:</b> {self.current_settings['zoom']}<br>
        <b>Использование интернета для карты:</b> {internet_status}
        """
        self.settings_label.setText(text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())