import os.path
import socket
import select


class http_response:
    def __init__(self):
        self.status = 0
        self.date = ''
        self.content = ''
        self.content_type = ''

    def get_response_str(self):
        eol = b'\r\n'
        status = self.status + eol
        date = self.date + eol
        content_type = self.content_type + eol
        content_length = b'Content-Length: ' + str(len(self.content))
        content =  self.content + eol + eol

        return status + date + content_type + content_length + content

def get_http_response(path, head_only=False):
    # eol = b'\r\n'
    # status = b'HTTP/1.0 200 OK' + eol
    # date = b'Date: Mon, 1 Jan 1996 01:01:01 GMT' + eol
    # content_type = b'Content-Type: text/plain' + eol
    # content_length = b'Content-Length: '

    response = http_response()
    filename = '.' + path
    if os.path.isfile(filename):
        file = open(filename, 'r')
        data = file.read()
        # TODO
        file.close()
    else:
        # TODO
        pass
    content = b'Hello, world! Fuck the system! Fuck the people!'
    return content


def get_response_str(request_type, path):
    if request_type == 'GET':
        response = get_http_response(path)
    elif request_type == 'HEAD':
        response = get_http_response(path, True)
    else:
        # TODO error, wrong request type
        pass
    return response.get_response_str()


EOL1 = b'\n\n'
EOL2 = b'\n\r\n'

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
host = '127.0.0.1'
port = 80
serversocket.bind((host, port))
serversocket.listen(1)
serversocket.setblocking(0)

epoll = select.epoll()
epoll.register(serversocket.fileno(), select.EPOLLIN)

print('Server started on ' + host + ":" + str(port))

try:
    connections = {}
    requests = {}
    responses = {}
    while True:
        events = epoll.poll(1)
        for fileno, event in events:
            if fileno == serversocket.fileno():
                connection, address = serversocket.accept()
                connection.setblocking(0)
                epoll.register(connection.fileno(), select.EPOLLIN)
                connections[connection.fileno()] = connection
                requests[connection.fileno()] = b''
                # responses[connection.fileno()] = get_response()
            elif event & select.EPOLLIN:
                requests[fileno] += connections[fileno].recv(1024)
                if EOL1 in requests[fileno] or EOL2 in requests[fileno]:
                    request = requests[fileno].split(' ')
                    request_type = request[0]
                    path = request[1]
                    responses[fileno] = get_response_str(request_type, path)
                    epoll.modify(fileno, select.EPOLLOUT)
                    print('-' * 40 + '\n' + requests[fileno].decode()[:-2])
            elif event & select.EPOLLOUT:
                bytes_written = connections[fileno].send(responses[fileno])
                responses[fileno] = responses[fileno][bytes_written:]
                if len(responses[fileno]) == 0:
                    epoll.modify(fileno, 0)
                    connections[fileno].shutdown(socket.SHUT_RDWR)
            elif event & select.EPOLLHUP:
                epoll.unregister(fileno)
                connections[fileno].close()
                del connections[fileno]
finally:
    epoll.unregister(serversocket.fileno())
    epoll.close()
    serversocket.close()
