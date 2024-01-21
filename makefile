#a: story
now: test

story:
	python -m datomic.astory2da
	python -m xtdb.astory2xt


.PHONY: tags test tests
export PYTHONPATH=`pwd`
test tests:	#non-db
	python -m base.qsyntax
	python -m base.test_qs
	python -m base.test_symbols
	python -m xtdb.test_query
	python -m datomic.schema
	#tests2:		#non-db2
	python -m xtdb.lucene
	python -m xtdb.test_requests
	python -m base.schema
	python -m base.test_objmap
	python -m base.objmapper
	python -m base.astory
	python -m datomic.mbrainz_schema
tests-xt test-xt xt:
	python -m xtdb.testdb
	-cd xtdb/ && PYTHONPATH=.. python try.py
	-python -m xtdb.astory2xt
tests-da test-da da:
	cd datomic/ && PYTHONPATH=.. python try.py
	cd datomic/ && PYTHONPATH=.. python try_mbrainz.py
	#cd datomic/ && PYTHONPATH=.. python story.py
	cd datomic/ && PYTHONPATH=.. python astory2da.py
tests-xt2 test-xt2 xt2:
	cd xtdb2/ && PYTHONPATH=.. python qs2.py
	-cd xtdb2/ && PYTHONPATH=.. python try2.py
all: test
	#$(MAKE) tests2
	$(MAKE) tests-xt
	$(MAKE) tests-xt2
	$(MAKE) tests-da

EXCLUDES= 1 dist xtdb*/others xtdb/srv*/* datomic/datomic-*/* datomic/mbrainz*
PYPACKS = $(VIRTUAL_ENV)/lib/python3*/site-packages
tags ctags:
	ctags $(EXCLUDES:%=--exclude="%") --links=no -R . $(PYPACKS)/edn_format $(PYPACKS)/transit

PROFILER = -m cProfile -o _profile
try:
	PYTHONPATH=. $(_ENVVARS) $(ENVVARS) python $(PROFILER) xtdb/try.py

try2: _ENVVARS= XTDB2=1 PORT=3002
try2: try

# vim:ts=4:sw=4:noexpandtab
