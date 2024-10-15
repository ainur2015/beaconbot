import mysql.connector
import time
from datetime import datetime, timedelta

def connect_db():
    """Подключение к базе данных MySQL"""
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='логин',
            password='пасс',
            database='база'
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        raise

def get_server_data(conn):
    """Получить данные серверов из таблицы server"""
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT id, ip_address, port, ok FROM server')
    return cursor.fetchall()

def get_lister_data(conn, ip_address, port):
    """Получить данные о времени и онлайн состоянии из таблицы lister"""
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT times, online FROM lister
        WHERE server = %s AND port = %s
    ''', (ip_address, port))
    results = cursor.fetchall()
    print(f"Полученные данные lister для {ip_address}:{port}: {results}")  # Отладочный вывод
    return results

def parse_float(value):
    """Преобразовать значение в float, если это возможно"""
    try:
        return float(value)
    except (ValueError, TypeError) as e:
        print(f"Не удалось преобразовать значение '{value}' в float. Ошибка: {e}")
        return None

def calculate_online_stats(data):
    """Вычислить статистику по онлайн состоянию"""
    now = time.time()
    day_start = now - 86400  # 24 * 60 * 60
    week_start = now - 604800  # 7 * 24 * 60 * 60
    month_start = now - 2592000  # 30 * 24 * 60 * 60

    day_online = []
    week_online = []
    month_online = []
    all_time_online = []

    for entry in data:
        times, online = entry.get('times'), entry.get('online')
        
        print(f"Обрабатываем: times={times}, online={online}")  # Отладочный вывод

        timestamp = parse_float(times)
        online_value = parse_float(online)

        if timestamp is None or online_value is None:
            continue

        if timestamp >= day_start:
            day_online.append(online_value)
        if timestamp >= week_start:
            week_online.append(online_value)
        if timestamp >= month_start:
            month_online.append(online_value)
        all_time_online.append(online_value)

    # Отладочный вывод
    print(f"Day online: {day_online}")
    print(f"Week online: {week_online}")
    print(f"Month online: {month_online}")
    print(f"All time online: {all_time_online}")

    def calculate_stats(online_list):
        """Вычислить максимальное, среднее и минимальное значения онлайн"""
        if not online_list:
            return (0, 0, 0)
        return (max(online_list), sum(online_list) / len(online_list), min(online_list))

    day_max, day_avg, day_min = calculate_stats(day_online)
    week_max, week_avg, week_min = calculate_stats(week_online)
    month_max, month_avg, month_min = calculate_stats(month_online)
    all_time_max, _, _ = calculate_stats(all_time_online)

    # Отладочный вывод
    print(f"Stats - Day: Max={day_max}, Avg={day_avg}, Min={day_min}")
    print(f"Stats - Week: Max={week_max}, Avg={week_avg}, Min={week_min}")
    print(f"Stats - Month: Max={month_max}, Avg={month_avg}, Min={month_min}")
    print(f"Stats - All Time: Max={all_time_max}")

    return {
        'day_max': day_max,
        'day_avg': day_avg,
        'day_min': day_min,
        'week_max': week_max,
        'week_avg': week_avg,
        'week_min': week_min,
        'month_max': month_max,
        'month_avg': month_avg,
        'month_min': month_min,
        'all_time_max': all_time_max
    }

def insert_or_update_onlines(conn, server_id, stats):
    """Вставить новые данные о онлайн состоянии в таблицу onlines или обновить существующую запись"""
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id FROM onlines WHERE id = %s', (server_id,))
        existing_record = cursor.fetchone()

        if existing_record:
            onlines_id = existing_record[0]
            cursor.execute('''
                UPDATE onlines
                SET daysmax = %s, dayssred = %s, daysmin = %s,
                    nedelmax = %s, nedelsred = %s, nedelmin = %s,
                    mecmax = %s, mecred = %s, mecmin = %s,
                    vse = %s
                WHERE id = %s
            ''', (stats['day_max'], stats['day_avg'], stats['day_min'],
                  stats['week_max'], stats['week_avg'], stats['week_min'],
                  stats['month_max'], stats['month_avg'], stats['month_min'],
                  stats['all_time_max'], onlines_id))
            print(f"Обновление записи для сервера ID {server_id}")
        else:
            cursor.execute('''
                INSERT INTO onlines (id, daysmax, dayssred, daysmin, nedelmax, nedelsred, nedelmin, mecmax, mecred, mecmin, vse)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (server_id, stats['day_max'], stats['day_avg'], stats['day_min'],
                  stats['week_max'], stats['week_avg'], stats['week_min'],
                  stats['month_max'], stats['month_avg'], stats['month_min'],
                  stats['all_time_max']))
            onlines_id = cursor.lastrowid
            print(f"Добавление записи для сервера ID {server_id}")

        conn.commit()
        return onlines_id
    except mysql.connector.Error as err:
        print(f"Error inserting or updating onlines: {err}")
        conn.rollback()
        raise

def update_server_with_onlines_id(conn, server_id, onlines_id):
    """Обновить запись о сервере с ID новой записи из таблицы onlines"""
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE server
            SET onlines = %s
            WHERE id = %s
        ''', (onlines_id, server_id))
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error updating server with id: {err}")
        conn.rollback()
        raise

def process_servers():
    """Обработать все серверы, обновить статистику и записать в базу данных"""
    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('SET autocommit=0')  # Отключаем автокоммит
        servers = get_server_data(conn)

        # Фильтруем серверы, оставляя только те, у которых ok = 1
        active_servers = [server for server in servers if server['ok'] == 1]
        print(f"Серверов ok = 1 в количестве {len(active_servers)}")
        print("Началось вычисление онлайна")

        total_servers = len(active_servers)
        for index, server in enumerate(active_servers):
            server_id = server['id']
            ip_address = server['ip_address']
            port = server['port']
            
            print(f"{index + 1}/{total_servers} сервер: {ip_address}:{port} записывается", end=" ")

            try:
                lister_data = get_lister_data(conn, ip_address, port)
                if not lister_data:
                    print("данные отсутствуют")
                    continue
                
                stats = calculate_online_stats(lister_data)
                onlines_id = insert_or_update_onlines(conn, server_id, stats)
                update_server_with_onlines_id(conn, server_id, onlines_id)
                print("записался")
            except Exception as e:
                print(f"не записался. Ошибка: {e}")

            conn.commit()  # Подтверждаем транзакцию
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        if conn:
            conn.rollback()  # Откатываем транзакцию в случае ошибки
    finally:
        if conn:
            conn.close()

def main():
    """Основной цикл выполнения скрипта"""
    while True:
        try:
            process_servers()
        except Exception as e:
            print(f"Unexpected error: {e}")
        print("Waiting for 3 minutes before running again...")
        time.sleep(180)  # 3 минуты

if __name__ == '__main__':
    main()