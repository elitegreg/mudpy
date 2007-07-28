#!/bin/bash
OTHER_TESTS="reactor"

cd `dirname $0`

export COVERAGE_FILE="`pwd`/.coverage"
export PYTHONPATH=.:$PYTHONPATH

rm -f $COVERAGE_FILE

# run tests in subdirs first
for other_test in $OTHER_TESTS
do
  ${other_test}/run_tests.sh
  if [ $? -ne 0 ]
  then
    echo "ERROR: ${other_test}"
    exit 1
  fi
done

# run tests/
for t in tests/*.py
do
  utils/coverage.py -x ${t}
  if [ $? -ne 0 ]
  then
    echo "ERROR: ${t}"
    exit 1
  fi
done

# Check coverage
./check_coverage.py

if [ $? -ne 0 ]
then
  echo "ERROR: coverage check failed"
  exit 1
fi

