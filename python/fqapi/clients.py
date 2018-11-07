import base64
try:
    import httplib
except ImportError:
    import http.client
    httplib = http.client
import json
import os
import socket
import ssl
import sys

_local_socket_path = '/FQ/CNCapi'
_remote_port = 987

from .errors import *

class HTTPSConnection(httplib.HTTPSConnection):
    def connect(self):
        sock = socket.create_connection((self.host, self.port),
                                        self.timeout, self.source_address)
        self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, ssl_version=ssl.PROTOCOL_TLSv1)

def _format_request(method, path, body, headers):
    request = '%s %s HTTP/1.1\r\n' % (method, path)
    for h in headers:
        request += '%s: %s\r\n' (h, headers[h])
    if body is not None:
        request += 'Content-Length: %d\r\n' % len(body)
        request += 'Content-Type: application/json\r\n'
    request += '\r\n'
    if body:
        request += body
    return request.encode('UTF-8')

def _read_response(resp):
    resp.begin()
    body = resp.read()
    body = json.loads(body.decode('UTF-8')) if body else None
    return resp.status, resp.reason, body

class GenericClient(object):
    '''
    Generic FQ CNC API client class.
    '''
    def request(self, method, path, body=None):
        """Make a request to the server.

        This routine is responsible for handling generic requests to the
        server.  Returns a dict or None, or raises fqapi.Error if the
        request failed.  Typically this routine would not be called by
        client code.  Use the get, put, post, and delete wrappers
        instead.

        Parameters:
        method -- the HTTP method to invoke
        path -- the absolute path to the resource
        body -- the data given to POST and PUT requests
        """
        body = json.dumps(body) if body is not None else None
        resp = self._request(method, path, body)
        code, msg, data = _read_response(resp)
        if code < 200 or code >= 300:
            raise Error(code, msg)
        return code,msg,data
    def get(self, path):
        """Issue a GET request."""
        return self.request('GET', path)
    def put(self, path, body):
        """Issue a PUT request."""
        return self.request('PUT', path, body)
    def post(self, path, body):
        """Issue a POST request."""
        return self.request('POST', path, body)
    def delete(self, path):
        """Issue a DELETE request."""
        return self.request('DELETE', path)

class LocalClient(GenericClient):
    """An API client connecting to the server on the same computer.
    Uses a `UNIX domain' socket to communicate with the server.
    Authentication is handled through standard UNIX credentials, so no
    extra passwords are needed."""
    def __init__(self, socket_path=None):
        """Initialize the client to connect to a local FQ CNC API server."""
        self.socket_path = socket_path or _local_socket_path
    def _request(self, method, path, body=None):
        req = _format_request(method, path, body, {})
        sock = socket.socket(socket.AF_UNIX)
        sock.connect(self.socket_path)
        sock.sendall(req)
        return httplib.HTTPResponse(sock, method=method)

class RemoteClient(GenericClient):
    """An API client connecting to a remote server.  Uses HTTPS over TCP
    to communicate with the server.  A username and password are
    required to authenticate the client."""
    def __init__(self, domain, username, password, port=None):
        """Initialize the client to connect to a remote FQ CNC API server.

        The `username' and `password' are the shell user name and
        password used to log in to either the CNC or SSH.
        """
        self.domain = domain
        self.httpconn = HTTPSConnection(domain, port or _remote_port)
        self.authorization = 'basic ' + base64.b64encode('{}:{}'.format(username, password).encode('UTF-8')).decode('ASCII')
    def _request(self, method, path, body=None):
        headers = self.httpconn.request(method, path, body, {
            'Authorization': self.authorization,
            'Content-Type': 'application/json',
            })
        return self.httpconn.getresponse()

class WrappingClient(GenericClient):
    """Enhanced FQ CNC API client class that traps error results.

    Attributes:
        errormsgs  A dictionary of error messages to provide in response to specific codes.
    """
    def __init__(self, errormsgs=None):
        self.errormsgs = {
            500: 'Internal API error',
        }
        self.errormsgs.update(errormsgs or {})

    def request(self, method, path, body=None):
        """Wrap the generic .request method and return only the result data.

        This method calls the generic .request method but traps
        errors by printing out a message and exiting the program
        with a non-zero code. Specific error messages for
        individual codes can be provided by setting
        client.errormsgs[CODE] to a string.

        Setting client.errormsgs[CODE] to None makes this
        wrapper treat that code as a valid return. This can be
        used to verify a resource doesn't already exist by
        setting client.errormsgs[200] to an error message and
        client.errormsgs[404] to None.
        """
        body = json.dumps(body) if body is not None else None
        resp = self._request(method, path, body)
        code, msg, data = _read_response(resp)
        if code in self.errormsgs:
            text = self.errormsgs[code]
        elif code < 200 or code >= 300:
            text = 'API error: {code} {msg}'
        else:
            text = None
        if text is None:
            return data
        text = text.format(code=code, msg=msg)
        program = os.path.basename(sys.argv[0])
        print('{}: {}'.format(program, text))
        exit(1)

class WrappingLocalClient(LocalClient, WrappingClient):
    def __init__(self, socket_path=None, errormsgs=None):
        LocalClient.__init__(self, socket_path)
        WrappingClient.__init__(self, errormsgs)

class WrappingRemoteClient(RemoteClient, WrappingClient):
    def __init__(self, domain, username, password, port=None, errormsgs=None):
        RemoteClient.__init__(self, domain, username, password, port)
        WrappingClient.__init__(self, errormsgs)
