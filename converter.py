#!/usr/local/bin/python

PYSEC_URL = 'http://127.0.0.1:8000/'

from django.conf import settings

import logging
import csv

from sys import path

from pysec.reports import report_form, report_fields, ReportException
from pysec.utils import quarter_split

from urllib import urlopen
from StringIO import StringIO
from lxml import etree

# FIXME - it would be better to have these use Django reverse-url stuff

logger = logging.getLogger('pysec.converter')

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
        error = None
        for action, elt in etree.iterparse(sio, events=("start",)):
            if elt.tag == 'error':
                error = elt.text
            elif elt.tag == 'report':
                cik = elt.get('cik')
                name = elt.get('name')
                url = elt.get('href')
                index[cik] = { 'name': name, 'url': url }
        if error:
            logger.error("Error message from pysec: " + error)
            return {}
        return index
    except:
        logger.error("parse error")
        raise


def get_report(report, quarter, cik):
    """
    Loads and parses a table of facts for a report/quarter/company.  Returns
    a dict of dicts keyed by date-span and then by value.

    Args:
        report (Str): name of the report
        quarter (Str): YYYYQ
        cik (Str): CIK (company ID)
    
    Returns:
        {
            "DATE RANGE 1": {
                "column name 1": VALUE1,
                "column name 2": VALUE2, ...
            },
            "DATE RANGE 2": {
                ...
        }
    """
    
    url = REPORT_URL % ( report, quarter, cik )
    logger.info("Loading from %s" % url)
    sio = StringIO(urlopen(url).read())
    p = None
    values = {}
    for action, elt in etree.iterparse(sio, events=("start",)):
        if elt.tag == "period":
            p = elt.get("date")
        elif elt.tag == "value":
            if not p:
                logger.warn("value tag outside period in %s" % url)
                p = "unknown"
            if p not in values:
                values[p] = {}
            v = elt.get("id")
            values[p][v] = elt.text

    return values
    

RPT = 'tax'
output_file = './test.csv'

MAX = 10

columns = [ 'Year', 'Quarter', 'CIK', 'Name', 'Dates' ] + report_fields(RPT)

# CSV output as follows:
#
# YYYY,Q,cik,name,date-range,f1,f2,f3, ... fn
#
# where f1..fn are the field names of the report

with open(output_file, 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames = columns)
    writer.writeheader()
    for quarter in QUARTERS:
        y, q = quarter_split(quarter)
        index = get_index(RPT, quarter)
        i = 0
        if index:
            for cik in index:
                logger.info("[%s] %s" % ( cik, index[cik]["name"] ))
                rows = get_report(RPT, quarter, cik)
                if rows:
                    for date, row in rows.items():
                        row['Year'] = y
                        row['Quarter'] = q
                        row['CIK' ] = cik
                        row['Name'] = index[cik]["name"]
                        row['Dates'] = date
                        writer.writerow(row)
        if i > MAX:
            logger.info("Reached maximum of %d records: quitting" % i)
            break
        i += 1

