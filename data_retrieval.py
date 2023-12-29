import requests
from bs4 import BeautifulSoup
import pandas as pd
import zipfile
from io import BytesIO

'''Create PL Data retriever class'''
class PowerliftingDataRetriever:

    '''initialize variable states'''
    def __init__(self):
        self.updated_dt_url = 'https://openpowerlifting.gitlab.io/opl-csv/bulk-csv.html'
        self.zip_url = 'https://openpowerlifting.gitlab.io/opl-csv/files/openpowerlifting-latest.zip'
        self.csv_data = None
        self.updated_date = None

    '''create function to retrieve csv from website and read as a df'''
    def retrieve_and_process_csv(self):
        response = requests.get(self.zip_url)

        if response.status_code == 200:
            with zipfile.ZipFile(BytesIO(response.content), 'r') as zipf:
                csv_file = self.find_csv_file(zipf)

                if csv_file:
                    with zipf.open(csv_file) as file:
                        self.csv_data = pd.read_csv(file)
                        self.csv_data = self.csv_data[self.csv_data['Country'] == 'USA']
                        return self.csv_data.head(10)  # Return the DataFrame
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

    '''create a function to absract the process of collecting the csv'''
    def find_csv_file(self, zipf):
        for file_name in zipf.namelist():
            if file_name.endswith('.csv'):
                return file_name
        return None


# Call the data retrieval functions when the application is started
if __name__ == "__main__":
    data_retriever = PowerliftingDataRetriever()
    df = data_retriever.retrieve_and_process_csv()  # Get the DataFrame
    data_retriever.retrieve_last_updated_date()


