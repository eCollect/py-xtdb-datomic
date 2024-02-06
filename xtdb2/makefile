now: tests
#try
#now: transit-tests
#now: qs

PORT=3002
REMOVE_AT_EXIT=--rm
#ARGS=--entrypoint bash		#just walk inside
#V2TAG=xtdb-ea
V2TAG=xtdb-standalone-ea
run:
	docker run -ti $(REMOVE_AT_EXIT) $(ARGS) -p $(PORT):3000 ghcr.io/xtdb/$(V2TAG) $(CMD)
dload upd update:
	docker pull ghcr.io/xtdb/$(V2TAG)
dr docker:
	sudo systemctl start docker

HOST=localhost
status:
	curl http://$(HOST):$(PORT)/status

## show :3000 as :3002 ; needs hacking SSL.* in /usr/lib/python3.10/site-packages/mitmproxy/net/tls.py
PORTNEW=3022
mitm:
	mitmproxy --mode reverse:http://localhost:$(PORT) -p $(PORTNEW)

clone:
	git clone -b 2.x --single-branch https://github.com/xtdb/xtdb/

test_req:
	-cd .. && python -m xtdb2.test_requests $(ARGS)
test_db:	#near-empty, use try.py instead
	-cd .. && python -m xtdb2.test_db $(ARGS)
tests:    test_req test_db

t2: ARGS=x.test_create
t2: test_db

qs:
	python qs.py
try:
	PYTHONPATH=.. python try.py $(ARGS)

test: qs try

t1:
	PYTHONPATH=.. python test_requests.py $(ARGS)

transit-tests tt-tests ttt:	#assuming . is where transit/ is
	PYTHONPATH=. python -m unittest tests/exemplars_test.py
	PYTHONPATH=. python -m unittest tests/regression_test.py

enc:
	python encode.py

.PHONY: bench
bench b:
	PYTHONPATH=. python bench-transit.py transit-format/examples/0.8/example.json

# vim:ts=4:sw=4:noexpandtab
