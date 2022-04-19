#!/bin/bash
# 
# Script start in project folder.

cp smallcube.service /etc/systemd/system/
systemctl start smallcube
systemctl enable smallcube


cp api_smallcube.nginx /etc/nginx/sites-available/
ln -s /etc/nginx/sites-available/api_smallcube.nginx /etc/nginx/sites-enabled/

#$IP="ip -o route get 1.1.1.1 | cut -d " " -f 7"
#openssl req -x509 -days 3650 -nodes -newkey rsa:2048 \
#  -out /etc/ssl/private/self-sigend.crt \
#  -keyout /etc/ssl/private/self-sigend.key \
#  -subj "/C=PL/ST=Podkarpackie/L=Podkarpackie/O=NoXgle Sebastian Wielgosz/CN=ip"
#
#cp api_smallcube_ssl.nginx /etc/nginx/sites-available/
#ln -s /etc/nginx/sites-available/api_smallcube_ssl.nginx /etc/nginx/sites-enabled/

cp api_smallcube.service /etc/systemd/system/
systemctl restart nginx
systemctl start api_smallcube
systemctl enable api_smallcube

nginx -t
systemctl status smallcube
systemctl status api_smallcube