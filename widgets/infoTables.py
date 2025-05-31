from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, 
                            QCheckBox, QWidget, QHBoxLayout,
                            QMenu, QAction, QHeaderView, QSizePolicy, QMessageBox)
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
    
    row_deleted = pyqtSignal(str)  # Передает source удаленной строки
    name_changed = pyqtSignal(str, str)  # source, новое_имя
    
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
        
        self.itemChanged.connect(self.on_item_changed)
    
    def on_item_changed(self, item):
        """Обработчик изменения данных в ячейке"""
        if item.column() == 3:  # Столбец "Имя"
            row = item.row()
            if row in self.row_to_source:
                source = self.row_to_source[row]
                new_name = item.text()
                self.name_changed.emit(source, new_name)
    
    def init_table(self):
        headers = ["", "", "", "ФИО", "Высота", "Время"]
        self.setHorizontalHeaderLabels(headers)
        
        # Настройка растягивания столбцов
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)  # Фиксированный размер для статуса
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)  # Фиксированный размер для чекбокса 1
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)  # Фиксированный размер для чекбокса 2
        
        self.setColumnWidth(0, 10)
        self.setColumnWidth(1, 20)
        self.setColumnWidth(2, 20)
        
        # Настройка растягивания таблицы
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.horizontalHeader().setStretchLastSection(True)
    
    def setup_context_menu(self):
        """Настраивает контекстное меню для таблицы"""
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, position):
        """Показывает контекстное меню"""
        menu = QMenu(self)

        # Получаем строку, по которой кликнули
        row = self.rowAt(position.y())

        # Если клик был по существующей строке
        if 0 <= row < self.rowCount() and row in self.row_to_source:
            source = self.row_to_source[row]

            # Добавляем заголовок с source
            header_action = QAction(f"Номер: {source}", self)
            header_action.setEnabled(False)  # Делаем неактивным (только текст)
            menu.addAction(header_action)

            # Добавляем разделитель
            menu.addSeparator()

        # Действие для удаления текущей строки
        delete_action = QAction("Удалить строку", self)
        delete_action.triggered.connect(lambda: self.confirm_delete_row(row))
        menu.addAction(delete_action)

        # Действие для удаления всех строк
        delete_all_action = QAction("Удалить все строки", self)
        delete_all_action.triggered.connect(self.confirm_delete_all_rows)
        menu.addAction(delete_all_action)

        menu.exec_(self.viewport().mapToGlobal(position))

    def confirm_delete_row(self, row):
        """Подтверждение удаления строки"""
        reply = QMessageBox.question(
            self,
            'Подтверждение удаления',
            'Вы уверены, что хотите удалить эту строку?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.delete_selected_row(row)

    def confirm_delete_all_rows(self):
        """Подтверждение удаления всех строк"""
        reply = QMessageBox.question(
            self,
            'Подтверждение удаления',
            'Вы уверены, что хотите удалить все строки?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.delete_all_rows()
    
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
            self.row_deleted.emit(source)
        self.source_to_row = {}
        self.row_to_source = {}
        self.row_update_times = {}
        self.checkboxes = {}
        
    def clear_table(self):
        sources = list(self.source_to_row.keys())
        for source in sources:
            self.remove_row_by_source(source)
        self.source_to_row = {}
        self.row_to_source = {}
        self.row_update_times = {}
        self.checkboxes = {}
    
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
                # Проверяем поле error при каждом обновлении
                
            # print(data_dict[source])
    
    def check_error_field(self, source, data):
        """Проверяет поле error в данных и устанавливает синий статус, сбрасывает время если error=True"""
        if source not in self.source_to_row:
            return
        # print(source, data.get("error"))
        if data.get("error"):
            row = self.source_to_row[source]
            # Устанавливаем синий цвет статуса
            container = self.cellWidget(row, 0)
            if container:
                dot_widget = container.findChild(StatusDotWidget)
                if dot_widget:
                    dot_widget.setColor(Qt.blue)
        else:
            row = self.source_to_row[source]
            # Устанавливаем зеленый цвет статуса
            container = self.cellWidget(row, 0)
            if container:
                dot_widget = container.findChild(StatusDotWidget)
                if dot_widget:
                    dot_widget.setColor(Qt.green)

            
    
    def add_row(self, source, data):
        row = self.rowCount()
        self.insertRow(row)
        self.source_to_row[source] = row
        self.row_to_source[row] = source
        self.row_update_times[row] = data["time"]
        
        self.set_status_dot(row, Qt.green)
        self.set_checkbox(row, 1, source, data["visible"])
        self.set_checkbox(row, 2, source, data["traceFlag"])
        self.update_row(source, data)
    
    def set_checkbox(self, row, column, source, checked):
        checkbox = QCheckBox()
        checkbox.setChecked(checked)
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
        
        self.set_item(row, 3, data.get("text", ""), editable=True)
        self.set_item(row, 4, f"{data.get('alt', 0)} м")
        self.set_item(row, 5, "0:00")
        self.check_error_field(source, data)
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
        if editable:
            item.setFlags(item.flags() | Qt.ItemIsEditable)
        else:
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.setItem(row, column, item)
    
    def update_status_color(self, row, elapsed_seconds):
        if 0 <= row < self.rowCount():       
            container = self.cellWidget(row, 0)
            if container:
                dot_widget = container.findChild(StatusDotWidget)
                if dot_widget:
                    if dot_widget.color == Qt.blue and elapsed_seconds <= 60:
                        color = Qt.blue
                    else:
                        color = Qt.green if elapsed_seconds < 60 else (
                            Qt.yellow if elapsed_seconds <= 300 else Qt.red)

                    dot_widget.setColor(color)
                    
# noinspection PyCompatibility

# import sys
# from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QPushButton, QVBoxLayout, QWidget, QCheckBox, QLineEdit, QMenu
# from PyQt5.QtCore import Qt, QObject
# from PyQt5.QtGui import QColor
# import time
# import os
# from PyQt5.QtCore import pyqtSignal, QObject

# from typing import TYPE_CHECKING

# if TYPE_CHECKING:
#     from gui import MainWindow

# class infoTables(QObject):
#     signalDeleteAbonent = pyqtSignal(str)
#     signalTpToMarker = pyqtSignal(tuple)
#     def __init__(self, gui: "MainWindow"):
#         super().__init__()
#         self.gui = gui
#         self.data = gui.data
        
        
#         self.listAbonents = []

#         self.editable_indices = ['text']

#         self.tableAbonent: QTableWidget = self.gui.tableAbonent
#         self.tableInfo: QTableWidget = self.gui.tableInfo
#         self.lineSearch: QLineEdit = self.gui.lineSearch
                
#         self.tableAbonent.cellClicked.connect(self.onAbonentRowClicked)
#         self.tableAbonent.itemChanged.connect(self.onItemChanged)
#         self.tableAbonent.setContextMenuPolicy(Qt.CustomContextMenu)
#         self.tableAbonent.customContextMenuRequested.connect(self.showContextMenu)
        
#         self.lineSearch.textChanged.connect(self.searchInfo)

        
        
#     def updateTable(self):
        
#         for source in self.data.dataAbonent.keys():
#             if source in self.listAbonents:
#                 self.updateCellValue(source, self.data.dataAbonent[source])
#             else:
#                 self.listAbonents.append(source)
#                 self.addDataTable(self.tableAbonent, (source, self.data.dataAbonent[source].get("time")), True)
    
#     def updateCellValue(self, source, data):
        
#         for index in range(len(self.listAbonents)):
#             if self.listAbonents[index] == source:
#                 self.tableAbonent.setItem(index, 2, QTableWidgetItem(data["time"]))
#                 break
    
#     def addDataTable(self, table: QTableWidget, dataRow: list, checkboxFlag: bool = False, checkboxColumn: int = 0,):
#         rowPosition = table.rowCount()
#         table.insertRow(rowPosition)
        
#         if checkboxFlag == True:
#             checkbox = QCheckBox()
#             checkbox.setChecked(False)
#             checkbox.stateChanged.connect(lambda state, row=rowPosition: self.checkboxStateChanged(table, state, row))
#             table.setCellWidget(rowPosition, checkboxColumn, checkbox)
        
#         for idx, dat in enumerate(dataRow):            
#             if idx >= checkboxColumn and checkboxFlag == True:
#                 idx = idx + 1
#             item = QTableWidgetItem(str(dat))
#             if idx != 1:
#                 item.setFlags(item.flags() & ~Qt.ItemIsEditable)
#             table.setItem(rowPosition, idx, item)

#     def checkboxStateChanged(self,table: QTableWidget, state, row):
#         source = self.listAbonents[row]
#         if state == 2:
#             self.gui.update_trace(source=source, flag=True)
#             # data[source].update({"visible": True})
#         else:
#             self.gui.update_trace(source=source, flag=False)
#             # data[source].update({"visible": False})
#         self.gui.updateUI()
        
#     def onAbonentRowClicked(self, row, column):
#         id = row
#         self.displayIntableInfo(id, self.data.dataAbonent)

#     def showContextMenu(self, pos):
#         # Получаем индекс строки, на которую кликнули
#         row = self.tableAbonent.rowAt(pos.y())
        
#         # Создаем контекстное меню
#         context_menu = QMenu()

#         # Добавляем действия в контекстное меню
#         if row >= 0:  # Проверяем, что кликнули по существующей строке
#             tpToMarker = context_menu.addAction("Переместиться")
#             delete_action = context_menu.addAction("Удалить")
#             deleteAll = context_menu.addAction("Удалить всё")
#             action = context_menu.exec_(self.tableAbonent.mapToGlobal(pos))

#             if action == delete_action:
#                 self.tableAbonent.removeRow(row)  # Удаляем строку
#                 self.signalDeleteAbonent.emit(self.listAbonents[row])
#                 self.listAbonents.pop(row)
#             if action == deleteAll:
#                 for index, item in enumerate(self.listAbonents):
#                     self.tableAbonent.removeRow(0)
#                     self.signalDeleteAbonent.emit(item)
#                 self.listAbonents = []
#             if action == tpToMarker:
#                 data = self.data.dataAbonent[self.listAbonents[row]]
#                 coords = (data["lat"], data["lon"])
#                 self.signalTpToMarker.emit(coords)
                
    
#     def displayIntableInfo(self, id, data):
        
#         while self.tableInfo.rowCount() > 0:
#             self.tableInfo.removeRow(0)
        
#         for key in data[self.listAbonents[id]].keys():
#             rowPosition = self.tableInfo.rowCount()
#             self.tableInfo.insertRow(rowPosition)
            
#             nameItem = QTableWidgetItem(str(key))
#             nameItem.setFlags(nameItem.flags() & ~Qt.ItemIsEditable)
#             self.tableInfo.setItem(rowPosition, 0, nameItem)
            
#             valueItem = QTableWidgetItem(str(data[self.listAbonents[id]].get(key)))
#             if not str(key) in self.editable_indices and len(self.editable_indices) != 0:
#                 valueItem.setFlags(nameItem.flags() & ~Qt.ItemIsEditable)
#             self.tableInfo.setItem(rowPosition, 1, valueItem)
            
#     def searchInfo(self):
#         search_text = self.lineSearch.text().lower()
        
#         for row in range(self.tableAbonent.rowCount()):
#             row_contains_match = False
#             for col in range(self.tableAbonent.columnCount()):
#                 item = self.tableAbonent.item(row, col)
#                 if item:
#                     if search_text in item.text().lower():
#                         row_contains_match = True
#                         item.setBackground(QColor("green"))  # Меняем цвет фона на красный
#                     else:
#                         item.setBackground(QColor("white"))  # Сбрасываем цвет фона

#             # Скрываем строки без совпадений
#             self.tableAbonent.setRowHidden(row, not row_contains_match)

#         # Если поле поиска пустое, сбрасываем выделение и показываем все строки
#         if not search_text:
#             for row in range(self.tableAbonent.rowCount()):
#                 for col in range(self.tableAbonent.columnCount()):
#                     item = self.tableAbonent.item(row, col)
#                     if item:
#                         item.setBackground(QColor("white"))  # Сбрасываем цвет фона
#                 self.tableAbonent.setRowHidden(row, False)  # Показываем все строки

#     def onItemChanged(self, item):
#         if item.column() == 1:
#             source = self.listAbonents[item.row()]
#             new_value = item.text()
#             if self.data.dataAbonent[source]["text"] != new_value:
#                 self.data.dataAbonent[source]["text"] = new_value
#                 self.gui.map