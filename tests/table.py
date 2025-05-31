from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, 
                            QCheckBox, QWidget, QHBoxLayout,
                            QMenu, QAction)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QBrush, QPainter
import time


class StatusDotWidget(QWidget):
    def __init__(self, color=QColor(Qt.green), parent=None):
        super().__init__(parent)
        self.color = color
        self.setFixedSize(20, 20)
        
    def setColor(self, color):
        self.color = color
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(self.color))
        painter.drawEllipse(5, 5, 10, 10)


class CustomTableWidget(QTableWidget):
    # Сигналы для чекбоксов
    checkbox_visible = pyqtSignal(str, bool)
    checkbox_trace = pyqtSignal(str, bool)
    # Сигналы для удаления
    row_deleted = pyqtSignal(str)  # Передает source удаленной строки
    all_rows_deleted = pyqtSignal()  # Сигнал для удаления всех строк
    
    def __init__(self, parent=None):
        super().__init__(0, 6, parent)
        self.source_to_row = {}
        self.row_to_source = {}
        self.row_update_times = {}
        self.checkboxes = {}
        
        self.init_table()
        self.setup_context_menu()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_all_timers)
        self.timer.start(1000)
    
    def init_table(self):
        headers = ["Статус", "Чекбокс 1", "Чекбокс 2", "Имя", "Высота", "Время после изменения"]
        self.setHorizontalHeaderLabels(headers)
        
        self.setColumnWidth(0, 40)
        self.setColumnWidth(1, 100)
        self.setColumnWidth(2, 100)
        self.setColumnWidth(3, 200)
        self.setColumnWidth(4, 100)
        self.setColumnWidth(5, 200)
    
    def setup_context_menu(self):
        """Настраивает контекстное меню для таблицы"""
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def show_context_menu(self, position):
        """Показывает контекстное меню"""
        menu = QMenu(self)
        
        # Получаем строку, по которой кликнули
        row = self.rowAt(position.y())
        
        # Действие для удаления текущей строки
        delete_action = QAction("Удалить строку", self)
        delete_action.triggered.connect(lambda: self.delete_selected_row(row))
        menu.addAction(delete_action)
        
        # Действие для удаления всех строк
        delete_all_action = QAction("Удалить все строки", self)
        delete_all_action.triggered.connect(self.delete_all_rows)
        menu.addAction(delete_all_action)
        
        menu.exec_(self.viewport().mapToGlobal(position))
    
    def delete_selected_row(self, row):
        """Удаляет выбранную строку и испускает сигнал"""
        if 0 <= row < self.rowCount() and row in self.row_to_source:
            source = self.row_to_source[row]
            self.remove_row_by_source(source)
            self.row_deleted.emit(source)
    
    def delete_all_rows(self):
        """Удаляет все строки и испускает сигнал"""
        sources = list(self.source_to_row.keys())
        for source in sources:
            self.remove_row_by_source(source)
        self.all_rows_deleted.emit()
    
    def update_from_dict(self, data_dict):
        current_sources = set(data_dict.keys())
        existing_sources = set(self.source_to_row.keys())
        
        for source in existing_sources - current_sources:
            self.remove_row_by_source(source)
        
        for source in current_sources - existing_sources:
            self.add_row(source, data_dict[source])
        
        for source in current_sources & existing_sources:
            row = self.source_to_row[source]
            if self.row_update_times[row] != data_dict[source]["time"]:
                self.update_row(source, data_dict[source])
    
    def add_row(self, source, data):
        row = self.rowCount()
        self.insertRow(row)
        self.source_to_row[source] = row
        self.row_to_source[row] = source
        self.row_update_times[row] = data["time"]
        
        self.set_status_dot(row, Qt.green)
        self.set_checkbox(row, 1, source)
        self.set_checkbox(row, 2, source)
        self.update_row(source, data)
    
    def set_checkbox(self, row, column, source):
        checkbox = QCheckBox()
        checkbox.stateChanged.connect(
            lambda state, s=source, col=column: self.on_checkbox_changed(s, col, state))
        
        checkbox_widget = QWidget()
        layout = QHBoxLayout(checkbox_widget)
        layout.addWidget(checkbox)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setCellWidget(row, column, checkbox_widget)
        
        if row not in self.checkboxes:
            self.checkboxes[row] = {}
        self.checkboxes[row][column] = checkbox
    
    def on_checkbox_changed(self, source, column, state):
        checked = state == Qt.Checked
        if column == 1:
            self.checkbox_visible.emit(source, checked)
        elif column == 2:
            self.checkbox_trace.emit(source, checked)
    
    def update_row(self, source, data):
        if source not in self.source_to_row:
            return
            
        row = self.source_to_row[source]
        self.row_update_times[row] = data["time"]
        
        self.set_item(row, 3, data.get("text", ""))
        self.set_item(row, 4, f"{data.get('alt', 0)} м")
        self.set_item(row, 5, "0:00")
        self.update_status_color(row, 0)
    
    def update_all_timers(self):
        current_time = time.time()
        for row in range(self.rowCount()):
            if row in self.row_update_times:
                elapsed = int(current_time - self.row_update_times[row])
                self.update_time_display(row, elapsed)
                self.update_status_color(row, elapsed)
    
    def update_time_display(self, row, elapsed_seconds):
        minutes = elapsed_seconds // 60
        seconds = elapsed_seconds % 60
        self.set_item(row, 5, f"{minutes}:{seconds:02d}")
    
    def remove_row_by_source(self, source):
        if source in self.source_to_row:
            row = self.source_to_row[source]
            self.removeRow(row)
            
            del self.source_to_row[source]
            del self.row_to_source[row]
            del self.row_update_times[row]
            if row in self.checkboxes:
                del self.checkboxes[row]
            
            for s, r in list(self.source_to_row.items()):
                if r > row:
                    self.source_to_row[s] = r - 1
                    self.row_to_source[r-1] = s
                    self.row_update_times[r-1] = self.row_update_times.pop(r)
                    if r in self.checkboxes:
                        self.checkboxes[r-1] = self.checkboxes.pop(r)
    
    def set_status_dot(self, row, color):
        dot_widget = StatusDotWidget(color)
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.addWidget(dot_widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setCellWidget(row, 0, container)
    
    def set_item(self, row, column, text, editable=False):
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(Qt.AlignCenter)
        if not editable:
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.setItem(row, column, item)
    
    def update_status_color(self, row, elapsed_seconds):
        if 0 <= row < self.rowCount():
            color = Qt.green if elapsed_seconds < 5 else (
                    Qt.blue if elapsed_seconds <= 10 else Qt.red)
            
            container = self.cellWidget(row, 0)
            if container:
                dot_widget = container.findChild(StatusDotWidget)
                if dot_widget:
                    dot_widget.setColor(color)
                    
import sys
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, 
                            QPushButton, QVBoxLayout, QWidget, QLabel)
# from table_widget import CustomTableWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Таблица с контекстным меню")
        self.setGeometry(100, 100, 800, 600)
        
        # Основной виджет и layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Метка для отображения состояния
        self.status_label = QLabel("Действия: ")
        layout.addWidget(self.status_label)
        
        # Кнопки для тестирования
        self.test_btn = QPushButton("Тест обновления")
        self.test_btn.clicked.connect(self.test_update)
        layout.addWidget(self.test_btn)
        
        # Таблица
        self.table = CustomTableWidget()
        layout.addWidget(self.table)
        
        # Подключаем сигналы
        self.table.checkbox_visible.connect(self.on_checkbox_visible)
        self.table.checkbox_trace.connect(self.on_checkbox_trace)
        self.table.row_deleted.connect(self.on_row_deleted)
        self.table.all_rows_deleted.connect(self.on_all_rows_deleted)
        
        # Тестовые данные
        self.sample_data = {
            "source1": {"text": "Объект 1", "alt": 100, "time": time.time()},
            "source2": {"text": "Объект 2", "alt": 200, "time": time.time()},
            "source3": {"text": "Объект 3", "alt": 300, "time": time.time()}
        }
        
        # Первоначальное заполнение
        self.table.update_from_dict(self.sample_data)
    
    def on_checkbox_visible(self, source, checked):
        self.status_label.setText(f"Чекбокс 1 для {source}: {'отмечен' if checked else 'снят'}")
    
    def on_checkbox_trace(self, source, checked):
        self.status_label.setText(f"Чекбокс 2 для {source}: {'отмечен' if checked else 'снят'}")
    
    def on_row_deleted(self, source):
        """Обработчик удаления строки"""
        if source in self.sample_data:
            del self.sample_data[source]
            self.status_label.setText(f"Удален объект: {source}")
    
    def on_all_rows_deleted(self):
        """Обработчик удаления всех строк"""
        self.sample_data.clear()
        self.status_label.setText("Все объекты удалены")
    
    def test_update(self):
        """Тестовый метод для демонстрации обновления"""
        for source in self.sample_data:
            test = random.randint(0, 11)
            if test % 2 == 1:
                self.sample_data[source]["alt"] = random.randint(50, 500)
                self.sample_data[source]["text"] = f"Обновлено {random.randint(1, 100)}"
                self.sample_data[source]["time"] = time.time()
        
        if "source4" not in self.sample_data:
            self.sample_data["source4"] = {
                "text": "Новый объект",
                "alt": 400,
                "time": time.time()
            }
        
        if len(self.sample_data) > 3 and random.random() > 0.5:
            key_to_remove = random.choice(list(self.sample_data.keys())[3:])
            del self.sample_data[key_to_remove]
        
        self.table.update_from_dict(self.sample_data)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())