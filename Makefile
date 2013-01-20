.PHONY: readme test clean

readme:
	python -c "import mangler; import tiddlywebplugins.gitstore as pkg; \
			print pkg.__doc__.strip()" > README

test: clean
	py.test -x --tb=short test

clean:
	find . -name "*.pyc" | xargs rm || true
	rm -rf html .figleaf coverage.lst # figleaf
	rm -rf htmlcov .coverage # coverage
	rm -rf test/__pycache__ # pytest
