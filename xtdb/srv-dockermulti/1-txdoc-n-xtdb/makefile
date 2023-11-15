MAKEFLAGS=-r

NAME=ok
X1= $(NAME)-xtdb-1-1
X2= $(NAME)-xtdb-2-1
X3= $(NAME)-xtdb-3-1
X4= $(NAME)-xtdb-4-1
X5= $(NAME)-xtdb-5-1
XK= $(NAME)-kafka-1
XC= $(NAME)-chkpt-1
XP= $(NAME)-pg-1
Xk=$(XK)
Xkafka=$(XK)
Xc=$(XC)
Xchkpt=$(XC)
Xp=$(XP)
Xpg=$(XP)

now:
	@echo "targets: {who}.{what} ; du ; ls ;;; who: 1 2 3 k/kafka c/chkpt p/pg ; what: l/log stop run bash ; e.g. k.run"

%.log %.l log.% l.%:
	docker logs $(X$*) $(TAIL)

%.stop stop.%:
	docker stop $(X$*) -t 55

%.start start.% %.run run.%:
	docker start $(X$*)

#run image then bash instead of everything else
%.bash bash.% %.sh sh.%:
	docker run -it --entrypoint /bin/bash $(X$*)

lall logall alll alllog: export TAIL=|tail -5
lall logall alll alllog:
	$(MAKE) l.p
	$(MAKE) l.k
	$(MAKE) l.1
	$(MAKE) l.2

du:
	du -msc data/[kp]*/  data/xtdb*/*/  data/chkpt*/*/*/

drls ls:
	docker container ls -a
	docker image ls -a
	docker volume ls

# vim:ts=4:sw=4:noexpandtab
