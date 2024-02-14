import os
from postgres_ingestion import PowerliftingDataHandler, PowerliftingDataRetriever
from datetime import datetime
import time
from config import DATABASE_URL


os.environ['DATABASE_URL'] = DATABASE_URL  #this value is stored in the config.py file and in the app environment vars - uncomment to use locally
database_url = os.environ.get('DATABASE_URL') #this value is stored in the config.py file and in the app environment vars

def etl_openpl_postgres(database_url: str) -> None:

    """
    Perform ETL (Extract, Transform, Load) process from OpenPowerlifting to a PostgreSQL Database.

    Parameters:
    - database_url (str): The URL of the PostgreSQL database.

    Returns:
    None
    """

    database_url = database_url
    postgres_instance = PowerliftingDataHandler(database_url)
    data_collector = PowerliftingDataRetriever()

    try:
        openpl_updated_dt = datetime.strptime(data_collector.retrieve_last_updated_date().rstrip('.'), '%Y-%m-%d')
        current_max_dt = datetime.strptime(postgres_instance.collect_max_dt('powerlifting_data'), '%Y-%m-%d')
    except ValueError as e:
        print(f"Error parsing dates: {e}")
        return

    print(f"Collected dates.\nOpenPowerlifting was last updated on {openpl_updated_dt}.")
    time.sleep(1)

    print(f"Most recent date in powerlifting_data Database is {current_max_dt}.")
    time.sleep(2)

    current_record_count = postgres_instance.collect_cnt_records('powerlifting_data')
    print(f"Current record count in powerlifting_data Database: {current_record_count}")
    print("Checking for newly available records to ingest...")
    time.sleep(1)

    print("Extracting data from OpenPowerlifting...")
    source_data = data_collector.process_subset_from_csv(filter_date=current_max_dt)

    if len(source_data) > 0:
        while True:
            etl_input = input(
                "Looks like there is newer data to ingest. Proceed with ETL to Postgres Database? (y/n)").lower()

            if etl_input == 'y':
                print("Loading data into powerlifting_data Database...")
                postgres_instance.insert_data(csv_data=source_data, table_name='powerlifting_data')
                print("Data is now available in powerlifting_data Database.")
                current_record_count = postgres_instance.collect_cnt_records('powerlifting_data')
                print(f"Current record count in powerlifting_data Database: {current_record_count}")
                break
            elif etl_input == 'n':
                print("Canceling ETL. Data will not be ingested into Postgres Database.")
                break
            else:
                print("Invalid input. Please enter 'y' or 'n'.")
    else:
        print("No additional records available. Data is already up to date in powerlifting_data Database.")


if __name__ == "__main__":
    etl_openpl_postgres(database_url)











