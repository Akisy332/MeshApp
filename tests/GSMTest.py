import socket
import time
import math
import random
from decimal import Decimal, ROUND_DOWN
from dotenv import load_dotenv
import sys
import os



def send_data_to_server(sock, data):
    try:
        # Отправляем данные
        sock.sendall(data.encode())
        print(f"Отправлено: {data}")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    
    load_dotenv()
    if not os.getenv('SERVER_IP'):
        print("Error: SERVER_IP not set in .env.local")
        sys.exit(1)
    
    server_ip = os.getenv('SERVER_IP')
    server_port = 5000
    lat = 56.45205
    lon = 84.96131
    radius = 0.0001  # Радиус окружности (в градусах)
    angle = 0  # Начальный угол в радианах

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Подключаемся к серверу
        sock.connect((server_ip, server_port))
        index = 1
        while True:
            if index > 6: index = 1
            
            # Вычисляем новые координаты
            lat += radius*index * math.sin(angle)
            lon += radius*index  * math.cos(angle)

            name = index
            error = bool(random.randint(0,1))
            msg = lat
            if error:
                msg = "E"
            # Формируем данные для отправки
            data_to_send = f"GL {index} {msg} {lon} 450 1.5 50 2"
            send_data_to_server(sock, data_to_send)

            # Увеличиваем угол для следующей позиции
            angle += 0.1  # Увеличиваем угол (измените значение для изменения скорости движения)
            index+=1
            time.sleep(0.5)  # Ждем 1 секунд перед следующей отправкой
    except KeyboardInterrupt:
        print("\nЗавершение работы приложения...")
        sock.close()
