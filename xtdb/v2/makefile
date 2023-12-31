PORT=3001
REMOVE_AT_EXIT=--rm
#ARGS=--entrypoint bash		#just walk inside
#V2TAG=xtdb-ea
V2TAG=xtdb-standalone-ea
run:
	docker run -ti $(REMOVE_AT_EXIT) $(ARGS) -p $(PORT):3000 ghcr.io/xtdb/$(V2TAG) $(CMD)
#old	docker run -ti $(REMOVE_AT_EXIT) $(ARGS) -p 5432:5432 -p 9832:9832 -p $(PORT):3000 ghcr.io/xtdb/$(V2TAG) $(CMD)

dload:
	docker pull ghcr.io/xtdb/$(V2TAG)

status:
	curl http://localhost:$(PORT)/status

## show :3000 as :3001 ; needs hacking SSL.* in /usr/lib/python3.10/site-packages/mitmproxy/net/tls.py
PORTNEW=3001
mitm:
	mitmproxy --mode reverse:http://localhost:$(PORT) -p $(PORTNEW)

# vim:ts=4:sw=4:noexpandtab
