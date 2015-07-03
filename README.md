pySec Reports
=============

## System description

The system has two components:

*pysec* - a Django web app which takes requests for reports and
returns HTML or XML web versions. This was built on Luke Rosiak's
[pysec](https://github.com/lukerosiak/pysec), which builds an index
of companies and filings, and downloads, unzips and parses filings
when they're requested.

I've added a basic report layer (a report is a set of XBRL facts to be
extracted from a form) and fleshed out the Django web app with a few
simple endpoints.

*converter* - a Python script which queries the pysec server, parses the
XML versions of reports, and uses the returned values to build a
CSV file.

## Pysec

[XBRL](http://www.xbrl.org/Specification/XBRL-2.1/REC-2003-12-31/XBRL-2.1-REC-2003-12-31+corrected-errata-2013-02-20.html)
or Extensible Business Reporting Language is a data format which is
required by the US SEC for company filings.  The SEC make these available via their [EDGAR](http://www.sec.gov/edgar/searchedgar/webusers.htm) interface.  Pysec queries Edgar to build an index of filings for a range of dates (filings are indexed by quarter).  It can then be used to download and parse filings from the index.

The web front-end I've built on top of pysec does two things:

* provides a simple report model for extracting the required
  information from an XBRL filing

* provides a way to access a list of all companies with a given report
  in a quarter, and then to request the reports for each company.

### XBRL and Reports

An XBRL document can be seen as a set of *facts*, each of which has a *context*.

Contexts correspond to time periods (or instants) and facts are the accounting values for those contexts.

For example, a company's computed expected tax is represented by the element:

    <IncomeTaxReconciliationIncomeTaxExpenseBenefitAtFederalStatutoryIncomeTaxRate>

The text content of this element is the fact's value, and the element
has an attribute which links it to a context representing the date
range to which it applies.

The contexts are defined in a separate section of the same XBRL
document. A given fact is likely to occur more than once in the same
filing (for example, income tax reconciliations have three years).

Each XBRL document represents a *form* - a particular regulatory
instrument, for example the 10-K is the primary reporting report for
US firms.

The simple report model here defines form and a list of facts to be extracted from it.  For example:

    form = 10-K

    facts:
    IncomeTaxReconciliationIncomeTaxExpenseBenefitAtFederalStatutoryIncomeTaxRate
    IncomeTaxReconciliationStateAndLocalIncomeTaxes
    IncomeTaxReconciliationForeignIncomeTaxRateDifferential
    IncomeTaxReconciliationTaxCreditsResearch
    IncomeTaxReconciliationDeductionsQualifiedProductionActivities
    IncomeTaxReconciliationOtherReconcilingItems
    IncomeTaxExpenseBenefit
    EffectiveIncomeTaxRateContinuingOperations

A report is extracted from a given XBRL form by selecting all elements
in the list of facts, looking up their contexts, and building a table
of facts / dates:

<table>
<tr><th></th><th>DMY1-DMY1</th><th>DMY2-DMY2</th><th>DMY3-DMY3</th></tr>
<tr><td>Field F</td><td>$F1</td><td>$F2</td><td>$F3</td></tr>
<tr><td>Field G</td><td>$G1</td><td>$G2</td><td>$G3</td></tr>
<tr><td>Field H</td><td>$H1</td><td>$H2</td><td>$H3</td></tr>
</table>

Note that it's not guaranteed that all facts in a report will be available in all dates: if they aren't, the cell is left blank.

### Web Services

The converter script reads filings using the Pysec reports endpoint. This has two basic URLs:

    http://pysec_host/reports/REPORT/YYYYQ[.xml]

    http://pysec_host/report/REPORT/YYYYQ/CIK[.xml]

The first, *reports*, returns a list of companies for which REPORT
should be available in the given quarter YYYYQ.

This list is generated from the database built by pysec from the EDGAR
index, and is filtered by form. For eg if the report is based on the
10-K, only companies with a 10-K in YYYYQ will be included.

The second, *report*, returns the report table for a given company in
a given year and quarter.  The company is specified using the CIK, a
unique identifier assigned to it by the SEC.

The *reports* list (in both XML and HTML versions) includes a link to the
*report* url for each company.

Note that it's possible that generating the report for a company might
fail, for a number of reasons:

* the download from the SEC times out
* the form required by the report doesn't exist - there are a few instances of the EDGAR index being inconsistent with the downloads for a company
* part of the form download is missing or corrupt, leading to an XBRL parse error
* the company has more than one filing for a given year/quarter/form

The last of these is a bug in the Pysec web front-end, which will be fixed.
