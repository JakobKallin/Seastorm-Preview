#!/bin/bash

echo "Running all the semantics test"

for f in *.py;
do
    echo -e '\n-------------------------------------------------------------'
    echo "Running test: $f"
    python $f
    echo -e '-------------------------------------------------------------\n'
done