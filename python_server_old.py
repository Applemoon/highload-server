#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

import socket
import select
import Queue
from multiprocessing import Process
import multiprocessing
import worker_process_old


HOST = '127.0.0.1'
PORT = 80
# EOL1 = '\n\n'
# EOL2 = '\n\r\n'
LOG_FLAG = True
RECEIVE_SIZE = 1024
SOCKET_TIMEOUT = 10  # в секундах
CPU_NUMBER = 1  # TODO

if __name__ == '__main__':
    # Проверка переданных аргументов
    # TODO
    # str(sys.argv[1])

    # Настройка сокета сервера
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    server_socket.setblocking(0)

    epoll = select.epoll()
    epoll.register(server_socket.fileno(), select.EPOLLIN | select.EPOLLONESHOT)

    # events_queue = multiprocessing.Queue()
    register_queue = multiprocessing.Queue()
    modify_queue = multiprocessing.Queue()
    unregister_queue = multiprocessing.Queue()
    processes = list()

    if LOG_FLAG:
        print('Server started on %s:%s' % (HOST, str(PORT)))

    try:
        for i in range(CPU_NUMBER):
            # args = (server_socket, events_queue, register_queue, modify_queue, unregister_queue, epoll)
            args = (server_socket, None, register_queue, modify_queue, unregister_queue, epoll)
            p = Process(target=worker_process_old.child, args=args, name="Worker " + str(i))
            p.start()
            # p.join()  # TODO ?
            processes.append(p)

        while True:
            # events_queue.put(epoll.poll(1))  # TODO 1?

            # events = epoll.poll(1)  # TODO ждем событий 1 сек
            # print "events", events
            # for fileno, event in events:
            #     if LOG_FLAG:
            #         print "events.put", fileno, event
            #     events_queue.put([fileno, event])

            try:
                while not register_queue.empty():
                    fileno, event = register_queue.get_nowait()
                    if LOG_FLAG:
                        print os.getpid(), "register_queue.get", fileno, event
                    epoll.register(fileno, event)
            except Queue.Empty:
                # print "Empty"  # TODO
                pass

            try:
                while not modify_queue.empty():
                    fileno, event = modify_queue.get_nowait()
                    if LOG_FLAG:
                        print "modify_queue.get", fileno, event
                    epoll.modify(fileno, event)
            except Queue.Empty:
                # print "Empty"  # TODO
                pass

            try:
                while not unregister_queue.empty():
                    fileno = unregister_queue.get_nowait()
                    if LOG_FLAG:
                        print "unregister_queue.get", fileno
                    epoll.unregister(fileno)
            except Queue.Empty:
                # print "Empty"  # TODO
                pass

            # events = epoll.poll(1)
            # for fileno, event in events:
            #     if fileno == server_socket.fileno():
            #         connection_socket, address = server_socket.accept()  # Установлено соединение с клиентом
            #         connection_socket.settimeout(SOCKET_TIMEOUT)
            #         connection_socket.setblocking(0)
            #         epoll.register(connection_socket.fileno(), select.EPOLLIN)
            #         connections[connection_socket.fileno()] = connection_socket
            #         requests[connection_socket.fileno()] = ''
            #     elif event & select.EPOLLIN:  # Доступно для чтения
            #         requests[fileno] += connections[fileno].recv(RECEIVE_SIZE)  # Чтение запроса
            #         if EOL1 in requests[fileno] or EOL2 in requests[fileno]:
            #             request = requests[fileno].split(' ')
            #             method = request[0]
            #             path = request[1]
            #             response = HttpResponse(method, path)
            #             responses[fileno] = response.to_str()
            #             epoll.modify(fileno, select.EPOLLOUT)
            #             if LOG_FLAG:
            #                 print('-' * 40 + '\n' + requests[fileno].decode()[:-2])
            #     elif event & select.EPOLLOUT:  # Доступно для записи
            #         bytes_written = connections[fileno].send(responses[fileno])
            #         responses[fileno] = responses[fileno][bytes_written:]
            #         if len(responses[fileno]) == 0:
            #             epoll.modify(fileno, 0)
            #             connections[fileno].shutdown(socket.SHUT_RDWR)
            #     elif event & select.EPOLLHUP:  # Hang up happened on the assoc. fd
            #         epoll.unregister(fileno)
            #         connections[fileno].close()
            #         del connections[fileno]
    finally:
        epoll.unregister(server_socket.fileno())
        epoll.close()
        server_socket.close()

        for p in processes:
            p.terminate()

# TODO указывать папку со статикой '-r ROOTDIR'
# TODO указывать число процессоров '-c NCPU'
# TODO отладочный вывод по флагу '-l'

# TODO распределить обработку событий на разные потоки в зависимости от дескриптора сокета (?)