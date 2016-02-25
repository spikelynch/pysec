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

REPORT_URL = PYSEC_URL + 'reportall/{}/{}.xml'
OUTFILE = 'facts.csv'

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


def get_fields(quarter, cik):
    """
    Loads the XML report of all facts and returns a list of element tags

    Args:
        quarter (Str): YYYYQ
        cik (Str): CIK (company ID)
    
    Returns:
        a tuple of - the list of tags, and an error message
    """
    
    url = REPORT_URL.format(quarter, cik)
    sio = StringIO(urlopen(url).read())
    facts = []
    error = None
    for event, elt in etree.iterparse(sio, events=("end",)):
        if elt.tag == "value":
            v = elt.get("id")
            if not v in facts:
                facts.append(v)
        elif elt.tag == "error":
            error = elt.text

    return facts, error

def try_quarters(cik):
    for y in range(2012, 2014):
        for q in range(1, 5):
            qtr = str(y) + str(q)
            facts, error = get_fields(qtr, cik)
            if not error:
                return facts
    print "No data found for {}".format(cik)
    return None



tickers = load_tickers(TICKER_LIST)


allfacts = {}
companies = {}

for t in tickers:
    cik = get_cik(t)
    companies[t] = { }
    if cik:
        companies[t]['cik'] = cik
        companies[t]['report'] = False
        print "ticker {}". format(t)
        facts = try_quarters(cik)
        if facts:
            companies[t]['status'] = 'OK'
            companies[t]['report'] = True
            for f in facts:
                if f not in allfacts:
                    allfacts[f] = { cik: 1 }
                else:
                    allfacts[f][cik] = 1
        else:
            companies[t]['status'] = 'No report'
            print "no reports for {}".format(t)
    else:
        companies[t]['status'] = 'No CIK'
        companies[t]['cik'] = ''
        print "ticker {} not found".format(t)
        
with open(OUTFILE, 'w') as f:
    f.write("Ticker," + ','.join(tickers) + "\n")
    f.write("CIK,"    + ','.join([ '"' + companies[t]['cik'] + '"' for t in tickers ]) + "\n")
    f.write("Status," + ','.join([ companies[t]['status'] for t in tickers ]) + "\n")
    for fact in sorted(allfacts.keys()):
        row = [ fact ]
        for t in tickers:
            cik = companies[t]['cik']
            if cik and companies[t]['report']:
                if allfacts[fact].get(cik, False):
                    row.append('y')
                else:
                    row.append('n')
            else:
                row.append('')
        f.write(','.join(row) + "\n")
        
