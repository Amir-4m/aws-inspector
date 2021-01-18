#!/usr/bin/env python3

import requests

from pathlib import Path

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, text

from core.consts import AWS_PROXY_API, AWS_PROXY_API_TOKEN
from core.logger import Logger

logger = Logger()


class DBService(object):
    BASE_DIR = Path(__file__).resolve().parent.parent

    def __init__(self, db_name):
        self.engine = create_engine(f'sqlite:///{self.BASE_DIR}/{db_name}.db')
        self.meta = MetaData()
        self.table_name = 'Servers'
        self.conn = self.engine.connect()
        self.__table = Table(
            self.table_name, self.meta,
            Column('id', Integer, primary_key=True),
            Column('server_id', Integer),
            Column('hash_key', String),
        )
        self.meta.create_all(self.engine)

    def insert(self, obj_id, obj_hash_key):
        insert = self.__table.insert().values(server_id=obj_id, hash_key=obj_hash_key)
        self.conn.execute(insert)

    def exists(self, server_id, hash_key):
        raw = text(
            f"SELECT count('id') FROM {self.table_name} where hash_key='{hash_key}' and server_id='{server_id}'"
        )
        result = self.conn.execute(raw).fetchone()[0]
        return result > 0


class APIService(object):
    HEADERS = {
        'Authorization': f'JWT {AWS_PROXY_API_TOKEN}',
    }

    SERVER_INSPECT_URL = f'{AWS_PROXY_API}/api/v1/inspectors/inspected-server/'
    SERVER_LIST_URL = f'{AWS_PROXY_API}/api/v1/inspectors/inquiry-server/'

    def custom_request(self, url, method='post', **kwargs):
        try:
            logger.info(f"[making request]-[method: {method}]-[URL: {url}]-[kwargs: {kwargs}]")
            response = requests.request(method, url, headers=self.HEADERS, **kwargs)
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(
                f'[making request failed]-[response err: {e.response.text}]-[status code: {e.response.status_code}]'
                f'-[URL: {url}]-[exc: {e}]'
            )
            raise Exception(e.response.text)
        except requests.exceptions.ConnectTimeout as e:
            logger.error(f'[request failed]-[URL: {url}]-[exc: {e}]')
            raise
        except Exception as e:
            logger.error(f'[request failed]-[URL: {url}]-[exc: {e}]')
            raise
        return result

    def get_servers_list(self):
        return self.custom_request(self.SERVER_LIST_URL, method='get')

    def post_server_status(self, data):
        return self.custom_request(url=self.SERVER_INSPECT_URL, method='post', json=data)
