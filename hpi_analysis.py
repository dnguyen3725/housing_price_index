from IPython.core.debugger import Tracer
import numpy as np
import pandas as pd
import csv
import Quandl

# Main Loop
def main():

    # Config
    years_to_analyze = 5

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

    test_set = ['The Villages, FL','Cedar Rapids, IA', 'Champaign-Urbana, IL']
    
    # Download HPI data
    print '*****************'
    print 'Downloading Data'
    hpi = pd.DataFrame()
    
    #for city in test_set:
    for city in dataset_code:
        
        # Download quandl data for city housing price index
        quandl_code = [database_code[city]+'/'+dataset_code[city]]
        
        print 'Downloading data for '+city
        
        # Get HPI data for each city
        hpi_data = Quandl.get(quandl_code,authtoken=auth['authtoken'])
        
        # Rename column to city name and merge into dataframe
        hpi_data.columns = [city]        
        hpi = pd.concat([hpi, hpi_data], axis=1)
        
    print 'Download Complete'
    print '*****************'
    
    # Compute 5 year housing appreciation
    total_appreciation = hpi.loc['12-31-2015']/hpi.loc['12-31-2010']
    
    appreciation = 100.0*(pow(total_appreciation,(1.0/5.0)) - 1)
    
    # Sort highest to lowest
    appreciation.sort_values(inplace=True,ascending=False)
    
    # Print out list
    for city in appreciation.index:
    
        print city + ': {:.3}'.format(appreciation[city]) + '%'
    
def get_authvals_csv(authf):
    
    vals = {}	#dict of vals to be returned
    
    with open(authf, 'rb') as f:
        f_iter = csv.DictReader(f)
        vals = f_iter.next()
        
    return vals
    
if __name__ == '__main__':
  main()