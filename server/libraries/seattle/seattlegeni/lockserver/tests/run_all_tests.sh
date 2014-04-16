#!/bin/bash

trunkdir=$1
SCRIPT_DIR=`dirname $0`

some_tests_failed=0

# Make sure we are in the tests/ directory, as the tests will be expecting it
# to be the current working directory.
pushd $SCRIPT_DIR >/dev/null



#####################################################
##                LOCKSERVER UNIT TESTS            
#####################################################

cd ..
echo `pwd`
utf=$trunkdir/utf/utf.py
utfutil=$trunkdir/utf/utfutil.py


cp $utf ./utf.py
cp $utfutil ./utfutil.py
cp tests/unit/ut_*.py .

if [ -e file.txt ]; then
  echo "Filename 'file.txt' or 'results.txt' already exists, skipping lockserver unit tests <ERROR>"
  some_tests_failed=1
else 
  python utf.py -m lockserverunit > file.txt
  retval=$?

  numErrors=`cat file.txt | egrep '(FAIL|ERROR)' | wc -l`
  cat file.txt

  if [ $numErrors -gt 0 -o "$retval" != "0" ]; then
    some_tests_failed=1
  fi
  rm file.txt
fi 

rm utf.py
rm utfutil.py


####################################################
##              INTEGRATION TESTS
####################################################

cp $utf ./utf.py
cp $utfutil ./utfutil.py
cp ./tests/integration/ut_*.py .

if [ -e file.txt ]; then
  echo "Filename 'file.txt' already exists, skipping integration tests <ERROR>"
  some_tests_failed=1
else 
  python utf.py -m integration > file.txt
  retval=$?
 
  numErrors=`cat file.txt | egrep '(FAIL|ERROR)' | wc -l`
  cat file.txt

  if [ $numErrors -gt 0 -o "$retval" != "0" ]; then
    some_tests_failed=1
  fi
  rm file.txt
fi 

rm ut*.py

popd >/dev/null

if [ "$some_tests_failed" == "1" ]; then
  echo "Some tests failed."
  exit 1
fi

