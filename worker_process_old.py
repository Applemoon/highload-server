#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

import socket
import select
from httpresponse import HttpResponse

SOCKET_TIMEOUT = 10  # в секундах
RECEIVE_SIZE = 1024
EOL1 = '\n\n'
EOL2 = '\n\r\n'
LOG_FLAG = True  # TODO


def child(server_socket, events_queue, register_queue, modify_queue, unregister_queue, epoll):
    connections = {}
    requests = {}
    responses = {}
    while True:
        # fileno, event = events_queue.get()  # TODO timeout, exception
        events = epoll.poll(1)
        for fileno, event in events:
            if fileno == server_socket.fileno():
                connection_socket, address = server_socket.accept()  # Установлено соединение с клиентом
                connection_socket.settimeout(SOCKET_TIMEOUT)
                connection_socket.setblocking(0)
                # epoll.register(connection_socket.fileno(), select.EPOLLIN)
                if LOG_FLAG:
                    print os.getpid(), "register_queue.put", connection_socket.fileno(), select.EPOLLIN
                register_queue.put([connection_socket.fileno(), select.EPOLLIN])  # TODO timeout, exception
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
                    # epoll.modify(fileno, select.EPOLLOUT)
                    if LOG_FLAG:
                        print "modify_queue.put", fileno, select.EPOLLOUT
                    modify_queue.put([fileno, select.EPOLLOUT])  # TODO timeout, exception
                    if LOG_FLAG:
                        print('-' * 40 + '\n' + requests[fileno].decode()[:-2])
            elif event & select.EPOLLOUT:  # Доступно для записи
                bytes_written = connections[fileno].send(responses[fileno])
                responses[fileno] = responses[fileno][bytes_written:]
                if len(responses[fileno]) == 0:
                    # epoll.modify(fileno, 0)
                    if LOG_FLAG:
                        print "modify_queue.put", fileno, 0
                    modify_queue.put([fileno, 0])
                    connections[fileno].shutdown(socket.SHUT_RDWR)
            elif event & select.EPOLLHUP:  # Hang up happened on the assoc. fd
                # epoll.unregister(fileno)
                if LOG_FLAG:
                    print "unregister_queue.put", fileno
                unregister_queue.put(fileno)  # TODO timeout, exception
                connections[fileno].close()
                del connections[fileno]