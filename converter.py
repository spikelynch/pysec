#!/usr/local/bin/python

PYSEC_URL = 'http://127.0.0.1:8000/'

from django.conf import settings
from django.core.urlresolvers import reverse

from sys import path

print "path = "
print path

from pysec.reports import report_form, report_fields

from urllib import urlopen
from StringIO import StringIO
from lxml import etree

INDEX_URL  = 'reports-xml'
REPORT_URL = 'report-xml'



QUARTERS = [ '201204' ]

MAXCOMPANIES = 100




def get_url(urlname, *args):
    url = reverse(urlname, args)
    return url


def get_index(report, quarter):
    """
    Loads the list of all companies with a form and returns a dict { cik:name }"""
    form = report_form(report)
    try:
        index = {}
        sio = StringIO(urlopen(get_url(INDEX_URL, form, quarter).read()))
        company = etree.iterparse(sio, events=("start",), tag="report")
        for action, elt in context:
            cik = elt.get('cik')
            name = elt.get('name')
            index[cik] = { 'name': name, 'url': url }
        return index
    except:
        print "parse error"
        raise


def get_report(report, cik, quarter):
    """Loads and parses a table of facts for a company/quarter/report"""
    url = RECONC % ( cik, quarter )
    print "Loading from %s" % url
    sio = StringIO(urlopen(INDEX).read())
    tree = etree.parse(sio)
    print tree



index = get_index('tax', QUARTERS[0])

for cik in index:
    print "[%s] %s: %s" % ( cik, index[cik].name, index[cik].url )

#get_reconciliation('320193', '20124')
