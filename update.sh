#!/bin/bash

python update_lists.py

git pull

if [ -n "$(git status --porcelain)" ]; then
  git add .
  git commit -m "Update tracker lists on $(date +'%Y-%m-%d %H:%M:%S')"
  git push origin main
  echo "Updates have been committed and pushed to the main branch."
else
  echo "No changes to commit."
fi