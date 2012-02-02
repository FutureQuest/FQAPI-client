import fqapi

RO = 'ro'
RW = 'rw'
WO = 'wo'

class Account:
	def __init__(self, conn, data):
		self.conn = conn
		self.setup(data)

	def setup(self, data):
		self.name = data['name']
		self.directory = data['directory']
		self.rw = data['rw']

	def delete(self):
		self.conn.delete('/1/ftp/%s' % self.name)

	def modify(self, name=None, directory=None, rw=None):
		data = self.conn.put('/1/ftp/%s' % self.name, {
			'name': name or self.name,
			'directory': directory or self.directory,
			'rw': rw or self.rw,
			})
		self.setup(data)
		return self

class FTP:
	def __init__(self, conn):
		self.conn = conn

	def list(self):
		data = self.conn.get('/1/ftp')
		return [
			Account(self.conn, item['name'], item['directory'], item['rw'])
			for item in data['accounts']
			]

	def add(self, name, directory, rw):
		data = self.conn.post('/1/ftp', {
			'name': name,
			'directory': directory,
			'rw': rw,
			})
		return Account(self.conn, data['name'], data['directory'], data['rw'])

	def delete(self, name):
		self.conn.delete('/1/ftp/%s'%name)

	def __iter__(self):
		return iter(self.list())
