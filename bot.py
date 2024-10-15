import vk_api 
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll
import random 
import json 
import asyncio 
import threading
import sys
from datetime import datetime


from config.vk_config import VK_TOKEN, VK_GROUP_ID
from config.message_utils import (
    handle_stat_command,
    bot_stat_command,
    toponline_server,
    servers_list,
    test_server,
    help_bot,
    comparison_server,
    alias_list,
    add_servers,
    removes_servers,
    add_alias,
    log_message,
    whois_domain,
    lang_command,
    ip_check,
    delete_bot_on_new_message,
    server_check,
    test_command,
    handle_port_command,
    close_servers,
)
from config.api_server import ip_api
from config.admin import system_protocol
from config.db_utils import is_user_banned, is_user_admin, get_bot_settings, create_user_if_not_exists, close_mysql_connection, open_mysql_connection, increment_clicks

def log_message1(message):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"

        with open("log1.txt", "a") as log_file:
            log_file.write(log_entry + "\n")
    except Exception as e:
        print("Ошибка при записи сообщения в лог:", e)

async def handle_event(vk, event):
    peer_id = event.obj.message['peer_id']
    message = event.obj.message['text']
    vk_id = event.obj.message['from_id']

    create_user_if_not_exists(vk_id)

    if message.startswith('/comparison') or message.startswith('/сравнить'): 
        await comparison_server(peer_id, message, vk_id, vk)

    elif message.startswith('/ping') or message.startswith('/пинг'): 
        increment_clicks(vk_id)
        await server_check(vk, peer_id, vk_id, message) 

    elif message.startswith('/ip') or message.startswith('/ип'): 
        ip_api(vk, peer_id, vk_id, message) 

    elif message.startswith('/bot') or message.startswith('/бот') or message.startswith('!бот'): 
        bot_stat_command(peer_id, vk_id, vk) 

    elif message.startswith('/help') or message.startswith('/помощь') or message.startswith('/хелп') or message.startswith('/команды'): 
        help_bot(vk, peer_id, vk_id) 

    elif message.startswith('/toponline') or message.startswith('/топсерверов'): 
        toponline_server(vk, peer_id, vk_id) 

    elif message.startswith('/servers') or message.startswith('/сервера'): 
        await servers_list(vk, peer_id, vk_id) 

    elif message.startswith('/aliases') or message.startswith('/Алиасес') or message.startswith('/Алиасы') or message.startswith('/алиасы'): 
        await alias_list(vk, peer_id, vk_id) 

    elif message.startswith('/add') or message.startswith('/добавить') or message.startswith('/mcadd'):
        add_servers(vk, peer_id, vk_id, message) 

    elif message.startswith('/removeserver') or message.startswith('/удалитьсервер'):
        await removes_servers(vk, peer_id, vk_id, message) 

    elif message.startswith('/alias') or message.startswith('/алиас'): 
        await add_alias(vk, peer_id, vk_id, message) 

    elif message.startswith('/graph') or message.startswith('/график'): #не готовая
        await test_server(vk, peer_id, vk_id) 

    elif message.startswith('/lang') or message.startswith('/язык'): #не готовая
        lang_command(peer_id, message, vk_id, vk)

    elif message.startswith('/зайти') or message.startswith('/connect'): #не готовая
        await test_server(vk, peer_id, vk_id) 

    elif message.startswith('/system') or message.startswith('/система'): 
        await system_protocol(peer_id, message, vk_id, vk)

    elif message.startswith('/domen') or message.startswith('/домен'): 
        whois_domain(peer_id, message, vk_id, vk)

    elif message.startswith('/checkip') or message.startswith('/чекип'): 
        await ip_check(peer_id, message, vk_id, vk)
        
    elif message.startswith('/mine') or message.startswith('/майн'): 
        await server_check(vk, peer_id, vk_id, message)
        
    elif message.startswith('/test') or message.startswith('/тест'): 
        await test_command(vk, peer_id, vk_id, message)
        
    elif message.startswith('/profile') or message.startswith('/профиль'): 
        await test_command(vk, peer_id, vk_id, message)

    elif message.startswith('/stats') or message.startswith('/стата') or message.startswith('/статистика') or message.startswith('!стата'): 
        handle_stat_command(peer_id, message, vk_id, vk)
        
    elif message.startswith('/port') or message.startswith('/порт'): 
        handle_port_command(peer_id, message, vk_id, vk)
        
    elif message.startswith('/закрыть') or message.startswith('/close') or message.startswith('/закрытьсервер'):
        close_servers(vk, peer_id, vk_id, message) 
    elif message.startswith('/открыть') or message.startswith('/open') or message.startswith('/открытьсервер'):
        close_servers(vk, peer_id, vk_id, message)     
        
    elif event.type == VkBotEventType.MESSAGE_EVENT:
        await handle_button_click(event, vk)

    if "@beacon_bot" in message:  # Проверяем, что бот упоминается в сообщении
        if "Повторный пинг" in message or "Repeated ping" in message: 
            payload_data = json.loads(event.obj.message['payload'])
            ip_address = payload_data.get("function_name", "")
            await process_server_request_and_send_vk(vk, peer_id, vk_id, ip_address)  

        elif "Статистика сервера" in message or "Server statistics" in message:
            payload_data = json.loads(event.obj.message['payload'])
            ip_address = payload_data.get("function_name", "")
            await handle_stat_command(peer_id, ip_address, vk_id, vk) 

        elif "Информация о IP-Адресе" in message or "Information about the IP Address" in message:
            payload_data = json.loads(event.obj.message['payload'])
            ip_address = payload_data.get("function_name", "")
            await ip_api(vk, peer_id, vk_id, ip_address) 

        elif "день" in message or "неделя" in message or "месяц" in message or "day" in message or "week" in message or "month" in message:
            payload_data = json.loads(event.obj.message['payload'])
            ip_address = payload_data.get("function_name", "")
            handle_stat_command(peer_id, ip_address, vk_id, vk) 

        elif "Добавить" in message or "Add" in message:
            payload_data = json.loads(event.obj.message['payload'])
            ip_address = payload_data.get("function_name", "")
            add_servers(vk, peer_id, vk_id, ip_address) 
            
        elif "Английский" in message or "Русский" in message or "English" in message or "Russia" in message:  
            payload_data = json.loads(event.obj.message['payload'])
            ip_address = payload_data.get("function_name", "")
            lang_command(peer_id, ip_address, vk_id, vk)


async def handle_longpoll_events(vk_session, vk, longpoll): 
    db_connection = open_mysql_connection() 

    try: 
        while True: 
            try: 
                for event in longpoll.listen(): 
                    event_json = json.dumps(event.raw, indent=4, ensure_ascii=False) 

                    if event.type == VkBotEventType.MESSAGE_NEW or event.type == VkBotEventType.MESSAGE_EVENT:
                        threading.Thread(target=asyncio.run, args=(handle_event(vk, event),)).start()
            except Exception as e: 
                log_message1(f"Ошибка LongPull {e}")
                close_mysql_connection(db_connection)  
                db_connection = open_mysql_connection()  
    finally: 
        close_mysql_connection(db_connection) 

async def main(): 
    vk_session = vk_api.VkApi(token=VK_TOKEN) 
    vk = vk_session.get_api() 
    longpoll = VkBotLongPoll(vk_session, VK_GROUP_ID) 

    while True: 
        try: 
            await handle_longpoll_events(vk_session, vk, longpoll) 
        except Exception as e: 
            log_message(f"Ошибка Main {e}")
            sys.exit(1)
   



def run_asyncio_task(asyncio_task):
    asyncio.run(asyncio_task)

if __name__ == "__main__":
    threading.Thread(target=run_asyncio_task, args=(main(),)).start()
