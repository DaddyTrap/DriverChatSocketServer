# -- coding: utf-8 --

import socket
import json

def min_json_dumps_to_bytes(json_dict):
    return json.dumps(json_dict,separators=(',',':')).encode('utf-8')

def main():
    test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    test_socket.connect(('localhost', 9999))

    # sign in
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
    s = test_socket.recv(1024)
    print(s)

    # enter room
    rid = input('rid: ')
    send_json = {
        'type': 'sys',
        'detail': 'enter room',
        'rid': int(rid)
    }
    test_socket.send(min_json_dumps_to_bytes(send_json) + b'\n')
    s = test_socket.recv(1024)
    print(s)

    # chat
    send_json = {
        'type': 'chat',
        'msg': '',
        'to': int(rid)
    }
    while True:
        msg = input()
        send_json['msg'] = msg
        test_socket.send(min_json_dumps_to_bytes(send_json) + b'\n')
        s = test_socket.recv(1024)
        print('recv: {}'.format(s.decode('utf-8')))
    
    test_socket.close()

if __name__ == '__main__':
    main()
