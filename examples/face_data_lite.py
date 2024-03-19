import sqlite3


class FaceData:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.check_table()

    def check_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS user (
                                        student_id TEXT PRIMARY KEY,
                                        username TEXT
                                        )''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS user_face (
                                               face_id TEXT PRIMARY KEY,
                                               student_id TEXT,
                                               face_data TEXT,
                                               img TEXT
                                               )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS sign_log (
                                       student_id TEXT PRIMARY KEY,
                                       sign_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                       sign_img TEXT
                                       )''')
        self.conn.commit()

    def list_all_user(self):
        # 执行 SQL 查询语句
        self.cursor.execute("SELECT * FROM user")
        # 获取所有结果
        rows = self.cursor.fetchall()
        return rows
    def list_all_user_face(self):
        # 执行 SQL 查询语句
        self.cursor.execute("SELECT * FROM user_face")
        # 获取所有结果
        rows = self.cursor.fetchall()
        return rows
    def create_user(self, student_id: str, username: str):
        self.cursor.execute('''INSERT INTO user (student_id, username) VALUES (?, ?)''',
                            (student_id, username))
        self.conn.commit()
    def add_face(self,face_id:str,student_id:str,face_data,img_path):
        self.cursor.execute('''INSERT INTO user_face (face_id,student_id, face_data,img) VALUES (?, ?, ?, ?)''',
                            (face_id,student_id,face_data, img_path))
        self.conn.commit()


    def exists_user(self, student_id: str) -> bool:
        self.cursor.execute('''SELECT * FROM user WHERE student_id = ?''', (student_id,))
        user = self.cursor.fetchone()
        return user is not None

    def create_table(self, table_name, columns):
        columns_str = ', '.join(columns)
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_str})")
        self.conn.commit()

    def insert_record(self, table_name, data):
        placeholders = ', '.join(['?' for _ in data])
        self.cursor.execute(f"INSERT INTO {table_name} VALUES ({placeholders})", tuple(data))
        self.conn.commit()

    def update_record(self, table_name, new_data, condition):
        update_str = ', '.join([f"{key} = ?" for key in new_data])
        condition_str = ' AND '.join([f"{key} = ?" for key in condition.keys()])
        values = list(new_data.values()) + list(condition.values())
        self.cursor.execute(f"UPDATE {table_name} SET {update_str} WHERE {condition_str}", tuple(values))
        self.conn.commit()

    def delete_record(self, table_name, condition):
        condition_str = ' AND '.join([f"{key} = ?" for key in condition.keys()])
        self.cursor.execute(f"DELETE FROM {table_name} WHERE {condition_str}", tuple(condition.values()))
        self.conn.commit()

    def select_records(self, table_name, condition=None):
        if condition:
            condition_str = ' AND '.join([f"{key} = ?" for key in condition.keys()])
            self.cursor.execute(f"SELECT * FROM {table_name} WHERE {condition_str}", tuple(condition.values()))
        else:
            self.cursor.execute(f"SELECT * FROM {table_name}")
        return self.cursor.fetchall()

    def __del__(self):
        self.conn.close()
