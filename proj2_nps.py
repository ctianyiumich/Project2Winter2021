#################################
##### Name: Tianyi Chi
##### Uniqname: ctianyi
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key

CACHE_json = "C:\\jiaPiao\\Umich\\Si507\\Proj 2\\CACHE.json"

def load_cache():
    try:
        cache_file = open(CACHE_json, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache

def save_cache(cache):
    cache_file = open(CACHE_json, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()

class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, category, name, address, zipcode, phone):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone

    def info(self):
        return f"{self.name} ({self.category}): {self.address} {self.zipcode}"


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    CACHE_dict = load_cache()
    BASE_URL = 'https://www.nps.gov'
    if BASE_URL in CACHE_dict.keys():
        return CACHE_dict[BASE_URL]
    else:
        response = requests.get(BASE_URL)
        soup = BeautifulSoup(response.text, 'html.parser')

        state_listing_parent = soup.find('ul', class_="dropdown-menu SearchBar-keywordSearch")
        state_listing_lis = state_listing_parent.find_all('li', recursive=False)

        states_dict = {}
        for state_listing_li in state_listing_lis:
            state_link_tag = state_listing_li.find('a')
            state_details_path = state_link_tag['href']
            states_dict[state_link_tag.text.strip().lower()]=BASE_URL+state_details_path

        CACHE_dict[BASE_URL]=states_dict
        save_cache(CACHE_dict)

        return CACHE_dict[BASE_URL]

def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    CACHE_dict = load_cache()
    if site_url in CACHE_dict.keys():
        print("Using cache")
        category = CACHE_dict[site_url]['category']
        name = CACHE_dict[site_url]['name']
        address = CACHE_dict[site_url]['address']
        zipcode = CACHE_dict[site_url]['zipcode']
        phone = CACHE_dict[site_url]['phone']
        return NationalSite(category, name, address, zipcode, phone)
    else:
        print("Fetching")
        site_response = requests.get(site_url)

        site_soup = BeautifulSoup(site_response.text, 'html.parser')

        site_name = site_soup.find('a', class_="Hero-title")
        site_category = site_soup.find('span', class_="Hero-designation")
        site_location = site_soup.find('span', class_="Hero-location")
        site_city = site_soup.find('span', itemprop="addressLocality")
        site_state = site_soup.find('span', itemprop="addressRegion")
        site_zipcode = site_soup.find('span', itemprop="postalCode")
        site_phone = site_soup.find('span', itemprop="telephone")

        if (site_name==None or len(site_name.text.strip())==0):
            name = "no name"
        else:
            name = site_name.text.strip()

        if (site_category==None or len(site_category.text.strip())==0):
            category = "no category"
        else:
            category = site_category.text.strip()

        if (site_city==None) or (site_state==None) or (len(site_city.text.strip())==0 or len(site_state.text.strip())==0):
            address = "no address"
        else:
            address = site_city.text.strip()+", "+site_state.text.strip()

        if (site_zipcode==None or len(site_zipcode.text.strip())==0):
            zipcode = "no zipcode"
        else:
            zipcode = site_zipcode.text.strip()

        phone = site_phone.text.strip()

        CACHE_dict[site_url]={'category':category, 'name':name, 'address':address, 'zipcode':zipcode, 'phone':phone}
        save_cache(CACHE_dict)
        return NationalSite(category, name, address, zipcode, phone)

def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    state_response = requests.get(state_url)
    state_soup = BeautifulSoup(state_response.text, 'html.parser')

    state_sites_parent = state_soup.find('ul', id="list_parks")
    state_sites_lis = state_sites_parent.find_all('li', class_="clearfix")

    sites_list=[]
    for state_sites_li in state_sites_lis:
        state_sites_h3 = state_sites_li.find('h3')
        state_sites_url = state_sites_h3.find('a')['href']
        state_full_url = 'https://www.nps.gov'+state_sites_url
        nationalsite = get_site_instance(state_full_url)
        sites_list.append(nationalsite)

    return sites_list

def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    CACHE_dict = load_cache()
    API_URL = f"https://www.mapquestapi.com/search/v2/radius?origin={site_object.zipcode}&radius=10&maxMatches=10&ambiguities=ignore&outFormat=json&key={secrets.API_KEY}"
    if API_URL in CACHE_dict:
        for place in CACHE_dict[API_URL]['searchResults']:
            place_obj_name = place['name']
            place_obj_category = place['fields']['group_sic_code_name']
            place_obj_city = place['fields']['city']
            place_obj_state = place['fields']['state']

            if (place_obj_name==None or len(place_obj_name)==0):
                place_obj_name == 'no name'
            if (place_obj_category==None or len(place_obj_category)==0):
                place_obj_category = "no category"
            if (place_obj_city==None or len(place_obj_city)==0 or place_obj_state==None or len(place_obj_state)==0):
                place_obj_address = "no address"
            else:
                place_obj_address = place_obj_city + ", " + place_obj_state

            print(f"- {place_obj_name} ({place_obj_category}): {place_obj_address}")
        return CACHE_dict[API_URL]
    else:
        response = requests.get(API_URL)
        API_dict = json.loads(response.text)
        for place in API_dict['searchResults']:
            place_obj_name = place['name']
            place_obj_category = place['fields']['group_sic_code_name']
            place_obj_city = place['fields']['city']
            place_obj_state = place['fields']['state']

            if (place_obj_name==None or len(place_obj_name)==0):
                place_obj_name == 'no name'
            if (place_obj_category==None or len(place_obj_category)==0):
                place_obj_category = "no category"
            if (place_obj_city==None or len(place_obj_city)==0 or place_obj_state==None or len(place_obj_state)==0):
                place_obj_address = "no address"
            else:
                place_obj_address = place_obj_city + ", " + place_obj_state

            print(f"- {place_obj_name} ({place_obj_category}): {place_obj_address}")
        CACHE_dict[API_URL]=API_dict
        save_cache(CACHE_dict)
    return API_dict

if __name__ == "__main__":
    states2url_dict = build_state_url_dict()
    state_name = input(f'Enter a state name (e.g. Michigan, michigan) or "exit"\n: ')
    while True:
        if state_name.lower() == 'exit':
            exit()
        elif state_name.lower() in states2url_dict.keys():
            state_url = states2url_dict[state_name.lower()]
            sites_obj_list = get_sites_for_state(state_url)
            display_str=f"List of national sites in {state_name.lower()}"
            print("-"*len(display_str))
            print(display_str)
            print("-"*len(display_str))
            i=1
            for site in sites_obj_list:
                print(f"[{i}] {site.info()}")
                i += 1
            detail_str = input(f'\nChoose a number for detail search or "exit" or "back"\n:')
            while True:
                if detail_str.isnumeric():
                    index = int(detail_str)-1
                    if (index < 0 or index > i-2):
                        print(f'[Error] Invalid input\n')
                        print(f'\n-------------------------------')
                        detail_str = input(f'Choose a number for detail search or "exit" or "back"\n:')
                    else:
                        get_nearby_places(sites_obj_list[index])
                        detail_str = input(f'\nChoose a number for detail search or "exit" or "back"\n:')
                elif detail_str.lower() == "back":
                    state_name = input(f'Enter a state name (e.g. Michigan, michigan) or "exit"\n: ')
                    break
                elif detail_str.lower() == "exit":
                    exit()
                else:
                    print(f'[Error] Invalid input\n')
                    print(f'\n-------------------------------')
                    detail_str = input(f'Choose a number for detail search or "exit" or "back"\n:')

        else:
            print(f'[Error] Enter a proper state name\n')
            state_name = input(f'Enter a state name (e.g. Michigan, michigan) or "exit"\n: ')