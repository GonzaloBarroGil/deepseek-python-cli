install:
	pip install -r requirements.txt
	chmod +x src/deepseek_cli.py
	ln -sf $(PWD)/src/deepseek_cli.py /usr/local/bin/deepseek-cli  # or use pip install -e .

test:
	python -m pytest tests/ -v

validate-spec:
	echo "Validating spec..."
	# Add JSON Schema validation of the spec file itself

freeze:
	pip freeze > requirements-lock.txt

