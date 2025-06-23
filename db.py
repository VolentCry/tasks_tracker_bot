import sqlite3

class Database():
    def __init__(self, db_path: str = "user_descks.db") -> None:
        self.conn = sqlite3.connect(db_path)
    
    def add_user(self, user_id: int, username: str):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO user_list (user_id, username, cnt_desk) VALUES (?, ?, ?)", (user_id, username, 0))
        self.conn.commit()

    def take_users_ids(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id FROM Users")
        user_ids = cursor.fetchall()
        return user_ids

    