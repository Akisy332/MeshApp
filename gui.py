import sys
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QMainWindow, QLabel
from PyQt5 import uic
from PyQt5.QtCore import Qt, QTimer, QThread

from PIL import Image, ImageDraw
import os
import threading
import time

from widgets.interMap import interMap
from widgets.infoTables import CustomTableWidget
from widgets.loadTiles import loadTiles
from widgets.console import ConsoleWidget
from dataHandlers import SerialPortWorker, TCPClientWorker, WiFiWorker
from data import userData,  SessionLogger, SessionDialog
from widgets.settings import SettingsDialog, SettingsManager


import sys
import serial.tools.list_ports
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QAction, QMenuBar
from PyQt5.QtWidgets import  QPushButton, QDialog, QWidget, QProgressBar, QMessageBox, QHBoxLayout
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                             QWidget, QListWidget, QDialog, QLabel, QHBoxLayout, 
                             QMessageBox, QTextEdit, QInputDialog, QListWidgetItem)
from PyQt5.QtCore import Qt, QDateTime


from ui.uiWidgets import Ui_MainWindow

def retry(retries=3, delay=0.5):
    def decor(func):
        def wrap(*args, **kwargs):
            for i in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f'Retrying {func.__name__}: {i}/{retries}')
                    time.sleep(delay)
                    if(i == retries-1):
                        raise e
        return wrap
    return decor

class MainWindow(QMainWindow):
    WIDTH = 1000  # Ширина окна
    HEIGHT = 500  # Высота окна
    
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()  # Создаем экземпляр
        self.ui.setupUi(self) 
        # uic.loadUi("ui/widgets.ui", self)  # Загружаем .ui файл
        self.ui.splitter.setStretchFactor(0,1)
        self.ui.splitter.setStretchFactor(1,0)

        # Дополнительные настройки, если нужно
        self.setWindowTitle("SkyWings")
        
        self.init_settings()
        self.ui.actionSettings.triggered.connect(self.open_settings)

        self.logger = SessionLogger()
        self.session_path = self.logger.initialize_session()
        self.ui.loadSession.triggered.connect(self.load_session)
        self.ui.newSession.triggered.connect(self.create_new_session)
        


        self.data = userData(self)
    
        self.current_path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        
        self.init_map()

        self.ui.console.setVisible(False)
        self.console = ConsoleWidget(self)
        
        self.ui.addTable_1.triggered.connect(self.data.randAbonent)
        self.ui.actionLoadTiles.triggered.connect(self.openLoadTilesWindow)
        self.ui.menuPortList.aboutToShow.connect(self.updatePortMenu)

        self.ui.action.triggered.connect(self.open_port)
        self.ui.action_2.triggered.connect(self.close_port)
        
        self.ui.actionTCPOpen.triggered.connect(self.openTCP)
        self.ui.actionTCPClose.triggered.connect(self.closeTCP)
        
        self.ui.actionWiFiOpen.triggered.connect(self.openWiFi)
        self.ui.actionWiFiClose.triggered.connect(self.closeWiFi)   
        
                
        # Создаем таблицу
        self.init_table()



        self.data.signalNewDataAbonent.connect(self.map.update_trace)
        
        self.show()
        
        self.serial_worker = None
        self.tcp_worker = None
        self.WiFi_worker = None
        
        self.selected_port = None

        self.updateUI()


    # Map
    def init_map(self):
        self.layoutMap = QVBoxLayout()
        self.ui.widgetMap.setLayout(self.layoutMap) # load widgetMap from .ui file
        lat = self.current_settings['home_latitude']
        lon = self.current_settings['home_longitude']
        zoom = self.current_settings['zoom']
        useDataBaseOnly = self.current_settings['use_internet_for_map']
        self.map = interMap(self, lat, lon, zoom, useDataBaseOnly)
        self.layoutMap.addWidget(self.map.map)

    # Table
    def init_table(self):
        # Создаем таблицу
        self.table = CustomTableWidget(self.ui.tableAbonent)  # Ваша кастомная таблица
        
        # Настройка layout родительского виджета
        layout = QVBoxLayout(self.ui.tableAbonent)
        layout.addWidget(self.table)
        
        # Убираем отступы layout (опционально)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Первоначальное заполнение
        self.table.update_from_dict(self.data.dataAbonent)
        
        # Подключаем сигналы
        self.table.checkbox_visible.connect(self.on_checkbox_visible)
        self.table.checkbox_trace.connect(self.on_checkbox_trace)
        
        self.table.row_deleted.connect(self.map.deleteAbonent)
        self.table.row_deleted.connect(self.data.deleteAbonent)
        
        self.table.name_changed.connect(self.change_name)
        
        # self.tables.signalTpToMarker.connect(self.map.choosePlace)
        
    def on_checkbox_visible(self, source, checked):
        self.data.dataAbonent[source]['visible'] = checked
        self.map.updateMarkers(self.data.dataAbonent)
        self.map.update_trace(source, self.data.dataAbonent[source])
    
    def on_checkbox_trace(self, source, checked):
        self.data.dataAbonent[source]['traceFlag'] = checked
        self.map.update_trace(source, self.data.dataAbonent[source])
    
    
    # Session
    def create_new_session(self):
        description, ok = QInputDialog.getMultiLineText(
            self, 
            "Новая сессия", 
            "Введите описание сессии:",
            ""
        )

        if ok and description:
            session_name, self.session_path = self.logger.create_new_session(description)

            QMessageBox.information(
                self, 
                "Успех", 
                f"Создана новая сессия: {session_name}\nОписание: {description}"
            )
            self.data.closeApp()
            self.table.delete_all_rows()
            
    def load_session(self):
        dialog = SessionDialog(self.logger, self)
        if dialog.exec_() == QDialog.Accepted:
            session = dialog.selected_session()
            
            if session:
                self.map.clearMap()
                if os.path.exists(self.session_path):
                    self.data.closeApp()
                self.table.clear_table()
                
                self.session_path = session['path']
                users = self.logger.get_session_users(session['path'])
                
                msg = (
                    f"Загружена сессия: {session['name']}\n"
                    f"Дата: {session['date']}\n"
                    f"Описание: {session['description']}\n"
                    f"Количество пользователей: {len(users)}"
                )
                
                data = self.data.newSession()
                self.table.update_from_dict(data)
                self.updateUI()
                QMessageBox.information(self, "Информация о сессии", msg)   
                       

    # Settings
    def init_settings(self):
        # Менеджер настроек
        self.settings_manager = SettingsManager()
        self.current_settings = self.settings_manager.load_settings()
        self.update_settings()

    def open_settings(self):
        dialog = SettingsDialog(self.settings_manager, self)
        dialog.set_settings(self.current_settings)
        
        if dialog.exec_() == QDialog.Accepted:
            self.current_settings = dialog.get_settings()
            self.update_settings()
            print("Настройки обновлены:", self.current_settings)
    
    def update_settings(self):
        self.WiFiIP = self.current_settings['ip_address']

    
    def change_name(self, source, name):
        self.data.dataAbonent[source]["text"] = name
        self.logger.save_session_users(self.session_path, self.data.dataAbonent)
        self.map.updateMarkers(self.data.dataAbonent)
    
    
    def routerTable(self):
        self.serial_worker.transmit("PB,2,0")

    def openLoadTilesWindow(self):
        lat = self.current_settings['home_latitude']
        lon = self.current_settings['home_longitude']
        zoom = self.current_settings['zoom']
        self.temp_window = loadTiles(self, lat, lon, zoom)
        self.temp_window.exec_()
    
    def updateUI(self):
        self.map.updateMarkers(self.data.dataAbonent)
        
        sources = list(self.data.dataAbonent.keys())
        for source in sources:
            data = self.data.dataAbonent[source]
            self.map.update_trace(source, data)

        self.table.update_from_dict(self.data.dataAbonent)



    def updatePortMenu(self):
        self.ui.menuPortList.clear()
        flag = True
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.device.find("ttyS") == -1:
                action = QAction(port.device, self)
                action.triggered.connect(lambda checked, p=port.device: self.onPortSelected(p))
                self.ui.menuPortList.addAction(action)
                flag = False
        if flag:
            action = QAction("Нет подключенных устройств", self)
            self.ui.menuPortList.addAction(action)

    def onPortSelected(self, port):
        print(f"Выбранный порт: {port}")
        self.selected_port = port  # Сохраняем выбранный порт

    def open_port(self):
        port = self.selected_port
        if not self.serial_worker or not self.serial_worker.isRunning():
            self.serial_worker = SerialPortWorker(port, 115200)  # Укажите скорость
            self.serial_worker.rawDataReceived.connect(self.receiveData)
            
            self.serial_worker.statusMessage.connect(self.handle_status_message)
            self.serial_worker.errorMessage.connect(self.handle_error_message)
            self.serial_worker.connectionStatus.connect(self.handle_connection_status)
            
            self.serial_worker.start()

    def close_port(self):
        if self.serial_worker:
            self.serial_worker.stop()
            self.serial_worker.wait()  # Ждем завершения потока
       
    def handle_status_message(self, source, message):
        print(f"Статус: {message}")
        QMessageBox.information(self, f"Статус подключения {source}",f"Статус: {message}")
        
    def handle_error_message(self, source, message):
        print(f"Ошибка: {message}")
        QMessageBox.critical(self, f"Ошибка {source}", message)
        
    def handle_connection_status(self, source, connected):
        status = "подключено" if connected else "отключено"
        print(f"Состояние подключения: {status}")
        QMessageBox.information(self, f"Статус подключения {source}",f"Статус: {status}")
        
    def send_data(self, data):
        if self.serial_worker:
            self.serial_worker.transmit(data)
        else:
            print("Убедитесь в подключении устройства")

    def receiveData(self, source, data):
        self.data.parser(source, data)
        self.updateUI()
        
    def openTCP(self):
        if not self.tcp_worker or not self.tcp_worker.isRunning():
            self.tcp_worker = TCPClientWorker()
            self.tcp_worker.connectionError.connect(self.errorMessage)
            self.tcp_worker.rawDataReceived.connect(self.receiveData)
            self.tcp_worker.statusMessage.connect(self.handle_status_message)
            self.tcp_worker.start()
    
    def errorMessage(self, message):
        QMessageBox.warning(self,"Ошибка", message)

    def closeTCP(self):
        if self.tcp_worker:
            self.tcp_worker.stop()
            self.tcp_worker.wait()  # Ждем завершения потока
            
    def openWiFi(self):

        if not self.WiFi_worker or not self.WiFi_worker.isRunning():
            self.WiFi_worker = WiFiWorker(self.WiFiIP, 8080)
            self.WiFi_worker.rawDataReceived.connect(self.receiveData)
            self.WiFi_worker.connectionError.connect(self.errorMessage)
            self.WiFi_worker.statusMessage.connect(self.handle_status_message)
            self.WiFi_worker.start()
            
    def closeWiFi(self):
        if self.WiFi_worker:
            self.WiFi_worker.stop()
            self.WiFi_worker.wait()  # Ждем завершения потока
        
    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Подтверждение выхода',
                                     "Вы уверены, что хотите выйти?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.data.closeApp()
            event.accept()  # Закрываем приложение
            
        else:
            event.ignore()  # Игнорируем событие закрытия



    
if __name__ == '__main__':
    app = QApplication(sys.argv)  # Создаем приложение
    window = MainWindow()  # Создаем экземпляр главного окна
    sys.exit(app.exec_())  # Запускаем приложение