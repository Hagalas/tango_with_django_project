from django.conf.urls import patterns, include, url
from views import index, about, category, add_category, add_page, register, \
user_login, restricted, user_logout, search, profile, track_url,like_category, \
suggest_category, auto_add_page
import views

urlpatterns = patterns('',
    url(r'^$', index, name='index'), # ADD THIS NEW TUPLE!
    url(r'^about/', about, name='about'),
    url(r'^add_category/$', views.add_category, name='add_category'), # NEW MAPPING!
    url(r'^category/(?P<category_name_url>\w+)/$', views.category, name='category'), # New!
    url(r'^category/(?P<category_name_url>\w+)/add_page/$', views.add_page, name='add_page'),
    url(r'^register/$', views.register, name='register'), # ADD NEW PATTERN !
    url(r'^login/$', views.user_login, name='login'),
    url(r'^restricted/$', views.restricted, name='restricted'),
    url(r'^logout/$', views.user_logout, name='logout'),
    #url(r'^search/$', views.search, name='search'),
    url(r'^profile/$', views.profile, name='profile'),
    url(r'^goto/$', views.track_url, name=track_url),
    url(r'^like_category/$', views.like_category, name='like_category'),
    url(r'^suggest_category/$', views.suggest_category, name='suggest_category'),
    url(r'^auto_add_page/$', views.auto_add_page, name='auto_add_page'),
)