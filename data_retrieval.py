import requests
import pandas as pd
from io import BytesIO
import zipfile
from bs4 import BeautifulSoup
from io import StringIO


def retrieve_and_process_csv():
    # URL of the website containing the zipped files
    zip_url = 'https://openpowerlifting.gitlab.io/opl-csv/files/openpowerlifting-latest.zip'

    # Fetch the zip file directly
    response = requests.get(zip_url)

    # Check if the request was successful
    if response.status_code == 200:
        # Unzip the file
        with zipfile.ZipFile(BytesIO(response.content), 'r') as zipf:
            csv_file = None

            # Look for a CSV file in the zip archive
            for file_name in zipf.namelist():
                if file_name.endswith('.csv'):
                    csv_file = file_name
                    break

            if csv_file:
                # Read the CSV data from the zip archive
                with zipf.open(csv_file) as file:
                    df = pd.read_csv(file)

                # Now, 'df' contains the CSV data, and you can use it for processing
                df = df[df['Country'] == 'USA']


                # Example: Display the first few rows of the DataFrame
                return df
            else:
                print('No CSV file found in the zip archive')
    else:
        print('Failed to retrieve the zip file.')

def retrieve_last_updated_date() -> str:
    url = "https://openpowerlifting.gitlab.io/opl-csv/bulk-csv.html"
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        div_element = soup.find('div', {'class': 'content'})

        first_li_text = None
        # Check if the div is found
        if div_element:
            # Find the unordered list (ul) element within the div
            ul_element = div_element.find('ul')

            # Extract text values from each list item (li) within the unordered list
            if ul_element:
                first_li = ul_element.find('li')

                # Check if the first list item is found
                if first_li:
                    first_li_text = first_li.text.strip()
                    first_li_int = first_li_text.find(":")
                    if first_li_int != -1:
                        updated_date = first_li_text[first_li_int + 1:].strip()
                else:
                    updated_date = '''(Could not find an updated date..)'''

                return updated_date

            else:
                print('Unable to find anu unordered lists in the div')

        else:
            print('No Div element found for class content')

    else:
        print('Failed to access the data')



# Call the data retrieval function when the application is started
if __name__ == "__main__":
    retrieve_and_process_csv()
    retrieve_last_updated_date()


