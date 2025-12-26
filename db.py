import sqlite3
import os

DATABASE_NAME = 'travel.db'


def get_connection():
    """Получить соединение с базой данных"""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Инициализация базы данных: создание таблиц и заполнение начальными данными"""
    conn = get_connection()
    cursor = conn.cursor()

    # Создание таблицы customers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            birthday DATE,
            phone TEXT,
            email TEXT,
            password_number TEXT,
            registration_date DATE
        )
    ''')

    # Создание таблицы employees
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            position TEXT,
            phone TEXT,
            email TEXT,
            password TEXT,
            hire_date DATE,
            photo_url TEXT
        )
    ''')

    ensure_employees_password(conn)

    # Создание таблицы hotels
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hotels (
            hotel_id INTEGER PRIMARY KEY AUTOINCREMENT,
            hotel_name TEXT,
            destination TEXT,
            stars INTEGER,
            description TEXT,
            amenities TEXT,
            photo_url TEXT
        )
    ''')

    # Создание таблицы tours
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tours (
            tour_id INTEGER PRIMARY KEY AUTOINCREMENT,
            destination TEXT,
            tour_name TEXT,
            description TEXT,
            duration_days INTEGER,
            price REAL,
            photo_url TEXT,
            itinerary TEXT,
            category TEXT
        )
    ''')

    # Создание таблицы additional_services
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS additional_services (
            service_id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_name TEXT,
            description TEXT,
            price REAL
        )
    ''')

    # Создание таблицы bookings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            tour_id INTEGER,
            employee_id INTEGER,
            hotel_id INTEGER,
            booking_date DATETIME,
            travel_start_date DATE,
            travel_end_date DATE,
            number_of_travelers INTEGER,
            total_amount REAL,
            payment_method TEXT,
            status TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (tour_id) REFERENCES tours(tour_id),
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
            FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id)
        )
    ''')

    # Создание таблицы flights
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flights (
            flight_id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER,
            airline TEXT,
            flight_number TEXT,
            departure_city TEXT,
            arrival_city TEXT,
            departure_date_time DATETIME,
            arrival_date_time DATETIME,
            ticket_price REAL,
            FOREIGN KEY (booking_id) REFERENCES bookings(booking_id)
        )
    ''')

    # Создание таблицы booking_services
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS booking_services (
            booking_service_id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER,
            service_id INTEGER,
            quantity INTEGER,
            FOREIGN KEY (booking_id) REFERENCES bookings(booking_id),
            FOREIGN KEY (service_id) REFERENCES additional_services(service_id)
        )
    ''')

    conn.commit()

    # Проверяем, есть ли уже данные в таблицах
    cursor.execute('SELECT COUNT(*) FROM customers')
    if cursor.fetchone()[0] == 0:
        insert_initial_data(conn)

    conn.close()


def ensure_employees_password(conn):
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(employees)")
    columns = {row[1] for row in cursor.fetchall()}
    if 'password' not in columns:
        cursor.execute('ALTER TABLE employees ADD COLUMN password TEXT')

    cursor.execute("UPDATE employees SET password = 'admin' WHERE password IS NULL")

    cursor.execute("SELECT 1 FROM employees WHERE email = 'admin'")
    if cursor.fetchone() is None:
        cursor.execute(
            """
            INSERT INTO employees (full_name, position, phone, email, password, hire_date, photo_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ('Администратор', 'Администратор', '', 'admin', 'admin', None, None)
        )

    conn.commit()


def insert_initial_data(conn):
    """Вставка начальных данных в таблицы"""
    cursor = conn.cursor()

    # Вставка данных в customers
    cursor.executemany('''
        INSERT INTO customers (full_name, birthday, phone, email, password_number, registration_date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', [
        ('Иванов Иван Иванович', '1985-05-15', '79150001122', 'ivanov@mail.ru', 'pass123', '2023-01-12'),
        ('Петров Сергей Олегович', '1990-08-22', '79160004567', 'petrov@mail.ru', 'pass456', '2023-03-08'),
        ('Сидорова Анна Петровна', '1980-11-30', '79170007890', 'sidorova@mail.ru', 'pass789', '2024-02-15')
    ])

    # Вставка данных в employees
    cursor.executemany('''
        INSERT INTO employees (full_name, position, phone, email, password, hire_date, photo_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', [
        ('Кузнецов Алексей Николаевич', 'Менеджер', '79151112233', 'kuznetsov@travel.ru', 'admin', '2020-04-01', 'photo1.jpg'),
        ('Смирнова Мария Сергеевна', 'Агент', '79153334455', 'smirnova@travel.ru', 'admin', '2021-06-15', 'photo2.jpg'),
        ('Попов Дмитрий Иванович', 'Администратор', '79156667788', 'popov@travel.ru', 'admin', '2022-09-10', 'photo3.jpg'),
        ('Администратор', 'Администратор', '', 'admin', 'admin', None, None)
    ])

    # Вставка данных в hotels
    cursor.executemany('''
        INSERT INTO hotels (hotel_name, destination, stars, description, amenities, photo_url)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', [
        ('Отель Люкс', 'Сочи', 5, 'Роскошный отель на берегу моря', 'Бассейн, СПА, ресторан', 'hotel1.jpg'),
        ('Отель Комфорт', 'Москва', 4, 'Уютный отель в центре города', 'Ресторан, фитнес-зал', 'hotel2.jpg'),
        ('Отель Эконом', 'Санкт-Петербург', 3, 'Бюджетный отель в историческом центре', 'Ресторан, бесплатный Wi-Fi', 'hotel3.jpg')
    ])

    # Вставка данных в tours
    cursor.executemany('''
        INSERT INTO tours (destination, tour_name, description, duration_days, price, photo_url, itinerary, category)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', [
        ('Сочи', 'Лето в Сочи', 'Отдых на черноморском побережье', 7, 45000, 'tour1.jpg', 'Экскурсии, пляжный отдых', 'Пляжный'),
        ('Москва', 'Экскурсия по Москве', 'Знакомство с достопримечательностями столицы', 5, 35000, 'tour2.jpg', 'Экскурсии, музеи', 'Экскурсионный'),
        ('Санкт-Петербург', 'Романтический Санкт-Петербург', 'Прогулки по историческому центру', 6, 40000, 'tour3.jpg', 'Экскурсии, театры', 'Культурный')
    ])

    # Вставка данных в additional_services
    cursor.executemany('''
        INSERT INTO additional_services (service_name, description, price)
        VALUES (?, ?, ?)
    ''', [
        ('Трансфер', 'Встреча и проводы в аэропорту', 1500),
        ('Экскурсия', 'Обзорная экскурсия по городу', 2500),
        ('Страховка', 'Медицинская страховка на время поездки', 1000)
    ])

    # Вставка данных в bookings
    cursor.executemany('''
        INSERT INTO bookings (customer_id, tour_id, employee_id, hotel_id, booking_date, travel_start_date, travel_end_date, number_of_travelers, total_amount, payment_method, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', [
        (1, 1, 1, 1, '2024-03-01 10:00:00', '2024-07-01', '2024-07-08', 2, 50000, 'Карта', 'Подтверждено'),
        (2, 2, 2, 2, '2024-03-02 11:00:00', '2024-07-10', '2024-07-15', 1, 40000, 'Наличные', 'Подтверждено'),
        (3, 3, 3, 3, '2024-03-03 12:00:00', '2024-07-15', '2024-07-21', 3, 60000, 'Карта', 'Подтверждено')
    ])

    # Вставка данных в flights
    cursor.executemany('''
        INSERT INTO flights (booking_id, airline, flight_number, departure_city, arrival_city, departure_date_time, arrival_date_time, ticket_price)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', [
        (1, 'Аэрофлот', 'SU123', 'Москва', 'Сочи', '2024-07-01 08:00:00', '2024-07-01 10:00:00', 10000),
        (2, 'S7 Airlines', 'S7456', 'Москва', 'Санкт-Петербург', '2024-07-10 09:00:00', '2024-07-10 11:00:00', 8000),
        (3, 'Utair', 'UT789', 'Москва', 'Сочи', '2024-07-15 10:00:00', '2024-07-15 12:00:00', 9000)
    ])

    # Вставка данных в booking_services
    cursor.executemany('''
        INSERT INTO booking_services (booking_id, service_id, quantity)
        VALUES (?, ?, ?)
    ''', [
        (1, 1, 2),
        (2, 2, 1),
        (3, 3, 3)
    ])

    conn.commit()


if __name__ == '__main__':
    # Удаляем старую базу данных, если нужно начать заново
    if os.path.exists(DATABASE_NAME):
        os.remove(DATABASE_NAME)
    
    init_db()
    print(f'База данных {DATABASE_NAME} успешно создана и заполнена данными!')
    
    # Проверка данных
    conn = get_connection()
    cursor = conn.cursor()
    
    print('\n--- Клиенты ---')
    cursor.execute('SELECT * FROM customers')
    for row in cursor.fetchall():
        print(dict(row))
    
    print('\n--- Туры ---')
    cursor.execute('SELECT * FROM tours')
    for row in cursor.fetchall():
        print(dict(row))
    
    conn.close()
