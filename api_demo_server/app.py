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


@app.post("/createdb")
def create_db():
    PSQL_DB.create_db("names_db")

@app.post("/dropdb")
def drop_db():
    PSQL_DB.drop_db("names_db")


@app.post("/login/")
def login(username: str = Form()):
    return {"username": username}
