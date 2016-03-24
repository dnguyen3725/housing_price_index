import pdb
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
    print 'Downloading Data'
    hpi_data = {}
    for city in test_set:
    #for city in dataset_code:
        
        quandl_code = [database_code[city]+'/'+dataset_code[city]]
        
        print 'Downloading data for '+city
        
        hpi_data[city] = Quandl.get(quandl_code,authtoken=auth['authtoken'])
        
        #current_index = hpi_data[city]['2015-12-31']
        #previous_index = hpi_data[city]['{}-12-31'.format(2015-years_to_analyze)]
        #appreciation[city] = current_index/previous_index
        
    print 'Download Complete'
    
    pdb.set_trace()
    
    print appreciation
    
def get_authvals_csv(authf):
    
    vals = {}	#dict of vals to be returned
    
    with open(authf, 'rb') as f:
        f_iter = csv.DictReader(f)
        vals = f_iter.next()
        
    return vals
    
if __name__ == '__main__':
  main()