#!/bin/bash

# <Author>
#   Justin Samuel
# <Date Started>
#   August 13, 2009
# <Purpose>
#   This script will start the various components of SeattleGeni in the correct
#   order (namely, lockserver first, then backend, then the rest). It will also
#   gracefully restart apache. This script should be used rather than
#   stopping/starting components individually to ensure that all components use
#   a fresh lockserver after they have been restarted.
# <Usage>
#    As root, run:
#      ./start_seattlegeni_components.sh
#    Once started, the processes will not exit until its children have. To kill
#    all components of seattlegeni (except apache), send a SIGINT or SIGTERM to
#    this process.

export PYTHONPATH="/home/geni/live/:/home/geni/live/seattle:/usr/local/lib/python2.5/site-packages"
export DJANGO_SETTINGS_MODULE="seattlegeni.website.settings"

# The seattlegeni/ directory in the directory deployed to (by the deployment script)
SEATTLECLEARINGHOUSE_DIR="/home/geni/live/seattlegeni"

# The directory that output to stdout/stderr will be logged to.
LOG_DIR="/home/geni/logs"

# A sude cmd to run processes as the user 'geni' with the correct environment
# variables for django.
SUDO_CMD="sudo -u geni PYTHONPATH=$PYTHONPATH DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"

# When run via crontab, the $USER environment variable may not be set.
if [ "$USER" == "" ]; then
  USER=`whoami`
fi

if [ "$USER" != "root" ]; then
  echo "You must run this script as root. Exiting."
  exit 1
fi

# ignore our grep script and also ignore screen instances...
ALREADY_RUNNING_COUNT=`ps -ef | grep start_seattlegeni_components.sh | grep -v grep | grep -v -i screen | grep -v $$ | wc -l`
# We expect one copy to be running, at least (this one).
if [ "$ALREADY_RUNNING_COUNT" != "0" ]; then
  echo "There appears to already be a copy of start_seattlegeni_components.sh running."
  echo "You'll need to kill the other running copy first."
  exit 1
fi

function shutdown() {
  echo "Shutting down seattlegeni components."
  # Tell kill to kill the process group (so, kill children) by giving a negative process id.
  # Note: "--" means the end of options
  kill -- -$$
  wait
  exit
}

# Catch the signals from a CTRL-C or "kill this_pid".
trap "shutdown" SIGINT SIGTERM

echo "Starting lockserver."
$SUDO_CMD python $SEATTLECLEARINGHOUSE_DIR/lockserver/lockserver_daemon.py >>$LOG_DIR/lockserver.log 2>&1 &
sleep 1 # Wait a moment to make sure it has started (lockserver is used by other components).

echo "Starting backend."
# We use dylink to enable affixes.  Dylink only imports from the current directory...
cd $SEATTLECLEARINGHOUSE_DIR/backend/ && $SUDO_CMD python backend_daemon.py >>$LOG_DIR/backend.log 2>&1 &
sleep 1 # Wait a moment to make sure it has started (backend is used by other components).

echo "Gracefully restarting apache."
apache2ctl graceful

echo "Starting check_active_db_nodes.py."
# We use dylink to enable affixes.  Dylink only imports from the current directory...
cd $SEATTLECLEARINGHOUSE_DIR/polling/ && $SUDO_CMD python check_active_db_nodes.py >>$LOG_DIR/check_active_db_nodes.log 2>&1 &
sleep 1 # We need to wait for each process to start before beginning the next
        # because repyhelper has an issue with concurrent file access. 
        # (OBSOLETE?)

# Note: Don't put a ".py" on the end of the TRANSITION_NAME values.

TRANSITION_NAME=transition_donation_to_canonical
echo "Starting transition script $TRANSITION_NAME"
# We use dylink to enable affixes.  Dylink only imports from the current directory...
cd $SEATTLECLEARINGHOUSE_DIR/node_state_transitions/ && $SUDO_CMD python $TRANSITION_NAME.py >>$LOG_DIR/$TRANSITION_NAME.log 2>&1 &
sleep 1

TRANSITION_NAME=transition_canonical_to_twopercent
echo "Starting transition script $TRANSITION_NAME"
# We use dylink to enable affixes.  Dylink only imports from the current directory...
cd $SEATTLECLEARINGHOUSE_DIR/node_state_transitions/ && $SUDO_CMD python $TRANSITION_NAME.py >>$LOG_DIR/$TRANSITION_NAME.log 2>&1 &
sleep 1

TRANSITION_NAME=transition_twopercent_to_twopercent
echo "Starting transition script $TRANSITION_NAME"
# We use dylink to enable affixes.  Dylink only imports from the current directory...
cd $SEATTLECLEARINGHOUSE_DIR/node_state_transitions/ && $SUDO_CMD python $TRANSITION_NAME.py >>$LOG_DIR/$TRANSITION_NAME.log 2>&1 &
sleep 1

TRANSITION_NAME=transition_onepercentmanyevents_to_canonical
echo "Starting transition script $TRANSITION_NAME"
# We use dylink to enable affixes.  Dylink only imports from the current directory...
cd $SEATTLECLEARINGHOUSE_DIR/node_state_transitions/ && $SUDO_CMD python $TRANSITION_NAME.py >>$LOG_DIR/$TRANSITION_NAME.log 2>&1 &

echo "All components started. Kill this process (CTRL-C or 'kill $$') to stop all started components (except apache)."

# Wait for all background processes to terminate.
wait
