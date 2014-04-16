The files in this directory are for collecting overall seattlegeni stats and
showing some pretty graphs with the data.

The idea is to put the public_html files somewhere web-accessible, and then
cron the running of scripts/update_graph_data.sh every ten minutes (or however
often you'd like) so that it updates files named *.txt that live in the
public_html directory.

When new versions are released, two files need to be manually updated on
the server they are on (not in svn):
  * public_html/version_events.txt
  * scripts/update_graph_data.sh

