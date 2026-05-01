import mysql.connector
from mysql.connector import Error

class DatabaseManager:
    def __init__(self, host, user, password, database=None):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            return self.connection
        except Error as e:
            print(f"Error while connecting to MySQL: {e}")
            return None

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()

    def execute_query(self, query, params=None):
        """Used for INSERT, UPDATE, DELETE requests"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Error executing query: {e}")
            return None
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()

    def fetch_all(self, query, params=None):
        """Used for SELECT requests returning multiple rows"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            return result
        except Error as e:
            print(f"Error fetching data: {e}")
            return []
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()

    def fetch_one(self, query, params=None):
        """Used for SELECT requests returning a single row"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            result = cursor.fetchone()
            return result
        except Error as e:
            print(f"Error fetching data: {e}")
            return None
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()

    def setup_database_and_tables(self):
        """Initialize database and schema if they don't exist"""
        try:
            # Connect without DB first to create it
            temp_conn = mysql.connector.connect(
                host=self.host, user=self.user, password=self.password
            )
            cursor = temp_conn.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS cooked_db")
            temp_conn.commit()
            cursor.close()
            temp_conn.close()

            # Now connect to specific DB
            self.database = 'cooked_db'
            self.connect()
            
            # Users Table
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # User Recipes Table (For Upload Portal)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS user_recipes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    ingredients TEXT NOT NULL,
                    instructions TEXT NOT NULL,
                    image_filename VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # Favorite API Recipes Table
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS favorite_meals (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    api_recipe_id INT NOT NULL,
                    recipe_title VARCHAR(255) NOT NULL,
                    recipe_image VARCHAR(512),
                    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # Meal Notes/History
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS meal_notes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    notes TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            print("Database setup complete.")
        except Error as e:
            print(f"Database setup failed: {e}")

if __name__ == "__main__":
    db = DatabaseManager('localhost', 'root', 'Omkar#140706')
    db.setup_database_and_tables()
