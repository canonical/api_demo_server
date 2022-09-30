import logging
import os
from typing import List
from typing import Tuple

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# set logger to be configurable from external
logger = logging.getLogger("api-demo-server")

DB_HOST = os.environ.get("DEMO_SERVER_DB_HOST", "127.0.0.1")
DB_PORT = os.environ.get("DEMO_SERVER_DB_PORT", "5432")

DB_USER = os.environ.get("DEMO_SERVER_DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DEMO_SERVER_DB_PASSWORD", "mysecretpassword")


class DataBase:
    def __init__(self) -> None:
        self.db_conn = None
        self.db_cursor = None

    def connect_to_db(self, db_name: str) -> None:
        """Connects to the database, creates if it does not exist."""
        try:
            self.db_conn = psycopg2.connect(
                dbname=db_name,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT,
            )
            self.db_conn.autocommit = True
        except psycopg2.OperationalError as exc:
            if f'database "{db_name}" does not exist' in str(exc):
                logger.error(f"Database {db_name} does not exist. Trying to create.")
                self.create_db(db_name)
                self.connect_to_db(db_name)
            else:
                raise
        self.db_cursor = self.db_conn.cursor()

        logger.info(f"Successfully connected to database: {db_name}")

    @staticmethod
    def create_db(db_name: str) -> None:
        """Creates database if it does not exist.

        Will work only for "postgres" user.
        """
        conn = psycopg2.connect(user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        # Prevent sql injection attack by using sql module instead of string concat
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
        logger.info(f"Database '{db_name}' was created.")

    def _table_exists(self, table_name: str) -> bool:
        """Checks if the table already exists."""
        assert self.db_cursor
        self.db_cursor.execute(
            "SELECT EXISTS (SELECT relname FROM pg_class WHERE relname=%s);", (table_name,)
        )
        if self.db_cursor.fetchone()[0]:
            logger.info(f"Table '{table_name}' already exists.")
            return True
        return False

    def delete_table(self, db_name: str, table_name: str) -> None:
        """Delete a table in database `db_name`"""
        if self.db_cursor is None:
            self.connect_to_db(db_name)

        self.db_cursor.execute(
            sql.SQL("DROP TABLE IF EXISTS {};").format(sql.Identifier(table_name))
        )
        logger.info(f"Table '{table_name}' is deleted")

    def create_table(self, db_name: str, table_name: str) -> None:
        """Create a table in database `db_name` if it doesn't already exist."""
        if self.db_cursor is None:
            self.connect_to_db(db_name)
        if self._table_exists(table_name):
            return
        self.db_cursor.execute(
            sql.SQL("CREATE TABLE {} (id serial PRIMARY KEY, data varchar);").format(
                sql.Identifier(table_name)
            )
        )
        self.db_conn.commit()
        logger.info(f"Table '{table_name}' was created in DB '{db_name}'")

    def add_name(self, name: str, db_name: str, table_name: str) -> None:
        self.create_table(db_name, table_name)

        self.db_cursor.execute(
            sql.SQL("INSERT INTO {} (data) VALUES (%s);").format(sql.Identifier(table_name)),
            (name,),
        )

    def all_names(self, db_name: str, table_name: str) -> List[Tuple[int, str]]:
        self.create_table(db_name, table_name)
        self.db_cursor.execute(sql.SQL("SELECT * FROM {}").format(sql.Identifier(table_name)))
        return self.db_cursor.fetchall()
