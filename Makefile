install:
	uv pip install -r app/requirements.txt

test:
	export PYTHONPATH=app:. && pytest

run:
	export PYTHONPATH=app && fastapi run app/main.py
	
run-dev:
	export PYTHONPATH=app && fastapi dev app/main.py