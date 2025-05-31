import serial
import time
import socket
import uuid
import os
from PyQt5.QtCore import QThread, pyqtSignal


class SerialPortWorker(QThread):
    rawDataReceived = pyqtSignal(str, str)
    statusMessage = pyqtSignal(str, str)  # Сигнал для статусных сообщений
    errorMessage = pyqtSignal(str, str)   # Сигнал для сообщений об ошибках
    connectionStatus = pyqtSignal(str, bool)  # Сигнал о состоянии подключения (True - подключено, False - отключено)

    def __init__(self, port, baudrate):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.running = True

    def transmit(self, message: str):
        """Отправка данных через UART."""
        try:
            if self.serial and self.serial.is_open:
                self.serial.write(message.encode())
                self.statusMessage.emit("USB","Данные успешно отправлены")
            else:
                self.errorMessage.emit("USB","Устройство не подключено")
        except Exception as e:
            error_msg = f"Ошибка при отправке данных: {e}"
            self.errorMessage.emit("USB", error_msg)

    def run(self):
        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=1)
            
            if not self.serial.is_open:
                self.errorMessage.emit("USB",f"Проверьте выбранный порт {self.port}")
            else:
                self.statusMessage.emit("USB",f"Устройство подключено к порту {self.port}")
                while self.running:
                    if self.serial.in_waiting > 0:
                        rawdataLine = self.serial.readline()
                        decodedLine = rawdataLine.decode('utf-8', errors='ignore')
                        self.rawDataReceived.emit("USB: ", decodedLine)
                        
                    time.sleep(0.1)
                
        except Exception as e:
            error_msg = f"Ошибка подключения: {e}"
            self.errorMessage.emit("USB",error_msg)


    def stop(self):
        self.running = False
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.statusMessage.emit("USB","Устройство отключено")
        self.connectionStatus.emit("USB",False)

class TCPClientWorker(QThread):
    rawDataReceived = pyqtSignal(str, str)
    connectionError = pyqtSignal(str)  # Сигнал для передачи сообщения об ошибке соединения
    statusMessage = pyqtSignal(str, str)  # Сигнал для статусных сообщений

    def __init__(self):
        super().__init__()
        self.host = ""
        self.port = 5000
        self.running = True
        self.client_socket = None
        self.device_uuid = self._get_or_create_device_uuid()

    def _get_or_create_device_uuid(self):
        """Получает или создает UUID устройства и сохраняет его в файл"""
        uuid_file = "device_uuid.txt"
        
        # Пытаемся прочитать существующий UUID
        if os.path.exists(uuid_file):
            try:
                with open(uuid_file, "r") as f:
                    return f.read().strip()
            except:
                pass
        
        # Генерируем новый UUID
        new_uuid = str(uuid.uuid4())
        try:
            with open(uuid_file, "w") as f:
                f.write(new_uuid)
        except:
            pass
            
        return new_uuid

    def _connect_to_server(self):
        """Подключается к серверу и отправляет UUID устройства"""
        try:
            self.client_socket = socket.socket()
            self.client_socket.connect((self.host, self.port))
            
            # Отправляем серверу UUID устройства
            self.client_socket.sendall(f"UUID:{self.device_uuid}".encode())
            
            # Получаем подтверждение от сервера
            response = self.client_socket.recv(1024).decode()
            print(response)
            if response.startswith("UUID_ACCEPTED"):
                self.statusMessage.emit("Server", "Подключение успешно")
                return True
            else:
                self.connectionError.emit("Ошибка идентификации устройства")
                return False
                
        except socket.error as e:
            self.connectionError.emit(f"Не удалось подключиться к серверу: {e}")
            return False
        except Exception as e:
            self.connectionError.emit(f"Ошибка подключения: {e}")
            return False

    def run(self):
        if not self._connect_to_server():
            return
        
        print(self.device_uuid)
            
        try:
            while self.running:
                # Отправляем запрос на получение данных
                self.client_socket.sendall("GET_DATA".encode())

                # Получаем ответ от сервера
                response = self.client_socket.recv(1024).decode()
                if response.startswith("NO_DATA_AVAILABLE") or response.startswith("NO_NEW_DATA"):
                    time.sleep(1)
                else:    
                    dataList = response.split('\n')
                    for dat in dataList:
                        self.rawDataReceived.emit("Server: ", dat)

        except socket.error as e:
            self.connectionError.emit("Соединение разорвано.\nПроверьте интернет соединение.")
        except Exception as e:
            self.connectionError.emit(f"Ошибка: {str(e)}")
        finally:
            self.stop()

    def stop(self):
        self.running = False
        if self.client_socket:
            self.client_socket.close()


class WiFiWorker(QThread):
    rawDataReceived = pyqtSignal(str, str)
    connectionError = pyqtSignal(str)
    statusMessage = pyqtSignal(str, str)  # Сигнал для статусных сообщений
    
    def __init__(self, ip, port):
        super().__init__()
        self.ip = ip
        self.port = port
        self.sock = None
        self.running = True

    def connect(self):
        """Подключаемся к ESP32."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.ip, self.port))
            self.statusMessage.emit("Server","Подключение успешно")
            print("Connected to ESP32")
        except Exception as e:
            self.connectionError.emit(f"Проверьте IP адрес на устройстве с введенным в настройках:\n{self.ip}")
            print(f"Ошибка подключения: {e}")
            self.running = False

    def send_data(self):
        """Отправка данных на ESP32."""
        while self.running:
            user_input = input("Введите сообщение для отправки (или 'exit' для выхода): ")
            if user_input.lower() == 'exit':
                print("Выход из программы.")
                self.running = False
                break
            try:
                self.sock.sendall(user_input.encode())
            except Exception as e:
                print(f"Ошибка при отправке данных: {e}")

    def receive_data(self):
        """Получение данных от ESP32."""
        
        try:
            while self.running:
                response = self.sock.recv(1024)
                if not response:
                    print("Соединение закрыто сервером.")
                    break
                        
                decodedLine = response.decode('utf-8', errors='ignore')  # Пробуем декодировать
                # print(f"Получено (текст): {decodedLine.strip()}")  # Выводим текстовые данные
                self.rawDataReceived.emit("WiFi: ", decodedLine)
            
        except Exception as e:
            self.connectionError.emit(f"WiFi соединение разорвано. \nПроверьте устройство.")
            print(f"Error in thread: {e}")


    def run(self):
        """Запуск клиента."""
        self.connect()
        self.receive_data()
        
    def stop(self):
        self.running = False
        if not self.sock is None:
            self.sock.close()