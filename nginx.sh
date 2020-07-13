cd /var/www/html/dme_api
source /var/www/deliver-me-env/bin/activate

sudo fuser -k 8080/tcp

sudo systemctl restart nginx

python manage.py runserver 8080 &

#sudo systemctl restart nginx

