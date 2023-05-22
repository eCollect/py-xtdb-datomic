running docker:

install docker (latest is v20.*) and docker-compose (v 2.x and up) ;
addusergroup yourself docker i.e.
` $ sudo usermod -a -G docker yourself `

###############

for non-root docker:

copy ./etc/* over to /etc
e.g. 
etc/docker/daemon.json: "userns-remap": "default"

"default" means user/group named "dockremap"

restarting dockerd will create such user in host system (check with `$ id dockremap`);
the etc/subuid etc/subgid give namespace-ranges ;
docker-ed processes will run as first uid/gid of those ranges (231072), 
host volumes MUST be accessible to it , and created stuff there will be owned by it.
So far only way for this is `chmod a+rw those-paths` - do it if created externaly beforehand.
Or, docker-compose can create needed volume-paths alright, but umask inside seems missing group-write
and kafka needs the kafka/ one to be group-writable (???)
so after first start to create them, it will die ; stop it, add group-write permissions there,
` $ sudo chmod g+w -R data/`
then start again

beware, images roots are overlay-mounted inside /var/lib/docker/... 
which is by default on / root host filesystem. If no space there.. 
move the whole /var/lib/docker/ elsewhere-with-lots-of-space and symlink it as /var/lib/docker

###############

docker-desktop:

is a complete VM (via qemu) in which it runs the dockers - and it overwrites the docker/docker-compose with its own.. 
which maybe overkill. no need.
Ah, and that gui cannot be accessed from another machine via DISPLAY:...
Seems the _.docker/config.json with the "credStore" inside is only needed for docker-desktop

others:
$ docker ps
$ docker logs some-container-name

see whats some image from inside:
#$ docker run -it theimagename bash
$ docker run -it --entrypoint /bin/bash myimage

if some container dies, to see what's inside:
$ docker commit the-container-name newimagename
$ docker run -it newimagename bash
https://forums.docker.com/t/run-command-in-stopped-container/343/20

beware, after docker attach xxx , pressing ctrl-C will go inside and kill it..

# vim:ts=4:sw=4:expandtab
