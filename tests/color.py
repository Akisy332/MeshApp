import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QColorDialog, QVBoxLayout, QLabel


class ColorPickerApp(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Color Picker Example')

        # Создаем кнопку для открытия диалога выбора цвета
        self.button = QPushButton('Выбрать цвет', self)
        self.button.clicked.connect(self.openColorDialog)

        # Метка для отображения выбранного цвета
        self.label = QLabel('Выбранный цвет: ', self)

        # Устанавливаем вертикальное расположение
        layout = QVBoxLayout()
        layout.addWidget(self.button)
        layout.addWidget(self.label)

        self.setLayout(layout)

    def openColorDialog(self):
        # Открываем диалог выбора цвета
        color = QColorDialog.getColor()

        # Проверяем, был ли выбран цвет
        if color.isValid():
            # Обновляем текст метки с выбранным цветом
            self.label.setText(f'Выбранный цвет: {color.name()}')
            # Меняем цвет текста метки на выбранный цвет
            self.label.setStyleSheet(f'color: {color.name()}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ColorPickerApp()
    ex.resize(300, 200)
    ex.show()
    sys.exit(app.exec_())
