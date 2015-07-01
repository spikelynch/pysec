"""
views.py

Django views module for the pysec endpoint


"""

from django.http import HttpResponse
from django.template.loader import get_template
from django.template import Context

from django.shortcuts import render

import logging

from pysec.models import Index

from lxml.html.soupparser import unescape

from pysec.reports import extract_report, report_fields, report_form, ReportException
from pysec.utils import quarter_split

#TAXRECELT = 'us-gaap:ScheduleOfEffectiveIncomeTaxRateReconciliationTableTextBlock'

# TAXRECELTS are the us-gaap elements for the tax reconciliation fields

logger = logging.getLogger(__name__)

def home(request):
    """Render and return the home page."""
    return render(request, 'pysec/home.html', {})

def search(request):
    """Look reports up by company name and return list."""
    search_text = request.GET.get('search', '')
    t = get_template('pysec/search.html')
    if search_text:
        reports = Index.objects.filter(form__contains='10-K', name__icontains=search_text)
        return render(request, 'pysec/search.html', {'reports': reports, 'search_text': search_text}) 
    else:
        return home(request)


def companies(request):
    """Look up companies with 10-K forms by their CIK."""
    companies = Index.objects.filter(form__contains='10-K').values('name', 'cik').distinct()
    return render(request, 'pysec/companies.xml', { 'companies': companies }, content_type='application/xml')


def company(request, company):
    """Show a page for an individual company."""
    reports = Index.objects.filter(cik=company)
    return render(request, 'pysec/company.html', {'reports': reports, 'cik': company})





def reports_html(request, report, quarter):
    """
    Returns a HTML page giving a list of all companies with a given report
    in a given quarter.

    Args:
        request (HTTPResquest): the Django request
        report (Str): the name of the report
        quarter (Str): the quarter as YYYYQ

    Return:
        HTTPResponse
    """
    return render(request, 'pysec/reports.html', reports(report, quarter))


def reports_xml(request, report, quarter):
    """
    Returns an XML document giving a list of all companies with a given report
    in a given quarter.

    Args:
        request (HTTPResquest): the Django request
        report (Str): the name of the report
        quarter (Str): the quarter as YYYYQ

    Return:
        HTTPResponse
    """
    return render(request, 'pysec/reports.xml', reports(report, quarter),  content_type='application/xml')



def reports(report, quarter):
    """
    Returns a values dict which can be rendered in either HTML or XML
    giving a list of reports for a quarter

    Args:
        report (Str): the name of the report
        quarter (Str): the quarter as YYYYQ

    Return:
        dict of fields for templates:
            
    
    """
    form = report_form(report)
    y, q = quarter_split(quarter)
    values = { 'report': report, 'form': form, 'quarter': quarter, 'y': y, 'q': q }
    try:
        companies = Index.objects.filter(quarter=quarter, form=form).values('name', 'cik').distinct()
        if companies:
            values['companies'] = companies
        else:
            values['error'] = "No reports found with the form required"
    except:
        values['error'] = "Index lookup failed"
    return values


    

def report_html(request, report, quarter, cik):
    """
    Returns the HTML rendered for a report

    Args:
        request (HTTPResquest): the Django request
        report (Str): the name of the report
        quarter (Str): the quarter as YYYYQ
        cik (Str): the company's cik number

    Return:
        HTTPResponse

    TODO: make some template tags which give readable versions of the
    dollar amounts ("677000000" -> "$677,000,000" or "$M677") and 
    percentages ("0.252" -> "25,2%")

    """
    form = report_form(report)
    values = { 'report': report, 'cik': cik, 'quarter': quarter, 'form': form }
    y, q = quarter_split(quarter)
    values['y'] = y
    values['q'] = q
    try:
        index = Index.objects.get(cik=cik, quarter=quarter, form=form)
        fields = report_fields(report)
        values['company'] = index.name
        try:
            dates, dicttable = extract_report(index, report, 'dates')
            table =  [ ( field, dicttable[field] ) for field in fields ]
            values['index'] = index
            values['table'] = table
            values['dates'] = map(split_date, dates)
            values['fields'] = fields
        except ReportException as e:
            print "EXCEPT"
            values['error'] = "Report extraction failed: %s" % e 
    except Exception as e:
        values['error'] = "Index record not found for %s: %s" % (cik, e)
    return render(request, 'pysec/report.html', values)




def report_xml(request, report, quarter, cik):
    """
    Returns the XML rendered for a report

    Args:
        request (HTTPResquest): the Django request
        report (Str): the name of the report
        cik (Str): the company's cik number
        quarter (Str): the quarter as YYYYQ

    Return:
        Httpresponse
 
    """
    
    form = report_form(report)
    values = { 'report': report, 'cik': cik, 'quarter': quarter, 'form': form }
    y, q = quarter_split(quarter)
    values['y'] = y
    values['q'] = q
    try:
        index = Index.objects.get(cik=cik, quarter=quarter, form=form)
        try:
            fields = report_fields(report)
            dates, dicttable = extract_report(index, report, 'fields')
            # Note: zipping in fields so that they are available in
            # the template at the element level
            sfields = sorted(fields)
            table = [ split_date(date) + (zip(sfields, dicttable[date]),) for date in dates ] 
            values['index'] = index
            values['report'] = report
            values['table'] = table
            values['dates'] =  map(split_date, dates)
            values['fields'] = fields
        except ReportException as e:
            values['error'] = "Report extraction failed for %s: %s" % (cik, e)
    except Exception as e:
        values['error'] = "Index lookup error for %s/%s/%s: %s" % (quarter, form, cik, e)
    return render(request, 'pysec/report.xml', values, content_type='application/xml')




def split_date(d):
    """Splits a pair of dates on ';', is guaranteed to return a 2-tuple"""
    l = d.split(';')
    if len(l) == 0:
        return ( None, None )
    elif len(l) == 1:
        return ( l[0], None )
    else:
        return tuple(l[:2])
