#!/usr/bin/env python3

from decouple import config

AWS_PROXY_API = config('AWS_PROXY_API')
AWS_PROXY_API_TOKEN = config('AWS_PROXY_API_TOKEN')
SERVER_PORT = config('SERVER_PORT', default=80)
NETCAT_TIMEOUT = config('NETCAT_TIMEOUT', default=5, cast=int)
