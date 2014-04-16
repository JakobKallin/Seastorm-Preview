#!/usr/bin/env bash

# This script runs all seattlegeni tests. It sends all output to stdout/stderr
# and exits with a non-zero if any tests fail.
#
# Usage: ./run_tests.sh trunkdir

trunkdir=$1

if [ ! -d "$trunkdir" ]; then
  echo "Usage: $0 trunkdir"
  exit 1
fi

# Whether any tests failed.
failure=0

# Deploy to a tmp directory.
# A mktemp command that works on mac/bsd and linux.
tmpdir=`mktemp -d -t tmp.XXXXXXXX` || exit 1

utf=$trunkdir/utf/utf.py
utfutil=$trunkdir/utf/utfutil.py

statekeys=$trunkdir/seattlegeni/node_state_transitions/statekeys

python $trunkdir/seattlegeni/deploymentscripts/deploy_seattlegeni.py $trunkdir $tmpdir/deploy

# Copy over the state keys as the deployment script doesn't do that.
cp -r $statekeys $tmpdir/deploy/seattlegeni/node_state_transitions/

pushd $tmpdir/deploy/seattlegeni

export PYTHONPATH=$tmpdir/deploy:$tmpdir/deploy/seattle:$PYTHONPATH
export DJANGO_SETTINGS_MODULE=seattlegeni.website.settings

##############################################################################
# Run the website core functionality tests.
##############################################################################
echo "############# Website core functionality tests #############"
pushd website/tests

# We assume each of these tests is a python script that returns a non-zero
# exit code on failure.

cp $utf ./utf.py
cp $utfutil ./utfutil.py


if [ -e file.txt ]; then
  echo "Filename 'file.txt' or 'results.txt' already exists, skipping website tests <ERROR>"
  failure=1
else 
  python utf.py -m website > file.txt
  retval=$?

  cat file.txt
  numErrors=`cat file.txt | egrep '(FAIL|ERROR)' | wc -l`
  
  if [ "$retval" != "0" -o $numErrors -gt 0 ]; then
    failure=1
  fi

  rm file.txt
fi 

rm utf.py
rm utfutil.py

popd

##############################################################################
# Run the html frontend tests.
##############################################################################
echo "############# html frontend tests #############"
pushd website/html/tests


cp $utf ./utf.py
cp $utfutil ./utfutil.py


if [ -e file.txt ]; then
  echo "Filename 'file.txt' or 'results.txt' already exists, skipping html tests"
  failure=1
else 
  python utf.py -m html > file.txt
  retval=$?

  cat file.txt
  numErrors=`cat file.txt | egrep '(FAIL|ERROR)' | wc -l`

  if [ "$retval" != "0" -o $numErrors -gt 0 ]; then
    failure=1
  fi
  rm file.txt
fi 

rm utf.py
rm utfutil.py

popd

##############################################################################
# Run the xmlrpc frontend tests.
##############################################################################
echo "############# xmlrpc frontend tests #############"
pushd website/xmlrpc/tests


cp $utf ./utf.py
cp $utfutil ./utfutil.py


if [ -e file.txt ]; then
  echo "Filename 'file.txt' already exists, skipping xmlrpc tests <ERROR>"
  failure=1
else 
  python utf.py -m xmlrpc > file.txt
  retval=$?

  cat file.txt
  numErrors=`cat file.txt | egrep '(FAIL|ERROR)' | wc -l`
  
  if [ "$retval" != "0" -o $numErrors -gt 0 ]; then
    failure=1
  fi

  rm file.txt
fi 

rm utf.py
rm utfutil.py

popd

##############################################################################
# Run the lockserver tests.
##############################################################################
echo "############# Lockserver tests #############"
pushd lockserver/tests


./run_all_tests.sh $trunkdir

if [ "$?" != "0" ]; then
  failure=1
fi

popd

##############################################################################
# Run the transition script tests.
##############################################################################
echo "############# Transition script tests #############"
pushd node_state_transitions/tests

cp $utf ./utf.py
cp $utfutil ./utfutil.py


if [ -e file.txt ]; then
  echo "Filename 'file.txt' or 'results.txt' already exists, skipping nodestatetransitions tests <ERROR>"
  failure=1
else 
  python utf.py -m nodestatetransitions > file.txt
  retval=$?  

  numErrors=`cat file.txt | egrep '(FAIL|ERROR)' | wc -l`
  cat file.txt
 
  if [ $numErrors -gt 0 -o "$retval" != "0" ]; then
    failure=1
  fi
  rm file.txt
fi 
rm utf.py
rm utfutil.py

popd

##############################################################################
# Clean up and exit.
##############################################################################
popd
rm -rf $tmpdir

echo "############# All tests completed #############"

if [ "$failure" == "0" ]; then
  echo "All tests passed."
else
  echo "Some tests failed."
fi

exit $failure

