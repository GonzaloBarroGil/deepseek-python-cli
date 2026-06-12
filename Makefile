install:
	pip install -e .

test:
	python -m pytest tests/ -v

validate-spec:
	python3 scripts/validate_spec.py

freeze:
	pip freeze > requirements-lock.txt

build:
	rm -rf dist/
	python -m build

publish:
	twine upload dist/*

.PHONY: install test validate-spec freeze build publish

