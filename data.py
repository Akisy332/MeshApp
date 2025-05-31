import random
import time
import os
from decimal import Decimal, ROUND_DOWN
from PyQt5.QtCore import pyqtSignal, QObject
import json

from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                             QWidget, QListWidget, QDialog, QLabel, QHBoxLayout, 
                             QMessageBox, QTextEdit, QInputDialog, QListWidgetItem, QMenu, QLineEdit, QGroupBox)
from PyQt5.QtCore import Qt, QDateTime

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gui import MainWindow

colors = {
    'blue': '#1f77b4',
    'orange': '#ff7f0e',
    'green': '#2ca02c',
    'red': '#d62728',
    'purple': '#9467bd',
    'brown': '#8c564b',
    'pink': '#e377c2',
    'gray': '#7f7f7f',
    'olive': '#bcbd22',
    'cyan': '#17becf'
}

class userData(QObject):
    signalNewDataAbonent = pyqtSignal(str, dict)
    def __init__(self, gui: "MainWindow"):
        super().__init__()
        self.gui = gui
        self.lastAbonent = {}
        self.dataAbonent = self.newSession()
        self.currectColor = 0

        self.static = {}

    def newSession(self): 
        self.dataAbonent = self.gui.logger.get_session_users(self.gui.session_path)
        return self.dataAbonent
        
    def setDataAbonent(self, newData):
            
        if newData.get('source') not in self.dataAbonent:
            self.dataAbonent[newData.get('source')] = {
                "lat": newData.get('lat'),
                "lon": newData.get('lon'),
                "alt": newData.get('alt'),
                
                "error": newData.get('error'),
                "time": time.time(),
                "visible": True,
                "text": str(''),
                "traceFlag": False,
                "color": str(self.getNewColor())
            }
            self.gui.logger.add_user_to_session(self.gui.session_path, newData.get('source'), self.dataAbonent[newData.get('source')])
            # print(newData.get('lat'), newData.get('lon'))
            if not newData.get('error'):
                self.gui.logger.add_user_location(self.gui.session_path, newData.get('source'), newData.get('lat'), newData.get('lon'))
        else:
            self.dataAbonent[newData.get('source')].update({
                "lat": newData.get('lat'),
                "lon": newData.get('lon'),
                "alt": newData.get('alt'),
                
                "error": newData.get('error'),
                "time": time.time()
            })
            
            if not newData.get('error'):
                self.gui.logger.add_user_location(self.gui.session_path, newData.get('source'), newData.get('lat'), newData.get('lon'))
            
            
            # lastLat = Decimal(self.lastAbonent.get('lat')).quantize(Decimal('0.00001'), rounding=ROUND_DOWN)
            # lastLon = Decimal(self.lastAbonent.get('lon')).quantize(Decimal('0.00001'), rounding=ROUND_DOWN)
            # lat = Decimal(newData.get('lat')).quantize(Decimal('0.00001'), rounding=ROUND_DOWN)
            # lon = Decimal(newData.get('lon')).quantize(Decimal('0.00001'), rounding=ROUND_DOWN)
            

        self.lastAbonent = newData
        self.gui.updateUI()

    def getNewColor(self) -> str:
        # return "#FF0000"
        color = list(colors.values())
        color = color[self.currectColor]
        if self.currectColor < len(colors.values())-1:
            self.currectColor += 1
        else:
            self.currectColor = 0
        return color

    def parser(self, source: str, decodedLine: str):
        data = {}
        try:
            text = decodedLine.strip()
            values = text.split()
            flag = True
            print(source, text)
            
            if 9 <= len(values) <= 10 and values[0][0]== "G" and values[0][1]== "L":
                if self.static.get(values[1]) is None:
                    
                    self.static[values[1]] = {
                    "Total": 1,
                    "Error": 0,
                    "Current": 0
                    }
                else:
                    self.static[values[1]]["Total"] +=1
                


            if 9 <= len(values) <= 10 and values[0][0]== "G" and values[0][1]== "L" and flag:
                self.gui.console.write(source + text)
                print(source, text)
                data['source'] = str(values[1]) # Unique id
                if not (values[2] == "E" or values[3] == "E" or values[4] == "E"):
                    if -90 <float(values[2]) < 90 and -180 < float(values[3]) < 180:
                        data['lat'] = float(values[2])
                        data['lon'] = float(values[3])
                        data['alt'] = float(values[4])
                        # data['climb'] = float(values[5])
                        # data['speed'] = float(values[6])
                        # data['mode'] = int(values[7])
                        data["error"] = False
                        self.setDataAbonent(data)
                        self.static[values[1]]["Current"] +=1
                    else:    
                        data['error'] = True
                        self.setDataAbonent(data) 
                        self.static[values[1]]["Error"] +=1
                else:
                    data['error'] = True
                    self.setDataAbonent(data) 
                    self.static[values[1]]["Error"] +=1
                    
                # print(self.static)
                    
            # else:
            #     print(decodedLine)
                
        except Exception as e:
            print(values)
            print(f"Error in parser: {e}")
        
    def deleteAbonent(self, source: str):
        if self.dataAbonent.get(source):
            del self.dataAbonent[source]
        self.gui.logger.delete_user_from_session(self.gui.session_path, source)

    def closeApp(self):
        self.gui.logger.save_session_users(self.gui.session_path, self.dataAbonent)
        self.lastAbonent = {}
        self.dataAbonent = {}
        self.currectColor = 0

        self.static = {}
        

    def randData(self):
        source = str(random.randint(0, 10))
        newData = {}
        newData['source'] = source
        newData['lat'] = float(random.uniform(-90.0, 90.0))
        newData['lon'] = float(random.uniform(-180.0, 180.0))
        newData['alt'] = int(random.randint(0, 100))
        newData["error"] = bool(random.randint(0,1))
        return newData

    def randAbonent(self):
        newData = self.randData()
        self.setDataAbonent(newData)



class SessionLogger():
    def __init__(self):
        self.sessions_dir = 'sessions'
        self.session_path = None  # Текущая активная сессия
        if not os.path.exists(self.sessions_dir):
            os.makedirs(self.sessions_dir)
    
    def create_new_session(self, description=""):
        # Создаем папку для сессии с уникальным именем
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd_hh-mm-ss")
        session_name = f"session_{timestamp}"
        session_path = os.path.join(self.sessions_dir, session_name)
        
        os.makedirs(session_path)
        
        # Создаем файл с описанием сессии
        with open(os.path.join(session_path, "description.txt"), 'w') as f:
            f.write(description)
        
        # Создаем пустой users_log.txt
        with open(os.path.join(session_path, "users_log.txt"), 'w') as f:
            json.dump({}, f)
        
        self.session_path = session_path
        return session_name, session_path
    
    def get_all_sessions(self):
        if not os.path.exists(self.sessions_dir):
            return []
        
        sessions = []
        for session_name in sorted(os.listdir(self.sessions_dir), reverse=True):
            session_path = os.path.join(self.sessions_dir, session_name)
            if os.path.isdir(session_path):
                # Читаем описание сессии
                desc_file = os.path.join(session_path, "description.txt")
                description = ""
                if os.path.exists(desc_file):
                    with open(desc_file, 'r', encoding='windows-1251') as f:
                        description = f.read().strip()
                
                sessions.append({
                    'name': session_name,
                    'path': session_path,
                    'description': description,
                    'date': session_name.replace("session_", "").replace("_", " ")
                })
        return sessions
    
    def get_session_users(self, session_path):
        users_log = os.path.join(session_path, "users_log.txt")
        if os.path.exists(users_log):
            with open(users_log, 'r') as f:
                return json.load(f)
        return {}
    
    def save_session_users(self, session_path, users_data):
        users_log = os.path.join(session_path, "users_log.txt")
        with open(users_log, 'w') as f:
            json.dump(users_data, f, indent=4)
    
    def add_user_to_session(self, session_path, user_id, user_data):
        users = self.get_session_users(session_path)
        users[user_id] = user_data
        self.save_session_users(session_path, users)
    
    def add_user_location(self, session_path, user_id, lat, lon):
        user_log_file = os.path.join(session_path, f"{user_id}_log.txt")
        if not os.path.exists(user_log_file):
            open(user_log_file, 'w').close()
        with open(user_log_file, 'a') as f:
            f.write(f"{lat} {lon}\n")
    
    def get_user_locations(self, session_path, user_id):
        user_log_file = os.path.join(session_path, f"{user_id}_log.txt")
        # print(os.path.exists(user_log_file))
        if os.path.exists(user_log_file):
            with open(user_log_file, 'r') as f:
                # Преобразуем каждую строку в список float
                return [[float(value) for value in line.strip().split() if value.strip()] for line in f]
        return 
    
    def delete_user_from_session(self, session_path, user_id):
        # Получаем текущих пользователей сессии
        users = self.get_session_users(session_path)
        
        if user_id not in users:
            return False
        
        # Удаляем пользователя из данных сессии
        del users[user_id]
        self.save_session_users(session_path, users)
        
        # Удаляем файл с логами пользователя, если он существует
        user_log_file = os.path.join(session_path, f"{user_id}_log.txt")
        if os.path.exists(user_log_file):
            os.remove(user_log_file)
        
        return True
    
    def initialize_session(self, session_name=None):
        """
        Инициализирует текущую сессию
        :param session_name: имя конкретной сессии (если None - берет последнюю или создает новую)
        :return: путь к текущей сессии
        """
        sessions = self.get_all_sessions()
        
        if session_name:
            # Ищем конкретную сессию по имени
            for session in sessions:
                if session['name'] == session_name:
                    self.session_path = session['path']
                    return self.session_path
            raise ValueError(f"Сессия {session_name} не найдена")
        
        if sessions:
            # Если есть существующие сессии - берем последнюю
            self.session_path = sessions[0]['path']
        else:
            # Если сессий нет - создаем новую с дефолтным описанием
            self.session_path = self.create_new_session("Автоматически созданная сессия")[1]
        
        return self.session_path
    

class SessionDialog(QDialog):
    def __init__(self, logger, parent=None):
        super().__init__(parent)
        self.logger = logger
        self.setWindowTitle("Выбор сессии")
        self.setFixedSize(600, 400)
        
        self.layout = QVBoxLayout()
        
        # Поле для отображения текущей активной сессии
        self.current_session_group = QGroupBox("Текущая активная сессия")
        self.current_session_layout = QVBoxLayout()
        
        self.session_name_label = QLabel("Имя: не выбрано")
        self.session_desc_label = QLabel("Описание: не выбрано")
        
        self.current_session_layout.addWidget(self.session_name_label)
        self.current_session_layout.addWidget(self.session_desc_label)
        self.current_session_group.setLayout(self.current_session_layout)
        
        self.label = QLabel("Доступные сессии:")
        self.session_list = QListWidget()
        self.session_list.itemDoubleClicked.connect(self.accept)
        self.session_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.session_list.customContextMenuRequested.connect(self.show_context_menu)
        
        self.load_button = QPushButton("Загрузить сессию")
        self.load_button.clicked.connect(self.accept)
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.cancel_button)
        
        self.layout.addWidget(self.current_session_group)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.session_list)
        self.layout.addLayout(button_layout)
        
        self.setLayout(self.layout)
        
        self.populate_sessions()
        self.update_current_session_info()  # Обновляем информацию о текущей сессии
    
    def populate_sessions(self):
        sessions = self.logger.get_all_sessions()
        self.session_list.clear()
        
        for session in sessions:
            item_text = f"{session['date']} - {session['description']}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, session)
            self.session_list.addItem(item)
            
            # Помечаем текущую активную сессию
            if self.logger.session_path and session['path'] == self.logger.session_path:
                item.setBackground(Qt.green)
                self.session_list.setCurrentItem(item)
    
    def update_current_session_info(self):
        """Обновляет информацию о текущей активной сессии"""
        if self.logger.session_path:
            sessions = self.logger.get_all_sessions()
            for session in sessions:
                if session['path'] == self.logger.session_path:
                    self.session_name_label.setText(f"Имя: {session['name']}")
                    self.session_desc_label.setText(f"Описание: {session['description']}")
                    return
        
        self.session_name_label.setText("Имя: не выбрано")
        self.session_desc_label.setText("Описание: не выбрано")
    
    def show_context_menu(self, position):
        item = self.session_list.itemAt(position)
        if not item:
            return
            
        menu = QMenu()
        
        edit_action = menu.addAction("Изменить описание")
        edit_action.triggered.connect(lambda: self.edit_session_description(item))
        
        delete_action = menu.addAction("Удалить")
        delete_action.triggered.connect(lambda: self.delete_session(item))
        
        menu.exec_(self.session_list.viewport().mapToGlobal(position))
    
    def activate_session(self, item):
        """Делает выбранную сессию активной"""
        session = item.data(Qt.UserRole)
        self.logger.session_path = session['path']
        self.update_current_session_info()
        
        # Обновляем подсветку в списке
        for i in range(self.session_list.count()):
            list_item = self.session_list.item(i)
            if list_item.data(Qt.UserRole)['path'] == self.logger.session_path:
                list_item.setBackground(Qt.green)
            else:
                list_item.setBackground(Qt.white)
    
    def edit_session_description(self, item):
        session = item.data(Qt.UserRole)
        new_description, ok = QInputDialog.getText(
            self, 
            "Изменить описание", 
            "Введите новое описание:", 
            QLineEdit.Normal, 
            session['description']
        )
        
        if ok and new_description:
            # Обновляем описание в файле
            desc_file = os.path.join(session['path'], "description.txt")
            with open(desc_file, 'w', encoding='windows-1251') as f:
                f.write(new_description)
            
            # Обновляем данные в списке
            session['description'] = new_description
            item.setData(Qt.UserRole, session)
            
            # Обновляем текст элемента
            item_text = f"{session['date']} - {new_description}"
            item.setText(item_text)
            
            # Если это текущая сессия - обновляем информацию
            if self.logger.session_path == session['path']:
                self.update_current_session_info()
    
    def delete_session(self, item):
        session = item.data(Qt.UserRole)
        
        # Нельзя удалить текущую активную сессию
        if self.logger.session_path == session['path']:
            QMessageBox.warning(self, "Ошибка", "Нельзя удалить текущую активную сессию!")
            return
        
        reply = QMessageBox.question(
            self, 
            "Удаление сессии", 
            f"Вы уверены, что хотите удалить сессию '{session['description']}'?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Удаляем папку сессии
                import shutil
                shutil.rmtree(session['path'])
                
                # Удаляем элемент из списка
                self.session_list.takeItem(self.session_list.row(item))
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить сессию: {str(e)}")
    
    def selected_session(self):
        selected = self.session_list.currentItem()
        self.logger.session_path = selected.data(Qt.UserRole)["path"]
        if selected:
            return selected.data(Qt.UserRole)
        return None