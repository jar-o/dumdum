.PHONY: build-package
build-package:
	cp ../dumdum.py .
	printf "#!/usr/bin/env python\n\n" > bin/dumdum
	cat ../dumdum.py >> bin/dumdum
	find .

.PHONY: upload-package
upload-package:
	@pip install twine
	rm -fr dist
	python setup.py sdist bdist_wheel
	twine register `ls dist/dumdum-*.tar.gz`
	twine register `ls dist/dumdum-*whl`
	twine upload dist/*
