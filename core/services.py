#!/usr/bin/env python3

import logging
import os
import re
import subprocess
import requests

from pathlib import Path

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, text, Boolean
from sqlalchemy.orm import sessionmaker

from core.consts import AWS_PROXY_API, AWS_PROXY_API_TOKEN, NETCAT_TIMEOUT

logger = logging.getLogger(__name__)


class DBService(object):
    BASE_DIR = Path(__file__).resolve().parent.parent

    def __init__(self, db_name):
        self.engine = create_engine(f'sqlite:///{self.BASE_DIR}/{db_name}.db', echo=True)
        self.meta = MetaData()
        self.table_name = 'Servers'
        self.conn = self.engine.connect()
        self.session = sessionmaker(bind=self.engine)

    def __table(self):
        table = Table(
            self.table_name, self.meta,
            Column('id', Integer, primary_key=True),
            Column('server_id', Integer),
            Column('hash_key', String),
        )

        self.meta.create_all(self.engine)
        return table

    def insert(self, obj_id, obj_hash_key):
        insert = self.__table().insert().values(server_id=obj_id, hash_key=obj_hash_key)
        self.conn.execute(insert)

    def exists(self, server_id, hash_key):
        raw = text(
            f"SELECT count('id') FROM {self.table_name} where hash_key={hash_key} and server_id={server_id}"
        )
        result = self.conn.execute(raw).fetchone()[0]
        return result > 0


class APIService(object):
    HEADERS = {
        'Authorization': AWS_PROXY_API_TOKEN,
    }

    SERVER_INSPECT_URL = f'{AWS_PROXY_API}/api/v1/inspectors/inspected-server/'
    SERVER_LIST_URL = f'{AWS_PROXY_API}/api/v1/inspectors/inquiry-server/'

    def api_call(self, method, url, data=None, params=None, files=None, **kwargs):
        try:
            if method.lower() == 'get':
                response = requests.get(url=url, headers=self.HEADERS, params=params, **kwargs)
            elif method.lower() == 'post':
                response = requests.post(url=url, headers=self.HEADERS, json=data, files=files, **kwargs)
            elif method.lower() == 'patch':
                response = requests.patch(url=url, headers=self.HEADERS, json=data, files=files, **kwargs)
            else:
                return None
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            logger.error(f'http error for requesting url {url} occurred: {e}')
            if e.response.status_code == 400:
                raise Exception(e.response.text)
            raise e
        except requests.exceptions.RequestException as e:
            logger.error(f'request error for requesting url {url} occurred: {e}')
            raise e

    def get_servers_list(self):
        return self.api_call('get', self.SERVER_LIST_URL).json()

    def post_server_status(self, data):
        return self.api_call(method='post', url=self.SERVER_INSPECT_URL, data=data)


class PingCheck:

    def __init__(self, input_string):
        self.input_string = input_string
        self.is_ping = False
        self.ip = None
        self.time = None
        self.success = 0
        self.domain = None
        self.ping()

    def ping(self):
        ip_pattern = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
        is_ip = ip_pattern.match(self.input_string)

        if is_ip is None:
            self.domain = self.input_string
        else:
            self.ip = self.input_string
            self.domain = ''

        try:
            ping = os.popen(f'ping -c 6 -q -s 1 {self.input_string}').read()
            self.ip = ping.split('\n')[0].split()[2][1:-1]
            self.time = ping.split('\n')[-3].split()[-1].lstrip('time')
            self.success = 100.0 - float(ping.split('\n')[-3].split(',')[2].rstrip('% packet loss'))
        except Exception as e:
            print(f"{self.domain or self.ip} {e}")
        return self.success >= 60.0


class NetcatCheck:

    def __init__(self, ip, port):
        self.is_ping = False
        self.nc(ip, port)

    def nc(self, ip, port):
        cmd = f"netcat -v -z -w{NETCAT_TIMEOUT} {ip} {port}"
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        res = str(process.stderr.read())

        self.is_ping = 'succeeded' in res
