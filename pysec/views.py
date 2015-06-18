"""
views.py

Django views module for the pysec endpoint


"""

from django.http import HttpResponse
from django.template.loader import get_template
from django.template import Context

from django.shortcuts import render

from pysec.models import Index

from lxml.html.soupparser import unescape

from pysec.reports import extract_report, report_fields

#TAXRECELT = 'us-gaap:ScheduleOfEffectiveIncomeTaxRateReconciliationTableTextBlock'

# TAXRECELTS are the us-gaap elements for the tax reconciliation fields



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




def report_html(request, report, cik, quarter):
    """
    Returns the HTML rendered for a report

    Args:
        request (HTTPResquest): the Django request
        report (Str): the name of the report
        cik (Str): the company's cik number
        quarter (Str): the quarter as YYYYQ

    Return:
        HTTPResponse

    TODO: make some template tags which give readable versions of the
    dollar amounts ("677000000" -> "$677,000,000" or "$M677") and 
    percentages ("0.252" -> "25,2%")

    """
    values = { 'report': None }
    try:
        index = Index.objects.get(cik=cik, quarter=quarter, form='10-K')
        if index:
            fields = report_fields(report)
            dates, dicttable = extract_report(index, report, 'dates')
            table =  [ ( field, dicttable[field] ) for field in fields ]
            values['index'] = index
            values['report'] = report
            values['table'] = table
            values['dates'] = dates
            values['fields'] = fields
        else:
            values['error'] = "Report extraction failed for %s" % cik
    except:
        values['error'] = "10-K not found for %s" % cik
        raise
    return render(request, 'pysec/report.html', values)




def report_xml(request, report, cik, quarter):
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
    
    values = { 'report': None }
    try:
        index = Index.objects.get(cik=cik, quarter=quarter, form='10-K')
        if index: 
            fields = report_fields(report)
            dates, dicttable = extract_report(index, report, 'fields')
            # Note: zipping in fields so that they are available in
            # the template at the element level
            sfields = sorted(fields)
            table = [ ( date, zip(sfields, dicttable[date]) ) for date in dates ] 
            values['index'] = index
            values['report'] = report
            values['table'] = table
            values['dates'] = dates
            values['fields'] = fields
        else:
            values['error'] = "Report extraction failed for %s" % cik
    except:
        values['error'] = "10-K not found for %s" % cik
        raise
    return render(request, 'pysec/report.xml', values, content_type='application/xml')



