import os
from datetime import datetime, timedelta
import mysql.connector
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, HourLocator
import mplcyberpunk
import logging
import vk_api
import time

logging.basicConfig(filename='beaconbot.log', level=logging.INFO,
                    format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

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

    try:
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

        query_30_days = f"SELECT times FROM lister WHERE server LIKE '{ip}%' AND times >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))"
        db_cursor.execute(query_30_days)
        result_30_days = db_cursor.fetchall()
        if not result_30_days:
            return None, "Недостаточно данных за последние 30 дней, чтобы построить график."

        return None, f"Нет данных для сервера {ip_address} за период {period}"
    except mysql.connector.Error as e:
        return None, f"Ошибка при проверке соединения с MySQL: {e}"

def plot_graph_and_save(data, filename, ip_address, period):
    plt.style.use("cyberpunk")
    times, online = zip(*data)
    online = [int(float(x)) for x in online]  # Приведение к целым числам

    plt.figure(figsize=(10, 6))
    times = [datetime.fromtimestamp(int(t)) for t in times]

    if period == 'день':
        current_time = datetime.now()
        start_of_day = current_time.replace(hour=0, minute=0, second=0, microsecond=0)

        times_filtered = [t for t in times if t >= start_of_day]
        online_filtered = [online[i] for i, t in enumerate(times) if t >= start_of_day]

        if times_filtered:
            plt.plot(times_filtered, online_filtered, '-', color='cyan', alpha=0.7)
            plt.fill_between(times_filtered, online_filtered, color='cyan', alpha=0.3)
            mplcyberpunk.add_glow_effects(gradient_fill=True)
            mplcyberpunk.add_gradient_fill(alpha_gradientglow=0.1)
            max_online = max(online_filtered)
            min_online = min(online_filtered)
            y_padding = 0.1 * (max_online - min_online)
            plt.ylim(min_online - y_padding, max_online + y_padding)

            plt.gca().xaxis.set_major_locator(HourLocator(interval=1))
            plt.gca().xaxis.set_major_formatter(DateFormatter('%H:%M\n'))
            plt.xticks(rotation=50)

            plt.xlabel('Время (часы)')
            plt.ylabel('Онлайн')
            plt.title(f'Сервер: {ip_address} (за день)')
        else:
            plt.text(0.5, 0.5, 'Нет данных за указанный период', horizontalalignment='center', verticalalignment='center', transform=plt.gca().transAxes)

    elif period in ['неделя', 'месяц']:

        grouped_data = {}
        for t, o in zip(times, online):
            key = t.date()
            grouped_data[key] = max(grouped_data.get(key, 0), o)

        times = list(grouped_data.keys())
        online = list(grouped_data.values())

        plt.plot(times, online, color='cyan', alpha=0.7, linewidth=3)
        plt.fill_between(times, online, color='cyan', alpha=0.3)
        mplcyberpunk.add_glow_effects(gradient_fill=True)
        mplcyberpunk.add_gradient_fill(alpha_gradientglow=2.0)
        max_online = max(online)
        min_online = min(online)
        y_padding = 0.1 * (max_online - min_online)
        plt.ylim(min_online - y_padding, max_online + y_padding)
        time_labels = [t.strftime('%d.%m') for t in times]
        plt.xticks(times, time_labels, rotation=45)

        plt.xlabel('Дата')
        plt.ylabel('Максимальный онлайн за день')
        plt.title(f'Сервер: {ip_address} (за {period})')

    else:
        plt.plot(times, online, color='cyan', alpha=0.7, linewidth=3)
        plt.fill_between(times, online, color='cyan', alpha=0.3)
        mplcyberpunk.add_glow_effects(gradient_fill=True)
        mplcyberpunk.add_gradient_fill(alpha_gradientglow=2.0)
        max_online = max(online)
        min_online = min(online)
        y_padding = 0.1 * (max_online - min_online)
        plt.ylim(min_online - y_padding, max_online + y_padding)
        time_labels = [t.strftime('%d.%m %H:%M') for t in times]
        plt.xticks(times, time_labels, rotation=45)

        plt.xlabel('Дата')
        plt.ylabel('Онлайн')
        plt.title(f'Сервер: {ip_address}')

    plt.savefig(filename, bbox_inches='tight')
    plt.close()

def upload_to_vk_and_save_to_db(filename, ip_address, period, db_cursor, vk_session):
    vk = vk_session.get_api()
    upload_url = vk.photos.getMessagesUploadServer()['upload_url']
    
    with open(filename, 'rb') as file:
        response = vk_session.http.post(upload_url, files={'photo': file}).json()

    photo = vk.photos.saveMessagesPhoto(**response)[0]
    owner_id = photo['owner_id']
    photo_id = photo['id']
    times = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    name = filename

    try:
        delete_query = "DELETE FROM stats WHERE name = %s"
        db_cursor.execute(delete_query, (filename,))
        logging.info(f"Удалены записи из таблицы stats для файла {filename}.")

        insert_query = "INSERT INTO stats (owner_id, vk_id, times, name) VALUES (%s, %s, %s, %s)"
        db_cursor.execute(insert_query, (owner_id, photo_id, times, name))
        logging.info(f"Вставлена новая запись в таблицу stats для файла {filename}.")

        os.remove(filename)
    except mysql.connector.Error as e:
        logging.error(f"Ошибка при записи в базу данных: {e}")
        return False
    
    return True

def main():
    db_config = {
        'host': 'localhost',
        'user': 'vh373935_becon',
        'password': '1hajUZwNtxfNIG2o',
        'database': 'vh373935_becon',
        'autocommit': True
    }
    vk_token = 'vk1.a.k12V9Sz0HhuSS1GSVlq9NLbKd0iHg_m-7HT_15tUNfZdr3L7rJ0nweJQpwag7Ma0HcLtc-g9MdX-qcbzH-yk2reatORVJGxsAgtmoxqBEXTH30lhoHR_jVpBEbnc9Mnrrvf6VFd4UtJUyxOF4QqDA2oVUbtHkBgFxYStoyBdBEUl-qfAyvj4j3ZFgfbcvsiwgBphc2m0nYcWKE2mVmvUvQ'

    vk_session = vk_api.VkApi(token=vk_token)

    grafics_folder = "grafics"
    if not os.path.exists(grafics_folder):
        os.makedirs(grafics_folder)

    while True:
        try:
            db_connection = mysql.connector.connect(**db_config)
            cursor = db_connection.cursor()

            logging.info("Успешное подключение к базе данных MySQL.")

            query_servers = "SELECT ip_address, port FROM server WHERE ok = 1"
            cursor.execute(query_servers)
            servers = cursor.fetchall()

            for server in servers:
                ip_address = server[0]
                port = server[1]

                for period in ['день', 'неделя', 'месяц']:
                    data, error = get_data_from_mysql(f"{ip_address}:{port}", period, cursor)

                    if error:
                        logging.error(f"Ошибка для сервера {ip_address}:{port}, период {period}: {error}")
                        continue

                    if data is None:
                        logging.info(f"Нет данных для сервера {ip_address}:{port}, период {period}")
                        continue

                    filename = os.path.join(grafics_folder, f"{ip_address}_{port}_{period}.png")
                    try:
                        plot_graph_and_save(data, filename, ip_address, period)
                        logging.info(f"Создан график для сервера {ip_address}:{port}, период {period}")

                        if upload_to_vk_and_save_to_db(filename, ip_address, period, cursor, vk_session):
                            logging.info(f"График загружен в ВКонтакте и информация записана в базу данных для сервера {ip_address}:{port}, период {period}")
                        else:
                            logging.error(f"Ошибка при загрузке графика в ВКонтакте для сервера {ip_address}:{port}, период {period}")

                    except Exception as e:
                        logging.error(f"Ошибка при создании графика для сервера {ip_address}:{port}, период {period}: {e}")

            cursor.close()
            db_connection.close()

            logging.info("Закрыто соединение с базой данных MySQL.")

            time.sleep(300)

        except mysql.connector.Error as e:
            logging.error(f"Ошибка при подключении или работе с базой данных MySQL: {e}")
            time.sleep(10)
        except Exception as e:
            logging.error(f"Произошла ошибка: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
