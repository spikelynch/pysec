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

from pysec.reports import extract_report

#TAXRECELT = 'us-gaap:ScheduleOfEffectiveIncomeTaxRateReconciliationTableTextBlock'

# TAXRECELTS are the us-gaap elements for the tax reconciliation fields

TAXRECELTS = {
    'Computed expected tax': 'IncomeTaxReconciliationIncomeTaxExpenseBenefitAtFederalStatutoryIncomeTaxRate',
    'State taxes, net of fed effect': 'IncomeTaxReconciliationStateAndLocalIncomeTaxes',
    'Indef. invested foreign earnings': 'IncomeTaxReconciliationForeignIncomeTaxRateDifferential',
    'R&D credit, net': 'IncomeTaxReconciliationTaxCreditsResearch',
    'Domestic Production Deduction': 'IncomeTaxReconciliationDeductionsQualifiedProductionActivities',
    'Other': 'IncomeTaxReconciliationOtherReconcilingItems',
    'Provision for income taxes': 'IncomeTaxExpenseBenefit',
    'Effective tax rate': 'EffectiveIncomeTaxRateContinuingOperations'
    }

TAXFIELDS = [
    'Computed expected tax',
    'State taxes, net of fed effect',
    'Indef. invested foreign earnings',
    'R&D credit, net',
    'Domestic Production Deduction',
    'Other',
    'Provision for income taxes',
    'Effective tax rate'
    ]


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


def report(request, cik, quarter, form):
    """
    Return an HTML version of a single form.

    Args:
        request (HTTPRequest): the Django request
        cik (Str): the company CIK number
        quarter (Str): the year and quarter as YYYYQ
        form (Str): the form to return (eg 10-K)

    Returns:
        HTTPResponse

    """
    errmsg = None
    report = None
    rows = None
    try:
        report = Index.objects.get(cik=cik, quarter=quarter, form=form)
    except Index.DoesNotExist:
        errmsg = "Could not find report %s for %s %s" % (form, cik, quarter)
    except Index.MultipleObjectsReturned:
        errmsg = "More than one report %s for %s %s" % (form, cik, quarter)
    except:
        errmsg = "Unknown error"
    if report:
        rows = get_report(report)
    values = { 'report': report, 'rows': rows, 'error': errmsg }
    return render(request, 'pysec/report.html', values)




def reconciliation(request, cik, quarter):
    """
    Returns the HTML rendered for a tax reconciliation report

    Args:
        request (HTTPResquest): the Django request
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
        report = Index.objects.get(cik=cik, quarter=quarter, form='10-K')
        if report: 
            dates, dicttable = extract_report(report, TAXRECELTS, 'dates')
            table =  [ ( field, dicttable[field] ) for field in TAXFIELDS ]
            values['report'] = report
            values['table'] = table
            values['dates'] = dates
            values['fields'] = TAXFIELDS
        else:
            values['error'] = "Report extraction failed for %s" % cik
    except:
        values['error'] = "10-K not found for %s" % cik
        raise
    return render(request, 'pysec/reconciliation.html', values)




def reconciliation_xml(request, cik, quarter):
    """
    Returns the XML rendered for a tax reconciliation report

    Args:
        request (HTTPResquest): the Django request
        cik (Str): the company's cik number
        quarter (Str): the quarter as YYYYQ

    Return:
        Httpresponse
 
    """
    
    values = { 'report': None }
    try:
        report = Index.objects.get(cik=cik, quarter=quarter, form='10-K')
        if report: 
            dates, dicttable = extract_report(report, TAXRECELTS, 'fields')
            print "dicttable"
            print dicttable
            # Note: zipping in the TAXFIELDS so that they are available in
            # the template at the element level
            staxfields = sorted(TAXFIELDS)
            table = [ ( date, zip(staxfields, dicttable[date]) ) for date in dates ] 
            values['report'] = report
            values['table'] = table
            values['dates'] = dates
            values['fields'] = TAXFIELDS
        else:
            values['error'] = "Report extraction failed for %s" % cik
    except:
        values['error'] = "10-K not found for %s" % cik
        raise
    return render(request, 'pysec/reconciliation.xml', values, content_type='application/xml')


def reports(request, cik, form):
    """
    Returns the HTML rendered for a list of reports

    Args:
        request (HTTPResquest): the Django request
        cik (Str): the company's cik number
        quarter (Str): the quarter as YYYYQ

    Return:
        HTTPResponse

    """
    values = { 'cik': cik, 'reports':[] }
    print "cik = %s, form = %s" % ( cik, form )
    reports = Index.objects.filter(cik=cik, form=form)
    if not reports:
        values['error'] = "No reports found for %s" % cik
    for report in reports:
        rows = get_report(report)
        if rows:
            if not 'name' in values:
                values['name'] = report.name
            values['reports'].append({ 'quarter': report.quarter,'rows': rows } )
    return render(request, 'pysec/reports.xml', values, content_type='application/xml')
        


def get_report(report):
    """
    Fetch the report from the xblr interface and build a simple table

    Args:
        report (Index): the report's index record from the database

    Returns:
        [ [ field, values ] ]
    """
    
    report.download()
    xbrl = report.xbrl()
    if xbrl:
        rows = []
        for f in xbrl.fields:
            rows.append( [ f, xbrl.fields[f] ] )
        return rows
    else:
        return None
    
