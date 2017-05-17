.PHONY: build-package
build-package:
	printf "#!/usr/bin/env python\n\n" > bin/dumdum
	cat dumdum.py >> bin/dumdum
	@find . | grep -v 'git'

.PHONY: upload-package
upload-package:
	@pip install twine
	rm -fr dist
	python setup.py sdist bdist_wheel
	twine register `ls dist/dumdum-*.tar.gz`
	twine register `ls dist/dumdum-*whl`
	twine upload dist/*
