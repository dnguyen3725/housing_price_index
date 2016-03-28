from IPython.core.debugger import Tracer
import numpy as np
import pandas as pd
import csv
import requests
import Quandl
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
from BeautifulSoup import BeautifulSoup
from math import floor

GOOGLEMAPURL = 'https://maps.googleapis.com/maps/api/geocode/json?address='

# Main Loop
def main():

    # Config
    years_to_analyze = 5
    
    # Color classes
    pcolor = ['#f7fcf5', '#e5f5e0', '#c7e9c0', '#a1d99b', '#74c476', '#41ab5d', '#238b45', '#006d2c', '#00441b']
    mcolor = ['#fff5f0', '#fee0d2', '#fcbba1', '#fc9272', '#fb6a4a', '#ef3b2c', '#cb181d', '#a50f15', '#67000d']


    test_set = ['Bend-Redmond, OR',
                'Reno, NV', 
                'San Francisco-Oakland-Hayward, CA',
                'Indianapolis-Carmel-Anderson, IN',]

    # Get quandl auth token
    auth = get_authvals_csv('quandl_auth.csv')

    # Get in HPI  database names
    database_code = {}
    dataset_code = {}
    with open('metro_hpi.csv', 'rb') as f:
        f_iter = csv.DictReader(f)
        for row in f_iter:
            database_code[row['name']]=row['database_code']
            dataset_code[row['name']]=row['dataset_code']
    
    # Download HPI data
    print '*****************'
    print 'Downloading Data'
    hpi = pd.DataFrame()
    lat = {}
    lon = {}
    county = {}
        
    #for city in test_set:
    for city in dataset_code:
        
        # Download quandl data for city housing price index
        quandl_code = [database_code[city]+'/'+dataset_code[city]]
        
        print 'Downloading HPI data for '+city
        
        # Get HPI data for each city
        hpi_data = Quandl.get(quandl_code,authtoken=auth['authtoken'])
        
        # Rename column to city name and merge into dataframe
        hpi_data.columns = [city]        
        hpi = pd.concat([hpi, hpi_data], axis=1)
        
        # Parse city name
        city_raw = city
        
        # Get state abbreviation
        state_abrev = []
        while city_raw[-2:] != ', ':
            
            # Get state abbreviation at end of city name
            state_abrev.append(city_raw[-2:])
            
            # Remove the last state abbreviation from the city name
            city_raw = city_raw[:-2]
            
            # Remove the hyphen from the end if there is one at the end of the city name
            if city_raw[-1] == '-':
                city_raw = city_raw[:-1]
                
        # Remove the comma at the end of the city name
        city_raw = city_raw[:-2]
        
        # Process cities until they've all been looked up
        while len(city_raw) > 0:
        
            # Look for hypens
            i_hyphen = city_raw.find('-')
            if city_raw.find('-') < 0:
            
                # There is only one city remaining in string, parse whole thing
                search_string = city_raw
                city_raw = ''
                
            else:
        
                # There is a hyphen in the the string, parse the first city
                search_string = city_raw[0:i_hyphen]
                city_raw = city_raw[i_hyphen+1:]
        
            # Check every combination of city and state
            for state in state_abrev:
            
                 # Generate URL for google maps API lookup
                print '  Searching Google maps for '+search_string+'+'+state
                gmap_url = GOOGLEMAPURL+search_string
            
                # Get lat/lon of google maps search
                response = requests.get(gmap_url)
            
                # Parse google maps return for lat lon
                resp_json_payload = response.json()
                try:
                    lat[city] = resp_json_payload['results'][0]['geometry']['location']['lat']
                    lon[city] = resp_json_payload['results'][0]['geometry']['location']['lng']
                except:
                    continue
                    
                # Parse return for county lookup
                for name in resp_json_payload['results'][0]['address_components']:
            
                    if name['short_name'].find('County') >= 0:
                
                        county_name = name['short_name'][:-7] + ', ' + state
                        county[county_name] = city
            
            
    print 'Download Complete'
    print '*****************'
    
    # Compute appreciation over time window
    appreciation = pd.DataFrame(columns=hpi.columns)
    sigma = pd.DataFrame(columns=hpi.columns)
    for time in hpi.index:
    
        # Get time at start of window
        t_window_start = time - years_to_analyze*12
        
        # Calculate appreciation if full window is in the database
        if t_window_start >= hpi.index[0]:
            
            # Get the total appreciation over time window
            total_appreciation_at_time = hpi.loc[time]/hpi.loc[t_window_start]
        
            # Get yearly appreciation over time window
            appreciation.loc[time] = 100.0*(pow(total_appreciation_at_time,(1.0/years_to_analyze)) - 1)
    
    # Get latest appreciation rates
    appreciation_latest = appreciation.loc[appreciation.index[-1]]
    
    # Sort highest to lowest
    appreciation_latest.sort_values(inplace=True,ascending=False)
        
    # Print out list
    hpi_ranking = open('hpi_ranking.txt', 'w')
    for city in appreciation_latest.index:
    
        hpi_ranking.write( city + ': {:.3}'.format(appreciation_latest[city]) + '%\n' )
    
    # Load the SVG map
    usa_svg = open('USA_Counties_with_FIPS_and_names.svg', 'r').read()

    # Parse map data
    usa_soup = BeautifulSoup(usa_svg, selfClosingTags=['defs','sodipodi:namedview'])

    # Find counties
    paths = usa_soup.findAll('path')

    # County style
    path_style = 'font-size:12px;fill-rule:nonzero;stroke:#FFFFFF;stroke-opacity:1; \
                  stroke-width:0.1;stroke-miterlimit:4;stroke-dasharray:none;stroke-linecap:butt; \
                  marker-start:none;stroke-linejoin:bevel;fill:'
    
    # Determine which counties need to be colored in
    for p in paths:
         
        if p['id'] not in ["State_Lines", "separator"]:
            # pass
            try:
                rate = appreciation_latest[county[p['inkscape:label']]]
            except:
                continue
             
            if rate > 0:
                color_class = int(floor(rate))
                color_class = min(color_class, len(pcolor)-1)
                color = pcolor[color_class]
            else:
                color_class = int(floor(-rate))
                color_class = min(color_class, len(mcolor)-1)
                color = mcolor[color_class]
 
            p['style'] = path_style + color

    # Output map
    usa_svg_out = open('hpi_map.svg', 'w')
    usa_svg_out.write(usa_soup.prettify())
    usa_svg_out.close()
    
    # Generate plots for appreciation rates
    plt.figure(1)
    plt.plot(appreciation)
    plt.xlabel('Year')
    plt.ylabel('Yearly Appreciation Rate over {} Years (%)'.format(years_to_analyze))
    #plt.legend(appreciation.columns)
    
    # Show plots
    plt.show()
    
def get_authvals_csv(authf):
    
    vals = {}	#dict of vals to be returned
    
    with open(authf, 'rb') as f:
        f_iter = csv.DictReader(f)
        vals = f_iter.next()
        
    return vals
    
if __name__ == '__main__':
  main()