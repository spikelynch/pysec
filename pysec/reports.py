"""
reports.py

Functions for fetching sections of SEC reports for a particular company/
year / column


"""

from pysec.models import Index




def extract_report(report, fields):
    """
    For an Index (representing a form/quarter/company), extract the 
    requested XBRL elements ("fact values") and turn them into a matrix
    where the rows are facts and the columns are date (ranges).

    XBRL assigns facts to dates or date ranges using 'contextRef' attributes
    which refer to a list of context elements which store the actual date or
    date ranges.  This routine does the lookup for all the contextRefs for
    the requested fields, and uses the union of all these for the columns.

    This can result in some items in the matrix being empty, if no element
    for the requested fact had an entry to a particular context/date range.
    Items like this are set to None.

    Args:
        report (Index): the index of this report from the database
        fields ( { Str: Str } ): a dict of XBRL elts.  The key value here
            is left up to the calling code.

    Returns:
        a tuple of date, table
        where date = [ sorted list of date ranges ]
              table = { key: [ v1, v2, v3, v4 ... ] }
        The values v1, v2, v3 are sorted in the same order as the dates.

    Note that this leaves it up to the template to sort the fields and rows

    """
    report.download()
    xbrl = report.xbrl()
    valdict = {}
    dates = get_dates(xbrl)
    idates = {}
    for label, tag in fields.items():
        factelts = xbrl.getNodeList('//us-gaap:' + tag)
        values = {}
        
        # Loop through all <tag> elements, get dates from contextRefs and
        # store all the results in valdict
        for factelt in factelts:
            contextref = factelt.get('contextRef')
            value = factelt.text
            if contextref in dates:
                date = dates[contextref]
            else:
                date = 'Unknown'
            if date in table[label]:
                print "Warning, duplicate date " + date + " for " + elt
            values[date] = value
            if not date in idates:
                idates[date] = 1
        valdict[label] = values

    cdates = sorted(idates.keys())

    # now generate a matrix of all dates x all fields, where empty cells
    # have None

    table = {}
    for label, vals in valdict.items():
        table[label] = [ vals.get(date, None) for date in cdates ]
    
         
    return cdates, table

def get_dates(xbrl):
    """
    Reads all of the <context> items from an XBRL document and returns
    a dict of date ranges keyed by context ID

    Args:
        xbrl (XBLR): the XBRL document

    Returns:
        { Str: Str }
    """
    
    contexts = [ el for el in xbrl.oInstance.iter("{%s}context" % XBRL_NS) ]
    dates    = {}
    dre = re.compile('[0-9]+-[0-9]+-[0-9]')
    for c in contexts:
        print c
        cref = c.get('id')
        for cc in c.iter('{%s}period' % XBRL_NS):
            dates[cref] = '-'.join(filter(dre.match, [ el.text for el in cc.iter() ]))
    return dates

