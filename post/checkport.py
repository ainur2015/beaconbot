import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import time

# Настройки подключения к базе данных (скрипт вместо CRON для действий)
db_config = {
    'host': 'localhost',
    'user': 'Логин',
    'password': 'Пароль',
    'database': 'БД'
}

def get_unix_timestamp():
    return int(datetime.utcnow().timestamp())

def connect_to_db():
    connection = None
    while connection is None:
        try:
            connection = mysql.connector.connect(**db_config)
            if connection.is_connected():
                print("Connected to MySQL database")
                return connection
        except Error as e:
            print(f"Error connecting to MySQL database: {e}")
            print("Retrying in 5 seconds...")
            time.sleep(5)
    return connection

def update_timesport(connection):
    cursor = connection.cursor()
    current_time = get_unix_timestamp()
    
    try:
        # Очистка таблицы ip_port
        cursor.execute("TRUNCATE TABLE ip_port")
        
        # Обновление столбца timesport
        cursor.execute("UPDATE psettings SET timesport = %s WHERE id = 1", (current_time,))
        connection.commit()
        
        print("Timesport updated and ip_port table cleared")
    except Error as e:
        print(f"Error during update_timesport: {e}")
        connection.rollback()

def update_times(connection):
    cursor = connection.cursor()
    current_time = get_unix_timestamp()
    
    try:
        # Обновление столбца checkport в таблице users
        cursor.execute("UPDATE users SET checkport = 0")
        
        # Обновление столбца times
        cursor.execute("UPDATE psettings SET times = %s WHERE id = 1", (current_time,))
        connection.commit()
        
        print("Times updated and checkport reset")
    except Error as e:
        print(f"Error during update_times: {e}")
        connection.rollback()

def main_loop():
    connection = connect_to_db()
    
    while True:
        try:
            cursor = connection.cursor()
            current_time = get_unix_timestamp()
            
            # Проверка времени в psettings
            cursor.execute("SELECT timesport, times FROM psettings WHERE id = 1")
            result = cursor.fetchone()
            
            if result:
                # Преобразование значений в целые числа
                timesport, times = result
                timesport = int(timesport)
                times = int(times)
                
                # Проверка, прошел ли час
                if current_time >= timesport + 3600:
                    update_timesport(connection)
                
                # Проверка, прошел ли день
                if current_time >= times + 86400:
                    update_times(connection)
            
            # Ожидание одной минуты
            time.sleep(60)
        
        except Error as e:
            print(f"Error during main loop: {e}")
            connection.close()
            connection = connect_to_db()

if __name__ == "__main__":
    main_loop()