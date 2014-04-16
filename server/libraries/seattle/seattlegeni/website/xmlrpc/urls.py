from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('seattlegeni.website.xmlrpc.dispatcher',
                       # top level urls and functions:
                       (r'', 'rpc_handler', {}, 'rpc_handler'),
                      )
