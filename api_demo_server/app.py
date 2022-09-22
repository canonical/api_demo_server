from starlette_exporter import PrometheusMiddleware, handle_metrics
from fastapi import FastAPI, Form
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
        if not self.db_exists(db_name):
            print(f"Database {db_name} was successfully removed")


PSQL_DB = DataBase()

app = FastAPI()
app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", handle_metrics)


@app.get("/")
def root():
    return {"message": "Hello World"}


@app.post("/createdb")
def create_db():
    PSQL_DB.create_db("names_db")

@app.post("/dropdb")
def drop_db():
    PSQL_DB.drop_db("names_db")


@app.post("/login/")
def login(username: str = Form()):
    return {"username": username}
