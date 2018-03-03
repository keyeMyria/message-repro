from django.conf.urls import url

from .views import MostRecentMessageTimes

urlpatterns = [
    url(r'^message-times/$', MostRecentMessageTimes.as_view(), name='message-times'),
]
