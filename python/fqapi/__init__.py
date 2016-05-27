'''
This module provides the low-level network connections to the FQ CNC API
daemon, either through a local UNIX-domain socket or through HTTPS.

The client object implmenents functions for doing low-level access to
the server: get, put, post, and delete.  Pass these the resource path
(ie "/1/server"), and optionally a Python dict containing the input data
for POST and PUT requests.  They return a Python dict containing the
response data or raise the exception fqapi.Error.

Use LocalClient when the application will be running on the same server
as the API. Use RemoteClient when the application needs to access the
API from anywhere.

For example:

import fqapi
client = fqapi.RemoteClient('example.com', 'username', 'password')
client = fqapi.LocalClient()
try:
	data = client.get("/1/server")
except fqapi.Error as error:
	# Handle exception
'''

from .errors import *
from .clients import LocalClient, RemoteClient, WrappingLocalClient, WrappingRemoteClient
