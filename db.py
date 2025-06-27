import sqlite3
from datetime import datetime

class Database():
    def __init__(self, db_path: str = "user_descks.db") -> None:
        self.conn = sqlite3.connect(db_path)
    
    def add_user(self, user_id: int, username: str, first_name: str):
        """Добавляет нового юзера в таблицу"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("INSERT INTO user_list (user_id, username, first_name, cnt_desk) VALUES (?, ?, ?, ?)", (user_id, username, first_name, 0))
        except sqlite3.IntegrityError:
            pass # Пользователь уже добавлен в БД
        self.conn.commit()

    def take_users_ids(self) -> list:
        """Возвращает список всех юзеров"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id FROM user_list")
        user_ids = cursor.fetchall()
        for i in range(len(user_ids)):
            user_ids[i] = user_ids[i][0]
        return user_ids
    
    def take_user_cnt_desks(self, user_id: int) -> int:
        cursor = self.conn.cursor()
        cursor.execute("SELECT cnt_desk FROM user_list WHERE user_id = ?", (user_id,))
        cnt_desks = cursor.fetchall()
        return cnt_desks[0][0]
    
    def create_desk(self, user_id: int):
        """Создаёт доску для определённого пользователя"""
        cursor = self.conn.cursor()

        # Обновляем количество доск юзера
        cursor.execute("SELECT cnt_desk FROM user_list WHERE user_id = ?", (user_id,))
        user_desk_cnt = int(cursor.fetchall()[0][0]) + 1
        cursor.execute("UPDATE user_list SET cnt_desk = ? WHERE user_id = ?", (user_desk_cnt, user_id))

        # Создаём новую таблицу под юзера
        cursor.execute(
            f'''
                CREATE TABLE IF NOT EXISTS Desk_{user_id}_{user_desk_cnt} (
                id_of_task INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                date TEXT,
                state BLOB NOT NULL
                )
            '''
        )

        """
        Структура доски:
        Доска содержит бесконечное кол-во строчек - это таски. Для каждого таска есть 5 столбиков: индекс(а-ля порядковый номер), название самого таска, описание(может быть пустым), 
        дата выполнения задача(дедлайн, может быть пустым, исходя из этой даты будут настраиваться напоминания), состояние таска(выполнен/невыполнен(1/0))
        """
        self.conn.commit()
    
    def add_task_to_desk(self, user_id: int, number_of_desk: int, task_name: str, **other):
        """Добавление задачи в определённую доску
        
        Дополнительные аргументы:

        task_description - описание таска: str
        date_time - время дедлайна: str

        """
        cursor = self.conn.cursor()
        
        # Проверка, есть ли вообще доски у юзера
        cursor.execute("SELECT cnt_desk FROM user_list WHERE user_id = ?", (user_id,))
        user_desk_cnt = int(cursor.fetchall()[0][0])
        if user_desk_cnt == 0: 
            raise ValueError(f"У пользователя {user_id} нет активных доск")

        try:
            if len(other) == 1:
                task_description = other['task_description']; date_time = "-"
            elif len(other) == 2:
                task_description = other['task_description']; date_time = other['date_time']
                date_time = datetime.strptime(date_time, "%d.%m.%Y").date()

                # Проверка на то, что дата валидна и человек не пытается запланировать дело на день, который уже прошёл
                if date_time <= datetime.now().date():
                    raise ValueError("Дата планирования уже прошла")
            else:
                task_description = "-"; date_time = "-"

            cursor.execute(f"INSERT INTO Desk_{user_id}_{number_of_desk} (name, description, date, state) VALUES (?, ?, ?, ?)", (task_name, task_description, date_time, 0))
        except sqlite3.IntegrityError:
            pass # Задача с таким названием уже добавлена
        self.conn.commit()
    
        
    

# db = Database()
# db.add_user(675244968, "teaking66", "Сёма")

# db.add_task_to_desk(675244968, 1, "Помыть ручки")
