import sys
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QDate
from db import init_db, get_connection


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Туристическое агентство - Авторизация')
        self.setFixedSize(350, 200)
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        layout.addWidget(QLabel('Туристическое агентство'))

        email_layout = QHBoxLayout()
        email_layout.addWidget(QLabel('Email:'))
        self.email_input = QLineEdit()
        email_layout.addWidget(self.email_input)
        layout.addLayout(email_layout)

        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel('Пароль:'))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(self.password_input)
        layout.addLayout(password_layout)

        login_btn = QPushButton('Войти')
        login_btn.clicked.connect(self.login)
        layout.addWidget(login_btn)

    def login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()

        if not email or not password:
            QMessageBox.warning(self, 'Ошибка', 'Заполните все поля')
            return

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM employees WHERE email = ? AND password = ?', (email, password))
        employee = cursor.fetchone()
        if employee:
            conn.close()
            self.admin_window = AdminWindow(dict(employee))
            self.admin_window.show()
            self.hide()
            return

        cursor.execute('SELECT * FROM customers WHERE email = ? AND password_number = ?',
                       (email, password))
        customer = cursor.fetchone()
        if customer:
            conn.close()
            self.client_window = ClientWindow(dict(customer))
            self.client_window.show()
            self.hide()
            return

        conn.close()
        QMessageBox.warning(self, 'Ошибка', 'Неверный email или пароль')


class AdminWindow(QMainWindow):
    def __init__(self, employee):
        super().__init__()
        self.employee = employee
        self.setWindowTitle(f'Панель администратора - {employee["full_name"]}')
        self.setMinimumSize(1100, 600)
        self.setup_ui()
        self.load_bookings()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        layout.addWidget(QLabel(f'Администратор: {self.employee["full_name"]}'))

        tabs = QTabWidget()
        tabs.addTab(self.create_bookings_tab(), 'Бронирования')
        tabs.addTab(self.create_tours_tab(), 'Туры')
        tabs.addTab(self.create_customers_tab(), 'Клиенты')
        layout.addWidget(tabs)

    def create_bookings_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel('Статус:'))
        self.status_filter = QComboBox()
        self.status_filter.addItems(['Все', 'Ожидает', 'Подтверждено', 'В работе', 'Выполнен', 'Отменён'])
        filter_layout.addWidget(self.status_filter)

        filter_layout.addWidget(QLabel('Дата с:'))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        filter_layout.addWidget(self.date_from)

        filter_layout.addWidget(QLabel('по:'))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate().addMonths(6))
        filter_layout.addWidget(self.date_to)

        filter_btn = QPushButton('Фильтровать')
        filter_btn.clicked.connect(self.filter_bookings)
        filter_layout.addWidget(filter_btn)

        show_all_btn = QPushButton('Показать все')
        show_all_btn.clicked.connect(self.load_bookings)
        filter_layout.addWidget(show_all_btn)

        layout.addLayout(filter_layout)

        self.bookings_table = QTableWidget()
        self.bookings_table.setColumnCount(9)
        self.bookings_table.setHorizontalHeaderLabels([
            'ID', 'Клиент', 'Тур', 'Отель', 'Дата начала',
            'Дата окончания', 'Кол-во', 'Сумма', 'Статус'
        ])
        layout.addWidget(self.bookings_table)

        btn_layout = QHBoxLayout()

        new_btn = QPushButton('Новое бронирование')
        new_btn.clicked.connect(self.new_booking)
        btn_layout.addWidget(new_btn)

        edit_btn = QPushButton('Редактировать')
        edit_btn.clicked.connect(self.edit_booking)
        btn_layout.addWidget(edit_btn)

        calc_btn = QPushButton('Расчёт стоимости')
        calc_btn.clicked.connect(self.calculate_cost)
        btn_layout.addWidget(calc_btn)

        layout.addLayout(btn_layout)
        return widget

    def create_tours_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.tours_table = QTableWidget()
        self.tours_table.setColumnCount(6)
        self.tours_table.setHorizontalHeaderLabels([
            'ID', 'Название', 'Направление', 'Дней', 'Цена', 'Категория'
        ])
        layout.addWidget(self.tours_table)

        self.load_tours()
        return widget

    def create_customers_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.customers_table = QTableWidget()
        self.customers_table.setColumnCount(5)
        self.customers_table.setHorizontalHeaderLabels([
            'ID', 'ФИО', 'Телефон', 'Email', 'Дата регистрации'
        ])
        layout.addWidget(self.customers_table)

        self.load_customers()
        return widget

    def load_bookings(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT b.booking_id, c.full_name, t.tour_name, h.hotel_name,
                   b.travel_start_date, b.travel_end_date, b.number_of_travelers,
                   b.total_amount, b.status
            FROM bookings b
            JOIN customers c ON b.customer_id = c.customer_id
            JOIN tours t ON b.tour_id = t.tour_id
            JOIN hotels h ON b.hotel_id = h.hotel_id
            ORDER BY b.booking_date DESC
        ''')
        bookings = cursor.fetchall()
        conn.close()

        self.bookings_table.setRowCount(len(bookings))
        for i, booking in enumerate(bookings):
            for j, value in enumerate(booking):
                item = QTableWidgetItem(str(value) if value else '')
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.bookings_table.setItem(i, j, item)

    def filter_bookings(self):
        status = self.status_filter.currentText()
        date_from = self.date_from.date().toString('yyyy-MM-dd')
        date_to = self.date_to.date().toString('yyyy-MM-dd')

        conn = get_connection()
        cursor = conn.cursor()

        query = '''
            SELECT b.booking_id, c.full_name, t.tour_name, h.hotel_name,
                   b.travel_start_date, b.travel_end_date, b.number_of_travelers,
                   b.total_amount, b.status
            FROM bookings b
            JOIN customers c ON b.customer_id = c.customer_id
            JOIN tours t ON b.tour_id = t.tour_id
            JOIN hotels h ON b.hotel_id = h.hotel_id
            WHERE b.travel_start_date >= ? AND b.travel_start_date <= ?
        '''
        params = [date_from, date_to]

        if status != 'Все':
            query += ' AND b.status = ?'
            params.append(status)

        query += ' ORDER BY b.booking_date DESC'

        cursor.execute(query, params)
        bookings = cursor.fetchall()
        conn.close()

        self.bookings_table.setRowCount(len(bookings))
        for i, booking in enumerate(bookings):
            for j, value in enumerate(booking):
                item = QTableWidgetItem(str(value) if value else '')
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.bookings_table.setItem(i, j, item)

    def load_tours(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT tour_id, tour_name, destination, duration_days, price, category FROM tours')
        tours = cursor.fetchall()
        conn.close()

        self.tours_table.setRowCount(len(tours))
        for i, tour in enumerate(tours):
            for j, value in enumerate(tour):
                item = QTableWidgetItem(str(value) if value else '')
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.tours_table.setItem(i, j, item)

    def load_customers(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT customer_id, full_name, phone, email, registration_date FROM customers')
        customers = cursor.fetchall()
        conn.close()

        self.customers_table.setRowCount(len(customers))
        for i, customer in enumerate(customers):
            for j, value in enumerate(customer):
                item = QTableWidgetItem(str(value) if value else '')
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.customers_table.setItem(i, j, item)

    def new_booking(self):
        dialog = BookingDialog(self, self.employee)
        if dialog.exec_() == QDialog.Accepted:
            self.load_bookings()

    def edit_booking(self):
        row = self.bookings_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, 'Ошибка', 'Выберите бронирование')
            return

        booking_id = int(self.bookings_table.item(row, 0).text())
        dialog = BookingDialog(self, self.employee, booking_id)
        if dialog.exec_() == QDialog.Accepted:
            self.load_bookings()

    def calculate_cost(self):
        row = self.bookings_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, 'Ошибка', 'Выберите бронирование')
            return

        booking_id = int(self.bookings_table.item(row, 0).text())

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT b.*, t.price as tour_price, t.tour_name
            FROM bookings b
            JOIN tours t ON b.tour_id = t.tour_id
            WHERE b.booking_id = ?
        ''', (booking_id,))
        booking = dict(cursor.fetchone())

        cursor.execute('''
            SELECT s.service_name, s.price, bs.quantity
            FROM booking_services bs
            JOIN additional_services s ON bs.service_id = s.service_id
            WHERE bs.booking_id = ?
        ''', (booking_id,))
        services = cursor.fetchall()

        cursor.execute('SELECT * FROM flights WHERE booking_id = ?', (booking_id,))
        flight = cursor.fetchone()

        conn.close()

        tour_cost = booking['tour_price'] * booking['number_of_travelers']
        services_cost = sum(s['price'] * s['quantity'] for s in services)
        flight_cost = flight['ticket_price'] * booking['number_of_travelers'] if flight else 0
        total = tour_cost + services_cost + flight_cost

        msg = f'Расчёт стоимости бронирования #{booking_id}\n\n'
        msg += f'Тур "{booking["tour_name"]}":\n'
        msg += f'  {booking["tour_price"]} x {booking["number_of_travelers"]} чел. = {tour_cost} руб.\n\n'
        msg += 'Дополнительные услуги:\n'

        for s in services:
            msg += f'  {s["service_name"]}: {s["price"]} x {s["quantity"]} = {s["price"] * s["quantity"]} руб.\n'

        if flight:
            msg += f'\nАвиабилеты:\n'
            msg += f'  {flight["ticket_price"]} x {booking["number_of_travelers"]} чел. = {flight_cost} руб.\n'

        msg += f'\nИТОГО: {total} руб.'

        QMessageBox.information(self, 'Расчёт стоимости', msg)

class BookingDialog(QDialog):
    def __init__(self, parent, employee, booking_id=None):
        super().__init__(parent)
        self.employee = employee
        self.booking_id = booking_id
        self.total_amount = 0
        self.setWindowTitle('Редактирование бронирования' if booking_id else 'Новое бронирование')
        self.setMinimumSize(500, 600)
        self.setup_ui()
        if booking_id:
            self.load_booking()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        client_group = QGroupBox('Данные клиента')
        client_layout = QFormLayout(client_group)

        self.customer_combo = QComboBox()
        self.load_customers()
        client_layout.addRow('Клиент:', self.customer_combo)

        self.new_customer_name = QLineEdit()
        client_layout.addRow('Новый клиент (ФИО):', self.new_customer_name)

        self.new_customer_phone = QLineEdit()
        client_layout.addRow('Телефон:', self.new_customer_phone)

        self.new_customer_email = QLineEdit()
        client_layout.addRow('Email:', self.new_customer_email)

        layout.addWidget(client_group)

        tour_group = QGroupBox('Тур')
        tour_layout = QFormLayout(tour_group)

        self.tour_combo = QComboBox()
        self.load_tours()
        self.tour_combo.currentIndexChanged.connect(self.update_price)
        tour_layout.addRow('Тур:', self.tour_combo)

        self.hotel_combo = QComboBox()
        self.load_hotels()
        tour_layout.addRow('Отель:', self.hotel_combo)

        layout.addWidget(tour_group)

        details_group = QGroupBox('Детали поездки')
        details_layout = QFormLayout(details_group)

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(30))
        details_layout.addRow('Дата начала:', self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate().addDays(37))
        details_layout.addRow('Дата окончания:', self.end_date)

        self.travelers_spin = QSpinBox()
        self.travelers_spin.setRange(1, 20)
        self.travelers_spin.setValue(1)
        self.travelers_spin.valueChanged.connect(self.update_price)
        details_layout.addRow('Кол-во туристов:', self.travelers_spin)

        layout.addWidget(details_group)

        services_group = QGroupBox('Дополнительные услуги')
        services_layout = QVBoxLayout(services_group)

        self.services_table = QTableWidget()
        self.services_table.setColumnCount(3)
        self.services_table.setHorizontalHeaderLabels(['Услуга', 'Цена', 'Количество'])
        self.load_services()
        services_layout.addWidget(self.services_table)

        layout.addWidget(services_group)

        payment_group = QGroupBox('Оплата')
        payment_layout = QFormLayout(payment_group)

        self.payment_combo = QComboBox()
        self.payment_combo.addItems(['Карта', 'Наличные', 'Перевод'])
        payment_layout.addRow('Способ оплаты:', self.payment_combo)

        self.status_combo = QComboBox()
        self.status_combo.addItems(['Ожидает', 'Подтверждено', 'В работе', 'Выполнен', 'Отменён'])
        payment_layout.addRow('Статус:', self.status_combo)

        self.total_label = QLabel('0 руб.')
        payment_layout.addRow('Итого:', self.total_label)

        layout.addWidget(payment_group)

        btn_layout = QHBoxLayout()

        cancel_btn = QPushButton('Отмена')
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton('Сохранить')
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

        self.update_price()

    def load_customers(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT customer_id, full_name FROM customers')
        self.customers = cursor.fetchall()
        conn.close()

        self.customer_combo.addItem('-- Выберите клиента --', None)
        for c in self.customers:
            self.customer_combo.addItem(c['full_name'], c['customer_id'])

    def load_tours(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT tour_id, tour_name, price FROM tours')
        self.tours = cursor.fetchall()
        conn.close()

        for t in self.tours:
            self.tour_combo.addItem(f"{t['tour_name']} ({t['price']} руб.)", t['tour_id'])

    def load_hotels(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT hotel_id, hotel_name, stars FROM hotels')
        hotels = cursor.fetchall()
        conn.close()

        for h in hotels:
            self.hotel_combo.addItem(f"{h['hotel_name']} ({h['stars']} звезд)", h['hotel_id'])

    def load_services(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT service_id, service_name, price FROM additional_services')
        self.services = cursor.fetchall()
        conn.close()

        self.services_table.setRowCount(len(self.services))
        for i, s in enumerate(self.services):
            self.services_table.setItem(i, 0, QTableWidgetItem(s['service_name']))
            self.services_table.setItem(i, 1, QTableWidgetItem(str(s['price'])))

            spin = QSpinBox()
            spin.setRange(0, 10)
            spin.valueChanged.connect(self.update_price)
            self.services_table.setCellWidget(i, 2, spin)

    def load_booking(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM bookings WHERE booking_id = ?', (self.booking_id,))
        booking = dict(cursor.fetchone())

        for i in range(self.customer_combo.count()):
            if self.customer_combo.itemData(i) == booking['customer_id']:
                self.customer_combo.setCurrentIndex(i)
                break

        for i in range(self.tour_combo.count()):
            if self.tour_combo.itemData(i) == booking['tour_id']:
                self.tour_combo.setCurrentIndex(i)
                break

        for i in range(self.hotel_combo.count()):
            if self.hotel_combo.itemData(i) == booking['hotel_id']:
                self.hotel_combo.setCurrentIndex(i)
                break

        self.start_date.setDate(QDate.fromString(booking['travel_start_date'], 'yyyy-MM-dd'))
        self.end_date.setDate(QDate.fromString(booking['travel_end_date'], 'yyyy-MM-dd'))
        self.travelers_spin.setValue(booking['number_of_travelers'])

        idx = self.payment_combo.findText(booking['payment_method'])
        if idx >= 0:
            self.payment_combo.setCurrentIndex(idx)

        idx = self.status_combo.findText(booking['status'])
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)

        cursor.execute('SELECT service_id, quantity FROM booking_services WHERE booking_id = ?',
                       (self.booking_id,))
        booking_services = {s['service_id']: s['quantity'] for s in cursor.fetchall()}

        for i, s in enumerate(self.services):
            spin = self.services_table.cellWidget(i, 2)
            if s['service_id'] in booking_services:
                spin.setValue(booking_services[s['service_id']])

        conn.close()
        self.update_price()

    def update_price(self):
        tour_idx = self.tour_combo.currentIndex()
        if 0 <= tour_idx < len(self.tours):
            tour_price = self.tours[tour_idx]['price']
        else:
            tour_price = 0

        travelers = self.travelers_spin.value()
        total = tour_price * travelers

        for i in range(self.services_table.rowCount()):
            spin = self.services_table.cellWidget(i, 2)
            if spin:
                total += self.services[i]['price'] * spin.value()

        self.total_label.setText(f'{total} руб.')
        self.total_amount = total

    def save(self):
        customer_id = self.customer_combo.currentData()

        conn = get_connection()
        cursor = conn.cursor()

        if not customer_id and self.new_customer_name.text().strip():
            new_email = self.new_customer_email.text().strip()
            if new_email:
                cursor.execute('SELECT customer_id FROM customers WHERE email = ?', (new_email,))
                existing = cursor.fetchone()
                if existing:
                    QMessageBox.warning(self, 'Ошибка', 'Клиент с таким email уже существует в базе')
                    conn.close()
                    return
            from datetime import date
            cursor.execute('''
                INSERT INTO customers (full_name, phone, email, registration_date)
                VALUES (?, ?, ?, ?)
            ''', (
                self.new_customer_name.text().strip(),
                self.new_customer_phone.text().strip(),
                new_email,
                date.today().isoformat()
            ))
            customer_id = cursor.lastrowid

        if not customer_id:
            QMessageBox.warning(self, 'Ошибка', 'Выберите или создайте клиента')
            conn.close()
            return

        tour_id = self.tour_combo.currentData()
        hotel_id = self.hotel_combo.currentData()

        if self.booking_id:
            cursor.execute('''
                UPDATE bookings SET
                    customer_id = ?, tour_id = ?, hotel_id = ?,
                    travel_start_date = ?, travel_end_date = ?,
                    number_of_travelers = ?, total_amount = ?,
                    payment_method = ?, status = ?
                WHERE booking_id = ?
            ''', (
                customer_id, tour_id, hotel_id,
                self.start_date.date().toString('yyyy-MM-dd'),
                self.end_date.date().toString('yyyy-MM-dd'),
                self.travelers_spin.value(), self.total_amount,
                self.payment_combo.currentText(), self.status_combo.currentText(),
                self.booking_id
            ))

            cursor.execute('DELETE FROM booking_services WHERE booking_id = ?', (self.booking_id,))
            booking_id = self.booking_id
        else:
            cursor.execute('''
                INSERT INTO bookings (customer_id, tour_id, employee_id, hotel_id,
                    booking_date, travel_start_date, travel_end_date,
                    number_of_travelers, total_amount, payment_method, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                customer_id, tour_id, self.employee['employee_id'], hotel_id,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                self.start_date.date().toString('yyyy-MM-dd'),
                self.end_date.date().toString('yyyy-MM-dd'),
                self.travelers_spin.value(), self.total_amount,
                self.payment_combo.currentText(), self.status_combo.currentText()
            ))
            booking_id = cursor.lastrowid

        for i, s in enumerate(self.services):
            spin = self.services_table.cellWidget(i, 2)
            if spin and spin.value() > 0:
                cursor.execute('''
                    INSERT INTO booking_services (booking_id, service_id, quantity)
                    VALUES (?, ?, ?)
                ''', (booking_id, s['service_id'], spin.value()))

        conn.commit()
        conn.close()

        QMessageBox.information(self, 'Успех', 'Бронирование сохранено')
        self.accept()


class ClientWindow(QMainWindow):
    def __init__(self, customer):
        super().__init__()
        self.customer = customer
        self.selected_tour_price = 0
        self.selected_tour_days = 0
        self.total_amount = 0
        self.setWindowTitle(f'Личный кабинет - {customer["full_name"]}')
        self.setMinimumSize(900, 500)
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        layout.addWidget(QLabel(f'Клиент: {self.customer["full_name"]}'))

        tabs = QTabWidget()
        tabs.addTab(self.create_booking_tab(), 'Забронировать тур')
        tabs.addTab(self.create_status_tab(), 'Мои бронирования')
        tabs.addTab(self.create_history_tab(), 'История поездок')
        layout.addWidget(tabs)

    def create_booking_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel('Категория:'))
        self.category_filter = QComboBox()
        self.category_filter.addItems(['Все', 'Пляжный', 'Экскурсионный', 'Культурный', 'Активный'])
        self.category_filter.currentIndexChanged.connect(self.filter_tours)
        filter_layout.addWidget(self.category_filter)
        layout.addLayout(filter_layout)

        self.tours_table = QTableWidget()
        self.tours_table.setColumnCount(6)
        self.tours_table.setHorizontalHeaderLabels([
            'ID', 'Название', 'Направление', 'Дней', 'Цена', 'Категория'
        ])
        self.tours_table.itemSelectionChanged.connect(self.on_tour_selected)
        layout.addWidget(self.tours_table)

        details_layout = QFormLayout()

        self.selected_tour_label = QLabel('Не выбран')
        details_layout.addRow('Выбранный тур:', self.selected_tour_label)

        self.hotel_combo = QComboBox()
        self.load_hotels()
        details_layout.addRow('Отель:', self.hotel_combo)

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setMinimumDate(QDate.currentDate().addDays(1))
        self.start_date.setDate(QDate.currentDate().addDays(30))
        details_layout.addRow('Дата начала:', self.start_date)

        self.travelers_spin = QSpinBox()
        self.travelers_spin.setRange(1, 10)
        self.travelers_spin.setValue(1)
        self.travelers_spin.valueChanged.connect(self.update_total)
        details_layout.addRow('Количество туристов:', self.travelers_spin)

        services_layout = QHBoxLayout()
        self.transfer_check = QComboBox()
        self.transfer_check.addItems(['Без трансфера', 'Трансфер (+1500 руб.)'])
        self.transfer_check.currentIndexChanged.connect(self.update_total)
        services_layout.addWidget(self.transfer_check)

        self.insurance_check = QComboBox()
        self.insurance_check.addItems(['Без страховки', 'Страховка (+1000 руб.)'])
        self.insurance_check.currentIndexChanged.connect(self.update_total)
        services_layout.addWidget(self.insurance_check)

        details_layout.addRow('Услуги:', services_layout)

        self.total_label = QLabel('0 руб.')
        details_layout.addRow('Итого:', self.total_label)

        layout.addLayout(details_layout)

        book_btn = QPushButton('Забронировать')
        book_btn.clicked.connect(self.make_booking)
        layout.addWidget(book_btn)

        self.load_tours()

        return widget

    def create_status_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        refresh_btn = QPushButton('Обновить')
        refresh_btn.clicked.connect(self.load_my_bookings)
        layout.addWidget(refresh_btn)

        self.my_bookings_table = QTableWidget()
        self.my_bookings_table.setColumnCount(7)
        self.my_bookings_table.setHorizontalHeaderLabels([
            'ID', 'Тур', 'Отель', 'Дата начала', 'Дата окончания', 'Сумма', 'Статус'
        ])
        layout.addWidget(self.my_bookings_table)

        self.load_my_bookings()

        return widget

    def create_history_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel('История ваших поездок'))

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(8)
        self.history_table.setHorizontalHeaderLabels([
            'ID', 'Тур', 'Направление', 'Отель', 'Даты', 'Туристов', 'Сумма', 'Статус'
        ])
        layout.addWidget(self.history_table)

        self.load_history()

        return widget

    def load_tours(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT tour_id, tour_name, destination, duration_days, price, category FROM tours')
        self.tours = cursor.fetchall()
        conn.close()

        self.display_tours(self.tours)

    def filter_tours(self):
        category = self.category_filter.currentText()
        if category == 'Все':
            self.display_tours(self.tours)
        else:
            filtered = [t for t in self.tours if t['category'] == category]
            self.display_tours(filtered)

    def display_tours(self, tours):
        self.tours_table.setRowCount(len(tours))
        for i, tour in enumerate(tours):
            for j, key in enumerate(['tour_id', 'tour_name', 'destination', 'duration_days', 'price', 'category']):
                item = QTableWidgetItem(str(tour[key]) if tour[key] else '')
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.tours_table.setItem(i, j, item)

    def load_hotels(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT hotel_id, hotel_name, stars FROM hotels')
        self.hotels = cursor.fetchall()
        conn.close()

        for h in self.hotels:
            self.hotel_combo.addItem(f"{h['hotel_name']} ({h['stars']} звезд)", h['hotel_id'])

    def on_tour_selected(self):
        row = self.tours_table.currentRow()
        if row >= 0:
            tour_name = self.tours_table.item(row, 1).text()
            price = self.tours_table.item(row, 4).text()
            days = self.tours_table.item(row, 3).text()
            self.selected_tour_label.setText(f'{tour_name} - {price} руб. ({days} дней)')
            self.selected_tour_price = float(price)
            self.selected_tour_days = int(days)
            self.update_total()
        else:
            self.selected_tour_label.setText('Не выбран')
            self.selected_tour_price = 0

    def update_total(self):
        total = self.selected_tour_price * self.travelers_spin.value()

        if self.transfer_check.currentIndex() == 1:
            total += 1500 * self.travelers_spin.value()

        if self.insurance_check.currentIndex() == 1:
            total += 1000 * self.travelers_spin.value()

        self.total_label.setText(f'{total} руб.')
        self.total_amount = total

    def make_booking(self):
        row = self.tours_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, 'Ошибка', 'Выберите тур')
            return

        tour_id = int(self.tours_table.item(row, 0).text())
        hotel_id = self.hotel_combo.currentData()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT employee_id FROM employees LIMIT 1')
        employee = cursor.fetchone()

        start_date = self.start_date.date().toString('yyyy-MM-dd')
        end_date = self.start_date.date().addDays(self.selected_tour_days).toString('yyyy-MM-dd')

        cursor.execute('''
            INSERT INTO bookings (customer_id, tour_id, employee_id, hotel_id,
                booking_date, travel_start_date, travel_end_date,
                number_of_travelers, total_amount, payment_method, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.customer['customer_id'], tour_id, employee['employee_id'], hotel_id,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            start_date, end_date,
            self.travelers_spin.value(), self.total_amount,
            'Карта', 'Ожидает'
        ))

        booking_id = cursor.lastrowid

        if self.transfer_check.currentIndex() == 1:
            cursor.execute('''
                INSERT INTO booking_services (booking_id, service_id, quantity)
                VALUES (?, 1, ?)
            ''', (booking_id, self.travelers_spin.value()))

        if self.insurance_check.currentIndex() == 1:
            cursor.execute('''
                INSERT INTO booking_services (booking_id, service_id, quantity)
                VALUES (?, 3, ?)
            ''', (booking_id, self.travelers_spin.value()))

        conn.commit()
        conn.close()

        QMessageBox.information(self, 'Успех',
                                f'Бронирование #{booking_id} создано!\n\n'
                                f'Тур: {self.tours_table.item(row, 1).text()}\n'
                                f'Даты: {start_date} - {end_date}\n'
                                f'Сумма: {self.total_amount} руб.\n\n'
                                'Статус: Ожидает подтверждения')

        self.load_my_bookings()

    def load_my_bookings(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT b.booking_id, t.tour_name, h.hotel_name,
                   b.travel_start_date, b.travel_end_date, b.total_amount, b.status
            FROM bookings b
            JOIN tours t ON b.tour_id = t.tour_id
            JOIN hotels h ON b.hotel_id = h.hotel_id
            WHERE b.customer_id = ?
            ORDER BY b.booking_date DESC
        ''', (self.customer['customer_id'],))
        bookings = cursor.fetchall()
        conn.close()

        self.my_bookings_table.setRowCount(len(bookings))
        for i, booking in enumerate(bookings):
            for j, value in enumerate(booking):
                item = QTableWidgetItem(str(value) if value else '')
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.my_bookings_table.setItem(i, j, item)

    def load_history(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT b.booking_id, t.tour_name, t.destination, h.hotel_name,
                   b.travel_start_date || ' - ' || b.travel_end_date as dates,
                   b.number_of_travelers, b.total_amount, b.status
            FROM bookings b
            JOIN tours t ON b.tour_id = t.tour_id
            JOIN hotels h ON b.hotel_id = h.hotel_id
            WHERE b.customer_id = ?
            ORDER BY b.travel_start_date DESC
        ''', (self.customer['customer_id'],))
        bookings = cursor.fetchall()
        conn.close()

        self.history_table.setRowCount(len(bookings))
        for i, booking in enumerate(bookings):
            for j, value in enumerate(booking):
                item = QTableWidgetItem(str(value) if value else '')
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.history_table.setItem(i, j, item)


if __name__ == '__main__':
    init_db()
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())