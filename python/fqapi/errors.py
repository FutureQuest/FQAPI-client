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
