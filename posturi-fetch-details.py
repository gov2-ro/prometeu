""" 
- [ ] fetch archive - save to index
- [ ] fetch latest (add to index)
- [ ] fetch details for jobs
- [ ] build SQLite.db 
"""

from urllib.request import Request, urlopen
from bs4 import BeautifulSoup as bs
from utils.common import fetch_data, save_json_to_file, data_root

baseurl='http://posturi.gov.ro/'
outputJsonRoot = data_root + 'posturi/'

