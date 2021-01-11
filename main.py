#!/usr/bin/env python3

import logging

from core.services import DBService, APIService, NetcatCheck, PingCheck
from core.consts import SERVER_PORT

logger = logging.getLogger(__name__)


def check_server_connection():
    response = APIService().get_servers_list()
    for server in response:
        try:
            ping_status = NetcatCheck(server['ip'], SERVER_PORT).is_ping or PingCheck(server['ip']).is_ping

            APIService().post_server_status(data={
                "hash_key": server['hash_key'],
                "server": server['id'],
                "is_active": ping_status
            })
            DBService('inspector').insert(server['id'], server['hash_key'])
        except Exception as e:
            logger.error(f'error in checking server connection {server["ip"]} : {e}')
            continue


if __name__ == "__main__":
    check_server_connection()
