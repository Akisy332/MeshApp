import os

def save_user_location(username, lat, lon):
    # Создаем имя файла на основе имени пользователя
    filename = f"{username}.txt"
    
    # Записываем информацию о местоположении в файл
    with open(filename, 'a') as file:
        file.write(f"{lat}, {lon}\n")
    print(f"Location saved for {username}.")

def read_user_location(username):
    filename = f"{username}.txt"
    
    # Проверяем, существует ли файл
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            content = file.read()
            print(f"Locations for {username}:\n{content}")
    else:
        print(f"No data found for {username}.")

# Пример использования
if __name__ == "__main__":
    while True:
        action = input("Введите 'save' для сохранения местоположения или 'read' для чтения данных (или 'exit' для выхода): ").strip().lower()
        
        if action == 'save':
            username = input("Введите имя пользователя: ").strip()
            lat = input("Введите широту (lat): ").strip()
            lon = input("Введите долготу (lon): ").strip()
            save_user_location(username, lat, lon)
        
        elif action == 'read':
            username = input("Введите имя пользователя для чтения данных: ").strip()
            read_user_location(username)
        
        elif action == 'exit':
            print("Выход из программы.")
            break
        
        else:
            print("Неверная команда. Пожалуйста, попробуйте снова.")
