export FLASK_APP=portfolio.py

all: venv install run

venv:
	@if [ ! -d "venv" ]; then python3 -m venv venv; fi

install:
	pip install -r requirements.txt || pip3 install -r requirements.txt

run:
	flask run --host 0.0.0.0 --port 5001

clean:
	rm -rf db/*.db
	rm -rf static/data/*.xml
	rm -rf static/data/*.csv
