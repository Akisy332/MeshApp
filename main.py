import gui
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import qSetMessagePattern
# import faulthandler; faulthandler.enable(file=sys.stderr, all_threads=True)


# qSetMessagePattern('%{appname} %{file} %{function} %{line} %{threadid}  %{backtrace depth=10 separator=\"\n\"}')

app = QApplication(sys.argv)  # Создаем приложение
window = gui.MainWindow()  # Создаем экземпляр главного окна

import traceback


try:
    sys.exit(app.exec_()) 
except Exception:
    print(traceback.format_exc())

