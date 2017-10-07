#!/usr/bin/env python3

import gmr_lib
import json
import sys

g = gmr_lib.GMRClient(sys.argv[1] if len(sys.argv) >= 2 else None)
assert g.auth_key is not None

def prn(g):
	print(json.dumps({'Games': g.session.games, 'Players': g.session.players}, indent = 2))

g.main_loop(prn)

