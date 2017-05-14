# -- coding: utf-8 --

import socket
import sys
import json

def main():
    if len(sys.argv) < 2:
        print('arguments not enough. 2nd arg is the file path.')
    with open(sys.argv[1], mode='rb') as f:
        data = f.read()
    test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    test_socket.connect(('localhost', 9999))
    send_json = {
        'type': 'file',
        'format': 'image',
        'length': len(data),
        'from': 1,
        'to': 2
    }
    send_json = json.dumps(send_json, separators=(',',':')).encode('utf-8') + b'\n'
    print('send_json: {}'.format(send_json))
    send_data = send_json + data
    test_socket.send(send_data)
    recv_data = test_socket.recv(1024*1024*1024)
    print('first recv: {}'.format(len(recv_data)))
    json_data = recv_data.decode('utf-8', errors='ignore')
    end = json_data.find('\n')
    json_data = json_data[:end] + '\n'
    print('json: {}'.format(json_data))
    json_len = len(json_data.encode('utf-8'))

    json_data = json.loads(json_data)
    data_len = json_data['length']

    recv_data = recv_data[json_len:]
    print('recv: {}'.format(len(recv_data)))
    with open('get.jpg', 'wb') as f:
        data_len -= len(recv_data)
        f.write(recv_data)
        while data_len > 0:
            recv_data = test_socket.recv(102400)
            print('recv: {}'.format(len(recv_data)))
            data_len -= len(recv_data)
            f.write(recv_data)

    test_socket.close()

if __name__ == '__main__':
    main()
