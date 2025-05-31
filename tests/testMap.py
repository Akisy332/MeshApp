import sys
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QLabel
from PyQt5.QtGui import QColor

# Определяем цвета
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

class ColorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        grid = QGridLayout()
        self.setLayout(grid)

        for i, (color_name, color_code) in enumerate(colors.items()):
            label = QLabel(color_name)
            label.setStyleSheet(f'background-color: {color_code}; color: white; padding: 20px; font-size: 16px;')
            grid.addWidget(label, i // 5, i % 5)  # Размещаем в сетке

        self.setWindowTitle('Цвета')
        self.setGeometry(100, 100, 800, 400)  # Устанавливаем размеры окна
        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ColorApp()
    sys.exit(app.exec_())
