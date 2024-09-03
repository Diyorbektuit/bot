import sqlite3


class Database:
    def __init__(self, path_to_db="main.db"):
        self.path_to_db = path_to_db
        self.create_table_users()
        self.create_table_referrals()

    @property
    def connection(self):
        return sqlite3.connect(self.path_to_db)

    def execute(self, sql: str, parameters: tuple = None, fetchone=False, fetchall=False, commit=False):
        if parameters is None:
            parameters = ()
        connection = self.connection
        connection.set_trace_callback(logger)
        cursor = connection.cursor()
        data = None
        try:
            cursor.execute(sql, parameters)
            if commit:
                connection.commit()
            if fetchall:
                data = cursor.fetchall()
            if fetchone:
                data = cursor.fetchone()
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
        finally:
            connection.close()
        return data

    def create_table_users(self):
        sql = """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            points INTEGER DEFAULT 0,
            referrer_id INTEGER,
            referral_count INTEGER DEFAULT 0
        );
        """
        self.execute(sql, commit=True)

    def create_table_referrals(self):
        sql = """
        CREATE TABLE IF NOT EXISTS referrals (
            referrer_id INTEGER,
            referred_id INTEGER,
            FOREIGN KEY (referrer_id) REFERENCES users(user_id),
            FOREIGN KEY (referred_id) REFERENCES users(user_id)
        );
        """
        self.execute(sql, commit=True)

    @staticmethod
    def format_args(sql, parameters: dict):
        sql += " AND ".join([
            f"{item} = ?" for item in parameters
        ])
        return sql, tuple(parameters.values())

    def add_user(self, user_id, username, referrer_id=None):
        sql = "INSERT INTO users (user_id, username, referrer_id) VALUES (?, ?, ?)"
        self.execute(sql, parameters=(user_id, username, referrer_id), commit=True)

    def add_referral(self, referrer_id: int, referred_id: int):
        sql = """
        INSERT INTO Referrals (referrer_id, referred_id)
        VALUES (?, ?);
        """
        self.execute(sql, parameters=(referrer_id, referred_id), commit=True)

        # Update referral count and points
        self.increment_referral_count(referrer_id)

    def increment_referral_count(self, referrer_id: int):
        sql = """
        UPDATE users SET referral_count = referral_count + 1
        WHERE user_id = ?;
        """
        self.execute(sql, parameters=(referrer_id,), commit=True)

    def add_points(self, user_id, points):
        sql = "UPDATE users SET points = points + ? WHERE user_id = ?"
        cursor = self.execute(sql, parameters=(points, user_id), commit=True)

    def get_user_points(self, user_id: int):
        sql = "SELECT points FROM users WHERE user_id = ?;"
        result = self.execute(sql, parameters=(user_id,), fetchone=True)
        return result[0] if result else 0

    def get_username(self, user_id: int):
        sql = "SELECT username FROM users WHERE user_id = ?;"
        result = self.execute(sql, parameters=(user_id,), fetchone=True)
        return result[0] if result else None

    def select_all_users(self):
        sql = "SELECT * FROM users;"
        return self.execute(sql, fetchall=True)

    def select_user(self, **kwargs):
        sql = "SELECT * FROM users WHERE "
        sql, parameters = self.format_args(sql, kwargs)
        return self.execute(sql, parameters=parameters, fetchone=True)

    def count_users(self):
        return self.execute("SELECT COUNT(*) FROM users;", fetchone=True)[0]

    def delete_users(self):
        self.execute("DELETE FROM users WHERE TRUE;", commit=True)

    def all_users_id(self):
        return self.execute("SELECT user_id FROM users;", fetchall=True)

    def user_exists(self, user_id: int):
        sql = "SELECT COUNT(*) FROM users WHERE user_id = ?;"
        result = self.execute(sql, parameters=(user_id,), fetchone=True)
        return result[0] > 0

    def add_referral_link_column(self):
        sql = """
        ALTER TABLE users ADD COLUMN referral_link TEXT;
        """
        self.execute(sql, commit=True)

    def recreate_table_users(self):
        self.execute("DROP TABLE IF EXISTS users;", commit=True)
        self.create_table_users()

    def add_referrer_id_column(self):
        sql = """
        ALTER TABLE users ADD COLUMN referrer_id INTEGER;
        """
        try:
            self.execute(sql, commit=True)
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e):
                print("Referrer ID column already exists.")

    def get_top_users_by_points(self, top_n=10):
        sql = """
        SELECT user_id, username, SUM(points) AS total_points
        FROM users
        GROUP BY user_id, username
        ORDER BY total_points DESC
        LIMIT ?;
        """
        return self.execute(sql, parameters=(top_n,), fetchall=True)


def logger(statement):
    print(f"""
_____________________________________________________        
Executing: 
{statement}
_____________________________________________________
""")
