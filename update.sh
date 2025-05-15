#!/bin/bash
REMOTE_HOST=hetzner

rsync -avP --delete ./ ${REMOTE_HOST}:/root/homelab-dashboard --exclude .git
ssh ${REMOTE_HOST} "cd /root/homelab-dashboard && docker compose down && docker compose up -d --build"

echo "Remote restart completed on ${REMOTE_HOST}"