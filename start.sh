nohup python3 machine_server.py >> machine_server.out &
nohup /usr/local/bin/gunicorn -w 20 -b 0.0.0.0:8888 web:app >> web.out &