now: try

PORT=3002
REMOVE_AT_EXIT=--rm
#ARGS=--entrypoint bash		#just walk inside
#V2TAG=xtdb-ea
V2TAG=xtdb-standalone-ea
run:
	docker run -ti $(REMOVE_AT_EXIT) $(ARGS) -p $(PORT):3000 ghcr.io/xtdb/$(V2TAG) $(CMD)
#old	docker run -ti $(REMOVE_AT_EXIT) $(ARGS) -p 5432:5432 -p 9832:9832 -p $(PORT):3000 ghcr.io/xtdb/$(V2TAG) $(CMD)

dload upd update:
	docker pull ghcr.io/xtdb/$(V2TAG)

status:
	curl http://localhost:$(PORT)/status

## show :3000 as :3002 ; needs hacking SSL.* in /usr/lib/python3.10/site-packages/mitmproxy/net/tls.py
PORTNEW=3002
mitm:
	mitmproxy --mode reverse:http://localhost:$(PORT) -p $(PORTNEW)

clone:
	git clone -b 2.x --single-branch https://github.com/xtdb/xtdb/

test_req:
	-cd .. && python -m xtdb2.test_requests $(ARGS)
test_db:
	-cd .. && python -m xtdb2.test_db $(ARGS)

b2: ARGS=x.test_create
b2: test_db

q2:
	python qs2.py
try:
	PYTHONPATH=.. python try2.py $(ARGS)

test: q2 try

t1:
	PYTHONPATH=.. python test_requests.py $(ARGS)

# vim:ts=4:sw=4:noexpandtab
