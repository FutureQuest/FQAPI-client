'''
This module provides the low-level network connections to the FQ CNC API
daemon, either through a local UNIX-domain socket or through HTTPS.

The client object implmenents functions for doing low-level access to
the server: get, put, post, and delete.  Pass these the resource path
(ie "/1/server"), and optionally a Python dict containing the input data
for POST and PUT requests.  They return a Python dict containing the
response data or raise the exception fqapi.Error.

For example:

import fqapi
client = fqapi.RemoteClient('example.com', 'username', 'password')
client = fqapi.LocalClient()
try:
	data = client.get("/1/server")
except fqapi.Error as error:
	# Handle exception
'''

import base64
import httplib
import json
import socket

import fqapi.ftp

_local_socket_path = '/var/run/FQapi'
_remote_port = 987

import socket, ssl

class HTTPSConnection(httplib.HTTPSConnection):
        def connect(self):
                sock = socket.create_connection((self.host, self.port),
                                                self.timeout, self.source_address)
                self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, ssl_version=ssl.PROTOCOL_TLSv1)

def _format_request(method, path, body, headers):
	request = '%s %s HTTP/1.0\r\n' % (method, path)
	for h in headers:
		request += '%s: %s\r\n' (h, headers[h])
	if body is not None:
		request += 'Content-Length: %d\r\n' % len(body)
		request += 'Content-Type: application/json\r\n'
	request += '\r\n'
	if body:
		request += body
	return request

def _read_response(resp):
	body = resp.read()
	body = json.loads(body) if body else None
	return resp.status, resp.reason, body

class Error(Exception):
	'''
	Error class used by all low-level client code.

	Object data:
	code -- the numerical code returned by the server, ie 500
	msg -- the text of the error message from the server
	'''
	def __init__(self, code, msg):
		self.code = code
		self.msg = msg
	def __str__(self):
		return "%s %s" % (self.code, self.msg)
	def __repr__(self):
		return "fqapi.Error(%r, %r)" % (self.code, self.msg)

class GenericClient:
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
		code,msg,data = self._request(method, path, body)
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

	def ftp(self):
		"""Return a new fqapi.ftp.FTP object."""
		return fqapi.ftp.FTP(self)

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
		resp = httplib.HTTPResponse(sock, method=method)
		resp.begin()
		return _read_response(resp)

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
		self.authorization = 'basic ' + base64.b64encode('%s:%s' % (username, password))
	def _request(self, method, path, body=None):
		headers = self.httpconn.request(method, path, body, {
			'Authorization': self.authorization,
			'Content-Type': 'application/json',
			})
		resp = self.httpconn.getresponse()
		return _read_response(resp)
