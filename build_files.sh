# build_files.sh
pip install -r requirements.txt
gunicorn3 --workers=3 wsgi:app --daemon