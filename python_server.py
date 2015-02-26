#!/usr/bin/env python
# -*- coding: utf-8 -*-
from _mysql import connection

import getopt
import socket
import sys
import multiprocessing
from multiprocessing import Process
from httpresponse import HttpResponse

HOST = '127.0.0.1'
PORT = 80
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
                data_buffer = connection_socket.recv(1024)
                if not data_buffer:
                    break
                data += data_buffer

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
            response = HttpResponse(method_str, path_str, document_dir).to_str()
            bytes_sent_total = 0
            while bytes_sent_total < len(response):
                data_to_send = response[bytes_sent_total:]
                bytes_sent_total += connection_socket.send(data_to_send)

            connection_socket.close()
        except KeyboardInterrupt:
            return

if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "r:c:l")
    except getopt.GetoptError:
        print "-r DOCUMENT_DIR - set document directory"
        print "-c CPU_COUNT - set CPU count"
        print "-l - get log output"
        sys.exit(1)

    for opt, arg in opts:
        if opt == '-r':
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

    processes = {}

    for i in range(cpu_count*2):
        proc = Process(target=child, args=(server_socket,), name="Worker " + str(i))
        processes[i] = proc
        proc.daemon = True
        proc.start()

        try:
            proc.join()
        except KeyboardInterrupt:
            print "Server shutdown"
            for p in processes:
                p.close()
            sys.exit(0)
