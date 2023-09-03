from urllib.request import Request, urlopen
from bs4 import BeautifulSoup as bs
import pandas as pd
from datetime import datetime
import os, json, re
from datetime import datetime
from utils.common import fetch_data, save_json_to_file, data_root
 
import demjson
import ast
py
# from tqdm import tqdm

baseurl='https://dispecerat.andnet.ro/index.php'
outputJsonRoot = data_root + 'andnet/tabel-'

legend = {
 "1. Evenimente rutiere:": "evenimente rutiere",
 "4. Drumuri naționale și autostrăzi cu circulația întreruptă:": "circulatie intrerupta",
 "5. Drumuri naționale și autostrăzi cu circulația îngreunată:": "circulatie ingreunata",
 "6. Drumuri naționale și autostrăzi pe care se efectueaza lucrări de reabilitare, modernizări, întretinere și reparații:": "lucrari",
 "7.1 Starea generală a părții carosabile:": "starea generala",
 "8. Conditii meteorologice:": "meteo",
 "9. Temperaturi:": "temperatura"
}

# - - - - - - - - - - - - - - - - - - - - -  
#  Functions
# - - - - - - - - - - - - - - - - - - - - -  

def extract_tablez(table_tag):
    """ Extract data from a table, return the column headers and the table rows"""
    # https://stackoverflow.com/a/44707545/107671
    # SCRAPE: Get a table
    # table_tag = soup.find("table", {"id" : 'SeasonSplits1_dgSeason%d_ctl00' % table_id})

    # SCRAPE: Extract table column headers
    columns = [th.text for th in table_tag.findAll("th")]

    rows = []
    # SCRAPE: Extract Table Contents
    for row in table_tag.tbody.findAll("tr"):
        # look  for vizualizare
        # rows.append ([{col.text} for col in row.findAll('td')])  # Gather all columns in the row
        rrow = []
        for td in row.findAll("td"):
            # rows.append([{td.text}])
            attrz = {}
            placeholder = ''
            if td.has_attr("placeholder"):
                placeholder = td["placeholder"]
            if td.has_attr("onclick"):
                onclick = td["onclick"]
                #  if it has onclick and placeholder ok
                # get attributes
                onclickx = onclick.split("(")
                onclicky = onclickx[1].split(")")
                attrz = onclicky[0].split(",")
                
            if len(attrz):
                rrow.append({'text': td.text, 'placeholder': placeholder, 'attrz': attrz})
                # print(len(attrz))
                # breakpoint()
            else:
                rrow.append({'text': td.text, 'placeholder': placeholder})
            # if attrz:
            #   breakpoint()
        rows.append(rrow) 
        # breakpoint()

    # RETURN: [columns, rows]
    return [columns, rows]

def swapCoords(x):
    out = []
    for iter in x:
        if isinstance(iter, list):
            out.append(swapCoords(iter))
        else:
            return [x[1], x[0]]
    return out

def getSection(xroads):

    rez = {"title": xroads["title"], "type": xroads["type"], "roads": []}
    rsize = len(xroads['data'])
    # pbar = tqdm(total=rsize)
    ii = 0
    for p in xroads["data"]:
        ii += 1
        # if ii >=4:
        #     break
        item = {
            "indice_drum": p["Indicativ drum"]["text"],
            "dela": p["De la km"]["text"],
            "panala": p["Pana la km"]["text"],
            "acces": 3614,
        }
        # ic(p)
        # xx = xroads[p]
        # print(type(xx))
        # print(  'NR. CRT.:' + p['NR. CRT.']['text'] + 'Indicativ drum:' + p['Indicativ drum']['text'] + 'De la km:' + p['De la km']['text'] + 'Pana la km:' + p['Pana la km']['text'] + 'De la data:' + p['De la data']['text'] + 'Pana la data:' + p['Pana la data']['text'] + 'Intre localitatile:' + p['Intre localitatile']['text'] + 'Cauza:' + p['Cauza']['text'] + 'Masuri de remediere:' + p['Masuri de remediere']['text']  )
        # breakpoint()

        # NOW PARSE GIS
        zurl = (
            mbaseurl
            + "?indice_drum="
            + p["Indicativ drum"]["text"]
            + "&dela="
            + p["De la km"]["text"]
            + "&panala="
            + p["Pana la km"]["text"]
            + "&acces=3614"
        )
        # zurl = "http://zx/gov2/dispecerat-cnadr/data/raw/sample-path.html"
        # tqdm.write('>> ' + str(ii) + ' / ' + str(rsize) + ' - ' + zurl)
        req = Request(
            zurl, headers={"User-Agent": "Mozilla/5.0"}
        )  # approach url cere pagina html

        try:
            webpage = urlopen(req).read()  # approach url obtine pagina hmtl in text (?)
        except:
            print("error downloading " + mbaseurl)
            quit()
        soup = bs(
            webpage, "html.parser"
        )  # parseaza html text si il aseaza frumos in pagina
        zcript = soup.select("body script")
        zzcript = (
            zcript[0]
            .contents[0]
            .string.replace("\t", "")
            .replace("\n", "")
            .replace(",}", "}")
            .replace(",]", "]")
        )
        strx = "{" + zzcript + "}"
        json_data = ast.literal_eval(json.dumps(strx))

        match1 = (
            re.search(r"data=\[{.*data2=", json_data, re.DOTALL)
            .group(0)
            .replace("data=", "")
            .replace(";var data2", "")
        )
        m1 = match1[:-1]  # remove last char from string
        obj1 = demjson.decode(m1)[0]
        item['Desc']=obj1['Desc']
        # FIXME: reverse coords
        krds = obj1['coords']
        xkrds=[]
        # breakpoint()
        for feature in krds:
            # feature  = 
            xkrds.append(swapCoords(feature))
        # breakpoint()
        item['coords']=xkrds
        # obj1['Desc']
        # obj1['coords']
        # breakpoint()
        # not needed
        # match2 = re.search(r'data_polygon=\[{.*function addPointGeom_polygon', json_data, re.DOTALL).group(0).replace('data_polygon=','').replace(';function addPointGeom_polygon','')
        rez['roads'].append(item)
        # pbar.update(1)
        # time.sleep(3)
    return rez 

def generate_slug(input_string):
    # Remove leading and trailing whitespaces
    input_string = input_string.strip()
    
    # Replace special characters with hyphens
    input_string = re.sub(r'[^\w\s-]', '', input_string)
    
    # Replace spaces with hyphens
    input_string = re.sub(r'\s+', '-', input_string)
    
    # Convert to lowercase
    input_string = input_string.lower()
    
    # Remove consecutive hyphens
    input_string = re.sub(r'[-]+', '-', input_string)
    
    # Remove any remaining non-alphanumeric characters
    input_string = re.sub(r'[^\w-]', '', input_string)
    
    return input_string

# Download data
# - - - - - - - - - - - - - - - - - - - - -  

req = Request(baseurl , headers={'User-Agent': 'Mozilla/5.0'}) #approach url cere pagina html

try:
  webpage = urlopen(req).read()  #approach url obtine pagina hmtl in text (?)
except:
  print('error downloading ' + baseurl)
  quit()
soup = bs(webpage, "html.parser") #parseaza html text si il aseaza frumos in pagina
content_wrapper = soup.find('div', class_ = 'categories-index')

carneWrapper = soup.find(id="pgprinc")
# div2 = soup.find("div", {"id": "pgprinc"})

carne = carneWrapper.findChildren("div", recursive=False)

# scrape Data
# - - - - - - - - - - - - - - - - - - - - -  



soup = bs(str(carne), "html.parser")
zijson = {
  'title':'',
  'data':{}
}
# gaseste titlu
# then loop through div.
carne1 = soup.findChildren("div", recursive=False)
carne = carne1[0].findChildren("div", recursive=False)

divz1 = soup.findChildren("div", recursive=False)
# title = divz1[0].select("p[class='h5']")
titlez = carne1[0].find("p", {"class": "h2"}).text
zijson['title'] = titlez

rid = 0
for rrow in divz1[0].findAll("div", {"class": "tablerow"}):
    zijson['data'][rid] = {}
    zijson['data'][rid]['data'] = []
    zijson['data'][rid]['title'] = rrow.find("p", {"class": "h5"}).text
    #     # title = rrow.select("p[class='h5']")
    # TODO: check if nodata
    alert = rrow.find("div", {"class": "alert"})
    if alert:
        zijson['data'][rid]['titley'] = alert.text
        zijson['data'][rid]['type'] = 'alert'
    table = rrow.find("table", {"class": "table"})
    if table:
        zijson['data'][rid]['type'] = 'table'
        # df = pd.read_html(str(table))
        zitable = extract_tablez(table)
     
        # TODO: convert zitable list to json
       
        for idx, zrow in enumerate(zitable[1]): # this enumerates too much

          zijson['data'][rid]['data'].append(dict(zip(zitable[0], zrow)))

    rid+=1
        
# niceData
# - - - - - - - - - - - - - - - - - - - - -  

mbaseurl = "https://andnet.ro/dispecerat/dispecerat.php"
mbaseurl = "https://dispecerat.andnet.ro/"
niceJson = {}

    
for z,set in zijson['data'].items():
    # print(set['title'])
    # print(set['type'])
    zidata = set['data']
        
    if len(zidata) > 1:
        niceJson[z] = {
            "name": set['title'],
            "data":[]
        }
        
        for row in zidata:
            
            nicerow = {}
            
            for kk, vv in row.items():
                if kk == 'Vizualizare':
                    # breakpoint()
                    ll = vv['attrz']
                    
                    nn = ll.pop(0)
                    nn = nn.strip('"')
                    nicerow['viz_name'] = nn
                    nicerow['map_zoom'] = ll
                    # del row[kk]
                else:
                    nicerow[kk] = vv['text']
            niceJson[z]['data'].append(nicerow)
            

# write json to files
# - - - - - - - - - - - - - - - - - - - - -  

for ix, dataset in niceJson.items():
    
    # print(dataset['name'])
    if dataset['name'] in legend:
        table_name = legend[dataset['name']]
    else:
        table_name = generate_slug(dataset['name'])
        # TODO: write json to file
    
    save_json_to_file(dataset['data'],outputJsonRoot + table_name + '.json')

# print(json.dumps(niceJson, ensure_ascii=False))