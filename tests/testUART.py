import serial
import serial.tools.list_ports
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox

class UARTClient:
    def __init__(self):
        self.port = None
        self.baudrate = 115200
        self.ser = None
        self.running = False

        # Создаем графический интерфейс
        self.root = tk.Tk()
        self.root.title("UART Client")

        # Фрейм для кнопок и списка
        frame = tk.Frame(self.root)
        frame.pack(padx=10, pady=10)

        # Список выбора портов
        self.port_list = tk.StringVar(self.root)
        self.port_dropdown = tk.OptionMenu(frame, self.port_list, *self.get_ports())
        self.port_dropdown.pack(side=tk.LEFT)

        # Кнопка "Обновить"
        self.refresh_button = tk.Button(frame, text="Обновить", command=self.refresh_ports)
        self.refresh_button.pack(side=tk.LEFT, padx=5)

        # Кнопка "Открыть"
        self.open_button = tk.Button(frame, text="Открыть", command=self.open_port)
        self.open_button.pack(side=tk.LEFT, padx=5)

        # Кнопка "Закрыть"
        self.close_button = tk.Button(frame, text="Закрыть", command=self.close_port, state='disabled')
        self.close_button.pack(side=tk.LEFT, padx=5)

        # Поле для вывода данных
        self.output_text = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state='disabled', width=50, height=20)
        self.output_text.pack(padx=10, pady=10)

        # Поле для ввода данных
        self.input_entry = tk.Entry(self.root, width=50)
        self.input_entry.pack(padx=10, pady=10)
        self.input_entry.bind("<Return>", self.send_data)  # Отправка данных по нажатию Enter

        # Кнопка выхода
        self.exit_button = tk.Button(self.root, text="Выход", command=self.exit_program)
        self.exit_button.pack(pady=5)

    def get_ports(self):
        """Получение доступных последовательных портов."""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        if not ports:
            ports = ["Нет доступных портов"]
        return ports

    def refresh_ports(self):
        """Обновление списка портов."""
        menu = self.port_dropdown["menu"]
        menu.delete(0, "end")  # Очистка текущего меню

        for port in self.get_ports():
            menu.add_command(label=port, command=lambda value=port: self.port_list.set(value))

        # Установка выбранного порта на первый доступный (если есть)
        if self.get_ports():
            self.port_list.set(self.get_ports()[0])

    def open_port(self):
        """Открытие выбранного порта."""
        selected_port = self.port_list.get()
        if selected_port == "Нет доступных портов":
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите доступный порт.")
            return
        
        try:
            self.ser = serial.Serial(selected_port, self.baudrate, timeout=1)
            self.running = True
            self.append_output(f"Подключено к {selected_port} на скорости {self.baudrate} бит/с.\n")
            self.close_button.config(state='normal')
            self.open_button.config(state='disabled')

            # Запуск потока для получения данных
            receive_thread = threading.Thread(target=self.receive_data)
            receive_thread.start()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка подключения: {e}")

    def close_port(self):
        """Закрытие порта."""
        if self.ser is not None and self.ser.is_open:
            self.running = False
            self.ser.close()
            self.append_output("Порт закрыт.\n")
            self.close_button.config(state='disabled')
            self.open_button.config(state='normal')
            self.refresh_ports()  # Обновляем список портов после закрытия

    def append_output(self, message):
        """Добавление сообщения в поле вывода."""
        self.output_text.config(state='normal')
        self.output_text.insert(tk.END, message)
        self.output_text.config(state='disabled')
        self.output_text.yview(tk.END)  # Прокрутка вниз

    def send_data(self, event=None):
        """Отправка данных через UART."""
        user_input = self.input_entry.get()
        if user_input.lower() == 'exit':
            self.exit_program()
            return
        
        if user_input and self.ser is not None and self.ser.is_open:
            try:
                self.ser.write(user_input.encode())
                self.append_output(f"Отправлено: {user_input}\n")
                self.input_entry.delete(0, tk.END)  # Очистка поля ввода
            except Exception as e:
                self.append_output(f"Ошибка при отправке данных: {e}\n")

    def receive_data(self):
        """Получение данных через UART."""
        while self.running:
            try:
                if self.ser.in_waiting > 0:
                    response = self.ser.readline().decode().strip()
                    self.append_output(f"Получено: {response}\n")
            except Exception as e:
                self.append_output(f"Ошибка при получении данных: {e}\n")
                break

    def exit_program(self):
        """Выход из программы."""
        if self.ser is not None and self.ser.is_open:
            self.close_port()
        self.root.quit()

    def run(self):
        """Запуск клиента."""
        # Запуск главного цикла tkinter
        self.root.mainloop()

if __name__ == "__main__":
    uart_client = UARTClient()
    uart_client.run()
