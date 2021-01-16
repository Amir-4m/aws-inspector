#!/usr/bin/env python3
import os
import re
import sys
import subprocess

from core.services import DBService, APIService
from core.consts import SERVER_PORT, NETCAT_TIMEOUT


def pinged(input_string):
    sys.stdout.write(f'[trying to ping]-[string: {input_string}]')
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
        sys.stdout.write(f'[ping completed!]-[result: {result}]')
    except Exception as e:
        print(f"{domain or ip} {e}")
        sys.stderr.write(f'[pinging failed!]-[string: {input_string}]-[exc: {e}]')
        return None
    return result


def nc(ip, port):
    sys.stdout.write(f'[trying to netcat]-[ip: {ip}]-[port: {port}]')

    cmd = f"netcat -v -z -w{NETCAT_TIMEOUT} {ip} {port}"
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res = str(process.stderr.read())
    result = 'succeeded' in res
    sys.stdout.write(f'[netcat completed]-[result: {result}]')
    return result


def check_server_connection():
    db = DBService('inspector')
    response = APIService().get_servers_list()
    sys.stdout.write(f'[getting servers list]')
    for server in response:
        try:
            if db.exists(server['id'], server['hash_key']):
                sys.stdout.write(f'[server exists in database]-[id: {server["id"]}]-[hash_key: {server["hash_key"]}]')
                continue

            ping_status = nc(server['ip'], SERVER_PORT) or pinged(server['ip'])
            sys.stdout.write(
                f'[posting server status to api]-[id: {server["id"]}]-[hash_key: {server["hash_key"]}]-[is_active: {ping_status}]'
            )
            APIService().post_server_status(data={
                "hash_key": server['hash_key'],
                "server": server['id'],
                "is_active": ping_status
            })
            sys.stdout.write(f'[inserting data to database]-[id: {server["id"]}]-[hash_key: {server["hash_key"]}]')
            db.insert(server['id'], server['hash_key'])
        except Exception as e:
            sys.stderr.write(f'error in checking server connection {server["ip"]} : {e}')


if __name__ == "__main__":
    check_server_connection()
