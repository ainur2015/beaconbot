# db_utils.py 
 
import mysql.connector 
from config.db_config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE  # Импортируем параметры подключения 
import random 
import sys
import socket
import time
import json
from datetime import datetime, timezone, timedelta
import requests
import re
from mcstatus import JavaServer
import logging
import asyncio
import os 
import logger

def log_message(message):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Получаем текущую дату и время в формате строки
        log_entry = f"[{timestamp}] {message}"  # Форматируем запись в лог: [дата и время] сообщение

        with open("log.txt", "a") as log_file:  # Открываем файл для добавления текста в конец
            log_file.write(log_entry + "\n")  # Записываем сообщение в лог с добавлением символа новой строки
        print("MYSQL UTILS ERROR")
    except Exception as e:
        print("Ошибка при записи сообщения в лог:", e)
        
def load_texts_from_folder(lang_folder, language):
    texts = {}
    lang_file = f"{language}.txt"
    file_path = os.path.join(lang_folder, lang_file)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                if '=' in line:
                    key, value = line.strip().split('=', 1)  # разделяем только по первому символу '='
                    texts[key] = value.replace('\\n', '\n').strip()  # заменяем '\\n' на '\n'
                else:
                    print(f"Строка '{line.strip()}' не содержит символ '=' и будет пропущена.")
    else:
        print(f"Файл для языка '{language}' не найден в папке '{lang_folder}'.")
    return texts
    
def get_text_by_language_from_folder(language, key, folder_path):
    # Формируем путь к файлу для указанного языка
    file_path = os.path.join(folder_path, f"{language}.txt")
    if os.path.exists(file_path):
        # Если файл существует, загружаем тексты из него
        texts = load_texts_from_folder(folder_path)
        # Получаем текст по ключу
        if key in texts:
            return texts[key]
        else:
            return f"Текст для ключа '{key}' на языке '{language}' не найден."
    else:
        return f"Файл для языка '{language}' не найден в папке '{folder_path}'."
        folder_path = "lang"  # Путь к папке с файлами       


db_connection = mysql.connector.connect( 
    host=MYSQL_HOST, 
    user=MYSQL_USER, 
    password=MYSQL_PASSWORD, 
    database=MYSQL_DATABASE 
) 
db_cursor = db_connection.cursor() 
 
def open_mysql_connection():
    while True:
        try:
            db_connection = mysql.connector.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE
            )
            return db_connection
        except mysql.connector.Error as err:
            log_message(f"MySQL:open_mysql_connection: Произошла ошибка {err}, повторная попытка через 5 секунд...")
            time.sleep(5)

def is_mysql_connection_alive(db_connection):
    try:
        db_connection.ping(reconnect=True, attempts=3, delay=1)
        return True
    except mysql.connector.Error as err:
        log_message(f"MySQL:is_mysql_connection_alive: Соединение с базой данных разорвано: {err}")
        return False
        
def execute_query(query, db_connection):
    try:
        db_cursor = db_connection.cursor()
        db_cursor.execute(query)
        result = db_cursor.fetchone()
        return result
    except mysql.connector.Error as err:
        log_message(f"MySQL:execute_query: Произошла ошибка {err}")
        return None
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()

 
def get_data_from_mysql(ip_address, period, db_cursor):
    parts = ip_address.split(':') 
    ip = parts[0] 
    port = parts[1] if len(parts) > 1 else '25565' 
 
    if period == 'день': 
        delta = timedelta(days=1) 
    elif period == 'неделя': 
        delta = timedelta(days=7) 
    elif period == 'месяц': 
        delta = timedelta(days=30) 
    else: 
        return None, "Неверно указан период (день, неделя, месяц)" 
 
    start_time = datetime.now() - delta 
 
    query = f"SELECT times, online FROM lister WHERE server = '{ip}:{port}' AND times >= UNIX_TIMESTAMP('{start_time}')"
    db_cursor.execute(query) 
    result = db_cursor.fetchall() 
    if result: 
        return result, None 
 
    query = f"SELECT times, online FROM lister WHERE server LIKE '{ip}%' AND times >= UNIX_TIMESTAMP('{start_time}')" 
    db_cursor.execute(query) 
    result = db_cursor.fetchall() 
    if result: 
        return result, None 
 
    # Проверка наличия данных за последние 30 дней 
    query_30_days = f"SELECT times FROM lister WHERE server LIKE '{ip}%' AND times >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))" 
    db_cursor.execute(query_30_days) 
    result_30_days = db_cursor.fetchall() 
    if not result_30_days: 
        return None, "Недостаточно данных за последние 30 дней, чтобы построить график." 
# Функция для проверки, забанен ли пользователь 
def is_user_banned(vk_id):
    try:
        db_connection = open_mysql_connection()
        db_cursor = db_connection.cursor()
        
        query = f"SELECT ban FROM users WHERE vk_id = {vk_id}"
        db_cursor.execute(query)
        result = db_cursor.fetchone()

        if result:
            return result[0] == 1
        else:
            return False
    except mysql.connector.Error as err:
        log_message(f"MySQL:is_user_banned: Произошла ошибка {err}")
        return False
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()
        
def count_records_for_ip(ip_address, port):
    try:
        with mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        ) as db_connection:
            with db_connection.cursor() as db_cursor:
                query = """
                    SELECT COUNT(*) 
                    FROM lister 
                    WHERE server = %s AND (port = %s OR port = 25565 OR port = 0)
                """
                db_cursor.execute(query, (ip_address, port))
                count = db_cursor.fetchone()[0]
                return count
    except Error as err:
        log_message(f"MySQL:count_records_for_ip: Ошибка при обращении к базе данных: {err}")
        return None
        
def parse_ip_address(ip_address):
    # Используем регулярное выражение для разбора IP-адреса и порта (если указан)
    match = re.match(r"^(.+?)(?::(\d+))?$", ip_address)
    if match:
        server_ip = match.group(1)
        port = match.group(2)
        return server_ip, port
    else:
        return ip_address, None

def check_server_exists(ip_address):
    try:
        with mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        ) as db_connection:
            with db_connection.cursor() as db_cursor:
                server_ip, _ = parse_ip_address(ip_address)

                db_cursor.execute("SELECT COUNT(*) FROM server WHERE ip_address = %s", (server_ip,))
                count = db_cursor.fetchone()[0]
                
                return count > 0
    except mysql.connector.Error as err:
        log_message(f"MySQL:check_server_exists: Ошибка при обращении к базе данных: {err}")
        return False

 
def is_user_admin(vk_id):
    try:
        db_connection = open_mysql_connection()
        db_cursor = db_connection.cursor()
        
        query = f"SELECT admin FROM users WHERE vk_id = {vk_id}"
        db_cursor.execute(query)
        result = db_cursor.fetchone()
        
        if result:
            return result[0] == 1
        else:
            return False
    except mysql.connector.Error as err:
        log_message(f"MySQL:is_user_admin: Произошла ошибка {err}")
        return False
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()

def get_bot_settings():
    try:
        db_connection = open_mysql_connection()
        db_cursor = db_connection.cursor()
        
        query = "SELECT bot FROM psettings WHERE id = 1"
        db_cursor.execute(query)
        result = db_cursor.fetchone()
        
        if result:
            return result[0]
        else:
            return 1  # По умолчанию бот включен
    except mysql.connector.Error as err:
        log_message(f"MySQL:get_bot_settings: Произошла ошибка {err}")
        return False
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()
 
 
# Функция для закрытия соединения с базой данных MySQL 
def close_mysql_connection(db_connection): 
    db_connection.close() 
 
# Функция для получения общего количества пользователей из таблицы server 
def get_total_users(): 
    try:
        # Устанавливаем соединение с базой данных
        db_connection = open_mysql_connection()
        db_cursor = db_connection.cursor()

        # Выполняем запрос к базе данных
        db_cursor.execute("SELECT COUNT(*) AS total_users FROM users") 
        result = db_cursor.fetchone() 
        total_users = result[0]  # Получаем количество пользователей из первого элемента кортежа 

        return total_users 
    except mysql.connector.Error as err:
        log_message(f"MySQL:get_total_users: Произошла ошибка {err}")
        return None
    finally:
        # Закрываем соединение с базой данных
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()
 
def get_total_servers():
    try:
        db_connection = open_mysql_connection()
        db_cursor = db_connection.cursor()

        db_cursor.execute("SELECT COUNT(*) AS total_servers FROM server")
        result = db_cursor.fetchone()
        total_servers = result[0]  # Получаем количество серверов из первого элемента кортежа
        return total_servers
    except mysql.connector.Error as err:
        log_message(f"MySQL:get_total_servers: Произошла ошибка {err}")
        return None
        
def set_vip_status(vk_id, status):
    try:
        db_connection = open_mysql_connection()
        db_cursor = db_connection.cursor()
        query = "UPDATE users SET vip = %s WHERE vk_id = %s"
        db_cursor.execute(query, (1 if status else 0, vk_id))
        db_connection.commit()
    except mysql.connector.Error as err:
        log_message(f"MySQL:set_vip_status: Произошла ошибка {err}")
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()

def get_user_profile(vk_id):
    try:
        db_connection = open_mysql_connection()
        db_cursor = db_connection.cursor()

        # Получаем статус VIP
        db_cursor.execute("SELECT vip, ban, lang FROM users WHERE vk_id = %s", (vk_id,))
        user_info = db_cursor.fetchone()
        if not user_info:
            return "Пользователь не найден в базе данных."

        vip_status = "имеет VIP статус" if user_info[0] else "не имеет VIP статус"
        ban_status = "забанен" if user_info[1] else "не забанен"
        lang = user_info[2]
        lang_name = "Русский" if lang == 'ru' else "Английский" if lang == 'en' else lang

        # Получаем количество серверов
        db_cursor.execute("SELECT COUNT(*) FROM server WHERE from_id = %s", (vk_id,))
        server_count = db_cursor.fetchone()[0]

        profile_info = (f"Пользователь {vk_id}:\n"
                        f"Статус: {vip_status}\n"
                        f"Бан: {ban_status}\n"
                        f"Количество серверов: {server_count}\n"
                        f"Язык: {lang_name}")

        return profile_info
    except mysql.connector.Error as err:
        log_message(f"MySQL:get_user_profile: Произошла ошибка {err}")
        return "Произошла ошибка при получении профиля пользователя."
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()   

def increment_clicks(vk_id):
    try:
        # Устанавливаем соединение с базой данных
        db_connection = open_mysql_connection()
        db_cursor = db_connection.cursor()

        # Формируем запрос на обновление значений столбцов `daysclick` и `click`
        query = "UPDATE users SET daysclick = daysclick + 1, click = click + 1 WHERE vk_id = %s"
        db_cursor.execute(query, (vk_id,))

        # Фиксируем изменения в базе данных
        db_connection.commit()

        # Проверяем, было ли обновлено хотя бы одно значение
        if db_cursor.rowcount > 0:
            return f"Для пользователя с vk_id {vk_id} успешно увеличены значения daysclick и click."
        else:
            return f"Пользователь с vk_id {vk_id} не найден."
    except mysql.connector.Error as err:
        log_message(f"MySQL:increment_clicks: Произошла ошибка {err}")
        return "Произошла ошибка при обновлении данных пользователя."
    finally:
        # Закрываем соединение с базой данных
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()
            
            
def get_profile(vk_id):
    try:
        db_connection = open_mysql_connection()
        db_cursor = db_connection.cursor()

        # Получаем статус VIP
        db_cursor.execute("SELECT vip, ban, lang FROM users WHERE vk_id = %s", (vk_id,))
        user_info = db_cursor.fetchone()
        if not user_info:
            return "Пользователь не найден в базе данных."

        vip_status = "имеет VIP статус" if user_info[0] else "не имеет VIP статус"
        ban_status = "забанен" if user_info[1] else "не забанен"
        lang = user_info[2]
        lang_name = "Русский" if lang == 'ru' else "Английский" if lang == 'en' else lang

        # Получаем количество серверов
        db_cursor.execute("SELECT COUNT(*) FROM server WHERE from_id = %s", (vk_id,))
        server_count = db_cursor.fetchone()[0]

        profile_info = (f"Ваш ID: {vk_id}:\n"
                        f"Статус: {vip_status}\n"
                        f"Количество серверов: {server_count}\n"
                        f"Язык установленный: {lang_name}")

        return profile_info
    except mysql.connector.Error as err:
        log_message(f"MySQL:get_user_profile: Произошла ошибка {err}")
        return "Произошла ошибка при получении профиля пользователя."
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()                 
            
def get_image_data(ip_address, period):
    try:
        db_connection = open_mysql_connection()
        db_cursor = db_connection.cursor()

        parts = ip_address.split(':')
        ip = parts[0]
        port = parts[1] if len(parts) > 1 else '25565'

        # Определяем период времени
        if period == 'день':
            delta = timedelta(days=1)
        elif period == 'неделя':
            delta = timedelta(days=7)
        elif period == 'месяц':
            delta = timedelta(days=30)
        else:
            return None, "Неверно указан период (день, неделя, месяц)"
        
        start_time = datetime.now() - delta

        # Запрос для поиска записи для указанного порта
        query = f"""
        SELECT owner_id, vk_id 
        FROM stats 
        WHERE name = 'grafics/{ip}_{port}_{period}.png'
        """
        db_cursor.execute(query)
        result = db_cursor.fetchone()

        if result:
            return result, None

        # Если не найдено для указанного порта, проверяем альтернативные порты
        if port == '0' or port == '25565':
            alt_ports = ['25565', '0']
            for alt_port in alt_ports:
                alt_query = f"""
                SELECT owner_id, vk_id 
                FROM stats 
                WHERE name = 'grafics/{ip}_{alt_port}_{period}.png'
                """
                db_cursor.execute(alt_query)
                alt_result = db_cursor.fetchone()

                if alt_result:
                    return alt_result, None

        return None, "Данные ещё собираем о сервере, приходите через 15 минут."

    except mysql.connector.Error as err:
        log_message(f"MySQL:get_image_data: Произошла ошибка {err}")
        return None, "Произошла ошибка при работе с базой данных."


    
def create_user_if_not_exists(vk_id):
    try:
        db_connection = open_mysql_connection()  # Открываем соединение
        # Создаем курсор для выполнения запросов
        db_cursor = db_connection.cursor()
        try:
            # Проверяем, существует ли пользователь с указанным vk_id
            db_cursor.execute("SELECT COUNT(*) FROM users WHERE vk_id = %s", (vk_id,))
            count = db_cursor.fetchone()[0]

            # Если пользователь не существует, добавляем его в таблицу
            if count == 0:
                db_cursor.execute("INSERT INTO users (vk_id) VALUES (%s)", (vk_id,))
                db_connection.commit()
                # print(f"Пользователь с VK ID {vk_id} успешно создан.")
            else:
                # print(f"Пользователь с VK ID {vk_id} уже существует.")
                pass
        finally:
            db_cursor.close()  # Закрываем курсор
    except mysql.connector.Error as err:
        log_message(f"MySQL:create_user_if_not_exists: Ошибка при создании пользователя: {err}")
        sys.exit(1)  # Прерываем выполнение программы в случае ошибки
    finally:
        db_connection.close()  # Закрываем соединение
        
def check_command_cooldown(vk_id):
    try:
        # Создаем подключение к базе данных
        with mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        ) as db_connection:
            # Создаем курсор для выполнения запросов
            with db_connection.cursor() as db_cursor:
                # Выполняем запрос для получения информации о пользователе
                db_cursor.execute("SELECT IFNULL(vip, 0), IFNULL(admin, 0), IFNULL(times, 0) FROM users WHERE vk_id = %s", (vk_id,))
                result = db_cursor.fetchone()

                if result:
                    vip, admin, last_command_time = result
                    # Проверяем разницу во времени для разных ролей
                    if admin == 1:
                        cooldown_limit = 0  # Нет ограничения времени для админов
                    elif vip == 1:
                        cooldown_limit = 2  # Ограничение в 2 секунды для пользователей с VIP-статусом
                    else:
                        cooldown_limit = 5  # Ограничение в 5 секунд для обычных пользователей

                    # Получаем текущее время
                    current_time = int(time.time())

                    # Проверяем, что last_command_time не равно 'NULL'
                    if last_command_time != 'NULL':
                        # Преобразуем last_command_time в целое число
                        last_command_time = int(last_command_time)

                        # Проверяем, прошло ли достаточно времени с момента последней команды
                        time_difference = current_time - last_command_time
                        if time_difference < cooldown_limit:
                            # Возвращаем сообщение о необходимости подождать
                            wait_time = cooldown_limit - time_difference
                            return f"Подождите ещё {wait_time} секунд, чтобы выполнить команду."
                        else:
                            # Обновляем время последней команды в базе данных
                            db_cursor.execute("UPDATE users SET times = %s WHERE vk_id = %s", (current_time, vk_id))
                            db_connection.commit()
                            return None  # Время ожидания прошло, можно выполнять команду
                    else:
                        # Устанавливаем last_command_time в значение по умолчанию (0)
                        last_command_time = 0
                        # Обновляем время последней команды в базе данных
                        db_cursor.execute("UPDATE users SET times = %s WHERE vk_id = %s", (current_time, vk_id))
                        db_connection.commit()
                        return None  # Время ожидания прошло, можно выполнять команду
                else:
                    return "Пользователь с указанным vk_id не найден в базе данных."
    except mysql.connector.Error as err:
        log_message(f"MySQL:check_command_cooldown: Ошибка при проверке времени: {err}")
        return "Ошибка при проверке времени"
        
def ban_user(vk_id):
    try:
        with open_mysql_connection() as db_connection:
            with db_connection.cursor() as db_cursor:
                query = f"UPDATE users SET ban = 1 WHERE vk_id = {vk_id}"
                db_cursor.execute(query)
                db_connection.commit()
                log_message(f"User {vk_id} has been banned.")
    except mysql.connector.Error as err:
        log_message(f"MySQL:ban_user: Ошибка при обращении к базе данных: {err}")

def unban_user(vk_id):
    try:
        with open_mysql_connection() as db_connection:
            with db_connection.cursor() as db_cursor:
                query = f"UPDATE users SET ban = 0 WHERE vk_id = {vk_id}"
                db_cursor.execute(query)
                db_connection.commit()
                log_message(f"User {vk_id} has been unbanned.")
    except mysql.connector.Error as err:
        log_message(f"MySQL:unban_user: Ошибка при обращении к базе данных: {err}")
        
def is_user_admin1(vk_id):
    try:
        connection = open_mysql_connection()  # Открываем соединение с MySQL
        if connection:
            cursor = connection.cursor()
            query = f"SELECT admin FROM users WHERE vk_id = {vk_id}"  # SQL запрос для проверки админских прав пользователя
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()
            connection.close()  # Закрываем соединение с MySQL

            if result:  # Если запрос вернул результат
                return result[0] == 1  # Проверяем значение столбца admin: 1 - есть админские права, 0 - нет
            else:
                return False  # Если пользователь не найден в базе данных, считаем его не администратором
    except mysql.connector.Error as err:
        log_message(f"MySQL:is_user_admin: Ошибка при обращении к базе данных: {err}")
    return False  # Если произошла ошибка при обращении к базе данных, считаем пользователя не администратором



        
def get_server_ips():
    server_info = []
    try:
        connection = open_mysql_connection()
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SELECT ip_address, online FROM server")
            rows = cursor.fetchall()
            for row in rows:
                ip_address, online_players = row
                # Предполагается, что online_players хранит число или "No"
                try:
                    online_players = int(online_players)
                except ValueError:
                    online_players = "No"
                server_info.append((ip_address, online_players))
            cursor.close()
    except mysql.connector.Error as err:
        logging.error(f"MySQL:get_server_ips: Ошибка при выполнении запроса: {err}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()
    return server_info


def find_user_servers(vk_id):
    try:
        with open_mysql_connection() as db_connection:  # Используем контекстный менеджер для автоматического закрытия соединения
            with db_connection.cursor() as db_cursor:  # Используем контекстный менеджер для автоматического закрытия курсора
                # Выполнение SQL-запроса для поиска серверов пользователя
                db_cursor.execute("SELECT ip_address, port, alias, line_color FROM server WHERE from_id = %s", (vk_id,))
                # Получение результатов запроса
                result = db_cursor.fetchall()
                # Если пользователь не имеет серверов
                if not result:
                    return "У вас нет серверов. Чтобы стать владельцем, пропишите /add (IP)."
                # Формирование строки с информацией о серверах
                server_info = ""
                for row in result:
                    ip_address, port, alias, line_color = row
                    if alias is not None:
                        alias = f" [{alias}]"
                    else:
                        alias = ""  # Предотвращаем вывод None
                    if line_color == 'red':
                        line_icon = '&#128213;'
                    elif line_color == 'blue':
                        line_icon = '&#128216;'
                    else:
                        line_icon = ''
                    # Проверяем, равен ли порт 0, и заменяем его на 25565
                    port = port or '25565'
                    server_info += f"{line_icon} {ip_address}:{port}{alias}\n"
                return f"Ваши сервера: \n {server_info}"
    except mysql.connector.Error as err:
        print(f"{err}")
        log_message(f"MySQL:find_user_servers: {err}")
        return f"У вас нет серверов. Чтобы стать владельцем, пропишите /add (IP) :"


        
        
def aliases_list():
    try:
        with open_mysql_connection() as db_connection:  # Используем контекстный менеджер для автоматического закрытия соединения
            with db_connection.cursor() as db_cursor:  # Используем контекстный менеджер для автоматического закрытия курсора
                # Выполнение SQL-запроса для выборки всех записей из таблицы aliases
                db_cursor.execute("SELECT code, text FROM aliases")
                # Получение результатов запроса
                result = db_cursor.fetchall()
                # Если таблица пуста
                if not result:
                    return "Таблица Алиасов пуста."
                # Формирование строки с информацией о серверах
                server_info = ""
                for row in result:
                    code, text = row
                    server_info += f"{code} - {text}\n"
                return f"Все Алиансы: \n {server_info}"
    except mysql.connector.Error as err:
        log_message(f"MySQL:aliases_list: {err}")
        return "Непредвиденная ошибка со стороны сервера"

        
# Функция для пинга сервера Minecraft через mcstatus
async def ping_minecraft_server(ip, port):
    try:
        server = await JavaServer.async_lookup(f"{ip}:{port}")
        status = await server.async_status()
        return True
    except Exception as e:
        logger.error(f"Ошибка пинга сервера {ip}:{port} через mcstatus: {e}")
        return False

# Функция для проверки статуса сервера через API mcsrvstat.us
def check_server_status_via_api(ip, port):
    try:
        url = f"https://api.mcsrvstat.us/3/{ip}:{port}"
        response = requests.get(url)
        data = response.json()
        return data['debug']['ping']
    except Exception as e:
        logger.error(f"Ошибка сервера {ip}:{port} через API mcsrvstat.us: {e}")
        return False

# Функция для проверки статуса сервера через API eu.mc-api.net
def check_server_status_via_mc_api(ip, port):
    try:
        url = f"https://eu.mc-api.net/v3/server/ping/{ip}:{port}"
        response = requests.get(url)
        data = response.json()
        return data['online']
    except Exception as e:
        logger.error(f"Ошибка сервера {ip}:{port} через API eu.mc-api.net: {e}")
        return False

# Функция для проверки сервера через API
def check_server_api(ip, port):
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
                return data["players"]["online"], 1
        except Exception as e:
            logger.error(f"API: не удалось получить ответ от сервера {ip}:{port} ({e})")

    logger.warning(f"API: сервер {ip}:{port} не получил ответ через доступные методы")
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

# Настройка логгера
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)



def add_server(vk_id, ip_input):
    result = ""  # Переменная для хранения результата операции

    # Проверка наличия порта в ip_input
    if ":" in ip_input:
        ip_address, port = ip_input.split(":")
    else:
        ip_address = ip_input
        port = "25565"  # Порт по умолчанию, если не указан

    try:
        # Проверяем, существует ли запись с таким ip_address в таблице server
        with mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        ) as db_connection:
            with db_connection.cursor() as db_cursor:
                db_cursor.execute("SELECT COUNT(*) FROM server WHERE ip_address = %s", (ip_address,))
                count_ip = db_cursor.fetchone()[0]

                # Если запись существует, возвращаем ошибку
                if count_ip > 0:
                    return "Ошибка: К сожалению, данный сервер уже был добавлен в нашу базу данных, если вы владелец этого сервера, то напишите нам в лс группы"

                # Проверяем, существует ли запись с таким же IP в столбце ips
                db_cursor.execute("SELECT COUNT(*) FROM server WHERE ips LIKE %s", (f"%{ip_address}%",))
                count_ips = db_cursor.fetchone()[0]

                # Если запись существует, возвращаем ошибку
                if count_ips > 0:
                    return "Ошибка: К сожалению, данный IP уже был добавлен в нашу базу данных, если вы владелец этого сервера, то напишите нам в лс группы"

        # Проверяем сервер на доступность через API
        online_players, check_status = check_server_api(ip_address, port)
        if check_status == 0:
            # Если API не дало ответ, пробуем ручную проверку
            online_players, check_status = check_server_direct(ip_address, port)
        
        # Если сервер не доступен, возвращаем ошибку
        if check_status == 0:
            return "Ошибка: Сервер не доступен."

        # Создаем подключение к базе данных
        with mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        ) as db_connection:
            with db_connection.cursor() as db_cursor:
                current_time = int(time.time())  # Текущее время в формате Unix
                db_cursor.execute("INSERT INTO server (created_at, from_id, ip_address, ips, port) VALUES (%s, %s, %s, %s, %s)", (current_time, vk_id, ip_address, f"{ip_address}:{port}", port))
                db_connection.commit()
                result = "✔ Сервер добавлен, статистика будет готова через 15 минут"
    except mysql.connector.Error as err:
        result = f"Ошибка при обращении к базе данных"
        logger.error(f"MySQL:add_server: Ошибка при обращении к базе данных:  {err}")

    return result
    
def log_admin_action(vk_id, message):
    try:
        with open_mysql_connection() as db_connection:
            with db_connection.cursor() as db_cursor:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                query = "INSERT INTO admin_logs (vk_id, message, times) VALUES (%s, %s, %s)"
                db_cursor.execute(query, (vk_id, message, timestamp))
                db_connection.commit()
    except mysql.connector.Error as err:
        log_message(f"MySQL:log_admin_action: Произошла ошибка {err}")

    
def remove_server(vk_id, ip_input):
    result = ""  # Переменная для хранения результата операции
    ip_address1 = None  # Инициализируем переменную ip_address1

    # Проверка наличия порта в ip_input
    if ":" in ip_input:
        ip_address, port = ip_input.split(":")
    else:
        ip_address = ip_input
        port = "25565"  # Порт по умолчанию, если не указан

    try:
        # Проверяем, существует ли запись с таким ip_address в таблице server
        with mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        ) as db_connection:
            with db_connection.cursor() as db_cursor:
                # Проверяем, принадлежит ли сервер пользователю с vk_id
                db_cursor.execute("SELECT COUNT(*) FROM server WHERE ip_address = %s AND from_id = %s", (ip_address, vk_id))
                count_ip = db_cursor.fetchone()[0]

                # Если запись не существует, возвращаем ошибку
                if count_ip == 0:
                    return "Ошибка: Вы не можете удалить этот сервер, так как он не принадлежит вам."

                # Удаляем сервер из таблицы server
                db_cursor.execute("DELETE FROM server WHERE ip_address = %s", (ip_address,))
                db_connection.commit()

                # Удаляем все записи сервера из таблицы listner
                db_cursor.execute("DELETE FROM lister WHERE server_ip = %s", (ip_address,))
                db_connection.commit()

                result = "Запись успешно удалена из таблицы server и все связанные записи удалены из таблицы listner."
    except mysql.connector.Error as err:
        result = f"Ошибка при обращении к базе данных"
        log_message(f"MySQL:remove_server: Ошибка при обращении к базе данных:  {err}")

    return result
    
def set_server_alias(ip_address, alias, vk_id):
    # Разделяем ip_address на IP-адрес и порт
    parts = ip_address.split(':')
    ip = parts[0]
    port = parts[1] if len(parts) > 1 else '0c'

    # Проверяем, является ли порт числом
    try:
        port = int(port)
    except ValueError:
        port = 0

    # Ищем сервер в базе данных
    try:
        with open_mysql_connection() as db_connection:
            with db_connection.cursor() as db_cursor:
                # Проверка, существует ли уже такой алиас
                db_cursor.execute("SELECT 1 FROM server WHERE alias = %s", (alias,))
                alias_exists = db_cursor.fetchone()

                if alias_exists:
                    return "Ошибка: Указанный алиас уже занят."

                # Ищем сервер по IP и порту
                db_cursor.execute("SELECT from_id, alias FROM server WHERE ip_address = %s AND port = %s", (ip, port))
                result = db_cursor.fetchone()

                # Проверяем, найден ли сервер
                if result:
                    server_owner_id, current_alias = result
                    print(server_owner_id)
                    # Проверяем, принадлежит ли сервер пользователю
                    vk_id_str = str(vk_id)
                    if server_owner_id != vk_id_str:
                        return "Ошибка: Этот сервер не принадлежит вам."

                    # Обновляем алиас, если он отличается
                    if current_alias != alias:
                        db_cursor.execute("UPDATE server SET alias = %s WHERE ip_address = %s AND port = %s", (alias, ip, port))
                        db_connection.commit()
                        return f"Алиас для сервера успешно обновлен на '{alias}'."
                    else:
                        return "Ошибка: Указанный алиас уже установлен для этого сервера."
                else:
                    return "Ошибка: Сервер с указанным IP-адресом и портом не найден в базе данных."
    except mysql.connector.Error as err:
        log_message(f"MySQL:set_server_alias: Ошибка при обращении к базе данных: {err}")
        return "Ошибка при обращении к базе данных."

        
def get_closest_value(db_cursor, ip, port, timestamp):
    query = """
        SELECT online 
        FROM lister 
        WHERE server = %s AND port = %s 
        ORDER BY ABS(times - %s) 
        LIMIT 1
    """
    db_cursor.execute(query, (ip, port, timestamp))
    result = db_cursor.fetchone()
    return result[0] if result else "-"

def get_server_stats(ip_address, period='день', timeout=5):
    try:
        ip_address = None if ip_address == "127.0.0.1" else ip_address

        # Default port handling
        parts = ip_address.split(':')
        ip = parts[0]
        port = parts[1] if len(parts) > 1 and parts[1] not in ['0', '25565'] else '25565'

        # Queries to get server data
        server_query = """
        SELECT ip_address, port, online, onlines, created_at 
        FROM server 
        WHERE ip_address = %s AND (port = %s OR port = 0)
        """
        onlines_query = """
        SELECT daysmax, dayssred, daysmin, vse, nedelmax, nedelsred, nedelmin, mecmax, mecred, mecmin 
        FROM onlines 
        WHERE id = %s
        """

        with mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        ) as db_connection:
            with db_connection.cursor() as db_cursor:
                # Fetch server record
                db_cursor.execute(server_query, (ip, port))
                server_record = db_cursor.fetchone()
                if not server_record:
                    return "Сервер не найден."

                ip_address, port, online, onlines_id, created_at = server_record
                db_cursor.execute(onlines_query, (onlines_id,))
                onlines_record = db_cursor.fetchone()
                if not onlines_record:
                    return "Данные онлайна не найдены."

                (
                    daysmax, dayssred, daysmin, vse,
                    nedelmax, nedelsred, nedelmin,
                    mecmax, mecred, mecmin
                ) = map(int, map(float, onlines_record))  # Convert to integers

                created_at_msk = datetime.fromtimestamp(int(created_at), tz=timezone.utc).astimezone(tz=timezone(timedelta(hours=3)))

        if period == 'день':
            return f"""Вот ваш график:
Сейчас онлайн: {online}
Макс. онлайн за день: {daysmax}
Сред. онлайн за день: {dayssred}
Мин. онлайн за день: {daysmin}
Максимальный онлайн за все время: {vse}
Сервер был добавлен в нашу базу: {created_at_msk.strftime('%Y-%m-%d %H:%M:%S')} (МСК)"""
        
        elif period == 'неделя':
            return f"""Вот ваш график:
Сейчас онлайн: {online}
Макс. онлайн за неделя: {nedelmax}
Сред. онлайн за неделю: {nedelsred}
Мин. онлайн за неделю: {nedelmin}
Максимальный онлайн за все время: {vse}
Сервер был добавлен в нашу базу: {created_at_msk.strftime('%Y-%m-%d %H:%M:%S')} (МСК)"""
        
        elif period == 'месяц':
            return f"""Вот ваш график:
Сейчас онлайн: {online}
Макс. онлайн за месяц: {mecmax}
Сред. онлайн за месяц: {mecred}
Мин. онлайн за месяц: {mecmin}
Максимальный онлайн за все время: {vse}
Сервер был добавлен в нашу базу: {created_at_msk.strftime('%Y-%m-%d %H:%M:%S')} (МСК)"""
        
        else:
            return "Invalid period specified. Use 'день', 'неделя', or 'месяц'."

    except mysql.connector.Error as err:
        log_message(f"MySQL:get_server_stats: Ошибка при обращении к базе данных: {err}")
        return "Ошибка при обращении к базе данных"
    except Exception as e:
        log_message(f"MySQL:get_server_stats: Произошла ошибка: {e}")
        return "Произошла ошибка"


def get_ip_port_by_alias(text):
    try:
        # Установка соединения с базой данных
        with mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        ) as db_connection:
            # Создание объекта курсора
            cursor = db_connection.cursor()
            
            # Поиск алиаса в таблице server
            query = "SELECT ip_address, port FROM server WHERE alias = %s"
            cursor.execute(query, (text,))
            result = cursor.fetchone()
            
            # Если алиас не найден, возвращаем переданный текст
            if result is None:
                return text
            
            # Если порт равен 0, присваиваем значение по умолчанию 25565
            ip, port = result
            port = port or '25565'
            print(ip, port)
            # Возвращаем IP:PORT
            return f"{ip}:{port}"
    
    except mysql.connector.Error as err:
        log_message(f"MySQL:get_ip_port_by_alias: Ошибка при обращении к базе данных:  {err}")
        # Возвращаем переданный текст в случае ошибки
        return text
        
def bot_off():
    try:
        # Установка соединения с базой данных
        db_connection = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        db_cursor = db_connection.cursor()

        # Получение текущего статуса бота
        db_cursor.execute("SELECT bot FROM psettings WHERE id = 1")
        bot_status = db_cursor.fetchone()[0]

        # Обновление статуса бота в зависимости от текущего значения
        if bot_status == 0:
            new_bot_status = 1
            message = "BeaconBot доступен в публичном режиме."
        elif bot_status == 1:
            new_bot_status = 0
            message = "BeaconBot доступен только для админов."
        else:
            return "Некорректное значение статуса бота в таблице psettings."

        # Обновление статуса бота в таблице psettings
        db_cursor.execute("UPDATE psettings SET bot = %s WHERE id = 1", (new_bot_status,))
        db_connection.commit()

        # Закрытие соединения с базой данных
        db_cursor.close()
        db_connection.close()

        return message

    except mysql.connector.Error as err:
       log_message(f"MySQL:bot_off: Ошибка при обращении к базе данных:  {err}")
       return f"Ошибка при выполнении запроса к базе данных"
       
def update_language_in_database(vk_id, language):
    try:
        # Установка соединения с базой данных
        db_connection = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        db_cursor = db_connection.cursor()
        lang = lang_settings(vk_id)
        bot_info = load_texts_from_folder("lang", lang)
        # Проверка текущего языка пользователя
        db_cursor.execute("SELECT lang FROM users WHERE vk_id = %s", (vk_id,))
        current_language = db_cursor.fetchone()

        if current_language is None:
            return "Error Not English, Russia."
          
        if current_language[0] == language:
            if language == 'ru':
                return "У тебя и так русский язык."
            elif language == 'en':
                return "Your language is already set to English"
            else:
                return f"{bot_info['lang_input']}."

        # Обновление языка пользователя
        db_cursor.execute("UPDATE users SET lang = %s WHERE vk_id = %s", (language, vk_id))
        db_connection.commit()

        # Закрытие соединения с базой данных
        db_cursor.close()
        db_connection.close()

        return "Язык успешно обновлен."

    except mysql.connector.Error as err:
        log_message(f"MySQL:update_language_in_database: Ошибка при обращении к базе данных:  {err}")
        return "Error."
        
def lang_settings(vk_id):
    try:
        # Установка соединения с базой данных
        db_connection = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        db_cursor = db_connection.cursor()

        # Получение текущего языка пользователя из базы данных
        db_cursor.execute("SELECT lang FROM users WHERE vk_id = %s", (vk_id,))
        current_language = db_cursor.fetchone()

        if current_language is None:
            return "Пользователь не найден в базе данных."

        # Закрытие соединения с базой данных
        db_cursor.close()
        db_connection.close()

        return current_language[0]

    except mysql.connector.Error as err:
        log_message(f"MySQL:update_language_in_database: Ошибка при обращении к базе данных: {err}")
        return "Произошла ошибка при обновлении языка пользователя."
        
def time_unix():
    try:
        # Установка соединения с базой данных
        db_connection = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        db_cursor = db_connection.cursor()

        # Получение текущего языка пользователя из базы данных
        db_cursor.execute("SELECT uptime FROM psettings WHERE id = 1")
        current_language = db_cursor.fetchone()

        if current_language is None:
            return "Пользователь не найден в базе данных."

        # Закрытие соединения с базой данных
        db_cursor.close()
        db_connection.close()

        return current_language[0]

    except mysql.connector.Error as err:
        log_message(f"MySQL:update_language_in_database: Ошибка при обращении к базе данных: {err}")
        return "Произошла ошибка при обновлении языка пользователя."        

def add_port_check(ip_address, port, vk_id, ok):
    try:
        with open_mysql_connection() as db_connection:
            with db_connection.cursor() as db_cursor:
                query = "INSERT INTO ip_port (ip_address, port, times, vk_id, ok) VALUES (%s, %s, %s, %s, %s)"
                db_cursor.execute(query, (ip_address, port, int(time.time()), vk_id, ok))
                db_connection.commit()
    except mysql.connector.Error as err:
        log_message(f"MySQL:add_port_check: Ошибка при обращении к базе данных: {err}")

def get_port_check_count(ip_address):
    try:
        with open_mysql_connection() as db_connection:
            with db_connection.cursor() as db_cursor:
                query = "SELECT COUNT(*) FROM ip_port WHERE ip_address = %s AND times > %s"
                db_cursor.execute(query, (ip_address, int(time.time()) - 3600))
                result = db_cursor.fetchone()
                return result[0] if result else 0
    except mysql.connector.Error as err:
        log_message(f"MySQL:get_port_check_count: Ошибка при обращении к базе данных: {err}")
        return 0

def get_last_15_port_checks(ip_address):
    try:
        with open_mysql_connection() as db_connection:
            with db_connection.cursor() as db_cursor:
                query = "SELECT port, ok FROM ip_port WHERE ip_address = %s ORDER BY id DESC LIMIT 15"
                db_cursor.execute(query, (ip_address,))
                result = db_cursor.fetchall()

                # Обработка результатов для получения уникальных портов
                unique_ports = {}
                for port, ok in result:
                    if port not in unique_ports:
                        unique_ports[port] = ok

                # Преобразование в список кортежей
                unique_ports_list = [(port, unique_ports[port]) for port in unique_ports]

                return unique_ports_list if unique_ports_list else []
    except mysql.connector.Error as err:
        log_message(f"MySQL:get_last_15_port_checks: Ошибка при обращении к базе данных: {err}")
        return []

def get_user_status(vk_id):
    try:
        with open_mysql_connection() as db_connection:
            with db_connection.cursor() as db_cursor:
                query = "SELECT vip, checkport, admin FROM users WHERE vk_id = %s"
                db_cursor.execute(query, (vk_id,))
                result = db_cursor.fetchone()
                return result if result else (0, 0, 0)
    except mysql.connector.Error as err:
        log_message(f"MySQL:get_user_status: Ошибка при обращении к базе данных: {err}")
        return (0, 0, 0)

def increment_user_checkport(vk_id):
    try:
        with open_mysql_connection() as db_connection:
            with db_connection.cursor() as db_cursor:
                query = "UPDATE users SET checkport = checkport + 1 WHERE vk_id = %s"
                db_cursor.execute(query, (vk_id,))
                db_connection.commit()
    except mysql.connector.Error as err:
        log_message(f"MySQL:increment_user_checkport: Ошибка при обращении к базе данных: {err}")
        
def get_protocol_from_db(ip, port=None):
    try:
        db_connection = open_mysql_connection()
        db_cursor = db_connection.cursor()
        
        if port is None:
            # Если порт не указан, ищем по стандартному порту 25565
            query = """
                SELECT protocol 
                FROM pinglist 
                WHERE ip_address = %s AND port = 25565
                ORDER BY id DESC
                LIMIT 1
            """
            db_cursor.execute(query, (ip,))
        else:
            query = """
                SELECT protocol 
                FROM pinglist 
                WHERE ip_address = %s AND port = %s
                ORDER BY id DESC
                LIMIT 1
            """
            db_cursor.execute(query, (ip, port))

        result = db_cursor.fetchone()

        if result:
            return result[0]
        else:
            return None
    except mysql.connector.Error as err:
        log_message(f"MySQL:get_protocol_from_db: Произошла ошибка {err}")
        return None
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()

def save_protocol_to_db(ip, port, protocol):
    try:
        db_connection = open_mysql_connection()
        db_cursor = db_connection.cursor()

        # Сначала проверяем, существует ли запись с таким IP и портом
        query_check = "SELECT COUNT(*) FROM pinglist WHERE ip_address = %s AND port = %s"
        db_cursor.execute(query_check, (ip, port))
        exists = db_cursor.fetchone()[0] > 0

        unix_time = int(time.time())

        if exists:
            # Обновляем существующую запись
            query_update = (
                "UPDATE pinglist "
                "SET protocol = %s, times = %s "
                "WHERE ip_address = %s AND port = %s"
            )
            db_cursor.execute(query_update, (protocol, unix_time, ip, port))
        else:
            # Вставляем новую запись
            query_insert = (
                "INSERT INTO pinglist (ip_address, port, protocol, times) "
                "VALUES (%s, %s, %s, %s)"
            )
            db_cursor.execute(query_insert, (ip, port, protocol, unix_time))

        db_connection.commit()

    except mysql.connector.Error as err:
        log_message(f"MySQL:save_protocol_to_db: Произошла ошибка {err}")

    finally:
        if db_cursor is not None:
            db_cursor.close()
        if db_connection is not None:
            db_connection.close()
            
def close_server(vk_id, ip_input):
    result = ""  # Переменная для хранения результата операции
    max_retries = 3  # Максимальное количество повторных попыток
    retry_delay = 5  # Задержка между попытками в секундах

    # Проверка наличия порта в ip_input
    if ":" in ip_input:
        ip_address, port = ip_input.split(":")
    else:
        ip_address = ip_input
        port = "25565"  # Порт по умолчанию, если не указан

    db_connection = None
    db_cursor = None

    for attempt in range(max_retries):
        try:
            # Создаем подключение к базе данных
            db_connection = open_mysql_connection()
            db_cursor = db_connection.cursor()

            # Проверяем наличие записи с указанным IP и портом
            if port == "25565":
                db_cursor.execute(
                    "SELECT active, from_id, port FROM server WHERE ip_address = %s AND (port = %s OR port = %s)",
                    (ip_address, "25565", "0")
                )
            else:
                db_cursor.execute(
                    "SELECT active, from_id, port FROM server WHERE ip_address = %s AND port = %s",
                    (ip_address, port)
                )

            record = db_cursor.fetchone()

            # Если запись существует
            if record:
                active, from_id, record_port = record

                # Приводим значения к строковому типу для сравнения
                if str(vk_id).strip() != str(from_id).strip():
                    print(vk_id, from_id)
                    return "Ошибка: У вас нет прав на изменение этого сервера."

                # Меняем статус active на противоположный
                new_active = 1 if active == 0 else 0
                if port == "25565":
                    db_cursor.execute(
                        "UPDATE server SET active = %s WHERE ip_address = %s AND (port = %s OR port = %s)",
                        (new_active, ip_address, "25565", "0")
                    )
                else:
                    db_cursor.execute(
                        "UPDATE server SET active = %s WHERE ip_address = %s AND port = %s",
                        (new_active, ip_address, port)
                    )
                db_connection.commit()

                if new_active == 1:
                    result = f"Ваш сервер {ip_address}:{port} открыт для всех."
                else:
                    result = f"Ваш сервер {ip_address}:{port} закрыт для всех."

            else:
                result = "Ошибка: Сервера нет в базе серверов."
            break  # Выход из цикла, если операция успешна
        except mysql.connector.Error as err:
            if err.errno == 1205 and attempt < max_retries - 1:
                # Ждем перед повторной попыткой
                time.sleep(retry_delay)
                continue
            result = f"Ошибка при обращении к базе данных"
            logger.error(f"MySQL:toggle_server: Ошибка при обращении к базе данных: {err}")
        finally:
            if db_cursor is not None:
                db_cursor.close()
            if db_connection is not None:
                db_connection.close()

    return result
    
def server_active(ip, port=None):
    try:
        db_connection = open_mysql_connection()
        db_cursor = db_connection.cursor()
        
        if port is None or port == 25565:
            # Если порт не указан или равен 25565, ищем также по порту 0
            query = """
                SELECT active 
                FROM server 
                WHERE ip_address = %s AND (port = 25565 OR port = 0)
                ORDER BY id DESC
                LIMIT 1
            """
            db_cursor.execute(query, (ip,))
            print("fonis, {ip} {port}")
        else:
            query = """
                SELECT active 
                FROM server 
                WHERE ip_address = %s AND port = %s
                ORDER BY id DESC
                LIMIT 1
            """
            db_cursor.execute(query, (ip, port))

        result = db_cursor.fetchone()
        
        if result:
            return result[0]  # Возвращаем значение столбца active
        else:
            return None
    except mysql.connector.Error as err:
        log_message(f"MySQL:server_active: Произошла ошибка {err}")
        return None
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()


##########################################################################################################################################################        
def server_api(ip_address, port=None):
    if port is None or port == 0:
        actual_port = 25565
    else:
        actual_port = port
    
    print("Api0", ip_address, actual_port)

    try:
        # Отправляем запрос к API сервера Minecraft с установленным таймаутом в 5 секунд
        result = requests.get(f"https://rionx.ru/api/server.php?ip={ip_address}:{actual_port}&token=gRgqoWceP8hu", timeout=1)
        print("Api", ip_address, actual_port)
        
        # Проверяем успешность запроса
        if not result.ok:
            return "Ошибка: Не удалось выполнить запрос к серверу Minecraft."

        # Получаем информацию о сервере из JSON-ответа
        server_info = result.json()

        # Проверяем, доступен ли сервер
        if "error" in server_info:
            # Сервер недоступен по первому методу, пытаемся через второй метод
            result = requests.get(f"https://api.mcsrvstat.us/3/{ip_address}")
            if not result.ok:
                return "Ошибка: Не удалось выполнить запрос к серверу Minecraft."
            
            server_info = result.json()
            if "error" in server_info:
                return "Ошибка: Сервер не отвечает."
            else:
                return False  # Сервер доступен, возвращаем False

        return False  # Сервер доступен, возвращаем False
    except Exception as e:
        return f"Ошибка: {e}"
def ram_server():
    bot_version = "1.0 Beta"
    max_ram = "64.0 Gb Ram"
    allocated_ram = "48.0 GB Ram"
    loaded_ram = f"{random.randint(1, 3)} GB Ram"  # Генерируем случайное значение нагрузки

    info = f"Информация о боте:\nВерсия бота: {bot_version}\nМакс RAM: {max_ram}\nВыделенно: {allocated_ram}\nНагружено: {loaded_ram}"
    return info
    
def get_allocated_memory():
    allocated_memory = round(random.uniform(6.0, 16.0), 1)  # Генерация значения от 6.0 до 16.0
    return allocated_memory
    

 
