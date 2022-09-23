import logging
import os

from api_demo_server.database import DataBase
from fastapi import FastAPI
from fastapi import Form
from starlette.responses import Response
from starlette_exporter import PrometheusMiddleware
from starlette_exporter import handle_metrics

log_file = os.environ.get("DEMO_SERVER_LOGFILE", "demo_server.log")

logger = logging.getLogger("api-demo-server")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    fmt="%(asctime)s (%(levelname)s) %(message)s", datefmt="%d.%m.%Y %H:%M:%S"
)

file_handler = logging.FileHandler(filename=log_file)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


PSQL_DB = DataBase()

app = FastAPI()
app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", handle_metrics)


async def catch_exceptions_middleware(request, call_next):
    try:
        return await call_next(request)
    except Exception:
        logger.exception("Exception occurred")
        return Response("Internal server error", status_code=500)


app.middleware("http")(catch_exceptions_middleware)


@app.get("/")
def root():
    return {"message": "Demo API server with prometheus endpoint"}


@app.post("/connectdb")
def connect_to_database():
    PSQL_DB.create_db("names_db")


@app.post("/dropdb")
def drop_database():
    PSQL_DB.drop_db("names_db")


@app.post("/createtable")
def create_table():
    PSQL_DB.create_table()


@app.post("/addname/")
def add_name(username: str = Form()):
    PSQL_DB.add_name(username)
    return {"username": username}


@app.get("/names")
def get_all_names():

    return {"names": dict(PSQL_DB.all_names)}


@app.get("/error")
def cause_error():
    return 1 / 0
