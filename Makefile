all: test

test:
	#python3 -m unittest discover -v -s tests -p '*.py'
	python3 -m unittest discover -s tests -p 'parser_test.py'

.PHONY: coverage

coverage: 
	python3-coverage run --omit=tests/* -m unittest discover -v -s tests -p '*.py' || true
	find mudpy -name '*.py' -exec python3-coverage annotate -d coverage {} \; 

clean:
	rm -f .coverage

