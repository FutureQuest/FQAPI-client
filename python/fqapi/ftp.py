"""
Accessor classes for handling FQ VAS FTP logins.

Example:

ftp = client.ftp()
account = ftp.add('newftp', 'www/ftp', 'wo')
account.modify(name='dropbox')
for account in ftp.list():
	print account.name, account.directory
"""

RO = 'ro'
RW = 'rw'
WO = 'wo'

class Account:
	"""A single FQ VAS FTP login."""
	def __init__(self, conn, data):
		self.conn = conn
		self._setup(data)

	def _setup(self, data):
		self.name = data['name']
		self.directory = data['directory']
		self.rw = data['rw']

	def delete(self):
		"""Delete this account on the server."""
		self.conn.delete('/1/ftp/%s' % self.name)

	def modify(self, name=None, directory=None, rw=None):
		"""Modify this account on the server."""
		data = self.conn.put('/1/ftp/%s' % self.name, {
			'name': name or self.name,
			'directory': directory or self.directory,
			'rw': rw or self.rw,
			})
		self._setup(data)
		return self

class FTP:
	def __init__(self, conn):
		self.conn = conn

	def list(self):
		"""List all the VAS FTP accounts.

		Returns a list of Account objects.
		"""
		data = self.conn.get('/1/ftp')
		return [
			Account(self.conn, item['name'], item['directory'], item['rw'])
			for item in data['accounts']
			]

	def add(self, name, directory, rw):
		"""Add an VAS FTP account.

		Returns a new Account object containing the current settings.
		"""
		data = self.conn.post('/1/ftp', {
			'name': name,
			'directory': directory,
			'rw': rw,
			})
		return Account(self.conn, data['name'], data['directory'], data['rw'])

	def delete(self, name):
		"""Delete the named VAS FTP account."""
		self.conn.delete('/1/ftp/%s'%name)

	def __iter__(self):
		return iter(self.list())
