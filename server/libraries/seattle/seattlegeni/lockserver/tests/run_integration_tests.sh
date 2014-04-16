#!/bin/bash

echo "Running integration tests."

for i in integration/*.py; do
  python $i >$i.output 2>&1
  retval=$?
  if [ "$retval" != "0" ]; then
    echo "Test " $i " failed"
    exit 1
  fi
done

echo "OK"

