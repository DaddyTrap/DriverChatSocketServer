# -- coding: utf-8 --

import socket
import json

def min_json_dumps_to_bytes(json_dict):
    return json.dumps(json_dict,separators=(',',':')).encode('utf-8')

def main():
    test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    test_socket.connect(('localhost', 9999))
    username = input('username: ')
    password = input('password: ')
    send_json = {
        'type': 'sys',
        'detail': 'sign in',
        'driver': {
            'username': username,
            'password': password
        }
    }
    test_socket.send(min_json_dumps_to_bytes(send_json) + b'\n')
    s = test_socket.recv(10240)
    print(s)
    test_socket.close()

if __name__ == '__main__':
    main()
