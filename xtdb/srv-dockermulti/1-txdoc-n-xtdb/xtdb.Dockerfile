FROM clojure:openjdk-11-tools-deps
#debian based
RUN apt-get update
RUN apt-get install -y curl

WORKDIR /usr/lib/xtdb
VOLUME /var/lib/xtdb

ADD deps.edn deps.edn
RUN mkdir /usr/lib/xtdb/resources
ADD resources/logback.xml resources/logback.xml
RUN clojure -Sforce -Spath >/dev/null

EXPOSE 3000

#HEALTHCHECK --interval=30s --timeout=3s --start-period=30s \
#    CMD curl --fail http://localhost:3000/_xtdb/status || exit 1
#    # exit 1: unhealthy - the container is not working correctly

#for rocksdb-memory
ENV MALLOC_ARENA_MAX=2

ADD cfg-xtdb.edn cfg-xtdb.edn
ARG GROUPID
###XXX no, this makes the image different
#RUN perl -ne "s/GROUPID/$GROUPID/;print" cfg-xtdb.edn > xtdb.edn	
#ENTRYPOINT ["clojure", "-m", "xtdb.main"]

ENV GROUPID=${GROUPID:-nogroupid}
CMD perl -ne "s/GROUPID/$GROUPID/;print" cfg-xtdb.edn > xtdb.edn && cat xtdb.edn && exec clojure -m xtdb.main

# vim:ts=4:sw=4:expandtab
