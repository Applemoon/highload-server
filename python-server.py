import os.path
import socket
import select


EOL1 = b'\n\n'
EOL2 = b'\n\r\n'
EOL3 = b'\r\n'
STATUS_OK = 200
STATUS_NOT_FOUND = 404
STATUS_METHOD_NOT_ALLOWED = 405


class HttpResponse:
    def __init__(self):
        self.filename = ''
        self.status = STATUS_OK
        self.date = ''
        self.content = ''
        self.content_type = ''
        self.server = ''  # TODO
        self.connection = ''  # TODO

    def get_response_str(self):
        response_str = b'HTTP/1.1 '
        if self.status == STATUS_OK:
            response_str += b'200 OK' + EOL3
        else:
            response_str += b'404 Not Found' + EOL3
        response_str += self.date + EOL3
        if self.status == STATUS_OK:
            self.set_content_type()
            response_str += self.content_type
            response_str += b'Content-Length: ' + str(len(self.content)) + EOL3 + EOL3
            response_str += self.content + EOL3

        return response_str

    def set_date_header(self):
        self.date = b'Date: Mon, 1 Jan 1996 01:01:01 GMT'  # TODO

    def set_server_header(self):
        self.server = ''   # TODO

    def set_connection_header(self):
        self.connection = ''  # TODO

    def set_content_type(self):
        self.content_type = b'Content-Type: '
        if self.filename.lower().endswith('.html'):
            self.content_type += b'text/html'
        elif self.filename.lower().endswith('.css'):
            self.content_type += b'text/css'
        elif self.filename.lower().endswith('.js'):
            self.content_type += b'application/javascript'
        elif self.filename.lower().endswith('.jpg') or self.filename.lower().endswith('.jpeg'):
            self.content_type += b'image/jpeg'
        elif self.filename.lower().endswith('.png'):
            self.content_type += b'image/png'
        elif self.filename.lower().endswith('.gif'):
            self.content_type += b'image/gif'
        elif self.filename.lower().endswith('.swf'):
            self.content_type += b'application/x-shockwave-flash'
        else:
            self.content_type = b'text/plain'

        self.content_type += EOL3


def get_http_response(path_str, head_only=False):
    response = HttpResponse()
    response.filename = './DOCUMENT_ROOT/' + path_str
    if response.filename.endswith('/'):
        response.filename += 'index.html'

    if os.path.isfile(response.filename):
        request_file = open(response.filename, 'r')
        data = request_file.read()
        request_file.close()
        if not head_only:
            response.content = data
    else:
        response.status = STATUS_NOT_FOUND
        # TODO content type?

    return response


def get_response_str(method_str, path_str):
    if method_str == 'GET':
        response = get_http_response(path_str)
    elif method_str == 'HEAD':
        response = get_http_response(path_str, True)
    else:
        response = HttpResponse()
        response.status = STATUS_NOT_FOUND

    response.set_server_header()
    response.set_date_header()
    response.set_connection_header()
    return response.get_response_str()


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
            elif event & select.EPOLLIN:
                requests[fileno] += connections[fileno].recv(1024)
                if EOL1 in requests[fileno] or EOL2 in requests[fileno]:
                    request = requests[fileno].split(' ')
                    method = request[0]
                    path = request[1]
                    responses[fileno] = get_response_str(method, path)
                    epoll.modify(fileno, select.EPOLLOUT)
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
