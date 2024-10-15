from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, HourLocator
import re
import mplcyberpunk

def plot_graph_and_save(data, filename, ip_address, period):
    plt.style.use("cyberpunk")  # Применяем стиль киберпанка

    times, online = zip(*data)
    online = [int(x) for x in online]

    plt.figure(figsize=(10, 6))
    times = [datetime.fromtimestamp(int(t)) for t in times]

    if period == 'день':
        current_time = datetime.now()
        start_of_day = current_time.replace(hour=0, minute=0, second=0, microsecond=0)

        # Находим временные метки, начиная с полуночи текущего дня
        times_filtered = [t for t in times if t >= start_of_day]
        online_filtered = [online[i] for i, t in enumerate(times) if t >= start_of_day]

        if times_filtered:
            plt.plot_date(times_filtered, online_filtered, linestyle='-', color='cyan', alpha=0.7)
            plt.fill_between(times_filtered, online_filtered, color='cyan', alpha=0.3)
            plt.grid(False)
            max_online = max(online_filtered)
            min_online = min(online_filtered)
            y_padding = 0.1 * (max_online - min_online)
            plt.ylim(min_online - y_padding, max_online + y_padding)

            plt.gca().xaxis.set_major_locator(HourLocator(interval=1))
            plt.gca().xaxis.set_major_formatter(DateFormatter('%H:%M\n'))
            plt.xticks(rotation=50)  # Поворачиваем метки времени на 90 градусов

            plt.xlabel('Время (часы)')
            plt.ylabel('Онлайн')
            plt.title(f'Сервер: {ip_address} (за день)')
        else:
            plt.text(0.5, 0.5, 'Нет данных за указанный период', horizontalalignment='center', verticalalignment='center', transform=plt.gca().transAxes)

    elif period == 'неделя':
        # Группируем данные по дням
        grouped_data = {}
        for t, o in zip(times, online):
            key = t.date()
            grouped_data[key] = max(grouped_data.get(key, 0), o)
        
        times = list(grouped_data.keys())
        online = list(grouped_data.values())

        plt.plot(times, online, color='cyan', alpha=0.7, linewidth=3)
        plt.fill_between(times, online, color='cyan', alpha=0.3)
        plt.grid(False)
        max_online = max(online)
        min_online = min(online)
        y_padding = 0.1 * (max_online - min_online)
        plt.ylim(min_online - y_padding, max_online + y_padding)
        time_labels = [t.strftime('%d.%m') for t in times]
        plt.xticks(times, time_labels, rotation=45)

        plt.xlabel('Дата')
        plt.ylabel('Максимальный онлайн за день')
        plt.title(f'Сервер: {ip_address} (за неделю)')

    elif period == 'месяц':
        # Группируем данные по дням
        grouped_data = {}
        for t, o in zip(times, online):
            key = t.date()
            grouped_data[key] = max(grouped_data.get(key, 0), o)
        
        times = list(grouped_data.keys())
        online = list(grouped_data.values())

        plt.plot(times, online, color='cyan', alpha=0.7, linewidth=3)
        plt.fill_between(times, online, color='cyan', alpha=0.3)
        plt.grid(False)
        max_online = max(online)
        min_online = min(online)
        y_padding = 0.1 * (max_online - min_online)
        plt.ylim(min_online - y_padding, max_online + y_padding)
        time_labels = [t.strftime('%d.%m') for t in times]
        plt.xticks(times, time_labels, rotation=45)

        plt.xlabel('Дата')
        plt.ylabel('Максимальный онлайн за день')
        plt.title(f'Сервер: {ip_address} (за месяц)')

    else:
        # Для других периодов выводим обычный график по времени
        plt.plot(times, online, color='cyan', alpha=0.7, linewidth=3)
        plt.fill_between(times, online, color='cyan', alpha=0.3)
        plt.grid(False)
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
    mplcyberpunk.add_glow_effects()  # Добавляем эффекты свечения
    plt.show()
    plt.close()


def group_data_by_day(times, online):
    grouped_data = {}
    for t, o in zip(times, online):
        key = t.date()
        grouped_data[key] = max(grouped_data.get(key, 0), o)
    return grouped_data

def comparison_server_graph(data1, data2, filename, ip_address1, ip_address2, period):
    # Удаление недопустимых символов из имени файла
    safe_filename = re.sub(r'[^\w\-_\. ]', '_', filename)
    
    # Разделение данных на временные метки и количество онлайна для каждого сервера
    times1, online1 = zip(*data1)
    times2, online2 = zip(*data2)
    
    # Преобразование онлайна в числовой формат
    online1 = [int(x) for x in online1]
    online2 = [int(x) for x in online2]

    # Создание нового графика
    plt.figure(figsize=(10, 6))
    
    # Преобразование временных меток в объекты datetime
    times1 = [datetime.fromtimestamp(int(t)) for t in times1]
    times2 = [datetime.fromtimestamp(int(t)) for t in times2]

    if period == 'день':
        # Создаем список временных меток с интервалом в 1 час от полуночи до текущего времени
        current_time = datetime.now()
        start_of_day = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        times_filtered = [start_of_day + timedelta(hours=i) for i in range(24)]

        # Создаем функции интерполяции для каждого сервера
        interp_func1 = interp1d([t.timestamp() for t in times1], online1, kind='linear', bounds_error=False, fill_value=(online1[0], online1[-1]))
        interp_func2 = interp1d([t.timestamp() for t in times2], online2, kind='linear', bounds_error=False, fill_value=(online2[0], online2[-1]))

        # Генерируем интерполированные значения онлайна для каждого сервера
        online_interp1 = [int(val) for val in interp_func1([t.timestamp() for t in times_filtered])]
        online_interp2 = [int(val) for val in interp_func2([t.timestamp() for t in times_filtered])]

        # Строим график онлайна для каждого сервера
        plt.plot([t.strftime('%d.%m') for t in times_filtered], online_interp1, label=f'{ip_address1} онлайн', color='blue', alpha=0.7, linewidth=2)
        plt.plot([t.strftime('%d.%m') for t in times_filtered], online_interp2, label=f'{ip_address2} онлайн', color='red', alpha=0.7, linewidth=2)

        # Добавляем горизонтальные линии для обозначения уровней онлайна
        max_online1 = max(online_interp1)
        max_online2 = max(online_interp2)
        max_online = max(max_online1, max_online2)
        step = 5000  # Шаг уровней онлайна
        levels = range(0, max_online + step, step)
        for level in levels:
            plt.axhline(y=level, color='gray', linestyle='--', linewidth=1)

        # Оформляем график
        plt.grid(True)
        plt.gca().set_facecolor('white')
        plt.xlabel('Дата')
        plt.ylabel('Онлайн')
        plt.title(f'Онлайн серверов: {ip_address1} и {ip_address2} (за день)')
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()

    elif period == 'неделя':
        # Создаем список дней за неделю
        current_time = datetime.now()
        start_of_week = current_time - timedelta(days=current_time.weekday())
        dates_filtered = [start_of_week + timedelta(days=i) for i in range(7)]

        # Создаем функции интерполяции для каждого сервера
        interp_func1 = interp1d([t.timestamp() for t in times1], online1, kind='linear', bounds_error=False, fill_value=(online1[0], online1[-1]))
        interp_func2 = interp1d([t.timestamp() for t in times2], online2, kind='linear', bounds_error=False, fill_value=(online2[0], online2[-1]))

        # Генерируем интерполированные значения онлайна для каждого сервера
        online_interp1 = [int(val) for val in interp_func1([t.timestamp() for t in dates_filtered])]
        online_interp2 = [int(val) for val in interp_func2([t.timestamp() for t in dates_filtered])]

        # Строим график онлайна для каждого сервера
        plt.plot([t.strftime('%d.%m') for t in dates_filtered], online_interp1, label=f'{ip_address1} онлайн', color='blue', alpha=0.7, linewidth=2)
        plt.plot([t.strftime('%d.%m') for t in dates_filtered], online_interp2, label=f'{ip_address2} онлайн', color='red', alpha=0.7, linewidth=2)

        # Добавляем горизонтальные линии для обозначения уровней онлайна
        max_online1 = max(online_interp1)
        max_online2 = max(online_interp2)
        max_online = max(max_online1, max_online2)
        step = 5000  # Шаг уровней онлайна
        levels = range(0, max_online + step, step)
        for level in levels:
            plt.axhline(y=level, color='gray', linestyle='--', linewidth=1)

        # Оформляем график
        plt.grid(True)
        plt.gca().set_facecolor('white')
        plt.xlabel('Дата')
        plt.ylabel('Онлайн')
        plt.title(f'Онлайн серверов: {ip_address1} и {ip_address2} (за неделю)')
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()

    elif period == 'месяц':
        # Определяем начало и конец текущего месяца
        current_time = datetime.now()
        start_of_month = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_of_month = start_of_month.replace(day=monthrange(current_time.year, current_time.month)[1])

        # Если текущая дата больше, чем 30 дней с начала месяца, то выводим до конца месяца
        if datetime.now() > (start_of_month + timedelta(days=30)):
            times_filtered = [start_of_month + timedelta(days=i) for i in range(31)]
        else:
            times_filtered = [start_of_month + timedelta(days=i) for i in range((datetime.now() - start_of_month).days + 1)]

        # Создаем функции интерполяции для каждого сервера
        interp_func1 = interp1d([t.timestamp() for t in times1], online1, kind='linear', bounds_error=False, fill_value=(online1[0], online1[-1]))
        interp_func2 = interp1d([t.timestamp() for t in times2], online2, kind='linear', bounds_error=False, fill_value=(online2[0], online2[-1]))

        # Генерируем интерполированные значения онлайна для каждого сервера
        online_interp1 = [int(val) for val in interp_func1([t.timestamp() for t in times_filtered])]
        online_interp2 = [int(val) for val in interp_func2([t.timestamp() for t in times_filtered])]

        # Строим график онлайна для каждого сервера
        plt.plot([t.strftime('%d.%m') for t in times_filtered], online_interp1, label=f'{ip_address1} онлайн', color='blue', alpha=0.7, linewidth=2)
        plt.plot([t.strftime('%d.%m') for t in times_filtered], online_interp2, label=f'{ip_address2} онлайн', color='red', alpha=0.7, linewidth=2)

        # Добавляем горизонтальные линии для обозначения уровней онлайна
        max_online1 = max(online_interp1)
        max_online2 = max(online_interp2)
        max_online = max(max_online1, max_online2)
        step = 5000  # Шаг уровней онлайна
        levels = range(0, max_online + step, step)
        for level in levels:
            plt.axhline(y=level, color='gray', linestyle='--', linewidth=1)

        # Оформляем график
        plt.grid(True)
        plt.gca().set_facecolor('white')
        plt.xlabel('Дата')
        plt.ylabel('Онлайн')
        plt.title(f'Онлайн серверов: {ip_address1} и {ip_address2} (за месяц)')
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()

    else:
        # Код для отображения данных по-умолчанию
        # В данном случае, допустим, мы просто строим график по временным меткам и онлайну для каждого сервера
        plt.plot(times1, online1, label=ip_address1, color='blue', alpha=0.7, linewidth=3)
        plt.plot(times2, online2, label=ip_address2, color='red', alpha=0.7, linewidth=3)
        plt.legend()

    # Сохранение графика в файл
    plt.savefig(safe_filename, bbox_inches='tight')
    # Закрытие графика
    plt.close()