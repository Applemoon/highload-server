#!/usr/bin/env python
# -*- coding: utf-8 -*-

import getopt
import socket
import sys
import multiprocessing
from multiprocessing import Process
from httpresponse import HttpResponse

HOST = '127.0.0.1'
PORT = 8081
EOL1 = '\n\n'
EOL2 = '\n\r\n'

log_flag = False
cpu_count = multiprocessing.cpu_count()
document_dir = './DOCUMENT_ROOT'


def child(server):
    while True:
        try:
            connection_socket, address = server.accept()
            data = ''
            while EOL1 not in data and EOL2 not in data:
                data += connection_socket.recv(1024)

            if log_flag:
                print data

            data = data.splitlines()
            if not data:
                continue

            first_line = data[0].split()
            if len(first_line) < 2:
                continue

            method_str = first_line[0]
            path_str = first_line[1]
            response = HttpResponse(method_str, path_str, document_dir)
            connection_socket.sendall(response.to_str())
        except KeyboardInterrupt:
            return

if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "d:c:l")
    except getopt.GetoptError:
        print "-d DOCUMENT_DIR - set document directory"
        print "-c CPU_COUNT - set CPU count"
        print "-l - get log output"
        sys.exit(1)

    for opt, arg in opts:
        if opt == '-d':
            document_dir = arg
        elif opt == '-c':
            cpu_count = arg
        elif opt == '-l':
            log_flag = True

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(socket.SOMAXCONN)

    if log_flag:
        print('Server started on %s:%s' % (HOST, str(PORT)))

    for i in range(cpu_count):
        p = Process(target=child, args=(server_socket,), name="Worker " + str(i))
        p.start()

        try:
            p.join()
        except KeyboardInterrupt:
            print "Server shutdown"
