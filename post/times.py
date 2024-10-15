import mysql.connector
from mysql.connector import Error
import time
from datetime import datetime, timedelta

def connect_to_mysql():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='бд',
            user='логин',
            password='пасс'
        )
        if connection.is_connected():
            print("Connected to MySQL database")
            return connection
    except Error as e:
        print(f"Error: {e}")
        return None

def delete_old_records(connection):
    try:
        cursor = connection.cursor()
        one_day_ago = datetime.now() - timedelta(days=1)
        query = "DELETE FROM stats WHERE times < %s"
        cursor.execute(query, (one_day_ago,))
        connection.commit()
        print(f"Deleted {cursor.rowcount} old records")
    except Error as e:
        print(f"Error: {e}")

def main():
    connection = None
    while True:
        if connection is None or not connection.is_connected():
            connection = connect_to_mysql()
        
        if connection and connection.is_connected():
            delete_old_records(connection)
        
        # Wait for some time before running again, e.g., 1 hour
        time.sleep(3600)

if __name__ == "__main__":
    main()
