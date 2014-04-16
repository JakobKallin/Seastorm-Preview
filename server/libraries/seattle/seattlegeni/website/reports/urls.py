from django.conf.urls.defaults import *

urlpatterns = patterns('seattlegeni.website.reports.views',

                       (r'^$', 'index', {}, 'index'),
                       (r'^all$', 'all', {}, 'all'),
                       (r'^donations$', 'donations', {}, 'donations'),
                       (r'^acquired_vessels$', 'acquired_vessels', {}, 'acquired_vessels'),
                       (r'^vessels_by_port$', 'vessels_by_port', {}, 'vessels_by_port'),
                       (r'^lan_sizes_by_port$', 'lan_sizes_by_port', {}, 'lan_sizes_by_port'),
                      )
