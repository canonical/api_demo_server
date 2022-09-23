from starlette_exporter import PrometheusMiddleware, handle_metrics
from fastapi import FastAPI, Form

from api_demo_server.database import DataBase

PSQL_DB = DataBase()

app = FastAPI()
app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", handle_metrics)


@app.get("/")
def root():
    return {"message": "Hello World"}


@app.post("/connectdb")
def connect_to_database():
    PSQL_DB.create_db("names_db")

@app.post("/dropdb")
def drop_db():
    PSQL_DB.drop_db("names_db")

@app.post("/createtable")
def create_table():
    PSQL_DB.create_table()


@app.post("/addname/")
def name(username: str = Form()):
    PSQL_DB.add_name(username)
    return {"username": username}

@app.get("/names")
def get_all_names():


    return {"names": dict(PSQL_DB.all_names)}
