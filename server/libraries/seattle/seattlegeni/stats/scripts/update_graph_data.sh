export PYTHONPATH=$PYTHONPATH:/home/geni/live:/home/geni/live/seattle
export DJANGO_SETTINGS_MODULE='seattlegeni.website.settings'

CURRENT_VERSION="0.1o"

name=node_overview
/home/geni/scripts/print_data_point.py $name $CURRENT_VERSION >>/var/www/stats/seattlegeni/$name.txt 2>>/var/www/stats/seattlegeni/$name.err

name=node_type
/home/geni/scripts/print_data_point.py $name >>/var/www/stats/seattlegeni/$name.txt 2>>/var/www/stats/seattlegeni/$name.err

name=vessels
/home/geni/scripts/print_data_point.py $name >>/var/www/stats/seattlegeni/$name.txt 2>>/var/www/stats/seattlegeni/$name.err

name=advertise
/home/geni/scripts/print_data_point.py $name >>/var/www/stats/seattlegeni/$name.txt 2>>/var/www/stats/seattlegeni/$name.err

