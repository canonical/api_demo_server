from fastapi import FastAPI, Form
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


class DataBase:
    def __init__(self):
        self.conn = None

    @property
    def connected(self):
        return self.conn is not None

    @property
    def cursor(self):
        if not self.connected:
            self.connect_to_postgres()

        return self.conn.cursor()

    def db_exists(self, name):
        self.cursor.execute("select exists(select * from pg_database where datname=%s)", (name,))
        return bool(self.cursor.fetchone()[0])

    def connect_to_postgres(self):
        if not self.connected:
            self.conn = psycopg2.connect(user="postgres", password="mysecretpassword", host="127.0.0.1", port="5432")
            self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            print("connected successfully")

    def create_db(self, db_name):
        if not self.db_exists(db_name):
            # Prevent sql injection attack by using sql module instead of string concat
            self.cursor.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(db_name))
            )

    def drop_db(self, db_name):
        # Prevent sql injection attack by using sql module instead of string concat
        self.cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(
            sql.Identifier(db_name))
        )


PSQL_DB = DataBase()

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Hello World"}


@app.post("/createdb")
def create_db():
    PSQL_DB.create_db("names_db")


@app.post("/login/")
def login(username: str = Form()):
    return {"username": username + "_boy"}
