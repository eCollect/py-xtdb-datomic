now: a b
a:
	-cd .. && python -m xtdb.test_requests $(ARGS)
b:
	-cd .. && python -m xtdb.testdb $(ARGS)
#	PYTHONPATH=.. python testdb.py

#b2: ARGS=x.test_status x.test_create

req:
	pip install -r ../requirements.txt

# vim:ts=4:sw=4:noexpandtab
