import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QPushButton

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gui import MainWindow

class ConsoleWidget():
    def __init__(self, gui: "MainWindow"):
        self.gui = gui
        self.console: QTextEdit = gui.ui.console
        self.console.setReadOnly(True)  # Делаем текстовое поле только для чтения
        self.console.setStyleSheet("font-family: monospace;")  # Устанавливаем моноширинный шрифт
        
    def write(self, text):
        if self.console:
            self.console.append(text)  # Добавляем текст в консоль
            self.console.ensureCursorVisible()  # Прокручиваем вниз для отображения нового текста
        