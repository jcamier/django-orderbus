# django-orderbus

## Project steps

uv venv # setup virtual env

source .venv/bin/activate

uv pip install django djangorestframework

django-admin startproject orderbus .

python manage.py startapp orders

uv pip install -e ".[dev]"

make setup

# Generate a secure random secret for HMAC
python -c "import secrets; print(secrets.token_hex(32))"

# Add to your .env file:
# WEBHOOK_SECRET=<the-generated-secret>
