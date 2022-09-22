import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


class DataBase:
    def __init__(self):
        self.conn = None
        self._cursor = None

    @property
    def connected(self):
        return self.conn is not None

    @property
    def cursor(self):
        if not self.connected:
            self.connect_to_postgres()

        if self._cursor is None:
            self._cursor = self.conn.cursor()

        return self._cursor

    @property
    def new_cursor(self):
        self._cursor = None
        return self.cursor

    def db_exists(self, name):
        self.cursor.execute("select exists(select * from pg_database where datname=%s)", (name,))
        if self.cursor.fetchone()[0]:
            print(f"Database {name} already exists.")
            return True
        return False

    def connect_to_postgres(self):
        if not self.connected:
            self.conn = psycopg2.connect(user="postgres", password="mysecretpassword", host="127.0.0.1", port="5432")
            self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            print("connected successfully")

    def connect_to_db(self, db_name):
        self.conn = psycopg2.connect(dbname=db_name ,user="postgres", password="mysecretpassword", host="127.0.0.1", port="5432")
        return self.new_cursor

    def create_db(self, db_name):
        if not self.db_exists(db_name):
            # Prevent sql injection attack by using sql module instead of string concat
            self.cursor.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(db_name))
            )
        self.connect_to_db(db_name)

    def drop_db(self, db_name):
        # Prevent sql injection attack by using sql module instead of string concat
        self.cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(
            sql.Identifier(db_name))
        )
        if not self.db_exists(db_name):
            print(f"Database {db_name} was successfully removed")

    def create_table(self):
        self.cursor.execute("CREATE TABLE names (id serial PRIMARY KEY, data varchar);")

    def add_name(self, name):
        self.cursor.execute("INSERT INTO names (data) VALUES (%s)", (name,))

    @property
    def all_names(self):
        self.cursor.execute("SELECT * FROM names;")
        return self.cursor.fetchall()

