def do_gunzip(b):
	import zlib
	return zlib.decompress(b, 31)


def do_gzip(b):
	import zlib
	z = zlib.compressobj(9, zlib.DEFLATED, 31, 9)
	r = z.compress(b)
	r += z.flush()
	return r


def load_and_compress(fname):
	with open(fname, 'rb') as f:
		return do_gzip(f.read())


def decompress_and_dump(fname, data):
	with open(fname, 'wb') as f:
		f.write(do_gunzip(data))


class GMRSession(object):
	def __init__(self, auth_key, interval = 5):
		self.auth_key = auth_key
		self.interval = interval
		import requests
		self.session = requests.Session()
		self.session.headers.update({'Accept': 'application/json'})
		self.uid = self.do_get('AuthenticateUser?authKey=' + self.auth_key)
		self.players = {self.uid: None}
		self.game_count = 1
		self.game_count_retries = 5
		self.update_status()

	def do_get(self, addr):
		r = self.session.get('http://multiplayerrobot.com/api/Diplomacy/' + addr)
		assert r.ok
		assert r.headers['Content-Type'] == 'application/json; charset=utf-8'
		return r.json()

	def update_status(self):
		r = self.do_get('GetGamesAndPlayers?playerIDText={}&authKey={}'
			.format('_'.join(str(i) for i in self.players), self.auth_key))
		for i in r['Players']:
			u = dict(i)
			j = u['SteamID']
			del u['SteamID']
			self.players[j] = u
		self.games = r['Games']
		f = False
		for i in self.games:
			pm = i['Players']
			pl = list(range(len(pm)))
			for j in pm:
				u = j['UserId']
				n = j['TurnOrder']
				pl[n] = u
				if u not in self.players:
					self.players[u] = None
					f = True
			i['Players'] = pl
		if f or (len(self.games) < self.game_count and self.game_count_retries > 0):
			if len(self.games) < self.game_count:
				self.game_count_retries -= 1
			import time
			time.sleep(self.interval)
			self.update_status()
		else:
			self.game_count_retries = 5
			self.game_count = len(self.games)

	def do_download(self, game_id, fname):
		r = self.session.get('http://multiplayerrobot.com/api/Diplomacy/' +
			'GetLatestSaveFileBytesCompressed?authKey={}&gameId={}'
			.format(self.auth_key, game_id))
		assert r.ok
		assert r.headers['Content-Type'] == 'application/octet-stream'
		assert r.headers['Content-Disposition'] == 'attachment; filename="(GMR) Play this one!.Civ5Save"'
		decompress_and_dump(fname, r.content)

	def do_upload(self, turn_id, fname):
		d = load_and_compress(fname)
		r = self.session.post('http://multiplayerrobot.com/Game/UploadSaveClient',
			data=[('turnId', str(turn_id)), ('isCompressed', 'True'), ('authKey', self.auth_key)],
			files=[('saveFileUpload', (str(turn_id) + '.Civ5Save', d))])
		assert r.ok
		assert r.headers['Content-Type'] == 'application/json; charset=utf-8'
		j = r.json()
		return j['ResultType'], j['PointsEarned']

	def close(self):
		try:
			self.session.close()
		except:
			pass


def shpath(*p):
	from os import path
	return path.expandvars(path.expanduser(path.join(*p)))


class GMRClient(object):
	def __init__(self, auth_key = None, cfgdir = '~/.local/share/gmr_client_py'):
		from os import path
		self.cfgdir = cfgdir
		self.auth_key = auth_key
		self.reload_config()
		self.proc = None

	def reload_config(self):
		import os
		cfgdir = shpath(self.cfgdir)
		if not os.path.isdir(cfgdir):
			os.mkdir(cfgdir)
		cfgfile = shpath(cfgdir, 'config')
		if not os.path.exists(cfgfile):
			self.save_dir = "~/.local/share/Aspyr/Sid Meier's Civilization 5/Saves/hotseat"
			self.civ_dir = '~/Civilization5'
			self.assets_subdir = 'steamassets/assets'
			self.cmdline = 'primusrun ./Civ5XP >/dev/null 2>&1'
			self.refresh_interval = 60
			self.minimum_interval = 5
			self.write_config()
		else:
			import json
			with open(cfgfile, 'r') as f:
				self.__dict__.update(json.load(f))
		self.reconnect()

	def write_config(self):
		import os
		import json
		cfgdir = shpath(self.cfgdir)
		if not os.path.isdir(cfgdir):
			os.mkdir(cfgdir)
		with open(shpath(self.cfgdir, 'config'), 'w') as f:
			json.dump({k: v for k, v in self.__dict__.items() if k in {
					'save_dir', 'civ_dir', 'assets_subdir', 'cmdline',
					'auth_key', 'refresh_interval', 'minimum_interval'}},
				f, indent = 4)

	def close(self):
		try:
			self.session.close()
		except:
			pass

	def reconnect(self):
		if self.auth_key is None:
			return
		self.close()
		self.session = GMRSession(self.auth_key, self.minimum_interval)

	def start_civ5(self):
		import subprocess
		import os
		self.proc = os.getpgid(subprocess.Popen(self.cmdline, shell = True,
			cwd = shpath(self.civ_dir), stdin = subprocess.DEVNULL,
			preexec_fn=os.setsid).pid)

	def stop_civ5(self):
		import os
		import signal
		if self.proc is not None:
			try:
				os.killpg(self.proc, signal.SIGKILL)
			except:
				pass
			self.proc = None

	def save_file(self, name):
		return shpath(self.save_dir, name + '.Civ5Save')

	def do_archive(self, name, copy = True, remove = True):
		import os
		adir = shpath(self.save_dir, 'archive')
		if not os.path.isdir(adir):
			os.mkdir(adir)
		dname = shpath(adir, name + '.Civ5Save')
		sname = self.save_file(name)
		if copy:
			with open(dname, 'wb') as t:
				with open(sname, 'rb') as f:
					t.write(f.read())
		if remove:
			os.unlink(sname)

	def download_save(self, game_id, name):
		self.session.do_download(game_id, self.save_file(name))

	def upload_save(self, turn_id, name):
		return self.session.do_upload(turn_id, self.save_file(name))

	def wait_for_save(self, name):
		fname = self.save_file(name)
		from os import path
		import time
		if not path.exists(fname):
			while not path.exists(fname):
				time.sleep(5)
		else:
			mt = path.getmtime(fname) + 5
			while mt > path.getmtime(fname):
				time.sleep(5)
		time.sleep(2)

	def do_turn(self, game):
		game_id = game['GameId']
		gname = game['Name']
		cturn = game['CurrentTurn']
		turn_id = cturn['TurnId']
		assert cturn['UserId'] == self.session.uid
		import re
		sname = '{}_{}_{}'.format(game_id, re.sub(r'[^A-Za-z_0-9.-]+', '', gname), turn_id)
		dname = sname + '_done'
		self.download_save(game_id, sname)
		self.do_archive(sname, remove = False)
		self.start_civ5()
		self.wait_for_save(dname)
		self.stop_civ5()
		self.do_archive(sname, copy = False)
		r = self.upload_save(turn_id, dname)
		self.do_archive(dname)
		return r

	def main_loop(self, upd_callback, turn_callback = lambda g: g[0]):
		import time
		games = None
		players = None
		while True:
			self.session.update_status()
			if games != self.session.games or players != self.session.players:
				upd_callback(self)
				games = self.session.games
				players = self.session.players
				g = [i for i in games if i['CurrentTurn']['UserId'] == self.session.uid]
				if g:
					g = turn_callback(g)
					if g is not None:
						self.do_turn(g)
						continue;
			time.sleep(self.refresh_interval)

