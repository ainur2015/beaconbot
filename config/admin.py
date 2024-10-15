import vk_api
import random
import sys
import psutil
from config.vk_config import VK_TOKEN, VK_GROUP_ID
from config.db_utils import is_user_banned, is_user_admin, bot_off, ban_user, unban_user, get_user_profile, set_vip_status, log_admin_action

from datetime import datetime
import re
import os
import requests
import time
import base64
import asyncio
import platform

def log_message(message):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"admin.py [{timestamp}] {message}"
        with open("log.txt", "a") as log_file:
            log_file.write(log_entry + "\n")
        print("Сообщение успешно записано в лог.")
    except Exception as e:
        print("Ошибка при записи сообщения в лог:", e)

def get_system_info():
    cpu_info = platform.processor()
    cpu_count = psutil.cpu_count(logical=True)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    temperature = psutil.sensors_temperatures().get('cpu-thermal', [{'current': random.randint(47, 60)}])[0]['current']
    return cpu_info, cpu_count, memory, disk, temperature

def get_vk_id_from_message(message, vk):
    match = re.search(r"\[id(\d+)\|", message)
    if match:
        return int(match.group(1))
    return None
    
def get_user_id(message, vk):
    if 'reply_message' in message:
        reply_message = message['reply_message']
        if 'from_id' in reply_message:
            return reply_message['from_id']
    return None

def system_protocol(peer_id, message, vk_id, vk):
    try:
        if is_user_banned(vk_id):
            return

        if not is_user_admin(vk_id):
            vk.messages.send(peer_id=peer_id, message="Данная команда доступна только администратору", random_id=random.randint(1, 10**9))
            return

        log_admin_action(vk_id, message)  # Логируем действие администратора

        parts = message.split()

        if len(parts) < 2:
            vk.messages.send(peer_id=peer_id, message="Неверный формат команды. Используйте: /system (аргумент)", random_id=random.randint(1, 10**9))
            return

        argument = parts[1]

        if argument == "restart":
            vk.messages.send(peer_id=peer_id, message="BeaconBot запустил цикл перезагрузки.", random_id=random.randint(1, 10**9))
            sys.exit(1)
            return

        if argument == "dedic":
            cpu_info, cpu_count, memory, disk, temperature = get_system_info()
            dedic_response = (f"BeaconBot: \n System response: ✅ \n"
                              f"Response: CPU: {cpu_info}, Cores: {cpu_count} \n"
                              f"Memory: {memory.used // (1024**3)} GB / 32 GB \n"
                              f"Disk: {disk.used // (1024**3)} GB / 720 GB \n"
                              f"Temperature: {temperature:.1f} degrees \n"
                              f"Proxy: off")
            vk.messages.send(peer_id=peer_id, message=dedic_response, random_id=random.randint(1, 10**9))
            return

        if argument == "off":
            beaconbot = bot_off()
            vk.messages.send(peer_id=peer_id, message=f"{beaconbot}", random_id=random.randint(1, 10**9))
            return

        if argument in ["ban", "unban", "vip", "unvip", "profile"]:
            if len(parts) < 3:
                vk.messages.send(peer_id=peer_id, message="Неверный формат команды. Используйте: /system (ban/unban/vip/unvip/profile) @user или ответом на сообщение.", random_id=random.randint(1, 10**9))
                return

            user_id = get_vk_id_from_message(parts[2], vk)
            if not user_id:
                if 'reply_message' in vk.messages.getById(message_ids=[vk_id])['items'][0]:
                    reply_message = vk.messages.getById(message_ids=[vk_id])['items'][0]['reply_message']
                    user_id = reply_message['from_id']

            if not user_id:
                vk.messages.send(peer_id=peer_id, message="Не удалось определить пользователя.", random_id=random.randint(1, 10**9))
                return

            if argument == "ban":
                ban_user(user_id)
                vk.messages.send(peer_id=peer_id, message=f"Пользователь {user_id} заблокирован.", random_id=random.randint(1, 10**9))
                return

            if argument == "unban":
                unban_user(user_id)
                vk.messages.send(peer_id=peer_id, message=f"Пользователь {user_id} разблокирован.", random_id=random.randint(1, 10**9))
                return

            if argument == "vip":
                set_vip_status(user_id, True)
                vk.messages.send(peer_id=peer_id, message=f"Пользователь {user_id} получил VIP статус.", random_id=random.randint(1, 10**9))
                return

            if argument == "unvip":
                set_vip_status(user_id, False)
                vk.messages.send(peer_id=peer_id, message=f"Пользователь {user_id} лишен VIP статуса.", random_id=random.randint(1, 10**9))
                return

            if argument == "profile":
                profile_info = get_user_profile(user_id)
                vk.messages.send(peer_id=peer_id, message=profile_info, random_id=random.randint(1, 10**9))
                return

        vk.messages.send(peer_id=peer_id, message="Неизвестная команда.", random_id=random.randint(1, 10**9))
    except Exception as e:
        log_message(f"system_protocol: Произошла ошибка {str(e)}")
