# build_files.sh
pip install -r requirements.txt
gunicorn --workers=3 wsgi:app --daemon