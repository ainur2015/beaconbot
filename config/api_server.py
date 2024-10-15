import vk_api
import random
from config.vk_config import VK_TOKEN, VK_GROUP_ID
from config.db_utils import *
import re
import os
import requests
import time
import base64
import socket
from config.message_utils import log_message, load_texts_from_folder, get_text_by_language_from_folder
import dns.resolver
import dns.reversename


vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

def get_ptr_record(ip_address):
    if ip_address == "Айпи для шуточного скрытия вашего айпи":
        return "ptr.vk.com"
    
    try:
        reverse_name = dns.reversename.from_address(ip_address)
        ptr_records = dns.resolver.resolve(reverse_name, "PTR")
        return str(ptr_records[0])
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.exception.Timeout, dns.resolver.NoNameservers):
        return "Unknown"

def ip_api(vk, peer_id, vk_id, message):
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
        parts = message.split()
        if len(parts) != 2:
            vk.messages.send(peer_id=peer_id, message=f"{bot_info['ip_error']}", random_id=random.randint(1, 10**9))
            return

        _, ip_address = parts
        
        domens = ip_address

        # Проверяем, является ли ip_address доменным именем
        try:
            ip = socket.gethostbyname(ip_address)
            ip_address = ip
        except socket.gaierror:
            pass

        result = requests.get(f"https://rionx.ru/api/ips.php?ip={ip_address}&token=gRgqoWceP8hu")
        if not result.ok:
            vk.messages.send(peer_id=peer_id, message=f"{bot_info['ip_no']}", random_id=random.randint(1, 10**9))
            return

        ip_info = result.json()
        print(f"{ip_address}")
        if ip_info.get('success', False) == False:
            vk.messages.send(peer_id=peer_id, message=f"{bot_info['ip_no']}", random_id=random.randint(1, 10**9))
            return

        response_text = f"{bot_info['ip_domen']} {domens}:\n\n"
        response_text += f"— IP: {ip_info.get('ip', 'Unknown')}\n"
        response_text += f"— {bot_info['ip_loc']} {ip_info.get('country_code', 'Unknown')}, {ip_info.get('country', 'Unknown')}, {ip_info.get('city', 'Unknown')}\n"
        
        if 'connection' in ip_info:
            response_text += f"— ASName: {ip_info['connection'].get('asn', 'Unknown')} {ip_info['connection'].get('isp', 'Unknown')}\n"
            response_text += f"— {bot_info['ip_prov']} (ISP): {ip_info['connection'].get('isp', 'Unknown')}\n"
            response_text += f"— {bot_info['ip_org']} {ip_info['connection'].get('org', 'Unknown')}\n"
        else:
            response_text += f"— ASName: Unknown\n— {bot_info['ip_prov']} (ISP): Unknown\n— {bot_info['ip_org']} Unknown\n"

        # Добавляем PTR запись
        ptr_record = get_ptr_record(ip_address)
        if ptr_record != "Unknown":
            response_text += f"— PTR {ptr_record}\n"
        else:
            response_text += ""

        print(response_text)

        lat = ip_info.get('latitude', 'Unknown')
        lon = ip_info.get('longitude', 'Unknown')
        
        message_with_coordinates = f"{response_text}\n"
        
        vk.messages.send(peer_id=peer_id, message=message_with_coordinates, random_id=random.randint(1, 10**9), lat=str(lat), long=str(lon))
        
        return response_text
    except Exception as e:
        log_message(f"API:ip_api: Ошибка {e}")