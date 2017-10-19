#!/usr/bin/env python3

import gmr_lib
import json
import sys
import time

g = gmr_lib.GMRClient(sys.argv[1] if len(sys.argv) >= 2 else None)
assert g.auth_key is not None

def prn(g):
	p = g.session.players
	#print(json.dumps({'Games': g.session.games, 'Players': p}, indent = 2))
	print('Update! ({})'.format(time.ctime()))
	print('==========')
	for i in g.session.games:
		print(i['Name'])
		t = i['CurrentTurn']['PlayerNumber']
		for j, u in enumerate(i['Players']):
			if u:
				print('>' if j == t else ' ', p[u]['PersonaName'])
		print('==========')

def nturn(l):
	try:
		n = next(i for i in l if i['Name'] != 'Testbench')
	except StopIteration:
		return None
	print('Playing turn in {}...'.format(n['Name']))
	return n

g.main_loop(prn, nturn)

