#!/bin/bash
#
# Run a single test file with coverage.
#
# Arguments can take the following forms. Be aware of the : (colons) below.
#
# test.module
# another.test:TestCase.test_method
# another.test:TestCase
# /path/to/test/file.py:test_function
#

PREFIX=$(pwd)
COVERAGE_FILE=.coveragerc
VE_BIN=$VIRTUAL_ENV/bin
coverage erase --rcfile=${COVERAGE_FILE}
export TFT_TESTING=True
${VE_BIN}/coverage run --rcfile=${COVERAGE_FILE} ${VE_BIN}/nosetests $1 \
         --nologcapture
coverage report -m --rcfile=${COVERAGE_FILE}
