#!/usr/local/bin/python

PYSEC_URL = 'http://127.0.0.1:8000/'

INDEX  = PYSEC_URL + 'reports/%s'
RECONC = PYSEC_URL + 'report/%s/%s'

from urllib import urlopen
from StringIO import StringIO
from lxml import etree

def get_index(form):
    """Loads the list of all companies with a form and returns a dict { cik:name }"""
    try:
        index = {}
        sio = StringIO(urlopen(INDEX % form).read())
        context = etree.iterparse(sio, events=("start",), tag="company")
        for action, elt in context:
            cik = elt.get('cik')
            name = elt.text
            index[cik] = name
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



#index = get_index()

#for cik in index:
#    print "[%s] %s" % ( cik, index[cik] )

get_reconciliation('320193', '20124')
