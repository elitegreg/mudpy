#!/bin/bash

# Usage: ./run_tests.sh 

cd `dirname $0`

export COVERAGE_FILE="`pwd`/.coverage"
export PYTHONPATH=.:$PYTHONPATH

rm -f $COVERAGE_FILE

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

