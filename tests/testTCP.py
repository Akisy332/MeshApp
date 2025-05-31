import socket
import threading

class ESP32Client:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.sock = None
        self.running = True

    def connect(self):
        """Подключаемся к ESP32."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.ip, self.port))
            print("Connected to ESP32")
        except Exception as e:
            print(f"Ошибка подключения: {e}")

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
        while self.running:
            try:
                response = self.sock.recv(1024)
                if not response:
                    print("Соединение закрыто сервером.")
                    break
                print("Received response:")
                if response[0] == 0xc1:
                    text = response[0:8]
                    response = response[8:]
                    # hex_representation = text
                    hex_representation = [f'{bytearray:02x}' for bytearray in text]
                    print(f"Получено (некорректные символы в hex): {hex_representation}")
                        
                decoded_line = response.decode('utf-8', errors='ignore')  # Пробуем декодировать
                print(f"Получено (текст): {decoded_line.strip()}")  # Выводим текстовые данные
                
            except Exception as e:
                print(f"Ошибка при получении данных: {e}")
                break

    def run(self):
        """Запуск клиента."""
        self.connect()
        
        send_thread = threading.Thread(target=self.send_data)
        receive_thread = threading.Thread(target=self.receive_data)

        send_thread.start()
        receive_thread.start()

        # Ждем завершения потоков
        send_thread.join()
        receive_thread.join()

        # Закрываем сокет после завершения работы
        self.sock.close()

if __name__ == "__main__":
    ESP32_IP = '192.168.222.130'  # Замените на IP-адрес вашего ESP32
    ESP32_PORT = 8080            # Порт, на котором работает ваш WiFiServer

    client = ESP32Client(ESP32_IP, ESP32_PORT)
    client.run()
