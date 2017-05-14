#!env python3
# -- coding:utf-8 --

import logging
logging.basicConfig(format='[%(levelno)s] [File %(filename)s Line %(lineno)d] [%(asctime)s] %(message)s', level=logging.INFO)
logging.root.setLevel(logging.INFO)
import time
import config
import os

from DCSocket import DCRequestHandler, DCTCPServer, DCTCPSocket

def main():
    server = DCTCPServer((config.HOST, config.PORT), DCRequestHandler)
    logging.warning("Server started at {}".format(str(time.strftime("%Y-%m-%d %H:%M:%S %z", time.localtime()))))
    server.serve_forever()
    
if __name__ == "__main__":
    if not os.path.exists(config.FILE_DIR):
        os.mkdir(config.FILE_DIR)
    main()
