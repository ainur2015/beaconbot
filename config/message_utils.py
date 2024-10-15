import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import random
from config.vk_config import VK_TOKEN, VK_GROUP_ID
from config.graph_utils import plot_graph_and_save, comparison_server_graph
from config.db_utils import *
from datetime import datetime
import re
import os
import time
import base64
import asyncio
from pprint import pprint
import whois
import json
import requests
import threading
import sys
import socket
from mcstatus import JavaServer
import logging
import psutil
import logger
import subprocess
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
import fitz  # PyMuPDF
from pdfminer.high_level import extract_text
from mctools import PINGClient
import uuid
import logger


vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

saved_temp_file = None
saved_message = None  # Initialize saved_message variable

def log_message(message):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Получаем текущую дату и время в формате строки
        log_entry = f"[{timestamp}] {message}"  # Форматируем запись в лог: [дата и время] сообщение

        with open("log.txt", "a") as log_file:  # Открываем файл для добавления текста в конец
            log_file.write(log_entry + "\n")  # Записываем сообщение в лог с добавлением символа новой строки
        print("ERROR MYSSAGE_UTILS")
        sys.exit(1)
    except Exception as e:
        print("Ошибка при записи сообщения в лог:", e)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        
def send_image_to_vk1(peer_id, filename):
    global saved_message, saved_temp_file
    try:
        # Отправляем сообщение "Подождите, создаю график..."
        if not saved_message:
            pass  # Placeholder for the action you want to perform when saved_message is None
        
        print("Начинаю отправку фото VK")
        upload_url = vk.photos.getMessagesUploadServer()['upload_url']
        
        # Загружаем фотографию на сервер ВКонтакте
        with open(filename, 'rb') as file:
            response = vk_session.http.post(upload_url, files={'photo': file}).json()
        
        # Сохраняем фотографию на сервере ВКонтакте
        photo = vk.photos.saveMessagesPhoto(**response)[0]
        owner_id = photo['owner_id']
        photo_id = photo['id']
        print("Закончил")
        
        # Редактируем сообщение, прикрепляя к нему фотографию
        vk.messages.send(peer_id=peer_id, message="", attachment=f'photo{owner_id}_{photo_id}', disable_mentions=1, random_id=random.randint(1, 10**9))
        
        # После успешной отправки удаляем файл с локального хранилища
        os.remove(filename)
        
        saved_temp_file = filename
    except Exception as e:
         log_message(f"send_image_to_vk1: Ошибка при отправке изображения {e}")
         
def test_command(vk, peer_id, vk_id, message):
    global saved_message, saved_temp_file
    try:
        # Отправляем сообщение "Подождите, создаю график..."
        if not saved_message:
            pass  # Placeholder for the action you want to perform when saved_message is None
        
        # Редактируем сообщение, прикрепляя к нему фотографию
        vk.messages.send(peer_id=peer_id, message="", attachment=f'photo-224527912_457240843', disable_mentions=1, random_id=random.randint(1, 10**9))
        
    except Exception as e:
         log_message(f"send_image_to_vk1: Ошибка при отправке изображения {e}")

MAX_EXECUTION_TIME = 20  # Ваше значение времени выполнения в секундах


def handle_stat_command(peer_id, message, vk_id, vk):
    try:
        print(message)
        if is_user_banned(vk_id):
            return
        if not is_user_admin(vk_id) and get_bot_settings() == 0:
            return

        cooldown_message = check_command_cooldown(vk_id)
        if cooldown_message:
            vk.messages.send(peer_id=peer_id, message=cooldown_message, random_id=random.randint(1, 10**9))
            return   

        parts = message.split()
        lang = lang_settings(vk_id)
        bot_info = load_texts_from_folder("lang", lang)

        # Определяем ip_port и период
        if len(parts) >= 2:
            ip_port = parts[1]
        else:
            vk.messages.send(peer_id=peer_id, message=f"{bot_info['stats_error']} ", random_id=random.randint(1, 10**9))
            return

        period = parts[2].strip() if len(parts) >= 3 else "день"  # Если период не указан, присваиваем "день"

        # Сопоставляем периоды
        period_mapping = {
            "day": "день",
            "nedel": "неделя",
            "week": "месяц",
            "month": "месяц",
            "mec": "месяц"
        }

        period = period_mapping.get(period, period)  # Меняем период, если он в словаре
        ip_port = get_ip_port_by_alias(ip_port)
        if not check_server_exists(ip_port):
            button_ned = json.dumps({"function_name": f"/add {ip_port}"})
            button_nedel = f"{bot_info['stats_dob']}"
            button_stats = {
                "action": {
                    "type": "text",
                    "label": button_nedel.strip(),
                    "payload": button_ned
                }
            }
            keyboard = {
                "inline": True,
                "buttons": [[button_stats]]
            }
            keyboard = json.dumps(keyboard, ensure_ascii=False).encode('utf-8')
            vk.messages.send(peer_id=peer_id, message=f"{bot_info['stats_error2']}", keyboard=keyboard, random_id=random.randint(1, 10**9))
            return
       
        ip_address, port = ip_port.split(":") if ":" in ip_port else (ip_port, "0")

        if port == "25565":
            port = "0"
        record_count = count_records_for_ip(ip_address, port)
        if record_count is not None and record_count < 3:
            vk.messages.send(peer_id=peer_id, message=f"{bot_info['stats_error3']}", random_id=random.randint(1, 10**9))
            return
        print(period)

        valid_periods = {"день", "неделя", "месяц"}

        if period not in valid_periods:
            vk.messages.send(peer_id=peer_id, message=f"{bot_info['stats_error4']}", random_id=random.randint(1, 10**9))
            return

        execution_thread = threading.Thread(target=execute_handle_stat_command, args=(ip_address, port, period, peer_id, vk, ip_port, vk_id))
        execution_thread.start()

        execution_thread.join(MAX_EXECUTION_TIME)

        if execution_thread.is_alive():
            raise TimeoutError("Превышено максимальное время выполнения")

    except Exception as e:
        log_message(f"handle_stat_command: Произошла ошибка {str(e)}")

def execute_handle_stat_command(ip_address, port, period, peer_id, vk, ips1, vk_id):
    try:
        image_data, error_message = get_image_data(ip_address, period)
        stats_message = get_server_stats(f"{ip_address}:{port}", period)
        if image_data:
            send_image_to_vk(vk, peer_id, image_data[0], image_data[1], ips1, vk_id, stats_message)
        else:
            vk.messages.send(peer_id=peer_id, message=error_message, disable_mentions=1, random_id=random.randint(1, 10**9))

    except Exception as e:
        log_message(f"execute_handle_stat_command: Произошла ошибка {str(e)}")

def send_image_to_vk(vk, peer_id, owner_id, photo_id, ips1, vk_id, stats_message):
    try:
        lang = lang_settings(vk_id)
        bot_info = load_texts_from_folder("lang", lang)

        button_ned = json.dumps({"function_name": f"/stats {ips1} nedel"})
        button_nedel = f"{bot_info['nedel']}"
        button_stats = {
            "action": {
                "type": "text",
                "label": button_nedel.strip(),
                "payload": button_ned
            }
        }

        button_mec = json.dumps({"function_name": f"/stats {ips1} mec"})
        button_mecec = f"{bot_info['mec']}"
        button_ip = {
            "action": {
                "type": "text",
                "label": button_mecec.strip(),
                "payload": button_mec
            }
        }

        keyboard = {
            "inline": True,
            "buttons": [[button_stats, button_ip]]
        }
        keyboard = json.dumps(keyboard, ensure_ascii=False).encode('utf-8')

        vk.messages.send(peer_id=peer_id, message=f" {stats_message} ", attachment=f'photo{owner_id}_{photo_id}', keyboard=keyboard, disable_mentions=1, random_id=random.randint(1, 10**9))

    except Exception as e:
        log_message(f"send_image_to_vk: Ошибка при отправке изображения {e}")

def format_uptime(start_time_unix):
    try:
        # Убедитесь, что start_time_unix - это число (float или int)
        start_time_unix = float(start_time_unix)
    except ValueError:
        return "Ошибка: Неверный формат времени запуска."

    # Получаем текущее время в формате Unix
    now_unix = time.time()
    
    # Рассчитываем разницу во времени
    uptime_seconds = now_unix - start_time_unix
    
    # Преобразуем разницу в дни, часы, минуты и секунды
    days = int(uptime_seconds // (24 * 3600))
    hours = int((uptime_seconds % (24 * 3600)) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    seconds = int(uptime_seconds % 60)
    
    # Форматируем строку
    uptime_str = f"&#9989; Uptime: {days} дн. {hours} ч. {minutes} мин. {seconds} сек."
    
    return uptime_str

def bot_stat_command(peer_id, vk_id, vk):
    try:
        print("Всё норм1")
        if is_user_banned(vk_id):
            return
        if not is_user_admin(vk_id) and get_bot_settings() == 0:
            return
        print("Всё норм2")

        # Получаем информацию о боте
        total_users = get_total_users()
        total_servers = get_total_servers()
        allocated_memory = get_allocated_memory()

        # Здесь нужно установить значение времени запуска, замените 1687470000 на ваше значение
        start_time_unix = 1724188923  # Замените на фактическое время запуска
        uptimes = format_uptime(start_time_unix)
        
        # Получаем информацию о реальной потребляемой памяти
        process = psutil.Process()
        real_memory_usage = process.memory_info().rss / (1024 * 1024)  # в мегабайтах
        lang = lang_settings(vk_id)

        # Словарь для сопоставления языков
        lang_dict = {
            'ru': 'Русский',
            'en': 'English'
        }

        # Получаем название языка из словаря, если он существует
        lang_name = lang_dict.get(lang, lang)
        bot_info = load_texts_from_folder("lang", lang)
        # Формируем сообщение с информацией о боте
        message = f"{bot_info['info_bot']}\n"
        message += f"{bot_info['pol_info']} {total_users}\n"
        message += f"{bot_info['serv_info']} {total_servers}\n"
        message += f"{bot_info['pot_ram']} {real_memory_usage:.2f} MB\n"
        message += f"{bot_info['beceda']} {peer_id}\n"
        message += f"{bot_info['id_vk']} {vk_id}\n"
        message += f"{bot_info['langi']} {lang_name} \n"
        message += f"{uptimes} \n"

        # Отправляем сообщение с информацией о боте
        vk.messages.send(peer_id=peer_id, message=message, disable_mentions=1, random_id=random.randint(1, 10**9))
    except Exception as e:
        log_message(f"bot_stat_command: Произошла ошибка {str(e)}")

    
# Ваши функции для обработки сообщений и callback-сообщений
def process_message_and_send_with_button(vk, peer_id, message, attachment=None, function_name=None):
    if re.search(r'[@*]', message):
        message = re.sub(r'([@*])', r'\1 ', message)
    
    if len(message.split()) > 40:
        shortened_message = shorten_message(message)
        cleaned_message = remove_banned_words(shortened_message)
        if function_name:
            send_message_with_button(vk, peer_id, cleaned_message, attachment, function_name)
        else:
            vk.messages.send(peer_id=peer_id, message=cleaned_message, attachment=attachment, disable_mentions=1, random_id=random.randint(1, 10**9))
    else:
        if function_name:
            send_message_with_button(vk, peer_id, message, attachment, function_name)
        else:
            vk.messages.send(peer_id=peer_id, message=message, attachment=attachment, disable_mentions=1, random_id=random.randint(1, 10**9))

# Ваша функция для удаления запрещенных слов
def remove_banned_words(message):
    with open('codes.txt', 'r') as file:
        banned_words = file.read().splitlines()
    
    for word in banned_words:
        message = message.replace(word, '')

    message = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', message)

    return message

def remove_color_codes(text):
    # Удаляем символы цвета из строки
    return re.sub(r'§.', '', text)

async def get_server_info(server_address, vk_id):
    try:
        # Получаем объект сервера асинхронно
        server = JavaServer.lookup(server_address)

        # Получаем статус сервера, включая MOTD
        status = await asyncio.wait_for(server.async_status(), timeout=1)

        # Получаем MOTD в виде строки и удаляем лишние пробелы и символы цвета
        motd_plain = status.description
        motd_plain = remove_color_codes(motd_plain)
        lang = lang_settings(vk_id)
        bot_info = load_texts_from_folder("lang", lang)
        status_plain = remove_color_codes(status.version.name)

        # Получаем иконку сервера в формате base64
        favicon_data = base64.b64decode(status.icon.removeprefix("data:image/png;base64,"))

        # Записываем иконку в файл
        image_filename = f"image_{time.time()}.png"
        with open(image_filename, 'wb') as f:
            f.write(favicon_data)

        # Формируем строку с информацией о сервере
        server_info = f"{bot_info['info_server']} ({server_address})\n\n"
        server_info += "╔ IP: {}\n".format(server_address)
        server_info += f"║ {bot_info['server_zaz']} {int(status.latency)} {bot_info['ms']}\n"
        server_info += f"║ {bot_info['server_idr']} {status_plain} \n"
        server_info += f"╚ {bot_info['server_online']} {status.players.online}/{status.players.max}\n\n"
        server_info += f"{motd_plain}\n"

        return server_info, image_filename  # Возвращаем кортеж из server_info и image_filename
    except asyncio.TimeoutError:
        return None, None
    except Exception as e:
        return None, None
        
   

import Levenshtein

def check_forbidden_words(text):

    forbidden_words = set()
    with open('codex.txt', 'r') as file:
        for line in file:
            forbidden_words.add(line.strip().lower())

    lines = text.splitlines()
    filtered_lines = []
    for line in lines:
        words = line.split()
        for i, word in enumerate(words):
            if word.lower() in forbidden_words:
                words[i] = ""
            else:
                for forbidden_word in forbidden_words:
                    if Levenshtein.distance(word.lower(), forbidden_word) == 1:
                        words[i] = ""
                        break

        filtered_lines.append(' '.join(words))
    
    return '\n'.join(filtered_lines)

async def server_check(vk, peer_id, vk_id, message):
    try:
        image_filename = None

        if is_user_banned(vk_id):
            return
        if not is_user_admin(vk_id) and get_bot_settings() == 0:
            return

        cooldown_message = check_command_cooldown(vk_id)
        if cooldown_message:
            vk.messages.send(peer_id=peer_id, message=cooldown_message, random_id=random.randint(1, 10**9))
            return

        lang = lang_settings(vk_id)
        bot_info = load_texts_from_folder("lang", lang)
        parts = message.split()
        if len(parts) != 2:
            vk.messages.send(peer_id=peer_id, message=f"{bot_info['ping_error']}", random_id=random.randint(1, 10**9))
            return

        _, ip_address = parts

        ip_address = get_ip_port_by_alias(ip_address)
        if ip_address == "127.0.0.1":
            ip_address = None

        if ip_address:
            parts = ip_address.split(':')
            ip = parts[0]
            port = int(parts[1]) if len(parts) > 1 else 25565  # Default Minecraft port

            print(ip, port)
            protocol = get_protocol_from_db(ip, port)
            if protocol is None:
                protocol = 47  # Default protocol

            checked_protocols = set()
            stats = None
            for proto_num in [protocol] + list(range(1, 101)):
                if proto_num in checked_protocols:
                    continue
                try:
                    ping = PINGClient(ip, port, proto_num=proto_num)
                    print(f"{protocol} tester")
                    start_time = time.time()
                    response_time = int((time.time() - start_time) * 1000)
                    stats = ping.get_stats()
                    ping.stop()
                    
                    if stats:
                        save_protocol_to_db(ip, port, proto_num)
                        break
                except Exception:
                    pass
                finally:
                    checked_protocols.add(proto_num)
            
            if not stats or not isinstance(stats, dict) or 'description' not in stats or 'players' not in stats or not isinstance(stats['players'], dict):
                vk.messages.send(peer_id=peer_id, message=f"{bot_info['ping_error2']}", random_id=random.randint(1, 10**9))
                return

            server_description = ""
            if isinstance(stats['description'], dict):
                server_description = stats['description'].get('text', 'N/A')
            elif isinstance(stats['description'], str):
                server_description = stats['description']
            else:
                vk.messages.send(peer_id=peer_id, message=f"{bot_info['stats_error5']}", random_id=random.randint(1, 10**9))
                return

            players_online = stats['players'].get('online', 'N/A')
            players_max = stats['players'].get('max', 'N/A')
            version = stats.get('version', {}).get('name', 'N/A')
            icon = stats.get('favicon', None)

            # Process server description to remove ANSI escape sequences
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            processed_description = ansi_escape.sub('', server_description)
            version = check_forbidden_words(version)
            version = remove_color_codes(version)
            processed_description = check_forbidden_words(processed_description)
            server_info = (
                f"{bot_info['info_server']} ({ip_address})\n"
                f"╔ {bot_info['ip_address']} {ip}:{port}\n"
                f"║ {bot_info['server_zaz']} {response_time} ms\n"
                f"║ {bot_info['server_idr']} {version}\n"
                f"╚ {bot_info['server_online']} {players_online}/{players_max}\n\n"
                f"{processed_description}"
            )

            # Prepare photo attachment if available
            attachment = None
            if icon:
                favicon_base64 = icon
                favicon_data = base64.b64decode(favicon_base64.replace('data:image/png;base64,', ''))

                # Create temporary image file
                image_filename = f"server_logo_{random.randint(1, 1000000)}.png"
                with open(image_filename, 'wb') as f:
                    f.write(favicon_data)

                # Upload and save photo to VK
                upload_url = vk.photos.getMessagesUploadServer()['upload_url']
                with open(image_filename, 'rb') as file:
                    response = requests.post(upload_url, files={'photo': file}).json()

                photo = vk.photos.saveMessagesPhoto(**response)[0]
                owner_id = photo['owner_id']
                photo_id = photo['id']
                attachment = f'photo{owner_id}_{photo_id}'

            # Разделение ip_address на IP и порт, если они указаны
            ip_address_parts = ip_address.split(':')
            ip_address = ip_address_parts[0]
            port = int(ip_address_parts[1]) if len(ip_address_parts) > 1 else 25565

            # Кнопка для повторного пинга
            button_payload_ping = json.dumps({"function_name": f"/ping {ip_address}:{port}"})
            button_text_ping = f"{bot_info['ping_pov']}"
            button_ping = {
                "action": {
                    "type": "text",
                    "label": button_text_ping.strip(),  # Удаление пробелов в начале и конце метки кнопки
                    "payload": button_payload_ping
                }
            }

            # Кнопка для запроса статистики сервера
            button_payload_stats = json.dumps({"function_name": f"/stats {ip_address}:{port}"})
            button_text_stats = f"{bot_info['stats_serv']}"
            button_stats = {
                "action": {
                    "type": "text",
                    "label": button_text_stats.strip(),
                    "payload": button_payload_stats
                }
            }

            # Кнопка для запроса информации о IP-адресе
            button_payload_ip = json.dumps({"function_name": f"/ip {ip_address}"})
            button_text_ip = f"{bot_info['info_ips']}"
            button_ip = {
                "action": {
                    "type": "text",
                    "label": button_text_ip.strip(),
                    "payload": button_payload_ip
                }
            }

            # Формирование клавиатуры
            keyboard = {
                "inline": True,
                "buttons": [[button_ping, button_stats], [button_ip]]
            }
            keyboard = json.dumps(keyboard)

            vk.messages.send(peer_id=peer_id, message=server_info, keyboard=keyboard, disable_mentions=1, attachment=attachment, random_id=random.randint(1, 10**9))

        else:
            vk.messages.send(peer_id=peer_id, message=f"{bot_info['stats_error5']}", random_id=random.randint(1, 10**9))

    except asyncio.TimeoutError:
        vk.messages.send(peer_id=peer_id, message="Сервер не вернул обратной связи", random_id=random.randint(1, 10**9))
    except Exception as e:
        if image_filename:
            log_message(f"server_check: Error {e}, image file: {image_filename}")
        else:
            vk.messages.send(peer_id=peer_id, message="Сервер не вернул обратной связи", random_id=random.randint(1, 10**9))
    finally:
        if image_filename and os.path.exists(image_filename):
            os.remove(image_filename)
        elif image_filename:
            log_message(f"server_check: Image file not found ({image_filename})")
      


        
def sanitize_text(text):
    # Удаление символов, добавление пробелов перед @ и * знаками
    sanitized_text = text.replace('@', ' @ ').replace('*', ' * ')

    # Проверка на наличие определенных слов из файла codes.txt и их замена на специальные символы
    with open('codes.txt', 'r') as file:
        for line in file:
            word = line.strip()
            if word in sanitized_text:
                sanitized_text = sanitized_text.replace(word, '*' * len(word))

    # Сокращение текста, если он слишком длинный
    max_length = 1000
    if len(sanitized_text) > max_length:
        sanitized_text = sanitized_text[:max_length] + '...'

    return sanitized_text

def send_message_with_button(vk, peer_id, ip_address, technical_info, vk_id, attachment=None):
    try:
        sanitized_info = sanitize_text(technical_info)
        lang = lang_settings(vk_id)
        bot_info = load_texts_from_folder("lang", lang)
        # Кнопка для повторного пинга
        button_payload_ping = json.dumps({"function_name": f"/ping {ip_address}"})
        button_text_ping = f"{bot_info['ping_pov']}"
        button_ping = {
            "action": {
                "type": "text",
                "label": button_text_ping.strip(),  # Удаление пробелов в начале и конце метки кнопки
                "payload": button_payload_ping
            }
        }

        # Кнопка для запроса статистики сервера
        button_payload_stats = json.dumps({"function_name": f"/stats {ip_address}"})
        button_text_stats = f"{bot_info['stats_serv']}"
        button_stats = {
            "action": {
                "type": "text",
                "label": button_text_stats.strip(),
                "payload": button_payload_stats
            }
        }

        # Кнопка для запроса информации о IP-адресе
        button_payload_ip = json.dumps({"function_name": f"/ip {ip_address}"})
        button_text_ip = f"{bot_info['info_ips']}"
        button_ip = {
            "action": {
                "type": "text",
                "label": button_text_ip.strip(),
                "payload": button_payload_ip
            }
        }

        # Формирование клавиатуры
        keyboard = {
            "inline": True,
            "buttons": [[button_ping, button_stats], [button_ip]]
        }
        keyboard = json.dumps(keyboard)
        
        # Отправка сообщения с кнопкой и, при наличии, изображением
        if attachment:
            upload_url = vk.photos.getMessagesUploadServer()['upload_url']
            with open(attachment, 'rb') as file:
                response = requests.post(upload_url, files={'photo': file}).json()
            
            photo = vk.photos.saveMessagesPhoto(**response)[0]
            owner_id = photo['owner_id']
            photo_id = photo['id']
            
            # Отправка сообщения с изображением и кнопкой
            vk.messages.send(peer_id=peer_id, message=sanitized_info, attachment=f'photo{owner_id}_{photo_id}', keyboard=keyboard, disable_mentions=1, random_id=random.randint(1, 10**9))
            os.remove(attachment)
        else:
            # Отправка сообщения с кнопкой без изображения
            vk.messages.send(peer_id=peer_id, message=sanitized_info, keyboard=keyboard, disable_mentions=1, random_id=random.randint(1, 10**9))
    except Exception as e:
        log_message(f"send_message_with_button: Произошла ошибка {e}")


def toponline_server(vk, peer_id, vk_id):
    if is_user_banned(vk_id):
        return
    if not is_user_admin(vk_id) and get_bot_settings() == 0:
        return
    cooldown_message = check_command_cooldown(vk_id)
    lang = lang_settings(vk_id)
    bot_info = load_texts_from_folder("lang", lang)
    if cooldown_message:
        vk.messages.send(peer_id=peer_id, message=cooldown_message, random_id=random.randint(1, 10**9))
        return

    try:
        # Получаем информацию о серверах и их онлайн игроках из базы данных
        server_info = get_server_ips()

        # Фильтруем данные: игнорируем "No" и значения меньше 0
        filtered_server_info = [(ip, online) for ip, online in server_info if isinstance(online, int) and online >= 0]

        # Используем словарь для уникальности по доменному имени
        unique_servers = {}
        for ip, online in filtered_server_info:
            # Извлекаем доменное имя без поддомена
            domain = ".".join(ip.split(".")[-2:])
            if domain not in unique_servers:
                unique_servers[domain] = (ip, online)

        # Преобразуем обратно в список кортежей
        unique_server_info = list(unique_servers.values())

        # Если информация о серверах не найдена после фильтрации, отправляем сообщение об ошибке
        if not unique_server_info:
            vk.messages.send(peer_id=peer_id, message=f"{bot_info['top_error']}", random_id=random.randint(1, 10**9))
            return

        # Сортируем серверы по количеству онлайн игроков и выбираем топ-10
        top_servers = sorted(unique_server_info, key=lambda x: x[1], reverse=True)[:10]

        # Формируем сообщение с информацией о топ-10 серверах
        message = f"{bot_info['top_10']}\n"
        for rank, (ip, online) in enumerate(top_servers, start=1):
            message += f"{rank}. {ip} - {bot_info['online']} {online} {bot_info['player']}\n"

        # Отправляем сообщение в VK
        vk.messages.send(peer_id=peer_id, message=message, disable_mentions=1, random_id=random.randint(1, 10**9))

    except Exception as e:
        logging.error(f"toponline_server: Произошла ошибка {e}")


        
        
def servers_list(vk, peer_id, vk_id):
    if is_user_banned(vk_id):
       
        return
    if not is_user_admin(vk_id) and get_bot_settings() == 0:
        
        return
        
    cooldown_message = check_command_cooldown(vk_id)
    if cooldown_message:
            vk.messages.send(peer_id=peer_id, message=cooldown_message, random_id=random.randint(1, 10**9))
            return
    
    try:
        # Получение списка серверов пользователя
        user_servers = find_user_servers(vk_id)
        
        # Отправка списка серверов в сообщении VK
        vk.messages.send(peer_id=peer_id, message=user_servers, random_id=random.randint(1, 10**9))
        
    except Exception as e:
        log_message(f"server_list: Произошла ошибка {e}")

def help_bot(vk, peer_id, vk_id):
    try:
        if is_user_banned(vk_id):
           
            return
        if not is_user_admin(vk_id) and get_bot_settings() == 0:
            
            return

        lang = lang_settings(vk_id)
        bot_info = load_texts_from_folder("lang", lang)
        # Формируем сообщение с информацией о боте
        message = f"{bot_info['help_list']}"
        
        vk.messages.send(peer_id=peer_id, message=message, random_id=random.randint(1, 10**9))
        
    except Exception as e:
        log_message(f"help_bot: Произошла ошибка {e}")
        
def test_server(vk, peer_id, vk_id):
    try:
        if is_user_banned(vk_id):
           
            return
        if not is_user_admin(vk_id) and get_bot_settings() == 0:
            
            return
            
        
        message = "Увы, команда не доступна вам."
        
        vk.messages.send(peer_id=peer_id, message=message, random_id=random.randint(1, 10**9))
        
    except Exception as e:
        log_message(f"test_server: Произошла ошибка {e}")
        
        
import asyncio

async def comparison_server(peer_id, message, vk_id, vk):
    try:
        # Проверки на бан, админские права и состояние бота
        if is_user_banned(vk_id):
            await asyncio.to_thread(vk.messages.send, peer_id=peer_id, message="Вы забанены и не можете использовать бота.", random_id=random.randint(1, 10**9))
            return
        if not is_user_admin(vk_id) and get_bot_settings() == 0:
            await asyncio.to_thread(vk.messages.send, peer_id=peer_id, message="Бот отключен администратором.", random_id=random.randint(1, 10**9))
            return
        # Проверка на VIP статус
        if not is_user_vip(vk_id):  # Предполагается, что у вас есть функция is_user_vip(vk_id)
            await asyncio.to_thread(vk.messages.send, peer_id=peer_id, message="Данная команда, доступна только VIP-Статусам.", random_id=random.randint(1, 10**9))
            return
        # Проверка кулдауна
        cooldown_message = check_command_cooldown(vk_id)
        if cooldown_message:
            await asyncio.to_thread(vk.messages.send, peer_id=peer_id, message=cooldown_message, random_id=random.randint(1, 10**9))
            return
        # Разделение сообщения на части
        parts = message.split()
        if len(parts) != 4:
            await asyncio.to_thread(vk.messages.send, peer_id=peer_id, message="Неверный формат команды. Используйте: /comparison (IP1) (IP2) (день, неделя, месяц)", random_id=random.randint(1, 10**9))
            return
        _, ip_address1, ip_address2, period = parts

        # Проверка доступности серверов
        if server_api(ip_address1) or server_api(ip_address2):
            await asyncio.to_thread(vk.messages.send, peer_id=peer_id, message="Один из серверов не вернул обратной связи.", random_id=random.randint(1, 10**9))
            return
        # Получение данных с серверов
        data1, error1 = await asyncio.to_thread(get_data_from_mysql, ip_address1, period)
        data2, error2 = await asyncio.to_thread(get_data_from_mysql, ip_address2, period)

        # Проверка ошибок
        if error1 or error2:
            await asyncio.to_thread(vk.messages.send, peer_id=peer_id, message="Произошла ошибка при получении данных.", random_id=random.randint(1, 10**9))
        else:
            # Создание графиков и отправка в VK
            filename = f'{ip_address1}_{ip_address2}_{period}.png'
            await asyncio.to_thread(comparison_server_graph, data1, data2, filename, ip_address1, ip_address2, period)
            await asyncio.to_thread(send_image_to_vk1, peer_id, filename)
    except Exception as e:
        # Логирование ошибок
        await asyncio.to_thread(log_message, f"comparison_server: Произошла ошибка {e}")

        
def alias_list(vk, peer_id, vk_id):
    if is_user_banned(vk_id):
       
        return
    if not is_user_admin(vk_id) and get_bot_settings() == 0:
        
        return
        
    
    try:
        # Получение списка серверов пользователя
        user_servers = aliases_list()
        
        # Отправка списка серверов в сообщении VK
        vk.messages.send(peer_id=peer_id, message=user_servers, random_id=random.randint(1, 10**9))
        
    except Exception as e:
        log_message(f"alias_list: Произошла ошибка {e}")
        
def add_servers(vk, peer_id, vk_id, message):
    try:
        # Проверка наличия бана пользователя
        if is_user_banned(vk_id):
            return
        
        # Проверка состояния бота
        if not is_user_admin(vk_id) and get_bot_settings() == 0:
            return
        lang = lang_settings(vk_id)
        bot_info = load_texts_from_folder("lang", lang)
        # Проверка времени отката команды

            
        # Разделение сообщения на части
        parts = message.split()
        
        # Проверка корректности формата сообщения
        if len(parts) != 2:
            vk.messages.send(peer_id=peer_id, message=f"{bot_info['add_error']}", random_id=random.randint(1, 10**9))
            return
        
        # Извлечение IP-адреса из сообщения
        _, ip_address = parts
        
        print("ok")
        result_message = add_server(vk_id, ip_address)
        
        # Отправка результата пользователю
        vk.messages.send(peer_id=peer_id, message=result_message, disable_mentions=1, random_id=random.randint(1, 10**9))
        
    except Exception as e:
        print(e)
        logger.error(f"add_servers: Произошла ошибка {e}")
        vk.messages.send(peer_id=peer_id, message=f"{bot_info['add_error2']}.", random_id=random.randint(1, 10**9))

def removes_servers(vk, peer_id, vk_id, message):
    try:
        # Проверка наличия бана пользователя
        if is_user_banned(vk_id):
           
            return
        
        # Проверка состояния бота
        if not is_user_admin(vk_id) and get_bot_settings() == 0:
            
            return
                       
        # Разделение сообщения на части
        parts = message.split()
        lang = lang_settings(vk_id)
        bot_info = load_texts_from_folder("lang", lang)
        # Проверка корректности формата сообщения
        if len(parts) != 2:
            vk.messages.send(peer_id=peer_id, message=f"{bot_info['remove_error']}", random_id=random.randint(1, 10**9))
            return
        
        _, ip_address = parts
              
        # Добавление сервера и получение списка серверов пользователя
        user_servers = remove_server(vk_id, ip_address)
        
        # Отправка списка серверов в сообщении VK
        vk.messages.send(peer_id=peer_id, message=user_servers, disable_mentions=1, random_id=random.randint(1, 10**9))
        
    except Exception as e:
        # Обработка ошибки
        log_message(f"removes_server: Произошла ошибка {e}")
        
def add_alias(vk, peer_id, vk_id, message):
    try:
        # Проверка наличия бана пользователя
        if is_user_banned(vk_id):
           
            return
        
        # Проверка состояния бота
        if not is_user_admin(vk_id) and get_bot_settings() == 0:
            
            return
            
            
        # Разделение сообщения на части
        parts = message.split()
        lang = lang_settings(vk_id)
        bot_info = load_texts_from_folder("lang", lang)
        # Проверка корректности формата сообщения
        if len(parts) != 3:
            vk.messages.send(peer_id=peer_id, message=f"{bot_info['alias_error']}", random_id=random.randint(1, 10**9))
            return
        
        _, ip_address, alias = parts
              
        # Добавление сервера и получение списка серверов пользователя
        user_servers = set_server_alias(ip_address, alias, vk_id)
        
        # Отправка списка серверов в сообщении VK
        vk.messages.send(peer_id=peer_id, message=user_servers, disable_mentions=1, random_id=random.randint(1, 10**9))
        
    except Exception as e:
        log_message(f"add_alias: Произошла ошибка {e}")

# Настройка логирования
logging.basicConfig(filename='whois.log', level=logging.ERROR, format='%(asctime)s - %(message)s')

def clean_status(status):
    return ', '.join(status)


def format_date(date):
    if isinstance(date, list):
        return ', '.join(d.strftime('%Y-%m-%d %H:%M') for d in date)
    elif isinstance(date, datetime):
        return date.strftime('%Y-%m-%d %H:%M')
    else:
        return 'Неизвестно'

def parse_whois_info(domain_info):
    try:
        response_message = "Информация предоставлена с Reg.ru\nИнформация о домене:\n"
        response_message += f"Домен {domain_info.get('domain_name', 'Неизвестно')}\n"
        response_message += f"╔ Регистратор: {domain_info.get('registrar', 'Неизвестно')}\n"
        
        # Статус
        if 'status' in domain_info:
            status_lines = []
            for status in domain_info['status']:
                # Удаляем ссылки на icann.org
                cleaned_status = re.sub(r'https://icann.org/[^ ]+', '', status)
                status_lines.append(cleaned_status.strip())
            
            status = ''.join(status_lines).replace(', ,', ',')
            response_message += f"║ Статус: {status}\n"
        
        # DNS серверы
        if 'name_servers' in domain_info:
            dns_servers = ''.join(domain_info['name_servers']).replace(', ,', ',')
            response_message += f"DNS серверы:\n{dns_servers}\n"
        
        # Остальная информация (дата создания, дата истечения регистрации и т.д.)
        response_message += f"Дата создания: {format_date(domain_info['creation_date'])}\n"
        response_message += f"Дата истечения регистрации: {format_date(domain_info['expiration_date'])}\n"
        
        # Преимущественное продление
        if 'priority_renewal_date' in domain_info:
            response_message += f"Преимущественное продление до: {format_date(domain_info['priority_renewal_date'])}\n"
        
        # Удаление строк с "Неизвестно"
        response_message = "\n".join(line for line in response_message.split('\n') if 'Неизвестно' not in line)
        
        return response_message.strip()
    except Exception as e:
        logging.error(f"Ошибка при формировании сообщения WHOIS: {str(e)}")
        return f"Ошибка при формировании сообщения WHOIS: {str(e)}"






def parse_pdf(pdf_path):
    try:
        document = fitz.open(pdf_path)
        text = ""
        for page_num in range(len(document)):
            text += document.load_page(page_num).get_text("text")
        return text
    except Exception as e:
        logging.error(f"Ошибка при чтении PDF файла: {str(e)}")
        return None

def extract_info_from_pdf(pdf_text):
    try:
        lines = pdf_text.split('\n')
        info = {}
        for line in lines:
            if line.startswith("Домен:"):
                info['domain_name'] = line.split(": ")[1]
            elif line.startswith("Сервер DNS:"):
                info['name_servers'] = line.split(": ")[1]
            elif line.startswith("Соcтояние:"):
                info['status'] = line.split(": ")[1]
            elif line.startswith("Администратор домена:"):
                info['admin'] = line.split(": ")[1]
            elif line.startswith("ИНН:"):
                info['inn'] = line.split(": ")[1]
            elif line.startswith("Регистратор:"):
                info['registrar'] = line.split(": ")[1]
            elif line.startswith("Дата регистрации:"):
                info['creation_date'] = line.split(": ")[1]
            elif line.startswith("Дата окончания регистрации:"):
                info['expiration_date'] = line.split(": ")[1]
            elif line.startswith("Преимущественное продление до:"):
                info['priority_renewal_date'] = line.split(": ")[1]
        return info
    except Exception as e:
        logging.error(f"Ошибка при извлечении информации из PDF: {str(e)}")
        return None

def whois_domain(peer_id, message, vk_id, vk):
    try:
        parts = message.split()
        if len(parts) != 2:
            vk.messages.send(peer_id=peer_id, message="Ошибка: Неверный формат команды.", random_id=random.randint(1, 10**9))
            return

        domain = parts[1].strip().lower()

        try:
            domain_info = whois.whois(domain)
        except Exception as e:
            domain_info = None
            logging.error(f"Ошибка при получении информации о домене через whois: {str(e)}")

        if domain_info:
            response_message = parse_whois_info(domain_info)
        else:
            # Скачивание PDF файла с информацией о домене
            pdf_url = f"https://www.reg.ru/whois/?dname={domain}&pdf=1"
            pdf_response = requests.get(pdf_url)
            pdf_path = f"{domain}.pdf"
            with open(pdf_path, 'wb') as f:
                f.write(pdf_response.content)

            # Извлечение текста из PDF
            pdf_text = parse_pdf(pdf_path)
            if pdf_text:
                pdf_info = extract_info_from_pdf(pdf_text)
                if pdf_info:
                    response_message = parse_whois_info(pdf_info)
                else:
                    response_message = f"Не удалось получить информацию о домене {domain}."
            else:
                response_message = f"Не удалось получить информацию о домене {domain}."

        vk.messages.send(peer_id=peer_id, message=response_message, disable_mentions=1, random_id=random.randint(1, 10**9))

    except Exception as e:
        vk.messages.send(peer_id=peer_id, message=f"Ошибка при выполнении команды: {str(e)}", disable_mentions=1, random_id=random.randint(1, 10**9))
        logging.error(f"Ошибка при выполнении whois_domain для домена {domain}: {str(e)}")
        # Функция handle_stat_command
def lang_command(peer_id, message, vk_id, vk):
    try:
        # Проверка наличия доступа к функционалу
        if is_user_banned(vk_id):
            return
        if not is_user_admin(vk_id) and get_bot_settings() == 0:
            return
            
            
        lang = lang_settings(vk_id)
        bot_info = load_texts_from_folder("lang", lang)
            
        button_ned = json.dumps({"function_name": f"/lang ru "})
        button_nedel = f"{bot_info['Russia']}"
        button_stats = {
            "action": {
                "type": "text",
                "label": button_nedel.strip(),
                "payload": button_ned
            }
        }

        button_mec = json.dumps({"function_name": f"/lang en"})
        button_mecec = f"{bot_info['English']}"
        button_ip = {
            "action": {
                "type": "text",
                "label": button_mecec.strip(),
                "payload": button_mec
            }
        }

        keyboard = {
            "inline": True,
            "buttons": [[button_stats, button_ip]]
        }
        keyboard = json.dumps(keyboard, ensure_ascii=False).encode('utf-8')

        parts = message.split()
        
        # Проверка корректности формата сообщения
        if len(parts) != 2:
            vk.messages.send(peer_id=peer_id, message=f"{bot_info['lang_knop']}", keyboard=keyboard, random_id=random.randint(1, 10**9))
            return

        # Проверка выбранного языка
        if parts[1] == "ru":
            russia = update_language_in_database(vk_id, "ru")
            vk.messages.send(peer_id=peer_id, message=russia, random_id=random.randint(1, 10**9))
        elif parts[1] == "en":
            english = update_language_in_database(vk_id, "en")
            vk.messages.send(peer_id=peer_id, message=english, random_id=random.randint(1, 10**9))
        else:
            # Если выбран неверный язык, отправить сообщение об ошибке
            vk.messages.send(peer_id=peer_id, message=f"{bot_info['lang_knop']}", keyboard=keyboard, random_id=random.randint(1, 10**9))
        
    except Exception as e:
        log_message(f"lang_command: Произошла ошибка {str(e)}")

    
def ip_info(ip_address):
    try:
        # Подставьте ваш URL API и токен вместо placeholder'ов
        url = f"https://rionx.ru/api/check.php?token=gRgqoWceP8hu&ip={ip_address}"
        
        # Отправляем GET-запрос к API
        response = requests.get(url)
        
        # Проверяем успешность запроса
        if response.status_code == 200:
            # Пытаемся разобрать JSON-ответ
            try:
                ip_data = json.loads(response.text)
                return ip_data
            except json.decoder.JSONDecodeError:
                # Если не удалось разобрать JSON-ответ, предполагаем, что это нестандартный формат
                return {"error": f"Ошибка при запросе WHOIS для IP-адреса {ip_address}: Не удалось разобрать JSON-ответ"}
        else:
            return {"error": f"Ошибка {response.status_code} при запросе WHOIS для IP-адреса {ip_address}"}
    except Exception as e:
        return {"error": f"Ошибка при запросе WHOIS для IP-адреса {ip_address}: {e}"}
   
def ip_check(peer_id, message, vk_id, vk):
    try:
        if is_user_banned(vk_id):
           
            return
        if not is_user_admin(vk_id) and get_bot_settings() == 0:
            
            return
            
        cooldown_message = check_command_cooldown(vk_id)
        if cooldown_message:
            vk.messages.send(peer_id=peer_id, message=cooldown_message, random_id=random.randint(1, 10**9))
            return
        parts = message.split()
        lang = lang_settings(vk_id)
        bot_info = load_texts_from_folder("lang", lang)
        if len(parts) != 2:
            vk.messages.send(peer_id=peer_id, message=f"{bot_info['check_error']}", random_id=random.randint(1, 10**9))
            return
        
        ip_address = parts[1]

        # Проверяем, является ли введенный адрес доменным и преобразуем его в IP-адрес, если это так
        try:
            ip_address = socket.gethostbyname(ip_address)
        except socket.gaierror:
            vk.messages.send(peer_id=peer_id, message=f"{bot_info['error']} {ip_address} {bot_info['check_error2']}", random_id=random.randint(1, 10**9))
            return
        
        try:
            ip_data = ip_info(ip_address)
            if "error" in ip_data:
                vk.messages.send(peer_id=peer_id, message=f"{bot_info['check_error3']} '{ip_data['error']}'", random_id=random.randint(1, 10**9))
            else:
                # Формирование сообщения на основе полученных данных
                response_message = f"{bot_info['ip_address']} {ip_address}\n"
                
                if 'inetnum' in ip_data:
                    response_message += f"╔ {bot_info['podset']} {ip_data['inetnum']}\n"
                if 'netname' in ip_data:
                    response_message += f"║ {bot_info['name']} {ip_data['netname']}\n"
                if 'country' in ip_data and 'descr' in ip_data:
                    response_message += f"║ {bot_info['strana']} {ip_data['country']} ({ip_data['descr']})\n"
                if 'status' in ip_data:
                    response_message += f"║ {bot_info['status']} {ip_data['status']}\n"
                if 'created' in ip_data:
                    response_message += f"║ {bot_info['sos']} {ip_data['created']}\n"
                if 'address' in ip_data:
                    response_message += f"║ {bot_info['address']} {ip_data['address']}\n"
                if 'person' in ip_data:
                    persons = ip_data['person'] if isinstance(ip_data['person'], list) else [ip_data['person']]
                    response_message += f"╚ {bot_info['vladeles']}"
                    for person in persons:
                        response_message += f"- {person}\n"

                if response_message.strip():  # Проверяем, содержит ли строка какие-либо символы, кроме пробелов
                    vk.messages.send(peer_id=peer_id, message=response_message, disable_mentions=1, random_id=random.randint(1, 10**9))
                else:
                    vk.messages.send(peer_id=peer_id, message=f"{bot_info['checkip_error']}", disable_mentions=1, random_id=random.randint(1, 10**9))
        except Exception as e:
            vk.messages.send(peer_id=peer_id, message=f"{bot_info['checkip_error2']} '{ip_address}'", disable_mentions=1, random_id=random.randint(1, 10**9))
            
    except Exception as e:
        log_message(f"ip_check: Произошла ошибка {str(e)}")
        

def delete_bot_on_new_message(vk, event):
    try:
        # Проверяем, присутствует ли ключ 'message' в объекте события
        if 'message' in event.obj:
            # Получаем ID сообщения
            message_id = event.obj.id
            
            # Проверяем, присутствует ли ключ 'from_id' в объекте сообщения
            if 'from_id' in event.obj.message:
                # Получаем ID пользователя
                user_id = event.obj.message['from_id']

                # Проверяем, является ли отправитель сообщения одним из запрещенных
                if user_id in [-223305896, -204239130]:
                    # Проверяем, отправлено ли сообщение ботом
                    if event.obj.message['from_id'] == -VK_GROUP_ID:
                        # Удаляем сообщение
                        vk.messages.delete(message_ids=message_id)
                        print(f"Успешно удалено сообщение от бота для пользователя с ID {user_id}")
                    else:
                        print("Сообщение не было отправлено ботом.")
                else:
                    print("Указанный ID пользователя не требует удаления сообщений от бота. ", user_id)
            else:
                print("Ключ 'from_id' отсутствует в объекте сообщения.")
        else:
            print("Ключ 'message' отсутствует в объекте события.")

    except Exception as e:
        print(f"delete_bot_on_new_message: Произошла ошибка {str(e)}")

def send_vk_message(vk, peer_id, message):
    vk.messages.send(peer_id=peer_id, message=message, random_id=random.randint(1, 10**9))

SPECIAL_IP_ADDRESSES = {"127.0.0.1", "0.0.0.0"}  # Добавьте сюда любые IP-адреса, которые должны обрабатываться особым образом
def handle_port_command(peer_id, message, vk_id, vk):
    try:
        parts = message.split()
        if len(parts) < 2:
            send_vk_message(vk, peer_id, "Ошибка: необходимо указать IP-адрес.")
            return
            
        if is_user_banned(vk_id):
           
            return
        if not is_user_admin(vk_id) and get_bot_settings() == 0:
            
            return   

        ip_port = parts[1]
        
        if len(parts) > 2 and parts[2].isdigit():
            port = int(parts[2])
            if not (0 <= port <= 65535):
                send_vk_message(vk, peer_id, "Ошибка: порт должен быть в диапазоне от 0 до 65535.")
                return
        else:
            port = 25565

        try:
            ip_address = socket.gethostbyname(ip_port)
        except socket.gaierror:
            send_vk_message(vk, peer_id, "Ошибка: некорректный IP-адрес или домен.")
            return

        vip, checkport_count, is_admin = get_user_status(vk_id)

        if not is_admin:
            port_check_count = get_port_check_count(ip_address)
            if port_check_count >= 15:
                last_15_checks = get_last_15_port_checks(ip_address)
                open_ports = [str(port) for port, ok in last_15_checks if ok == 1]
                closed_ports = [str(port) for port, ok in last_15_checks if ok == 0]

                status_message = "Данный айпи-адрес уже проверяли много раз, попробуйте через час вновь.\n"
                status_message += "Открытые порты: " + ", ".join(open_ports) + "\n"
                status_message += "Закрытые порты: " + ", ".join(closed_ports)

                send_vk_message(vk, peer_id, status_message)
                return

            if not vip and checkport_count >= 5:
                send_vk_message(vk, peer_id, "Увы, у вас исчерпан лимит (увеличить лимит можно преобрести vip).")
                return

        execution_thread = threading.Thread(target=execute_port_check, args=(ip_address, port, peer_id, vk, vk_id))
        execution_thread.start()

        execution_thread.join(MAX_EXECUTION_TIME)
        if execution_thread.is_alive():
            raise TimeoutError("Превышено максимальное время выполнения")

    except Exception as e:
        log_message(f"handle_port_command: Произошла ошибка {str(e)}")

def execute_port_check(ip_address, port, peer_id, vk, vk_id):
    try:
        if ip_address in SPECIAL_IP_ADDRESSES:
            status_message = f"&#10060; Порт {port} на IP-адресе {ip_address} закрыт."
            add_port_check(ip_address, port, vk_id, 0)
            send_vk_message(vk, peer_id, status_message)
            return

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((ip_address, port))
        sock.close()

        if result == 0:
            add_port_check(ip_address, port, vk_id, 1)
            status_message = f"&#9989; Порт {port} на IP-адресе {ip_address} открыт."
        else:
            add_port_check(ip_address, port, vk_id, 0)
            status_message = f"&#10060; Порт {port} на IP-адресе {ip_address} закрыт."

        send_vk_message(vk, peer_id, status_message)
        increment_user_checkport(vk_id)
    except Exception as e:
        log_message(f"execute_port_check: Произошла ошибка {str(e)}")
        send_vk_message(vk, peer_id, "Произошла ошибка при проверке порта.")
        
def close_servers(vk, peer_id, vk_id, message):
    try:
        # Проверка наличия бана пользователя
        if is_user_banned(vk_id):
            return
        
        # Проверка состояния бота
        if not is_user_admin(vk_id) and get_bot_settings() == 0:
            return
        lang = lang_settings(vk_id)
        bot_info = load_texts_from_folder("lang", lang)
        # Проверка времени отката команды

            
        # Разделение сообщения на части
        parts = message.split()
        
        # Проверка корректности формата сообщения
        if len(parts) != 2:
            vk.messages.send(peer_id=peer_id, message=f"{bot_info['close_error']}", random_id=random.randint(1, 10**9))
            return
        
        # Извлечение IP-адреса из сообщения
        _, ip_address = parts
        
        print("ok")
        ip_address = get_ip_port_by_alias(ip_address)
        result_message = close_server(vk_id, ip_address)
        
        # Отправка результата пользователю
        vk.messages.send(peer_id=peer_id, message=result_message, disable_mentions=1, random_id=random.randint(1, 10**9))
        
    except Exception as e:
        print(e)
        logger.error(f"add_servers: Произошла ошибка {e}")
        vk.messages.send(peer_id=peer_id, message=f"{bot_info['close_error2']}.", random_id=random.randint(1, 10**9))        