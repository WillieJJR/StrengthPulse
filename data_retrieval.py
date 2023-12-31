import requests
from bs4 import BeautifulSoup
import pandas as pd
import zipfile
from io import BytesIO
import time

'''Create PL Data retriever class'''
class PowerliftingDataRetriever:

    '''initialize variable states'''
    def __init__(self):
        self.updated_dt_url = 'https://openpowerlifting.gitlab.io/opl-csv/bulk-csv.html'
        self.zip_url = 'https://openpowerlifting.gitlab.io/opl-csv/files/openpowerlifting-latest.zip'
        self.csv_data = None
        self.updated_date = None

    '''create function to retrieve csv from website and read as a df'''
    def retrieve_and_process_csv(self, chunk_size = 10000, print_interval=250000):
        response = requests.get(self.zip_url)

        if response.status_code == 200:
            with zipfile.ZipFile(BytesIO(response.content), 'r') as zipf:
                csv_file = self.find_csv_file(zipf)

                if csv_file:
                    chunks = pd.read_csv(zipf.open(csv_file), chunksize=chunk_size)
                    filtered_chunks = []
                    records_ingested = 0
                    #filter_date = pd.to_datetime(filter_date)

                    for chunk in chunks:

                        #test
                        #chunk['Date'] = pd.to_datetime(chunk['Date'])
                        # Apply filtering directly during reading
                        filtered_chunk = chunk[chunk['Country'] == 'USA']
                        #filtered_chunk = filtered_chunk[filtered_chunk['Date'] >= filter_date]
                        filtered_chunks.append(filtered_chunk)

                        records_ingested += chunk.shape[0]

                        # Print records ingested at regular intervals
                        if records_ingested % print_interval == 0:
                            print(f"Records Ingested: {records_ingested}")

                    # Concatenate filtered chunks into a single DataFrame
                    self.csv_data = pd.concat(filtered_chunks, ignore_index=True)
                    return self.csv_data  # Return the DataFrame
                else:
                    print('No CSV file found in the zip archive')
        else:
            print('Failed to retrieve the zip file.')


    '''create function to extract the date of the last refresh of this data'''
    def retrieve_last_updated_date(self):
        url = self.updated_dt_url
        response = requests.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            div_element = soup.find('div', {'class': 'content'})

            if div_element:
                ul_element = div_element.find('ul')

                if ul_element:
                    first_li = ul_element.find('li')

                    if first_li:
                        first_li_text = first_li.text.strip()
                        first_li_int = first_li_text.find(":")
                        if first_li_int != -1:
                            self.updated_date = first_li_text[first_li_int + 1:].strip()
                    else:
                        self.updated_date = '(Could not find an updated date..)'

                    return self.updated_date
                else:
                    print('Unable to find any unordered lists in the div')
            else:
                print('No Div element found for class content')
        else:
            print('Failed to access the data')

    def process_subset_from_csv(self, filter_date, chunk_size=10000, print_interval=250):
        response = requests.get(self.zip_url)

        if response.status_code == 200:
            with zipfile.ZipFile(BytesIO(response.content), 'r') as zipf:
                csv_file = self.find_csv_file(zipf)

                if csv_file:
                    chunks = pd.read_csv(zipf.open(csv_file), chunksize=chunk_size)
                    filtered_chunks = []
                    total_records_ingested = 0  # Track total records ingested across all chunks
                    filter_dt = pd.to_datetime(filter_date)

                    # Count total number of chunks
                    total_records = sum(1 for line in zipf.open(csv_file))
                    quotient, remainder = divmod(total_records, chunk_size)
                    total_chunks = quotient + (remainder > 0)

                    for chunk_number, chunk in enumerate(chunks, start=1):
                        chunk['Date'] = pd.to_datetime(chunk['Date'])

                        # Apply filtering directly during reading
                        filtered_chunk = chunk[chunk['Country'] == 'USA']
                        filtered_chunk = filtered_chunk[filtered_chunk['Date'] > filter_dt]
                        filtered_chunks.append(filtered_chunk)

                        records_ingested = filtered_chunk.shape[0]
                        total_records_ingested += records_ingested

                        # Print records ingested for the current chunk
                        print(f"Processing Chunk {chunk_number} of {total_chunks}")

                        # Print total records ingested at regular intervals
                        if chunk_number % print_interval == 0 or chunk_number == total_chunks:
                            print(f"New Records Available: {total_records_ingested}")

                    # Concatenate filtered chunks into a single DataFrame
                    self.csv_data = pd.concat(filtered_chunks, ignore_index=True)
                    return self.csv_data  # Return the DataFrame
                else:
                    print('No CSV file found in the zip archive')
        else:
            print('Failed to retrieve the zip file.')

    '''create a function to absract the process of collecting the csv'''
    def find_csv_file(self, zipf):
        for file_name in zipf.namelist():
            if file_name.endswith('.csv'):
                return file_name
        return None





# Call the data retrieval functions when the application is started
if __name__ == "__main__":
    data_retriever = PowerliftingDataRetriever()
    data_retriever.retrieve_and_process_csv()  # Get the DataFrame
    data_retriever.retrieve_last_updated_date()
    data_retriever.process_subset_from_csv()

