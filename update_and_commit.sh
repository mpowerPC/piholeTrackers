#!/bin/bash

git config --global user.email $EMAIL

git remote set-url origin https://$GITHUB_USER:$GITHUB_TOKEN@github.com/mpowerPC/piholeTrackers.git

git pull origin main

python3 update_lists.py

if [ -n "$(git status --porcelain)" ]; then
  git add .
  git commit -m "Update tracker lists on $(date +'%Y-%m-%d %H:%M:%S')"
  git push origin main
  echo "Updates have been committed and pushed to the main branch."

  PIHOLE_API_URL="http://$PIHOLE_IP_ADDRESS/admin/api.php?auth=$PIHOLE_API_TOKEN&action=reload"
  curl -X GET "$PIHOLE_API_URL"

  echo "Pi-hole Gravity lists have been updated."
else
  echo "No changes to commit."
fi