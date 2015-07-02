SEC Reports
===========

## System description

The system has two components:

*pysec* - a Django web app which takes requests for reports and returns
HTML or XML web versions. pysec downloads packages from the SEC website when 

*converter* - a Python scripts which queries pysec and builds a CSV report for multiple companies/quarters

## TODO

Split the date ranges into Start and End, plus handle cases where the
context is an Instant rather than a Range - DONE

Multiple objects returned on a get: /report/tax/20124/841360.xml

This exception isn't being handled at the pysec level - DONE

Reproducibility features:

* the original URL of the download -- DONE
* status - errors or warnings -- DONE

started run of 100 x 8 at 3.45pm approximately



