#!/bin/bash

if [ -z "$SSA_DBNAME" -o -z "$SSA_DBHOST" -o -z "$SSA_DBUSER" -o -z "$SSA_DBPASS" ]; then
	echo >&2 'error: configuration is uninitialized and dbname/host/user/password option is not specified '
	echo >&2 '  You need to specify all of SSA_DBNAME, SSA_DBHOST, SSA_DBUSER and SSA_DBPASS'
	echo >&2 '  Optionally you can also specify SSA_MAILHOST, SSA_MAILUSER and SSA_MAILPASS'
	exit 1
fi

if ! grep -q 'Workaround for MySQL' /opt/Services-Status/ServiceStatus/settings.py; then
	cat >>/opt/Services-Status/ServiceStatus/settings.py <<EOF
# Workaround for MySQL error
from django.db.backends.mysql.base import DatabaseWrapper
DatabaseWrapper.data_types['DateTimeField'] = 'datetime' # fix for MySQL 5.5
EOF
fi

python3 -c "from django.core.management import utils; print('SECRET_KEY = \'' + utils.get_random_secret_key()+'\'')" > secret.txt
sed -i "s/^SECRET_KEY/#SECRET_KEY/g; /^#SECRET_KEY/ r secret.txt" /opt/Services-Status/ServiceStatus/settings.py
rm -f secret.txt
sed -i "s/ALLOWED_HOSTS = \[\]/ALLOWED_HOSTS = ['*']/" /opt/Services-Status/ServiceStatus/settings.py
sed -i "s/XXXDBNAMEXXX/$SSA_DBNAME/g" /opt/Services-Status/ServiceStatus/settings.py
sed -i "s/XXXDBUSERXXX/$SSA_DBUSER/g" /opt/Services-Status/ServiceStatus/settings.py
sed -i "s/XXXDBPASSXXX/$SSA_DBPASS/g" /opt/Services-Status/ServiceStatus/settings.py
sed -i "s/XXXDBHOSTXXX/$SSA_DBHOST/g" /opt/Services-Status/ServiceStatus/settings.py
sed -i "s/XXXSMTPHOSTXXX/$SSA_SMTPHOST/g" /opt/Services-Status/ServiceStatus/settings.py
sed -i "s/XXXSMTPUSERXXX/$SSA_SMTPUSER/g" /opt/Services-Status/ServiceStatus/settings.py
sed -i "s/XXXSMTPPASSXXX/$SSA_SMTPPASS/g" /opt/Services-Status/ServiceStatus/settings.py

for dir in uploads media; do
	if ! [ -L /opt/Services-Status/ServiceStatus/$dir ] || [ "$(readlink -- /opt/Services-Status/ServiceStatus/$dir)" != /var/www/$dir ]; then
		cd /opt/Services-Status/ServiceStatus
		[ -a $dir ] && /bin/mv -f $dir $dir-bkp
		ln -s /var/www/$dir $dir
	fi
done


cd /opt/Services-Status
sleep 30
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py create_initial_objects

/etc/init.d/nginx start
gunicorn --access-logfile - --workers 4 --user www-data --group www-data --bind 127.0.0.1:8800 --access-logformat '%(h)s/%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"' ServiceStatus.wsgi:application
