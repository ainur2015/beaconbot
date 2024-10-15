import mysql.connector
import requests
import asyncio
from mcstatus import JavaServer
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Функция для пинга сервера Minecraft
async def ping_minecraft_server(ip, port):
    try:
        server = await JavaServer.async_lookup(f"{ip}:{port}")
        status = await server.async_status()
        motd_plain = status.description if isinstance(status.description, str) else status.description.get('text', '')
        status_plain = status.version.name
        logger.info(f"{ip}:{port} - {status.players.online} players online")
        return True, motd_plain, status_plain
    except Exception as e:
        logger.error(f"Ошибка пинга сервера {ip}:{port} через mcstatus: {e}")
        return False, None, None

# Функция для проверки статуса сервера через API mcsrvstat.us
def check_server_status_via_api(ip, port):
    try:
        url = f"https://api.mcsrvstat.us/3/{ip}:{port}"
        response = requests.get(url)
        data = response.json()
        if data['debug']['ping']:
            motd_plain = data.get('motd', {}).get('clean', "")
            status_plain = data.get('version', "")
            return True, motd_plain, status_plain
        else:
            return False, None, None
    except Exception as e:
        logger.error(f"Ошибка сервера {ip}:{port} через API: {e}")
        return False, None, None

# Функция для проверки статуса сервера через API eu.mc-api.net
def check_server_status_via_mc_api(ip, port):
    try:
        url = f"https://eu.mc-api.net/v3/server/ping/{ip}:{port}"
        response = requests.get(url)
        data = response.json()
        if data['online']:
            motd_plain = data.get('motd', {}).get('clean', "")
            status_plain = data.get('version', "")
            return True, motd_plain, status_plain
        else:
            return False, None, None
    except Exception as e:
        logger.error(f"Ошибка сервера {ip}:{port} через mc-api.net: {e}")
        return False, None, None

# Функция для обновления записей в базе данных и записи в файлы
import os

def update_database_and_files(cursor, ip, port, ok):
    try:
        cursor.execute(
            "UPDATE server SET ok = %s WHERE ip_address = %s AND port = %s",
            (1 if ok else 0, ip, port)
        )

        # Создаем папку logs, если её нет
        if not os.path.exists('logs'):
            os.makedirs('logs')

        if ok:
            with open("logs/access.txt", "a") as access_file:
                access_file.write(f"{ip}:{port} - успешно\n")
        else:
            with open("logs/denied.txt", "a") as denied_file:
                denied_file.write(f"{ip}:{port} - не успешно\n")

    except Exception as e:
        logger.error(f"Ошибка обновления базы данных и записи в файлы: {e}")


# Асинхронная функция для проверки серверов
async def check_servers():
    connection = None
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="vh373935_becon",
            password="1hajUZwNtxfNIG2o",
            database="vh373935_becon"
        )

        if connection.is_connected():
            logger.info("Подключено к базе данных MySQL")
            cursor = connection.cursor()
            cursor.execute("SELECT ip_address, port FROM server")
            servers = cursor.fetchall()

            for server in servers:
                ip, port = server
                if port == 0:
                    port = 25565

                logger.info(f"Проверка сервера: {ip}:{port}")
                success, motd, status = await ping_minecraft_server(ip, port)
                if not success:
                    success, motd, status = check_server_status_via_api(ip, port)
                if not success:
                    success, motd, status = check_server_status_via_mc_api(ip, port)

                update_database_and_files(cursor, ip, port, success)

            connection.commit()
            cursor.close()
            logger.info("База данных и файлы успешно обновлены")

    except mysql.connector.Error as e:
        logger.error(f"Ошибка при подключении к MySQL: {e}")

    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")

    finally:
        if connection is not None and connection.is_connected():
            connection.close()
            logger.info("Соединение с базой данных закрыто")

# Основная асинхронная функция
async def main3():
    while True:
        logger.info("Запуск проверки серверов")
        await check_servers()
        logger.info("Ожидание перед следующей проверкой...")
        await asyncio.sleep(100)  # Пауза на 100 секунд перед следующим запуском

if __name__ == "__main__":
    asyncio.run(main3())
