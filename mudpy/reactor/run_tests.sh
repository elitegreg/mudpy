#!/bin/sh
cd `dirname $0`

export PYTHONPATH=.

for test in tests/*.py
do
  ../utils/coverage.py -x ${test}
  if [ $? -ne 0 ]
  then
    echo "$test failed!"
    exit 1
  fi
done


