from disaster_scrapers import Scraper
import requests
import json, re


class cmteb(Scraper):
    owner = "gov2-ro"
    repo = "github-scrapers"
    # repo = "gh-scraping-data"
    # filepath = "misc/cmteb.json"
    filepath = "cmteb.json"

    url = 'https://www.cmteb.ro/harta_stare_sistem_termoficare_bucuresti.php'
    
    def fetch_data(self):
        html_content = requests.get(self.url, timeout=10).text
        passed_features = {}
        # TODO: also list by location and note status color
        for color in ['verde', 'rosu', 'galben']:
            pattern = r'var passedFeatures_{} = (.+?);'.format(color)
            data = re.search(pattern, html_content)
            if data:
                data_str = data.group(1)
                passed_features[color] = json.loads(data_str)
    
        # return json.loads(content)
        return passed_features