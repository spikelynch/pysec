
import xbrl

example_10k = "/Users/mike/Desktop/SEC_XML/aapl-20140927.xml"

x = xbrl.XBRL(example_10k)

print x.fields 

