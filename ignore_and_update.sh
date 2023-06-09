#!/usr/bin/env bash

# Pull and restart
cd /home/frappe/frappe-bench/apps/clientside
git add .
git stash
cd /home/frappe/frappe-bench/apps/setup_app
git add .
git stash
sudo bench update --no-backup
