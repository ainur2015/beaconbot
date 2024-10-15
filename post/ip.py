import mysql.connector
import socket
from concurrent.futures import ThreadPoolExecutor

# Подключаемся к базе данных
def connect_to_db():
    return mysql.connector.connect(
        host='localhost',
        user='логин',
        password='пасс',
        database='база'
    )

# Получаем данные из таблицы servers
def get_servers_data(cursor):
    query = "SELECT id, ip_address FROM server"
    cursor.execute(query)
    return cursor.fetchall()

# Функция для преобразования домена в IP-адрес
def resolve_ip(server):
    id, ip_or_domain = server
    try:
        ip = socket.gethostbyname(ip_or_domain)
    except socket.gaierror:
        ip = None
    return id, ip_or_domain, ip

# Основная логика поиска дубликатов
def find_duplicates(servers):
    ip_map = {}
    duplicates = []
    for server in servers:
        id, ip_or_domain, ip = server
        if ip:
            if ip in ip_map:
                duplicates.append((ip_or_domain, ip, ip_map[ip]))
            else:
                ip_map[ip] = ip_or_domain
    return duplicates

# Основная функция
def main():
    db_connection = connect_to_db()
    cursor = db_connection.cursor()
    
    servers = get_servers_data(cursor)
    
    with ThreadPoolExecutor() as executor:
        resolved_servers = list(executor.map(resolve_ip, servers))
    
    duplicates = find_duplicates(resolved_servers)
    
    for duplicate in duplicates:
        print(f"Сервер (домен) {duplicate[0]} с айпи адресом {duplicate[1]} дубликат с сервером (домен) {duplicate[2]}")
    
    cursor.close()
    db_connection.close()

if __name__ == "__main__":
    main()
