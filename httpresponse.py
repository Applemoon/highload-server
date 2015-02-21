#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import urllib2
import os.path

STATUS_OK = '200 OK'
STATUS_NOT_FOUND = '404 Not Found'
STATUS_METHOD_NOT_ALLOWED = '405 Method Not Allowed'
EOL3 = '\r\n'


class HttpResponse:
    def __init__(self, method_str, path_str):
        self.filename = ''
        self.content = ''
        self.status = STATUS_OK
        self.date = datetime.now().strftime('Date: %a, %d %b %Y %H:%M:%S GMT +3')
        self.server = 'Server: python-server (Unix)'
        self.connection = 'Connection: close'
        # self.connection = 'Connection: Keep-Alive'

        self.create_response(method_str, path_str)

    def create_response(self, method_str, path_str):
        self.filename = './DOCUMENT_ROOT' + path_str
        if self.filename.endswith('/'):
            self.filename += 'index.html'
        self.filename = urllib2.unquote(self.filename)
        if '?' in self.filename:
            self.filename = self.filename.split('?')[0]

        if method_str == 'GET' or method_str == 'HEAD':
            if '..' not in self.filename and os.path.isfile(self.filename):
                self.status = STATUS_OK
                if method_str != 'HEAD':
                    request_file = open(self.filename, 'r')
                    self.content = request_file.read()
                    request_file.close()
            else:
                self.status = STATUS_NOT_FOUND
        else:
            self.status = STATUS_METHOD_NOT_ALLOWED

    def to_str(self):
        response_str = 'HTTP/1.1 '
        response_str += self.status + EOL3
        response_str += self.date + EOL3
        response_str += self.server + EOL3
        response_str += self.connection + EOL3
        if self.status == STATUS_OK:
            response_str += self.get_content_type() + EOL3
            response_str += 'Content-Length: ' + str(len(self.content)) + EOL3
            response_str += EOL3  # Пустая строка
            response_str += self.content + EOL3

        print response_str
        return response_str

    def get_content_type(self):
        content_type = 'Content-Type: '
        if self.filename.lower().endswith('.html'):
            content_type += 'text/html'
        elif self.filename.lower().endswith('.css'):
            content_type += 'text/css'
        elif self.filename.lower().endswith('.js'):
            content_type += 'application/javascript'
        elif self.filename.lower().endswith('.jpg') or self.filename.lower().endswith('.jpeg'):
            content_type += 'image/jpeg'
        elif self.filename.lower().endswith('.png'):
            content_type += 'image/png'
        elif self.filename.lower().endswith('.gif'):
            content_type += 'image/gif'
        elif self.filename.lower().endswith('.swf'):
            content_type += 'application/x-shockwave-flash'
        else:
            content_type += 'text/plain'

        return content_type