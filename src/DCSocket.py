#!env python3
# -- coding:utf-8 --

import logging
logging.basicConfig(format='[%(levelno)s] [File %(filename)s Line %(lineno)d] [%(asctime)s] %(message)s', level=logging.INFO)
logging.root.setLevel(logging.INFO)

import socketserver
import socket
import threading
import time
import datetime
import json
import pymysql
import hashlib
import traceback
import os

import config
from DCModelService import DCModelService

g_db_connection = pymysql.connect(**config.DATABASE['main'], cursorclass=pymysql.cursors.DictCursor)

MAX_FILE_SIZE = 1024 * 1024 * 10

socketserver.TCPServer.allow_reuse_address = True

def min_json_dumps_to_bytes(json_dict):
    return json.dumps(json_dict,separators=(',',':')).encode('utf-8')

def gen_filename(seed):
    name = hashlib.md5(seed).hexdigest()
    return name

class BaseDCTCPSocket(socket.socket):
    """
    driver = {
        "username": String,
        "did": Integer,
        "room": [rid0, rid1, ...]
    }
    """
    driver = {}
    read_thread = None

    msg_queue = []

    data = b""
    self_socket = None

    server_socket = None

    def __init__(self, other_socket=None, server_socket=None):
        socket.socket.__init__(
            self,
            other_socket.family,
            other_socket.type,
            other_socket.proto,
            other_socket.fileno()
            )
        logging.info('connected with ip_addr: {}'.format(self.getpeername()))
        self.server_socket = server_socket
        self.self_socket = other_socket
        self.read_thread = threading.Thread(target=self.read_loop)
        self.read_thread.start()

    def handle_read(self):
        while len(self.msg_queue) > 0:
            msg = self.msg_queue[0]
            del self.msg_queue[0]
            self.handle_one_msg(msg)

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
                self.data += self.recv(1024)
                if len(self.data) == 0:
                    # 使Driver登出
                    self.driver = None
                    return
                # parse data to messages
                data_str = self.data.decode('utf-8', errors='ignore')
                newline = data_str.find('\n')
                while newline != -1:
                    isfile = False
                    msg_bytes_len = len(data_str[0:newline + 1].encode('utf-8'))
                    logging.info(data_str[0:newline])
                    try:
                        msg = json.loads(data_str[0:newline])
                        self.data = self.data[msg_bytes_len:]
                        logging.info(msg)
                        if msg['type'] == 'file' and msg['updown'] == 'up':
                            isfile = True
                            # read file
                            logging.info("Reading file")
                            self.msg_queue.append(msg)
                            logging.info('msg queue: {}'.format(json.dumps([item if not isinstance(item, bytes) else 'bytes' for item in self.msg_queue])))
                            msg = self.read_file(msg)
                            logging.info("File Read complete")
                        self.msg_queue.append(msg)
                        # logging.info(self.msg_queue)
                    except Exception as e:
                        # logging.error(str(e))
                        # traceback.print_exc()
                        raise e
                    finally:
                        if isfile:
                            data_str = self.data.decode('utf-8', errors='ignore')
                        else:
                            data_str = data_str[newline + 1:]
                        newline = data_str.find('\n')

                self.handle_read()
            except Exception as e:
                logging.warning(str(e))
                # traceback.print_last()
                traceback.print_exc()
                logging.warning("Received error in {}\tGoing to kill self.".format(json.dumps(self.driver, indent=4)))
                self.driver = None

    def __del__(self):
        self.read_thread._stop()

"""
Only for class *DCTCPSocket*
"""
def auth(func):
    def wrapper(self, *args, **kwargs):
        if not self.driver:
            send_json = kwargs['msg']
            send_json['status'] = False
            send_json['msg'] = 'sign in first'
            self.sendall(min_json_dumps_to_bytes(send_json) + b'\n')
            return None
        return func(self, *args, **kwargs)
    return wrapper

class DCTCPSocket(BaseDCTCPSocket):
    def log_request(self, req_name):
        logging.info('{} request from {}'.format(req_name, self.getpeername()))

    def handle_type_sys(self, msg):
        if msg['detail'] == 'sign up':
            self.handle_detail_sign_up(msg)
        elif msg['detail'] == 'sign in':
            self.handle_detail_sign_in(msg)
        elif msg['detail'] == 'enter room':
            self.handle_detail_enter_room(msg)
        elif msg['detail'] == 'quit room':
            self.handle_detail_quit_room(msg)
        elif msg['detail'] == 'room list':
            self.handle_detail_room_list(msg)
        elif msg['detail'] == 'driver list':
            self.handle_detail_driver_list(msg)

    @auth
    def handle_detail_room_list(self, msg):
        self.log_request('room list')
        service = DCModelService(g_db_connection)
        rooms = service.ListRooms()
        for i in rooms:
            i['created_at'] = i['created_at'].strftime("%Y-%m-%d %H:%M:%S %z")
        send_json = {
            'type': 'sys',
            'detail': 'room list',
            'rooms': rooms
        }
        self.sendall(min_json_dumps_to_bytes(send_json) + b'\n')

    def update_driver_list(self, rid):
        service = DCModelService(g_db_connection)
        clients = self.server_socket.get_room_clients(rid)
        dids = []
        for item in clients:
            if item.driver and item.driver['did'] not in dids:
                dids.append(item.driver['did'])

        drivers = []
        
        for did in dids:
            driver = service.SearchDriverWithDid(did)
            del driver['username']
            del driver['password']
            del driver['created_at']
            drivers.append(driver)
        send_json = {
            'type': 'sys',
            'detail': 'driver list',
            'rid': rid,
            'drivers': drivers
        }
        self.server_socket.send_clients(min_json_dumps_to_bytes(send_json) + b'\n', clients)

    @auth
    def handle_detail_driver_list(self, msg):
        self.log_request('driver list')
        rid = int(msg['rid'])
        
        self.update_driver_list(rid)

    def handle_detail_sign_up(self, msg):
        self.log_request('sign up')
        service = DCModelService(g_db_connection)
        driver = msg['driver']
        res = service.CreateDriver(driver['username'], driver['password'], driver['name'])
        send_json = {
            "type": 'sys',
            'detail': 'sign up',
            'status': res['status'],
            'msg': '创建成功' if res['status'] else '创建失败',
            'did': res['did']
        }
        self.sendall(min_json_dumps_to_bytes(send_json) + b'\n')

    def handle_detail_sign_in(self, msg):
        self.log_request('sign in')
        send_json = {
            'type': 'sys',
            'detail': 'sign in',
            'status': True,
            'msg': ''
        }
        service = DCModelService(g_db_connection)
        req_driver = msg['driver']
        logging.info(req_driver)
        driver = service.SearchDriverWithUsername(req_driver['username'])
        if driver != None and driver['password'] == hashlib.sha256(req_driver['password'].encode('utf-8') + config.DRIVER_SALT).hexdigest():
            self.driver = {
                'username': driver['username'],
                'did': driver['did']
            }
            # 登录成功
            send_json['driver'] = {
                'did': driver['did'],
                'name': driver['name'],
                'badge': driver['badge'],
                'created_at': driver['created_at'].strftime("%Y-%m-%d %H:%M:%S %z"),
                'avatar': driver['avatar']
            }
            send_json['msg'] = '登录成功'
            send_json['status'] = True
            self.sendall(min_json_dumps_to_bytes(send_json) + b'\n')
        else:
            # 登录失败
            send_json['status'] = False
            send_json['msg'] = '登录失败'
            self.sendall(min_json_dumps_to_bytes(send_json) + b'\n')

    @auth
    def handle_detail_enter_room(self, msg):
        self.log_request('enter room')
        send_json = {
            'type': 'sys',
            'detail': 'enter room',
            'rid': None,
            'status': True
        }
        try:
            rid = int(msg['rid'])
        except KeyError as e:
            logging.warn(str(e))
            logging.warn("key error when did({}) is requesting enter room".format(self.driver['did']))
            send_json['status'] = True
            self.sendall(min_json_dumps_to_bytes(send_json) + b'\n')
            return
        send_json['rid'] = rid
        if not 'room' in self.driver:
            self.driver['room'] = []
        self.driver['room'].append(rid)
        self.sendall(min_json_dumps_to_bytes(send_json) + b'\n')
        self.update_driver_list(rid)

    @auth
    def handle_detail_quit_room(self, msg):
        send_json = {
            'type': 'sys',
            'detail': 'enter room',
            'rid': None,
            'status': True
        }
        try:
            rid = int(msg['rid'])
        except KeyError as e:
            logging.warn(str(e))
            logging.warn("key error when did({}) is requesting quit room".format(self.driver['did']))
            send_json['status'] = True
            self.sendall(min_json_dumps_to_bytes(send_json) + b'\n')
            return
        send_json['rid'] = rid
        if not 'room' in self.driver:
            self.driver['room'] = []
        try:
            self.driver['room'].remove(rid)
        except ValueError as e:
            logging.warn("no such rid when did({}) is requesting quit room".format(self.driver['did']))
            send_json['status'] = False
        self.sendall(min_json_dumps_to_bytes(send_json) + b'\n')
        self.update_driver_list(rid)

    @auth
    def handle_type_file(self, msg):
        self.log_request('type file')
        data_bytes = None
        if msg['updown'] == 'up':
            data_bytes = self.msg_queue[0]
            del self.msg_queue[0]
        if msg['detail'] == 'driver avatar':
            self.handle_detail_driver_avatar(msg, data_bytes)
        elif msg['detail'] == 'room avatar':
            self.handle_detail_room_avatar(msg, data_bytes)
        elif msg['detail'] == 'badge':
            self.handle_detail_badge(msg)
        elif msg['detail'] == 'chat':
            self.handle_detail_chat(msg, data_bytes)

        # data_bytes = self.msg_queue[0]
        # del self.msg_queue[0]
        # logging.info('msg queue: {}'.format(json.dumps([item if not isinstance(item, bytes) else 'bytes' for item in self.msg_queue])))
        # self.send(min_json_dumps_to_bytes(msg) + b'\n' + data_bytes)

    def handle_detail_driver_avatar(self, msg, data_bytes=None):
        send_json = msg
        service = DCModelService(g_db_connection)
        if msg['updown'] == 'up':
            # 验证身份
            if msg['driver']['did'] != self.driver['did']:
                send_json['status'] = False
                self.sendall(min_json_dumps_to_bytes(send_json) + b'\n')
                return
            name = gen_filename(data_bytes[0:20] + str(time.clock()).encode('utf-8'))
            if name is None:
                name = 'driver_default.png'
            path = config.FILE_DIR + name
            # 写文件
            try:
                with open(path, 'rb') as f:
                    f.write(data_bytes)
            except Exception as e:
                logging.warn(str(e))
                send_json['status'] = False
                self.sendall(min_json_dumps_to_bytes(send_json) + b'\n')
                return
            service.SetAvatar(msg['driver']['did'], path)
        elif msg['updown'] == 'down':
            logging.info("dealing with down")
            send_json['status'] = True
            try:
                name = service.GetAvatar(msg['driver']['did'])
                if not name:
                    name = 'driver_default.png'
                path = config.FILE_DIR + name
                with open(path, 'rb') as f:
                    data_bytes = f.read()
                send_json['length'] = len(data_bytes)
                self.sendall(min_json_dumps_to_bytes(send_json) + b'\n' + data_bytes)
            except Exception as e:
                logging.warn(str(e))
                traceback.print_exc()
                send_json['status'] = False
                self.sendall(min_json_dumps_to_bytes(send_json) + b'\n')
                return

    def handle_detail_room_avatar(self, msg, data_bytes=None):
        send_json = msg
        service = DCModelService(g_db_connection)
        if msg['updown'] == 'down':
            send_json['status'] = True
            try:
                name = service.GetRoomAvatar(msg['room']['rid'])
                if name is None:
                    name = 'room_default.png'
                path = config.FILE_DIR + name
                with open(path, 'rb') as f:
                    data_bytes = f.read()
                send_json['length'] = len(data_bytes)
                self.sendall(min_json_dumps_to_bytes(send_json) + b'\n' + data_bytes)
            except Exception as e:
                send_json['status'] = False
                self.sendall(min_json_dumps_to_bytes(send_json) + b'\n')
                return

    def handle_detail_badge(self, msg):
        send_json = msg
        service = DCModelService(g_db_connection)
        if msg['updown'] == 'down':
            send_json['status'] = True
            badges = service.GetBadge(msg['did'])
            badge = badges[0] if len(badges) > 0 else None
            if badge == None:
                send_json['status'] = False
                self.sendall(min_json_dumps_to_bytes(send_json) + b'\n')
            else:
                with open(config.FILE_DIR + badge, 'rb') as f:
                    data_bytes = f.read()
                send_json['length'] = len(data_bytes)
                self.sendall(min_json_dumps_to_bytes(send_json) + b'\n' + data_bytes)

    def handle_detail_chat(self, msg, data_bytes=None):
        send_json = msg
        if msg['updown'] == 'up':
            self.server_socket.chat_file(msg, self.driver, data_bytes)

    @auth
    def handle_type_chat(self, msg):
        self.server_socket.chat(msg, self.driver)

    def handle_one_msg(self, msg):
        # logging.info('msg queue: {}'.format(json.dumps([item if not isinstance(item, bytes) else 'bytes' for item in self.msg_queue])))
        # logging.info(msg)
        if msg['type'] == 'sys':
            self.handle_type_sys(msg)
        elif msg['type'] == 'chat':
            self.handle_type_chat(msg)
        elif msg['type'] == 'file':
            self.handle_type_file(msg)
        
class DCRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.server.clients.append(DCTCPSocket(self.request, self.server))

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
                continue
            try:
                client.send(data)
            except Exception as e:
                logging.warning(str(e))
                logging.warning("Send error in {}".format(json.dumps(client.driver, indent=4)))
                client.driver = None

        # delete
        for index in reversed(will_del_index):
            del self.clients[index]

    def send_clients(self, data, clients_list):
        for sock in clients_list:
            try:
                sock.send(data)
            except Exception as e:
                logging.warn(str(e))
                continue

    def send_loop(self):
        send_json = {
            'type': 'sys',
            'detail': 'check alive'
        }
        while True:
            # self.send_all(min_json_dumps_to_bytes(send_json) + b'\n')
            time.sleep(5)

    def get_room_clients(self, rid):
        send_list = []
        for c in self.clients:
            if c.driver and 'room' in c.driver and rid in c.driver['room']:
                send_list.append(c)
        return send_list

    def chat_file(self, recv_json, from_driver, data_bytes):
        rid = int(recv_json['to'])
        # build json
        data = {
            'type': 'file',
            'format': 'image',
            'detail': 'chat',
            'room': {
                'rid': rid
            },
            'from': from_driver['did'],
            'length': len(data_bytes)
        }
        send_list = self.get_room_clients(rid)
        logging.info(send_list)
        return self.send_clients(min_json_dumps_to_bytes(data) + b'\n' + data_bytes, send_list)

    def chat(self, recv_json, from_driver):
        rid = int(recv_json['to'])
        # build json
        data = {
            'type': 'chat',
            'msg': recv_json['msg'],
            'to': rid,
            'from': from_driver['did']
        }
        send_list = self.get_room_clients(rid)
        logging.info(send_list)
        return self.send_clients(min_json_dumps_to_bytes(data) + b'\n', send_list)
