from fastapi import FastAPI, Form
import psycopg2
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT # <-- ADD THIS LINE






def connect_to_db():
    conn = psycopg2.connect(user = "postgres", password = "mysecretpassword", host = "127.0.0.1", port = "5432")
    print("connected successfully")
    return conn

def create_db(conn, db_name):
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)  # <-- ADD THIS LINE

    cur = conn.cursor()

    # cur.execute("SELECT datname FROM pg_database;")

    # list_database = cur.fetchall()

    # cur.execute("select exists(select * from information_schema.tables where table_name=%s)", (db_name,))
    cur.execute("select exists(select * from pg_database where datname=%s)", (db_name,))
    if not cur.fetchone()[0]:

        # Use the psycopg2.sql module instead of string concatenation
        # in order to avoid sql injection attacs.
        cur.execute(sql.SQL("CREATE DATABASE {}").format(
            sql.Identifier(db_name))
        )
    else:
        cur.execute(sql.SQL("DROP DATABASE {}").format(
            sql.Identifier(db_name))
        )
        print("Database dropped")




app = FastAPI()


@app.get("/")
def root():
    return {"message": "Hello World"}

@app.post("/login/")
def login(username: str = Form()):
    conn = connect_to_db()
    create_db(conn, "names_db")
    return {"username": username + "_boy"}
