'''
This module provides the low-level network connections to the FQ API
daemon, either through a local UNIX-domain socket or through HTTPS.

Both of the client classes implement a single function, "request".  Pass
it the method (ie "GET"), resource path (ie "/1/server"), and optionally
a Python dict containing the input data for POST and PUT requests.  It
returns a Python dict containing the response data or raises the
exception fqapi.Error.

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

def format_request(method, path, body, headers):
	request = '%s %s HTTP/1.0\r\n' % (method, path)
	for h in headers:
		request += '%s: %s\r\n' (h, headers[h])
	if body is not None:
		body = json.dumps(body)
		request += 'Content-Length: %d\r\n' % len(body)
		request += 'Content-Type: application/json\r\n'
	request += '\r\n'
	if body:
		request += body
	return request

def read_response(resp):
	body = resp.read()
	body = json.loads(body) if body else None
	return resp.status, resp.reason, body

class Error(Exception):
	def __init__(self, code, msg):
		self.code = code
		self.msg = msg
	def __str__(self):
		return "%s %s" % (self.code, self.msg)
	def __repr__(self):
		return "fqapi.Error(%r, %r)" % (self.code, self.msg)

class GenericClient:
	def request(self, path, body=None):
		code,msg,data = self._request(path, body)
		if code <> 200:
			raise Error(code, msg)
		return data
	def get(self, path):
		return self.request('GET', path)
	def put(self, path, body):
		return self.request('PUT', path, body)
	def post(self, path, body):
		return self.request('POST', path, body)
	def delete(self, path):
		return self.request('DELETE', path)

	def ftp(self):
		return fqapi.ftp.FTP(self)

class LocalClient:
	'''An API client connecting to the server on the same computer'''
	def __init__(self, socket_path=None):
		self.socket_path = socket_path or _local_socket_path
	def _request(self, method, path, body=None):
		req = format_request(method, path, body, {})
		sock = socket.socket(socket.AF_UNIX)
		sock.connect(self.socket_path)
		sock.sendall(req)
		resp = httplib.HTTPResponse(sock, method=method)
		resp.begin()
		return read_response(resp)

class RemoteClient:
	'''An API client connecting to a server over HTTPS'''
	def __init__(self, domain, username, password, port=None):
		self.domain = domain
		self.httpconn = httplib.HTTPSConnection(domain, port or _remote_port)
		self.authorization = 'basic ' + base64.b64encode('%s:%s' % (username, password))
	def _request(self, method, path, body=None):
		body = json.dumps(body) if body is not None else None
		headers = self.httpconn.request(method, path, body, {
			'Authorization': self.authorization,
			'Content-Type': 'application/json',
			})
		resp = self.httpconn.getresponse()
		return read_response(resp)
