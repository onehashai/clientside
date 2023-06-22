#!/usr/bin/env bash


# Pull and restart
cd /home/frappe/frappe-bench/apps/clientside
git add .
git stash
git pull
cd /home/frappe/frappe-bench/apps/setup_app
git add .
git stash
git pull
cd /home/frappe/frappe-bench/apps/whitelabel
git add .
git stash
git pull
bench --site app.onehash.store migrate
sudo supervisorctl restart all
sudo bench setup production frappe