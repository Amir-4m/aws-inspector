import sys
from datetime import datetime


class Logger(object):

    def error(self, message):
        sys.stderr.write(f"[{datetime.now()}] {message} \n")
        # sys.stderr.flush()

    def info(self, message):
        sys.stdout.write(f"[{datetime.now()}] {message} \n")
        # sys.stdout.flush()
