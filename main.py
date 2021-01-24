#!/usr/bin/env python3
import json
import os
import re
import subprocess

from core.logger import Logger
from core.services import DBService, APIService
from core.consts import SERVER_PORT, NETCAT_TIMEOUT

logger = Logger()


def pinged(input_string):
    logger.info(f'[trying to ping]-[string: {input_string}]')
    ip_pattern = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
    is_ip = ip_pattern.match(input_string)
    success = 0

    if is_ip is None:
        domain = input_string
        ip = None
    else:
        ip = input_string
        domain = ''

    try:
        ping = os.popen(f'ping -c 6 -q -s 1 {input_string}').read()
        ip = ping.split('\n')[0].split()[2][1:-1]
        success = 100.0 - float(ping.split('\n')[-3].split(',')[2].rstrip('% packet loss'))
        result = success >= 60.0
        logger.info(f'[ping completed!]-[result: {result}]')
    except Exception as e:
        print(f"{domain or ip} {e}")
        logger.error(f'[pinging failed!]-[string: {input_string}]-[exc: {e}]')
        return None
    return result


def nc(ip, port):
    logger.info(f'[trying to netcat]-[ip: {ip}]-[port: {port}]')

    cmd = f"netcat -v -z -w{NETCAT_TIMEOUT} {ip} {port}"
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res = str(process.stderr.read())
    result = 'succeeded' in res
    logger.info(f'[netcat completed]-[result: {result}]')
    return result


def check_server_connection():
    db = DBService('inspector')
    response = APIService().get_servers_list()
    logger.info(f'[getting servers list]')
    try:
        isp = APIService().get_ip_info()['org']
    except Exception as e:
        logger.info(f'[could not catch ip info. trying ip cache file ...]-[exc: {e}]')
        if os.path.isfile('ip_info.json'):
            with open('ip_info.json') as file:
                isp = json.load(file)['org']
        else:
            isp = ''
    for server in response:
        try:
            if db.exists(server['id'], server['hash_key']):
                logger.info(f'[server exists in database]-[id: {server["id"]}]-[hash_key: {server["hash_key"]}]')
                continue

            ping_status = nc(server['ip'], SERVER_PORT) or pinged(server['ip'])
            logger.info(
                f'[posting server status to api]-[id: {server["id"]}]-[hash_key: {server["hash_key"]}]-[is_active: {ping_status}]'
            )
            APIService().post_server_status(data={
                "hash_key": server['hash_key'],
                "server": server['id'],
                "is_active": ping_status,
                "ip": server['ip'],
                "isp": isp
            })
            logger.info(f'[inserting data to database]-[id: {server["id"]}]-[hash_key: {server["hash_key"]}]')
            db.insert(server['id'], server['hash_key'])
        except Exception as e:
            logger.error(f'error in checking server connection {server["ip"]} : {e}')


if __name__ == "__main__":
    check_server_connection()
