import gui
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import qSetMessagePattern
from dotenv import load_dotenv, find_dotenv
import sys
import os


# import faulthandler; faulthandler.enable(file=sys.stderr, all_threads=True)


# qSetMessagePattern('%{appname} %{file} %{function} %{line} %{threadid}  %{backtrace depth=10 separator=\"\n\"}')

load_dotenv(find_dotenv('.env.local'), override=True)
if not os.getenv('SERVER_IP'):
    print("Error: SERVER_IP not set in .env.local")
    sys.exit(1)

app = QApplication(sys.argv)  # Создаем приложение
window = gui.MainWindow()  # Создаем экземпляр главного окна

import traceback



try:
    sys.exit(app.exec_()) 
except Exception:
    print(traceback.format_exc())

