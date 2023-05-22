CDDAT=cd datomic-pro-*/

KEY=akey
SECRET=asecret

what:
	@echo what target? $(MAKEFILE_LIST)
	@perl -ne 'print if s/(^[A-Za-z0-9_][- A-Za-z0-9_.]*):.*/  $$1/' $(abspath $(MAKEFILE_LIST))

run:	#XXX NOT $(MAKE) but make , separate
	make transactor	#needs to run in background
	make rest		#needs to run... - talk to this one

#see config/samples/*transactor*.properties
transactor_FLAGS = -Ddatomic.printConnectionInfo=true
transactor:	 # kind=dev --> dev://localhost:4334
	$(CDDAT) && exec bin/transactor $(transactor_FLAGS) ../dev-transactor.properties &
	sleep 3
	pgrep -f -l clojure.main.*datomic.launcher | grep java
	echo $@-ok

#bin/run -m datomic.peer-server -h host -p port -a access-key,secret -d dbname,URI
#db-uri docs: https://docs.datomic.com/on-prem/javadoc/datomic/Peer.html#connect-java.lang.Object-
#The dev, free, and limited-edition protocols use an additional port to communicate with storage. By default it is one higher than the specified transactor port. You can override it by specifying h2-port in the query string

#XXX with the ending /
DBROOT= datomic:dev://localhost:4334/
DBNAME= adbname
DBURI = $(DBROOT)$(DBNAME)
#XXX beware: dbroot//aname means EMPTY NAME "", not aname !!! XXX and cannot be deleted once created..

createdb: #transactor
	$(CDDAT) && echo 'u="$(DBURI)"; Peer.createDatabase(u); Peer.connect(u);' | bin/shell
#Peer.createDatabase returns: true if just-created, false if exists
#shows console then exits
#$(CDDAT) && bin/shell ../create.adbname.shell
#does not show anything if success

peer: #createdb
	$(CDDAT) && bin/run -m datomic.peer-server -h localhost -p 8998 -a $(KEY),$(SECRET) -d hello,$(DBURI)
#KEY/SECRET = needed to connect to localhost:8998 for db-aliased 'hello'

console:
	$(CDDAT) && bin/console -p 8991 devv $(DBROOT)
#-> visit http://localhost:8991/browse -> see storage aliased as devv

#https://docs.datomic.com/on-prem/api/rest.html
rest:	#-o origins-for-CORS
	$(CDDAT) && exec bin/rest -p 8992 devv $(DBROOT) &
	sleep 3
	pgrep -f -l clojure.main.*datomic.rest | grep java && until curl localhost:8992/data/devv/ ; do sleep 2 ; done
	echo $@-ok
#-> http://localhost:8992/    ; storage is aliased as devv

stop:
	pkill -f clojure.main.*datomic

######

schema s:	#tests
	PYTHONPATH=.. python schema.py

mbrainz-import:
	# prints progress -- ~1,000 segments in restore
	XPWD=`pwd` && $(CDDAT) && bin/datomic restore-db file://$$XPWD/mbrainz-1968-1973 $(DBROOT)mbrainz-1968-1973

#no:
# gns24_pydatomic - https://github.com/gns24/pydatomic

# vim:ts=4:sw=4:noexpandtab
