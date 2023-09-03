import json, re, requests, os

data_root = 'data/'
# owner = "gov2-ro"
# repo = "gh-scraping-data"

def fetch_data(url):
    # current_date_time = datetime.datetime.now().strftime('%y-%m-%d %H:%M')
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch data from the website. HTTP Error {response.status_code}")
        return None

    return response.text
# Define a custom sorting key function


def order_bylatlong(item):
    # TODO: add parameter to select, NW, SE , order?
    return (item["longitudine"], item["latitudine"])
 

def save_json_to_file(data, json_file, compact = 'compact', mode = ''):
    
    """ 
    compact:
        compact (DEFAULT)           :   each element in one line + ensure_ascii=False
        compact_encoded             :   each element in one line, encoded
        pretty                      :   pretty print
        pretty_ensure_ascii_false   :   pretty print + ensure_ascii=False 
        inline                      :   one line
        inline_ensure_ascii_false   :   one line + ensure_ascii=False 

     """
    
    """     
    # check if file has changed
    if mode != 'overwrite':
        if os.path.getsize(json_file):
            with open(json_file) as file:
                prev_json = json.load(file)
                data = remove_empty_elements(data)
                prev_json = remove_empty_elements(prev_json)            

            if compact   == 'compact':
                zprev_json = compact_json(prev_json)
                zdata = compact_json(data)
            elif compact == 'compact-encoded':
                zprev_json = compact_json(prev_json, 0)
                zdata = compact_json(data, 0)
            elif compact == 'pretty':
                zprev_json = json.dumps(prev_json, indent=4)
                zdata = json.dumps(data, indent=4)
            elif compact == 'pretty_ensure_ascii_false':
                zprev_json = json.dumps(prev_json, indent=4, ensure_ascii=False )
                zdata = json.dumps(data, indent=4, ensure_ascii=False )
            elif compact == 'inline':
                zprev_json = json.dumps(prev_json)
                zdata = json.dumps(data)
            elif compact == 'inline_ensure_ascii_false':
                zprev_json = json.dumps(prev_json, ensure_ascii=False)
                zdata = json.dumps(data, ensure_ascii=False)
            else:
                zprev_json = json.dumps(prev_json)
            uprev_json = json.loads(zprev_json)    
            xprev_json, zdata = json.dumps(uprev_json, sort_keys=True), json.dumps(data, sort_keys=True)
            uprev_json = convert_json_values_to_strings(xprev_json)
            zdata = convert_json_values_to_strings(zdata)
            if uprev_json == zdata:
                # print('no changes in ' + json_file)
                return ''
            else:
                print (str(len(prev_json)) + ' / ' + str(len(xprev_json)) + ' -> ' + str(len(data)) + ' / ' + str(len(zdata)) )
                print(str(len(data)) + ' / ' +len(prev_json) )
                # with open('prev.json', 'w') as filep:      
                #     filep.write(xprev_json)
                # with open('current.json', 'w') as filec:      
                #     filec.write(zdata)
    """
    with open(json_file, 'w') as file:      
        if compact   == 'compact':
            file.write(compact_json(data))
        elif compact == 'compact-encoded':
            file.write(compact_json(data, 0))
        elif compact == 'pretty':
            json.dump(data, file, indent=4)
        elif compact == 'pretty_ensure_ascii_false':
            json.dump(data, file, indent=4, ensure_ascii=False )
        elif compact == 'inline':
            json.dump(data, file)
        elif compact == 'inline_ensure_ascii_false':
            json.dump(data, file, ensure_ascii=False)
        else:
            json.dump(data, file)                
        # return data
    file.close()


def compact_json(source_data, encode = 1):
    # Compact the JSON data
    # each json element in one line
    nice_json_str=''
    for element in source_data:
        nice_json_str += '{'
        for attr, val in element.items():
            if type(val) is list:
                val = str(val)
            if type(val) == int or type(val) == float:
                val = val
            elif type(val) is str: 
                val = val.strip()
                # val = json.dumps(val)  if encode else '"' + val + '"'
                val = json.dumps(val, ensure_ascii=False) if encode else json.dumps(val)
            else:
                print('err: ' + str(type(val)))
            
            nice_json_str += '"' + attr + '": ' + str(val) + ',\n'
        nice_json_str += '},\n'

    nice_json_str = '[' + nice_json_str + ']';
    nice_json_str = nice_json_str.replace(',\n}', '\n}')

    # Replace '},\n]' with '}\n]'
    nice_json_str = nice_json_str.replace('},\n]', '}\n]')
    nice_json_str = nice_json_str.replace('},\n{"', '},\n{\n"')
    nice_json_str = nice_json_str.replace('\n"', '\n\t"')
    nice_json_str = nice_json_str.replace('[{"', '[{\n\t"')

    return(nice_json_str)

def remove_empty_elements(d):
    """recursively remove empty lists, empty dicts, or None elements from a dictionary"""

    def empty(x):
        return x is None or x == {} or x == []

    if not isinstance(d, (dict, list)):
        return d
    elif isinstance(d, list):
        return [v for v in (remove_empty_elements(v) for v in d) if not empty(v)]
    else:
        return {k: v for k, v in ((k, remove_empty_elements(v)) for k, v in d.items()) if not empty(v)}
    
def convert_json_values_to_strings(obj):
    if isinstance(obj, dict):
        # If it's a dictionary, convert values to strings recursively
        return {key: convert_json_values_to_strings(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        # If it's a list, convert elements to strings recursively
        return [convert_json_values_to_strings(item) for item in obj]
    else:
        # If it's not a dictionary or list, convert it to a string
        return str(obj)