#!/bin/bash

export PYTHONPATH=.:$PYTHONPATH

for t in tests/*.py
do
  python ${t}
  if [ $? -ne 0 ]
  then
    echo "ERROR: ${t}"
    exit 1
  fi
done

