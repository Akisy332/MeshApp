import socket
import time

def client_program():
    # host = socket.gethostname()  # серверный хост
    host = "103.90.75.178"
    port = 5000  # порт, на котором работает сервер

    client_socket = socket.socket()  # создаем сокет
    client_socket.connect((host, port))  # подключаемся к серверу

    try:
        while True:
            # Отправляем запрос на получение данных
            client_socket.sendall("GET_DATA".encode())

            # Получаем ответ от сервера
            response = client_socket.recv(1024).decode()
            data = response.split('\n')
            for dat in data:
                if dat.__sizeof__() > 80:
                    addr, lat, lon, alt, rateСlimb, speed, mode, numberPacket = dat.split()

            # Ждем некоторое время перед следующим запросом
            time.sleep(5)  # например, 5 секунд
    except ValueError:
        print(dat)
    except KeyboardInterrupt:
        print("Client is shutting down...")
    finally:
        client_socket.close()  # закрываем сокет

if __name__ == '__main__':
    client_program()
