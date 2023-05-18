# build_files.sh
pip install -r requirements.txt
gunicorn 127.0.0.1:5000 wsgi:app