all: test

format:
	black .
	isort .

test:
	black . --check
	isort -c .
	flake8 .
	mypy --ignore-missing-imports app
	pytest --strict -vvl --cov=app --cov-report=term-missing --cov-fail-under=85

clean:
	rm -rf log/*

