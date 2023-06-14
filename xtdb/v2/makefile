PORT=3001
run:
	docker run -ti --rm -p 5432:5432 -p 9832:9832 -p $(PORT):3000 ghcr.io/xtdb/xtdb-ea
dload:
	docker pull ghcr.io/xtdb/xtdb-ea

## show :3000 as :3001 ; needs hacking SSL.* in /usr/lib/python3.10/site-packages/mitmproxy/net/tls.py
PORTNEW=3001
mitm:
	mitmproxy --mode reverse:http://localhost:$(PORT) -p $(PORTNEW)

# vim:ts=4:sw=4:noexpandtab
