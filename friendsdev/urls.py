from django.conf.urls.defaults import *
from django.contrib import admin

urlpatterns = patterns('',
    # Example:
    # (r'^friendsdev/', include('friendsdev.foo.urls')),

    # Uncomment this for admin:
    (r'^admin/(.*)', admin.site.root),
)
