import requests

def get_invasive_status(taxon_key, test=False):
    # Global Register of Introduced and Invasive Species - United States
    dataset_key = '32ad19ed-6b89-447a-9242-795c0897f345'
    
    # Construct the request URL
    url = f"https://api.gbif.org/v1/occurrence/count?datasetKey={dataset_key}&taxonKey={taxon_key}"
    
    # Make the GET request
    response = requests.get(url)
    
    # Check the response status
    if response.status_code == 200:
        is_invasive = response.json()
        return False if is_invasive == 0 else True
    else:
        print(f"Request failed with status code: {response.status_code}")