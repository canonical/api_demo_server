import logging
import os

from fastapi import FastAPI
from fastapi import Form
from starlette.responses import RedirectResponse
from starlette.responses import Response
from starlette_exporter import PrometheusMiddleware
from starlette_exporter import handle_metrics

from . import __version__
from .database import DataBase


def define_logger():
    """Define logger to output to the file and to STDOUT."""
    log = logging.getLogger("api-demo-server")
    log.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        fmt="%(asctime)s (%(levelname)s) %(message)s", datefmt="%d.%m.%Y %H:%M:%S"
    )
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)

    log_file = os.environ.get("DEMO_SERVER_LOGFILE", "demo_server.log")
    file_handler = logging.FileHandler(filename=log_file)
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)
    return log


logger = define_logger()

PSQL_DB = DataBase()

app = FastAPI()
app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", handle_metrics)


async def catch_exceptions_middleware(request, call_next):
    """Middleware to catch all exceptions.

    All exceptions that were raised during handling of the request will be caught
    and logged with the traceback, then 500 response will be returned to the user.
    """
    try:
        return await call_next(request)
    except Exception:
        logger.exception("Exception occurred")
        return Response("Internal server error", status_code=500)


app.middleware("http")(catch_exceptions_middleware)


@app.get("/")
def root():
    """Just redirect from root path to Swagger UI"""
    return RedirectResponse(url="/docs")


@app.post("/dropdb")
def drop_database():
    PSQL_DB.drop_db("names_db")


@app.post("/createtable")
def create_table():
    PSQL_DB.create_table(db_name="names_db", table_name="names")


@app.post("/addname/")
def add_name(username: str = Form()):
    PSQL_DB.add_name(username, db_name="names_db", table_name="names")
    return {"username": username}


@app.get("/names")
def get_all_names():
    return {"names": dict(PSQL_DB.all_names(db_name="names_db", table_name="names"))}


@app.get("/error")
def cause_error():
    return 1 / 0


@app.get("/version")
def get_version():
    return {"version": __version__}
