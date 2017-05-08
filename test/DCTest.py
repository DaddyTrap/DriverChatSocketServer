# -- coding: utf-8 --

import socket

def min_json_dumps_to_bytes(json_dict):
    return json.dumps(json_dict,separators=(',',':')).encode('utf-8')

class DCTest(socket.socket):
    def __init__(self):
        socket.socket.__init__(self)

    def sign_in(self, username, password):
        send_json = {
            'type': 'sys',
            'detail': 'sign in',
            'driver': {
                'username': username,
                'password': password
            }
        }
        self.send(min_json_dumps_to_bytes(send_json) + 'b\n')
        s = self.recv(1024)
        print(s)

    def sign_up(self, username, password, name):
        send_json = {
            'type': 'sys',
            'detail': 'sign up',
            'driver': {
                'username': username,
                'password': password,
                'name': name
            }
        }
        self.send(min_json_dumps_to_bytes(send_json) + 'b\n')
        s = self.recv(1024)
        print(s)

    def chat(self, msg, to):
        send_json = {
            'type': 'chat',
            'msg': msg,
            'to': int(to)
        }
        self.send(min_json_dumps_to_bytes(send_json) + b'\n')
        s = self.recv(1024)
        print(s)
    
    def chat_file(self, file_desc, to):
        send_json = {
            
        }
