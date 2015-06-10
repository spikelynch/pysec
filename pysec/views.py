# views for edgar browser

from django.http import HttpResponse
from django.template.loader import get_template
from django.template import Context

from pysec.models import Index



def home(request):
    t = get_template('pysec/home.html')
    html = t.render(Context())
    return HttpResponse(html)

def company(request, company):
    t = get_template('pysec/company.html')
    reports = Index.objects.filter(cik=company)
    html = t.render(Context({'reports': reports, 'cik': company}))
    return HttpResponse(html)

def report(request, id):
    errmsg = None
    try:
        report = Index.objects.get(pk=id)
    except Index.DoesNotExist:
        errmsg = "Could not find report with id %s" % id
    except Index.MultipleObjectsReturned:
        errmsg = "More than one report with id %s" % id
    except:
        errmsg = "Unknown error"
        raise
    t = get_template('pysec/report.html');
    html = t.render(Context({'report': report, 'error': errmsg}))
    return HttpResponse(html)
        


def search(request):
    search_text = request.GET.get('search', '')
    t = get_template('pysec/search.html')
    if search_text:
        reports = Index.objects.filter(name__icontains=search_text)
        html = t.render(Context({'reports': reports, 'search': search_text}))
        return HttpResponse(html)
    else:
        return home(request)

