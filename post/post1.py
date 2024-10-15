import mysql.connector
import requests
import json
from mcstatus import JavaServer
import random
import time
import socks  # PySocks library
import socket  # Для управления сокетами
import logging  # Модуль для логирования

# Настройка логгера
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

# Счетчики
checked_servers = 0
successful_checks = 0

# Переключатель для использования прокси
use_proxy = False  # Установите True для использования прокси, False для работы без прокси

# Функция для получения данных прокси-серверов из файла
def get_proxies():
    with open('proxies.txt', 'r') as file:
        proxies = [line.strip() for line in file if line.strip()]
    return proxies

# Функция для ввода данных для подключения к базе данных MySQL
def get_mysql_config():
    # Загрузка конфигурации MySQL из файла или другого защищенного источника
    mysql_config = {
        'user': 'логин',
        'password': 'пасс',
        'host': 'localhost',
        'database': 'база',
        'raise_on_warnings': True
    }
    return mysql_config

# Получаем данные прокси из файла
proxies = get_proxies()

# Получаем конфигурацию MySQL
mysql_config = get_mysql_config()

# Функция для получения случайного прокси
def get_random_proxy():
    return random.choice(proxies)

# Функция для проверки доступности прокси
def check_proxy(proxy):
    try:
        ip, port = proxy.split(":")
        socks.set_default_proxy(socks.SOCKS5, ip, int(port))
        socket.socket = socks.socksocket  # Применение настройки к сокету
        # Проверка доступности прокси путем подключения к известному серверу
        test_socket = socket.create_connection(("www.google.com", 80), timeout=3)
        test_socket.close()
        return True
    except socks.ProxyConnectionError:
        logger.error(f"Прокси: {proxy} недоступна (невозможно подключиться)")
    except socks.GeneralProxyError as e:
        logger.error(f"Прокси: {proxy} недоступна (общая ошибка прокси: {e})")
    except socket.timeout:
        logger.error(f"Прокси: {proxy} недоступна (таймаут подключения)")
    except Exception as e:
        logger.error(f"Прокси: {proxy} недоступна ({e})")
    return False

# Функция для проверки сервера через API
def check_server_api(ip, port):
    global checked_servers, successful_checks

    if not port or port == 0:
        port = 25565

    urls = [
        f"https://eu.mc-api.net/v3/server/ping/{ip}:{port}",
        f"https://api.mcstatus.io/v2/status/java/{ip}:{port}"
    ]

    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("online"):
                logger.info(f"API: сервер {ip}:{port} получил ответ успешно")
                successful_checks += 1
                return data["players"]["online"], 1
        except Exception as e:
            logger.error(f"API: не удалось получить ответ от сервера {ip}:{port} ({e})")

    logger.warning(f"API: сервер {ip}:{port} не получил ответ через доступные методы")
    checked_servers += 1
    return "No", 0

# Функция для проверки сервера вручную без прокси
def check_server_direct(ip, port):
    try:
        server = JavaServer.lookup(f"{ip}:{port}")
        status = server.status()
        logger.info(f"Вручную проверка прошла успешно: {ip}:{port}")
        return status.players.online, 1
    except Exception as e:
        logger.error(f"Вручную проверка не прошла: {ip}:{port} ({e})")
        return "No", 0

# Функция для проверки сервера
def check_server(ip, port=None):
    global checked_servers, successful_checks

    if not port or port == 0:
        port = 25565

    if use_proxy:
        # Проверка через mcstatus с прокси
        while proxies:
            proxy = get_random_proxy()
            if not check_proxy(proxy):
                proxies.remove(proxy)
                continue

            try:
                # Настройка прокси для mcstatus
                socks.set_default_proxy(socks.SOCKS5, *proxy.split(":"))
                socket.socket = socks.socksocket  # Применение настройки к сокету

                server = JavaServer.lookup(f"{ip}:{port}")
                status = server.status()
                logger.info(f"Проверка через mcstatus с прокси прошла успешно: {ip}:{port} через прокси {proxy}")
                successful_checks += 1
                return status.players.online, 1
            except Exception as e:
                logger.error(f"Ошибка при получении статуса сервера Minecraft {ip}:{port} через прокси {proxy}: {e}")
                proxies.remove(proxy)  # Удаление недоступной прокси
                continue  # Попробовать следующую прокси

    # Если прокси не сработали или прокси не используется, попробуем API
    online, ok = check_server_api(ip, port)
    if ok == 1:
        return online, 1

    # Если API не сработали, попробуем напрямую без прокси
    return check_server_direct(ip, port)

# Функция для обновления статуса сервера в MySQL
def update_server_status(conn):
    cursor = conn.cursor()

    cursor.execute("SELECT ip_address, port FROM server")
    servers = cursor.fetchall()
    total_servers = len(servers)  # Общее количество серверов

    with open('error.txt', 'w') as error_file:  # Открытие файла для записи ошибок
        for idx, (ip, port) in enumerate(servers, start=1):
            online, ok = check_server(ip, port)
            if ok == 1:
                cursor.execute(
                    "UPDATE server SET online = %s, ok = %s WHERE ip_address = %s AND port = %s",
                    (online, ok, ip, port)
                )
                cursor.execute(
                    "INSERT INTO lister (server, times, online, port) VALUES (%s, %s, %s, %s)",
                    (ip, int(time.time()), online, port)
                )
                logger.info(f"{idx}/{total_servers} Сервер {ip}:{port} проверен успешно с онлайном {online}")
            else:
                error_msg = f"{idx}/{total_servers} Сервер {ip}:{port} не удалось проверить вручную или через API."
                logger.warning(error_msg)
                error_file.write(f"{ip}:{port}\n")  # Запись в файл

    conn.commit()
    cursor.close()

# Функция для запуска задачи обновления статуса серверов
def run_scheduled_task(conn, interval=300):
    global checked_servers, successful_checks

    while True:
        update_server_status(conn)
        time.sleep(interval)

        total_servers = checked_servers + successful_checks
        logger.info(f"Серверов проверено {checked_servers}/{total_servers}")

if __name__ == "__main__":
    try:
        # Подключение к MySQL
        conn = mysql.connector.connect(**mysql_config)
        logger.info("Успешное подключение к базе данных MySQL")

        # Запуск задачи обновления статуса каждые 5 минут
        run_scheduled_task(conn)

    except mysql.connector.Error as err:
        logger.error(f"Ошибка при подключении к базе данных MySQL: {err}")

    finally:
        # Закрытие соединения с MySQL
        if 'conn' in locals() and conn.is_connected():
            conn.close()
            logger.info("Соединение с базой данных MySQL закрыто")
