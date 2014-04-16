from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()
# the format for urlpatterns is
# (regular exp, function, optional dictionary, optional name)
urlpatterns = patterns('seattlegeni.website.html.views',

                       # Previously defined in accounts/urls.py.                       
                       (r'^register$', 'register',{},'register'),
                       (r'^login$', 'login',{},'login'), 
                       (r'^logout$', 'logout',{},'logout'),
                       (r'^accounts_help$', 'accounts_help',{},'accounts_help'),
                       #(r'^simplelogin$', 'simplelogin',{},'simplelogin'), 
                       # OpenID/OAuth error pages
                       (r'^error$', 'error',{}, 'error'),
                       (r'^associate_error$', 'associate_error',{}, 'associate_error'),
                       # OpenID/OAuth auto register page
                       (r'^auto_register$', 'auto_register',{},'auto_register'),
                       # Top level urls and functions:
                       # show the user info page for this user listing the public/private keys, and user information
                       (r'^profile$', 'profile', {}, 'profile'), # was user_info
                       # OpenID/OAuth auto registered users get sent here after creation
                       #(r'^new_auto_register_user$', 'new_auto_register_user', {}, 'new_auto_register_user'), #currently not used
                       # show the used resources page (with all the currently acquired vessels)
                       (r'^myvessels$', 'myvessels', {}, 'myvessels'), # was used_resources
                       # show the help page
                       (r'^help$', 'help', {}, 'help'),
                       # getdonations page (to download installers)
                       (r'^getdonations$', 'getdonations', {}, 'getdonations'),

                       # 'My GENI' page functions:
                       # get new resources (from form)
                       (r'^get_resources$', 'get_resources', {}, 'get_resources'),

                       # delete some specific resource for this user (from form)
                       (r'^del_resource$', 'del_resource', {}, 'del_resource'),
                       # delete all resources for this user (from form)
                       (r'^del_all_resources$', 'del_all_resources', {}, 'del_all_resources'),

                       # renew some specific resource for this user (from form)
                       (r'^renew_resource$', 'renew_resource', {}, 'renew_resource'),
                       # renew all resource for this user (from form)
                       (r'^renew_all_resources$', 'renew_all_resources', {}, 'renew_all_resources'),

                       # Display and allow changing the API key.
                       (r'^api_info$', 'api_info', {}, 'api_info'),

                       # Form to generate or upload a new key.
                       (r'^change_key$', 'change_key', {}, 'change_key'),
                       
                       # Profile page functions:
                       # delete the user's private key from the server (from form)
                       (r'^del_priv$', 'del_priv', {}, 'del_priv'),
                       # download the user's private key (from form)
                       (r'^priv_key$', 'priv_key', {}, 'priv_key'),
                       # download the user's public key (from form)
                       (r'^pub_key$', 'pub_key', {}, 'pub_key'),
                       
#                       (r'^private/$', 'home.views.private'),
#                      # create a new share with another use (from form)
#                      (r'^new_share$', 'new_share', {}, 'new_share'),
#                      # delete an existing share with another user (from form)
#                      (r'^del_share$', 'del_share', {}, 'del_share'),

                       # AJAX functions, called by the 'My GENI' page
                       #(r'^ajax_getcredits$', 'ajax_getcredits', {}, 'ajax_getcredits'),
                       #(r'^ajax_getshares$', 'ajax_getshares', {}, 'ajax_getshares'),
                       #(r'^ajax_editshare$', 'ajax_editshare', {}, 'ajax_editshare'),
                       #(r'^ajax_createshare$', 'ajax_createshare', {}, 'ajax_createshare'),
                       #(r'^ajax_getvessels$', 'ajax_getvessels', {}, 'ajax_getvesseles'),
                      )
