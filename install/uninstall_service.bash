#!/bin/bash
# 
# Script start in project folder.

systemctl stop smallcube
systemctl disable smallcube
rm /etc/systemd/system/smallcube.service
rm /etc/systemd/system/smallcube.service
rm /usr/lib/systemd/system/smallcube.service
rm /usr/lib/systemd/system/smallcube.service
systemctl daemon-reload
systemctl reset-failed

systemctl stop api_smallcube
systemctl disable api_smallcube
rm /etc/systemd/system/api_smallcube.service
rm /etc/systemd/system/api_smallcube.service
rm /usr/lib/systemd/system/api_smallcube.service
rm /usr/lib/systemd/system/api_smallcube.service
systemctl daemon-reload
systemctl reset-failed

rm -f /etc/nginx/sites-enabled/api_smallcube.nginx
rm -f /etc/nginx/sites-available/api_smallcube.nginx