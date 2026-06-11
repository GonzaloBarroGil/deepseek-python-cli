install:
	pip install -e .

test:
	python -m pytest tests/ -v

validate-spec:
	python3 scripts/validate_spec.py

freeze:
	pip freeze > requirements-lock.txt

build:
	python -m build

publish:
	twine upload dist/*

