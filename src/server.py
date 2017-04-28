#!env python3
# -- coding:utf-8 --

import logging
logging.basicConfig(format='[In line %(lineno)d] [%(asctime)s] %(message)s', level=logging.INFO)
import time

from DCSocket import DCRequestHandler, DCTCPServer, DCTCPSocket

HOST, PORT = "0.0.0.0", 9999

def main():
    server = DCTCPServer((HOST, PORT), DCRequestHandler)
    logging.warning("Server started at {}".format(str(time.strftime("%Y-%m-%d %H:%M:%S %z", time.localtime()))))
    server.serve_forever()
    
if __name__ == "__main__":
    main()
