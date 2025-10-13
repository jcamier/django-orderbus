# django-orderbus

## Project steps

uv venv # setup virtual env

source .venv/bin/activate

uv pip install django djangorestframework

django-admin startproject orderbus .

python manage.py startapp orders

uv pip install -e ".[dev]"

make setup
