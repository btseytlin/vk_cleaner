"""vk_cleaner URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from .views import index, friend_list, logout, delete_friend, about
from django.views.generic import RedirectView

urlpatterns = [
    
    url(r'^$', index, name='index'),
    url(r'^logout$', logout, name='logout'),
    url(r'^friend_list$', friend_list, name='friend_list'),
    url(r'^about$', about, name='about'),
    url(r'^ajax/delete_friend/$', delete_friend, name='delete_friend'),
    
]
