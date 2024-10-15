import os
from mcstatus import JavaServer

# Функция для проверки статуса сервера
def check_server_status(server_address):
    try:
        server = JavaServer.lookup(server_address)
        status = server.status()
        return True, status.players.online, status.latency
    except Exception as e:
        return False, None, None

# Открытие файла с адресами серверов и их проверка
file_path = "error.txt"

if os.path.exists(file_path):
    with open(file_path, 'r') as file:
        servers = file.readlines()

    for server in servers:
        server = server.strip()
        if server:
            is_online, players, latency = check_server_status(server)
            if not is_online:
                print(f"Сервер ({server}) не сумел ответить.")
else:
    print(f"Файл {file_path} не найден.")
