#
# Makefile by Carl J. Nobile
#

include include.mk

PREFIX		= $(shell pwd)
PACKAGE_DIR	= $(shell echo $${PWD\#\#*/})
DISTNAME	= $(PACKAGE_DIR)-$(VERSION)
LOGS_DIR	= $(PREFIX)/logs
DOCS_DIR	= $(PREFIX)/docs
TODAY		= $(shell date +"%Y-%m-%d_%H%M")
RM_REGEX	= '(^.*.pyc$$)|(^.*.wsgic$$)|(^.*~$$)|(.*\#$$)|(^.*,cover$$)'
RM_CMD		= find $(PREFIX) -regextype posix-egrep -regex $(RM_REGEX) \
                  -exec rm {} \;
COVERAGE_DIR	= $(PREFIX)/.coverage_tests
COVERAGE_FILE	= $(PREFIX)/.coveragerc
PIP_ARGS	= # Pass var for pip install.

#----------------------------------------------------------------------
all	: tar

#----------------------------------------------------------------------
.PHONY	: tar
tar	: clean
	@(cd ..; tar -czvf $(DISTNAME).tar.gz --exclude=".git" \
          --exclude="logs/*.log" --exclude="dist/*" $(PACKAGE_DIR))

.PHONY	: tests
tests	: clean
	@rm -rf $(DOCS_DIR)/htmlcov
	@coverage erase --rcfile=$(COVERAGE_FILE)
	$${VIRTUAL_ENV}/bin/coverage run --rcfile=$(COVERAGE_FILE) \
        $${VIRTUAL_ENV}/bin/nosetests --nologcapture
	@coverage report --rcfile=$(COVERAGE_FILE)
	@echo $(TODAY)

# To add a pre-release candidate such as 'rc1' to a test package name an
# environment variable needs to be set that setup.py can read.
#
# make build TEST_TAG=rc1
# make upload-test TEST_TAG=rc1
#
# The tarball would then be named python-daemon-2.0.0rc1.tar.gz
#
.PHONY	: build
build	: clean
	python setup.py sdist

.PHONY	: upload
upload	: clobber
	python setup.py sdist
	python setup.py bdist_wheel --universal
	twine upload --repository pypi dist/*

.PHONY	: upload-test
upload-test: clobber
	python setup.py sdist
	python setup.py bdist_wheel --universal
	twine upload --repository testpypi dist/*

.PHONY	: install-dev
install-dev:
	pip install $(PIP_ARGS) -r requirements/development.txt

#----------------------------------------------------------------------
.PHONY	: clean
clean	:
	$(shell $(RM_CMD))
	@rm -rf *.egg-info
	@rm -rf dist

.PHONY	: clobber
clobber	: clean
	@rm -f $(LOGS_DIR)/*.log
	@rm -f $(LOGS_DIR)/*.pid
	@rm -f $(LOGS_DIR)/*.txt
	@rm -rf __pycache__
	@rm -rf build dist
