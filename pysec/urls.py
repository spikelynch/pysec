"""pysec URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin

from . import views

urlpatterns = [
    url(r'^admin/',           include(admin.site.urls)),
    url(r'^$',                views.home,    name='home'),
    url(r'^search'      ,     views.search,  name='search'),
    url(r'^company/([0-9]+)', views.company, name='company'),
    url(r'^report/([0-9]+)/([0-9]{5})/(.*)$',  views.report,  name='report'),
    url(r'^reconciliation/([0-9]+)/([0-9]{5})\.xml$',  views.reconciliation_xml,  name='reconciliation'),
    url(r'^reconciliation/([0-9]+)/([0-9]{5})$',  views.reconciliation,  name='reconciliation'),
    url(r'^companies/',       views.companies, name='companies'),
    url(r'^reports/([0-9]+)/(.*)$',  views.reports,  name='reports')
]
