#!/bin/bash
REMOTE_HOST=hetzner

rsync -avP --delete ./ ${REMOTE_HOST}:/root/homelab-dashboard
ssh ${REMOTE_HOST} "cd /root/homelab-dashboard && docker compose down && docker rmi homelab-dashboard-app && docker compose up -d"

echo "Remote restart completed on ${REMOTE_HOST}"