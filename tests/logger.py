import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                             QWidget, QListWidget, QDialog, QLabel, QHBoxLayout, 
                             QMessageBox, QTextEdit, QInputDialog, QListWidgetItem)
from PyQt5.QtCore import Qt, QDateTime

class SessionLogger():
    def __init__(self):
        self.sessions_dir = 'sessions'
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
                    with open(desc_file, 'r') as f:
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
        
        # Создаем файл для логов пользователя
        user_log_file = os.path.join(session_path, f"{user_id}_log.txt")
        if not os.path.exists(user_log_file):
            open(user_log_file, 'w').close()
    
    def add_user_location(self, session_path, user_id, lat, lon):
        user_log_file = os.path.join(session_path, f"{user_id}_log.txt")
        with open(user_log_file, 'a') as f:
            f.write(f"{lat} {lon}\n")
    
    def get_user_locations(self, session_path, user_id):
        user_log_file = os.path.join(session_path, f"{user_id}_log.txt")
        if os.path.exists(user_log_file):
            with open(user_log_file, 'r') as f:
                return [line.strip().split() for line in f if line.strip()]
        return []

class SessionDialog(QDialog):
    def __init__(self, logger, parent=None):
        super().__init__(parent)
        self.logger = logger
        self.setWindowTitle("Выбор сессии")
        self.setFixedSize(600, 400)
        
        self.layout = QVBoxLayout()
        
        self.label = QLabel("Доступные сессии:")
        self.session_list = QListWidget()
        self.session_list.itemDoubleClicked.connect(self.accept)
        
        self.description = QTextEdit()
        self.description.setReadOnly(True)
        
        self.load_button = QPushButton("Загрузить сессию")
        self.load_button.clicked.connect(self.accept)
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.cancel_button)
        
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.session_list)
        self.layout.addWidget(QLabel("Описание сессии:"))
        self.layout.addWidget(self.description)
        self.layout.addLayout(button_layout)
        
        self.setLayout(self.layout)
        
        self.populate_sessions()
        self.session_list.currentItemChanged.connect(self.show_session_description)
    
    def populate_sessions(self):
        sessions = self.logger.get_all_sessions()
        self.session_list.clear()
        
        for session in sessions:
            item_text = f"{session['date']} - {session['description'][:50]}"
            if len(session['description']) > 50:
                item_text += "..."
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, session)
            self.session_list.addItem(item)
    
    def show_session_description(self, current):
        if current:
            session = current.data(Qt.UserRole)
            self.description.setPlainText(session['description'])
    
    def selected_session(self):
        selected = self.session_list.currentItem()
        if selected:
            return selected.data(Qt.UserRole)
        return None

class LoggerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.logger = SessionLogger()
        self.setWindowTitle("Менеджер сессий")
        self.setFixedSize(400, 200)
        
        self.central_widget = QWidget()
        self.layout = QVBoxLayout()
        
        self.new_session_btn = QPushButton("Новая сессия")
        self.new_session_btn.clicked.connect(self.create_new_session)
        
        self.load_session_btn = QPushButton("Загрузить сессию")
        self.load_session_btn.clicked.connect(self.load_session)
        
        self.layout.addWidget(self.new_session_btn)
        self.layout.addWidget(self.load_session_btn)
        
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)
    
    def create_new_session(self):
        description, ok = QInputDialog.getMultiLineText(
            self, 
            "Новая сессия", 
            "Введите описание сессии:",
            ""
        )

        if ok and description:
            session_name, session_path = self.logger.create_new_session(description)
            # Пример добавления тестовых данных
            test_user = {
                "lat": 55.751244,
                "lon": 37.618423,
                "alt": 150,
                "time": QDateTime.currentDateTime().toSecsSinceEpoch(),
                "visible": True,
                "text": "Тестовый пользователь",
                "traceFlag": False,
                "color": "#1f77b4",
                "error": False
            }

            self.logger.add_user_to_session(session_path, "user1", test_user)
            self.logger.add_user_location(session_path, "user1", 55.751244, 37.618423)
            self.logger.add_user_location(session_path, "user1", 55.752345, 37.619534)

            QMessageBox.information(
                self, 
                "Успех", 
                f"Создана новая сессия: {session_name}\nОписание: {description}"
            )
    
    def load_session(self):
        dialog = SessionDialog(self.logger, self)
        if dialog.exec_() == QDialog.Accepted:
            session = dialog.selected_session()
            if session:
                users = self.logger.get_session_users(session['path'])
                
                msg = (
                    f"Загружена сессия: {session['name']}\n"
                    f"Дата: {session['date']}\n"
                    f"Описание: {session['description']}\n"
                    f"Количество пользователей: {len(users)}"
                )
                
                QMessageBox.information(self, "Информация о сессии", msg)

if __name__ == "__main__":
    app = QApplication([])
    window = LoggerApp()
    window.show()
    app.exec_()