"""Connection pool management — wraps pymysql with Database protocol."""

from typing import Dict

import pymysql
from dbutils.pooled_db import PooledDB

from sync.abstractions import Database, Cursor


class PyMySQLCursor(Cursor):
    """Wraps pymysql cursor to satisfy Cursor protocol."""

    def __init__(self, raw_cursor):
        self._cur = raw_cursor

    def execute(self, sql, params=None):
        self._cur.execute(sql, params)
        return self

    def executemany(self, sql, params_list):
        self._cur.executemany(sql, params_list)

    def fetchall(self):
        return self._cur.fetchall()

    def fetchone(self):
        return self._cur.fetchone()

    def close(self):
        self._cur.close()


class PyMySQLDatabase(Database):
    """Wraps pymysql connection to satisfy Database protocol."""

    def __init__(self, raw_conn):
        self._conn = raw_conn

    def cursor(self):
        return PyMySQLCursor(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


class PooledDatabaseFactory:
    """Creates and caches connection pools by key."""

    def __init__(self):
        self._pools: Dict[str, PooledDB] = {}

    def get_or_create(self, key: str, config: dict, pool_size: int = 5) -> Database:
        if key not in self._pools:
            self._pools[key] = PooledDB(
                creator=pymysql,
                maxconnections=pool_size,
                blocking=True,
                host=config["host"],
                port=config["port"],
                database=config["database"],
                user=config["user"],
                password=config["password"],
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False,
            )
        return PyMySQLDatabase(self._pools[key].connection())

    def close_all(self):
        for pool in self._pools.values():
            pool.close()
        self._pools.clear()
