# views for edgar browser

from django.http import HttpResponse
from django.template.loader import get_template
from django.template import Context

from django.shortcuts import render

from pysec.models import Index



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
    return render(request, 'pysec/companies.xml', { 'companies', companies }, 'application/xml')


def company(request, company):
    reports = Index.objects.filter(cik=company)
    return render(request, 'pysec/company.html', {'reports': reports, 'cik': company})

def report_html(request, cik, quarter, form):
    values = report(request, 'html', cik, quarter, form)
    return render(request, 'pysec/report.html', values)

def report_xml(request, cik, quarter, form):
    values = report(request, 'xml', cik, quarter, form)
    return render(request, 'pysec/report.xml', values, content_type='application/xml')

# report returns a dict which can be fed to either the xml or html template

def report(request, fmt, cik, quarter, form):
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
    return { 'report': report, 'rows': rows, 'error': errmsg }





def get_report(report):
    report.download()
    xbrl = report.xbrl()
    if xbrl:
        rows = []
        for f in xbrl.fields:
            rows.append( [ f, xbrl.fields[f] ] )
        return rows
    else:
        return [ [ 'The report was not parsed', 'Boo' ] ]
    



