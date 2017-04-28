#!env python3
# -- coding:utf-8 --

import logging
logging.basicConfig(format='[In line %(lineno)d] [%(asctime)s] %(message)s', level=logging.INFO)

import socketserver
import socket
import threading
import time
import json
import pymysql

import config
from DCModelService import DCModelService

g_db_connection = pymysql.connect(**config.DATABASE['main'], cursorclass=pymysql.cursors.DictCursor)

MAX_FILE_SIZE = 1024 * 1024 * 10

socketserver.TCPServer.allow_reuse_address = True

class BaseDCTCPSocket(socket.socket):
    driver = {}
    read_thread = None

    msg_queue = []

    data = b""
    self_socket = None

    def __init__(self, other_socket=None):
        socket.socket.__init__(
            self,
            other_socket.family,
            other_socket.type,
            other_socket.proto,
            other_socket.fileno()
            )
        self.self_socket = other_socket
        self.read_thread = threading.Thread(target=self.read_loop)
        self.read_thread.start()

    def handle_read(self):
        while len(self.msg_queue) > 0:
            logging.warn("handle read start")
            msg = self.msg_queue[0]
            del self.msg_queue[0]
            self.handle_one_msg(msg)
            logging.warn("handle read end")

    def handle_one_msg(self, msg):
        raise NotImplementedError()

    def read_file(self, msg_json):
        bytes_len = msg_json['length']
        trash = False
        if bytes_len > MAX_FILE_SIZE:
            trash = True
        ret = b''
        while bytes_len > 0:
            if len(self.data) >= bytes_len:
                ret += self.data[:bytes_len]
                self.data = self.data[bytes_len:]
                break
            else:
                ret += self.data
                bytes_len -= len(self.data)
                self.data = self.recv(10240)
        return ret

    def read_loop(self):
        while True:
            try:
                self.data += self.recv(10240)
                if len(self.data) == 0:
                    return

                # parse data to messages
                data_str = self.data.decode('utf-8', errors='ignore')
                newline = data_str.find('\n')
                # logging.warn(data_str)
                while newline != -1:
                    msg_bytes_len = len(data_str[0:newline + 1].encode('utf-8'))
                    try:
                        msg = json.loads(data_str[0:newline])
                        logging.warn(msg)
                        if msg['type'] == 'file':
                            # read file
                            logging.warn("Reading file")
                            self.data = self.data[msg_bytes_len:]
                            logging.warn("Data cut")
                            self.msg_queue.append(msg)
                            msg = self.read_file(msg)
                            logging.warn("Read complete")
                        self.msg_queue.append(msg)
                    except Exception as e:
                        logging.error(e)
                    finally:
                        logging.warn("finally start")
                        self.data = self.data[msg_bytes_len:]
                        data_str = data_str[newline + 1:]
                        newline = data_str.find('\n')
                        logging.warn("finally end")

                self.handle_read()
            except Exception as e:
                logging.warning(str(e))
                logging.warning("Received error in {}\tGoing to kill self.".format(json.dumps(self.driver, indent=4)))
                self.driver = None

    def __del__(self):
        self.read_thread._stop()

class DCTCPSocket(BaseDCTCPSocket):
    # @classmethod
    def auth(func):
        def wrapper(self, *args, **kwargs):
            if not self.driver:
                return None
            return func(self, *args, **kwargs)
        return wrapper
    
    def handle_type_sys(self, msg):
        if msg['detail'] == 'sign up':
            self.handle_detail_sign_up(msg)
        elif msg['detail'] == 'sign in':
            self.handle_detail_sign_in(msg)

    def handle_detail_sign_up(self, msg):
        logging.warn(msg)
        service = DCModelService(g_db_connection)
        driver = msg['driver']
        res = service.CreateDriver(driver['username'], driver['password'], driver['name'])
        return {
            "type": 'sys',
            'detail': 'sign up',
            'status': res['status'],
            'msg': '创建成功',
            'did': res['did']
        }

    def handle_detail_sign_in(self, msg):
        pass

    def handle_type_file(self, msg):
        logging.warn("handle type file start")
        data_bytes = self.msg_queue[0]
        del self.msg_queue[0]
        with open('test.jpg', 'wb') as f:
            f.write(data_bytes)
        logging.warn("handle type file end")
        send_json = {
            "type": 'file',
            'format': 'image',
            'length': len(data_bytes),
            'from': 1,
            'to': 1
        }
        try:
            send_json_bytes = json.dumps(send_json,separators=(',',':')).encode('utf-8') + b'\n'
        except Exception as e:
            logging.warn(str(e))
        logging.warn(send_json_bytes)
        self.send(send_json_bytes + data_bytes)

    @auth
    def handle_type_chat(self, msg):
        pass

    def handle_one_msg(self, msg):
        logging.warn("handle one msg start")
        if msg['type'] == 'sys':
            self.handle_type_sys(msg)
        elif msg['type'] == 'chat':
            self.handle_type_chat(msg)
        elif msg['type'] == 'file':
            self.handle_type_file(msg)
        logging.warn("handle one msg end")
        
class DCRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.server.clients.append(DCTCPSocket(self.request))

class DCTCPServer(socketserver.TCPServer):
    """
    clients = [{
        "socket": socket,
        "driver": {
            "id": Number
        },
        "thread": Thread
    }, ...]
    """
    
    clients = []

    send_thread = None

    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True):
        socketserver.TCPServer.__init__(self, server_address, RequestHandlerClass, bind_and_activate)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.send_thread = threading.Thread(target=self.send_loop)
        self.send_thread.start()

    """
    防止finish把socket断开
    """
    def shutdown_request(self, request):
        pass

    def send_all(self, data):
        will_del_index = []
        for i in range(0, len(self.clients)):
            client = self.clients[i]
            if client.driver == None:
                will_del_index.append(i)
            try:
                client.send(data)
            except Exception as e:
                logging.warning(e)
                logging.warning("Send error in {}".format(json.dumps(client.driver, indent=4)))

        # delete
        for index in reversed(will_del_index):
            del self.clients[index]

    def send_loop(self):
        while True:
            time.sleep(1)
            # self.send_all(b"testing\n")
