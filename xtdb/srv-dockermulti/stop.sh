#!/bin/sh
docker-compose down -t 55
#seems this timeout is ignored, only whats inside stop_grace_period: matters
