#!/usr/bin/env python2

from django.conf import settings

import logging, csv, re

from sys import path

from pysec.reports import report_form, report_fields, ReportException
from pysec.utils import quarter_split
from requests import get

from urllib import urlopen
from StringIO import StringIO
from lxml import etree

PYSEC_URL = 'http://127.0.0.1:8000/'
TICKER_LIST = 'tickers.txt'

TICKER_URL = 'http://www.sec.gov/cgi-bin/browse-edgar?CIK={}&Find=Search&owner=exclude&action=getcompany'
CIK_RE = re.compile(r'.*CIK=(\d{10}).*')


logger = logging.getLogger('pysec.fields')



def load_tickers(filepath):
    with open(filepath) as file:
        tickers = [ line.rstrip('\r\n') for line in file if line[0] != '#'  ]
    print tickers
    return tickers

def get_cik(ticker):
    results = CIK_RE.findall(get(TICKER_URL.format(ticker)).content)
    if results:
        return results[0]
    else:
        return None


index = Index.objects.get(cik=cik, quarter=quarter, form=form)


    

tickers = load_tickers(TICKER_LIST)

for t in tickers:
    cik = get_cik(t)
    if cik:
        print "{} -> {}".format(t, cik)
        #facts = get_fields(cik)
        #print ','.join([ t ] + facts)
    else:
        print "ticker {} not found".format(t)
        
