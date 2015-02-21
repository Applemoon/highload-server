#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import select
import sys
from httpresponse import HttpResponse


HOST = '127.0.0.1'
PORT = 80
EOL1 = '\n\n'
EOL2 = '\n\r\n'
LOG_FLAG = True
RECEIVE_SIZE = 1024
SOCKET_TIMEOUT = 10  # в секундах

# Проверка переданных аргументов
str(sys.argv[1])

# Настройка сокета сервера
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(5)
server_socket.setblocking(0)

epoll = select.epoll()
epoll.register(server_socket.fileno(), select.EPOLLIN)

if LOG_FLAG:
    print('Server started on %s:%s' % (HOST, str(PORT)))

try:
    connections = {}
    requests = {}
    responses = {}
    while True:
        events = epoll.poll(1)
        for fileno, event in events:
            if fileno == server_socket.fileno():
                connection_socket, address = server_socket.accept()  # Установлено соединение с клиентом
                connection_socket.settimeout(SOCKET_TIMEOUT)
                connection_socket.setblocking(0)
                epoll.register(connection_socket.fileno(), select.EPOLLIN)
                connections[connection_socket.fileno()] = connection_socket
                requests[connection_socket.fileno()] = ''
            elif event & select.EPOLLIN:  # Доступно для чтения
                requests[fileno] += connections[fileno].recv(RECEIVE_SIZE)  # Чтение запроса
                if EOL1 in requests[fileno] or EOL2 in requests[fileno]:
                    request = requests[fileno].split(' ')
                    method = request[0]
                    path = request[1]
                    response = HttpResponse(method, path)
                    responses[fileno] = response.to_str()
                    epoll.modify(fileno, select.EPOLLOUT)
                    if LOG_FLAG:
                        print('-' * 40 + '\n' + requests[fileno].decode()[:-2])
            elif event & select.EPOLLOUT:  # Доступно для записи
                bytes_written = connections[fileno].send(responses[fileno])
                responses[fileno] = responses[fileno][bytes_written:]
                if len(responses[fileno]) == 0:
                    epoll.modify(fileno, 0)
                    connections[fileno].shutdown(socket.SHUT_RDWR)
            elif event & select.EPOLLHUP:  # Hang up happened on the assoc. fd
                epoll.unregister(fileno)
                connections[fileno].close()
                del connections[fileno]
finally:
    epoll.unregister(server_socket.fileno())
    epoll.close()
    server_socket.close()

# TODO указывать папку со статикой '-r ROOTDIR'
# TODO указывать число процессоров '-c NCPU'
# TODO отладочный вывод по флагу '-l'

# TODO распределить обработку событий на разные потоки в зависимости от дескриптора сокета (?)