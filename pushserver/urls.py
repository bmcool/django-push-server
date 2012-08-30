from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^register/apns/', 'apns.views.device'),
    url(r'^register/gcm/', 'gcm.views.device'),
    url(r'^admin/', include(admin.site.urls)),
)
