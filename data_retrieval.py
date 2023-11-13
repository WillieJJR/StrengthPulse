import requests
import pandas as pd
from io import BytesIO
import zipfile
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
                print(df.columns)
                df = df[df['Country'] == 'USA']


                # Example: Display the first few rows of the DataFrame
                return df
            else:
                print('No CSV file found in the zip archive')
    else:
        print('Failed to retrieve the zip file.')


# Call the data retrieval function when the application is started
if __name__ == "__main__":
    retrieve_and_process_csv()


