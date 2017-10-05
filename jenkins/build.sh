cp ~/secrets.py app/
virtualenv env
source env/bin/activate
pip install feedgen
pip install -r requirements.txt --upgrade
pip install . --upgrade
