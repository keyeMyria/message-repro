from django.conf.urls import include, url
from django.contrib import admin
from django.http import HttpResponse

urlpatterns = [
    url(r'', include('messaging.urls')),
    url(r'^$', lambda r: HttpResponse()),
    url(r'^admin/', admin.site.urls),
]
