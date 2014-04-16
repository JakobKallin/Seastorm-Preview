from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('seattlegeni.website.html.views',
                       
                       # 'Get Donations' functions:
                       # show the main download page for downloading installers
                       (r'^(?P<username>\w{3,32})/$', 'download', {}, 'installers'),
                       # build and download the android installer
                       (r'^(?P<username>\w{3,32})/seattle_android.zip$', 'build_android_installer', {}, 'android_installer'),
                       # build and download the windows installer
                       (r'^(?P<username>\w{3,32})/seattle_win.zip$', 'build_win_installer', {}, 'win_installer'),
                       # build and download the linux installer
                       (r'^(?P<username>\w{3,32})/seattle_linux.tgz$', 'build_linux_installer', {}, 'linux_installer'),
                       # build and download the mac installer
                       (r'^(?P<username>\w{3,32})/seattle_mac.tgz$', 'build_mac_installer', {}, 'mac_installer'),
                       # help page
                       (r'^(?P<username>\w{3,32})/help$', 'donations_help', {}, 'donations_help'),
                      )
