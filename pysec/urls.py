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
    url(r'^reports/([a-z]+)/([0-9]{5})$',              views.reports_html, name='reports-html'),
    url(r'^reports/([a-z]+)/([0-9]{5})\.xml$',         views.reports_xml, name='reports-xml'),
    url(r'^report/([a-z]+)/([0-9]{5})/([0-9]+)$',      views.report_html, name='report-html'),
    url(r'^report/([a-z]+)/([0-9]{5})/([0-9]+)\.xml$', views.report_xml,  name='report-xml')
]
