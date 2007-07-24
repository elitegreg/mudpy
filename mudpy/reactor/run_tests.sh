#!/bin/sh
export PYTHONPATH=`dirname $0`

for test in tests/*.py
do
  echo $PYTHONPATH
  python $test
  if [ $? -ne 0 ]
  then
    echo "$test failed!"
    exit 1
  fi
done


