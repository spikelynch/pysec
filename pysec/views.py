# views for edgar browser

import re
from django.http import HttpResponse
from django.template.loader import get_template
from django.template import Context

from django.shortcuts import render

from pysec.models import Index

from lxml.html.soupparser import unescape

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

XBRL_NS = "http://www.xbrl.org/2003/instance"

def home(request):
    return render(request, 'pysec/home.html', {})

def search(request):
    search_text = request.GET.get('search', '')
    t = get_template('pysec/search.html')
    if search_text:
        reports = Index.objects.filter(form__contains='10-K', name__icontains=search_text)
        return render(request, 'pysec/search.html', {'reports': reports, 'search_text': search_text}) 
    else:
        return home(request)




def companies(request):
    companies = Index.objects.filter(form__contains='10-K').values('name', 'cik').distinct()
    return render(request, 'pysec/companies.xml', { 'companies': companies }, content_type='application/xml')


def company(request, company):
    reports = Index.objects.filter(cik=company)
    return render(request, 'pysec/company.html', {'reports': reports, 'cik': company})


def report(request, cik, quarter, form):
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
    values = {}
    try:
        report = Index.objects.get(cik=cik, quarter=quarter, form='10-K')
        if report: 
            rec = get_reconciliation(report)
            values = { 'report': report, 'table': rec }
        else:
            values = { 'report': None, 'table': None, 'error': "10-K not found for %s" % cik }
    except:
        values = { 'report': None, 'table': None, 'error': "10-K not found for %s" % cik }
        raise
    return render(request, 'pysec/reconciliation.html', values)


def reports(request, cik, form):
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
    report.download()
    xbrl = report.xbrl()
    if xbrl:
        rows = []
        for f in xbrl.fields:
            rows.append( [ f, xbrl.fields[f] ] )
        return rows
    else:
        return None
    
# Try to fish out the reconciliation text table

def get_reconciliation_daggy(report):
    report.download()
    xbrl = report.xbrl()
    if xbrl:
        rec = xbrl.getNode(TAXRECELT)
        text = rec.text
        return text
    else:
        return None

def get_reconciliation_getfactvalue(report):
    report.download()
    xbrl = report.xbrl()
    table = []
    for y in range(1, 4):
        if xbrl.loadYear(y):
            values = {}
            for label, elt in TAXRECELTS.items():
                values[elt] = xbrl.GetFactValue('us-gaap:' + elt, 'Duration')
            table.append(values)
    return table


def get_reconciliation(report):
    report.download()
    xbrl = report.xbrl()
    table = {}
    dates = get_dates(xbrl)
    print "Context to dates lookup: "
    print dates
    for label, elt in TAXRECELTS.items():
        xpath = '//us-gaap:' + elt
        ves = xbrl.getNodeList('//us-gaap:' + elt)
        table[label] = {}
        for ve in ves:
            contextref = ve.get('contextRef')
            value = ve.text
            if contextref in dates:
                date = dates[contextref]
            else:
                date = 'U'
            if date in table[label]:
                print "Warning, duplicate date " + date + " for " + elt
            table[label][date] = value
    print table
    return table


def get_dates(xbrl):
    contexts = [ el for el in xbrl.oInstance.iter("{%s}context" % XBRL_NS) ]
    dates    = {}
    dre = re.compile('[0-9]+-[0-9]+-[0-9]')
    for c in contexts:
        print c
        cref = c.get('id')
        for cc in c.iter('{%s}period' % XBRL_NS):
            dates[cref] = '-'.join(filter(dre.match, [ el.text for el in cc.iter() ]))
    return dates



# doing my own version of GetFactValue because the context detection
# stuff in xbrl.py isn't working

# def (x, ):
                
#         factValue = None
            
#         if ConceptPeriodType == "Instant":
#             ContextReference = self.fields['ContextForInstants']
#         elif ConceptPeriodType == "Duration":
#             ContextReference = self.fields['ContextForDurations']
#         else:
#             #An error occured
#             return "CONTEXT ERROR"
        
#         if not ContextReference:
#             return None


#         oNode = self.getNode("//" + SeekConcept + "[@contextRef='" + ContextReference + "']")
#         if oNode is not None:                    
#             factValue = oNode.text
#             if 'nil' in oNode.keys() and oNode.get('nil')=='true':
#                 factValue=0
#                 #set the value to ZERO if it is nil
#             #if type(factValue)==str:
#             try:
#                 factValue = float(factValue)
#             except:
#                 print 'couldnt convert %s=%s to string' % (SeekConcept,factValue)
#                 factValue = None
#                 pass
            
#         return factValue   
                    
        
