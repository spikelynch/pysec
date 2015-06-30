#!/usr/local/bin/python

PYSEC_URL = 'http://127.0.0.1:8000/'

from django.conf import settings

from sys import path

from pysec.reports import report_form, report_fields, ReportException

from urllib import urlopen
from StringIO import StringIO
from lxml import etree

# FIXME - it would be better to have these use Django reverse-url stuff

INDEX_URL  = PYSEC_URL + 'reports/%s/%s.xml'
REPORT_URL = PYSEC_URL + 'report/%s/%s/%s.xml'



QUARTERS = [ '20124' ]

MAXCOMPANIES = 100





def get_index(report, quarter):
    """
    Loads the list of all companies with a form and returns a dict { cik:name }"""
    try:
        index = {}
        sio = StringIO(urlopen(INDEX_URL % (report, quarter)).read())
        reports = etree.iterparse(sio, events=("start",))
        error = None
        for action, elt in reports:
            if elt.tag == 'error':
                error = elt.text
            elif elt.tag == 'report':
                cik = elt.get('cik')
                name = elt.get('name')
                url = elt.get('href')
                index[cik] = { 'name': name, 'url': url }
        if error:
            print "Error message from pysec: " + error
            return {}
        return index
    except:
        print "parse error"
        raise


def get_report(report, quarter, cik):
    """Loads and parses a table of facts for a company/quarter/report"""
    url = REPORT_URL % ( report, quarter, cik )
    print "Loading from %s" % url
    sio = StringIO(urlopen(url).read())
    tree = etree.parse(sio)
    print tree


RPT = 'tax'

MAX = 10

for q in QUARTERS:

    index = get_index(RPT, q)
    i = 0
    if index:
        for cik in index:
            print cik
            data = get_report(RPT, q, cik)
            if i > MAX:
                break
            i += 1
            

    #    print "[%s] %s: %s" % ( cik, index[cik].name, index[cik].url )

#get_reconciliation('320193', '20124')
