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

STD_COLUMNS =  [ 'Year', 'Quarter', 'Source', 'Error', 'CIK', 'Name', 'Start', 'End' ]

QUARTERS = [ '20121', '20122', '20123', '20124', '20131', '20132', '20133', '20134' ]

MAXCOMPANIES = 10

OUTCSV = './test10.csv';



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
            print "Error message from pysec: %s" + error
            return {}
        return index
    except:
        print "Parse error"
        raise


def best_source(sources):
    if "xbrl" in sources:
        return sources["xbrl"]
    if "index" in sources:
        return sources["index"]
    if "html" in sources:
        return sources["html"]
    return ""


def get_report(report, quarter, cik):
    """
    Loads and parses a table of facts for a report/quarter/company.  Returns
    a dict of dicts keyed by date-span and then by value.

    Args:
        report (Str): name of the report
        quarter (Str): YYYYQ
        cik (Str): CIK (company ID)
    
    Returns:
        a 2-tuple of values, error:
        [
            ( STARTDATE, ENDDATE, { dict by field } ),
            ( STARTDATE2, ENDDATE2, { dict by field } )
        ],
        error (Str)
    """
    
    url = REPORT_URL % ( report, quarter, cik )
    print "Loading from %s" % url
    sio = StringIO(urlopen(url).read())
    start = None
    end = None
    values = []
    sources = {}
    row = {}
    error = None
    for event, elt in etree.iterparse(sio, events=("end",)):
        if elt.tag == "period":
            start = elt.get("start")
            end = elt.get("end")
            row["Source"] = best_source(sources)
            values.append((start, end, row))
            #sources = {}
            row = {}
        elif elt.tag == "value":
            v = elt.get("id")
            row[v] = elt.text
        elif elt.tag == "source":
            sources[elt.get("id")] = elt.get("href")
        elif elt.tag == "error":
            error = elt.text

    return values, error
    

RPT = 'tax'
output_file = OUTCSV


columns =  STD_COLUMNS + report_fields(RPT)

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
                print "[%s] %s" % ( cik, index[cik]["name"] )
                rows, error = get_report(RPT, quarter, cik)
                if error:
                    row = {}
                    row['Year'] = y
                    row['Quarter'] = q
                    row['CIK' ] = cik
                    row['Name'] = index[cik]["name"]
                    row['Error'] = error
                    writer.writerow(row)
                    print "Error %s" % error
                else:
                    for start, end, row in rows:
                        row['Year'] = y
                        row['Quarter'] = q
                        row['CIK' ] = cik
                        row['Name'] = index[cik]["name"]
                        row['Start'] = start
                        row['End'] = end
                        writer.writerow(row)
                i += 1
                print "i = %d" % i
                if i == MAXCOMPANIES:
                    print "Reached maximum of %d records: quitting" % i
                    break

