.PHONY: setup \
	run \
	db \
	createsuperuser \
	black \
	flake8 \
	mypy \


# alias for virtual environment
virtualenv:
	python3 -m venv venv

# project setup
setup: virtualenv
	. venv/bin/activate; pip install pip wheel setuptools
	. venv/bin/activate; pip install -r requirements.txt

# run server
run: virtualenv
	. venv/bin/activate; python ./manage.py runserver

# run migrations
db: virtualenv
	. venv/bin/activate; python ./manage.py migrate

# create superuser
createsuperuser: virtualenv
	. venv/bin/activate; python ./manage.py createsuperuser

# format code with black
black: virtualenv
	. venv/bin/activate; black ./

# check codestyle with flake8
flake8: virtualenv
	. venv/bin/activate; flake8 ./

# check types with mypy
mypy: virtualenv
	. venv/bin/activate; mypy ./
