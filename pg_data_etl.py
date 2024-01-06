from postgres_ingestion import PowerliftingDataHandler, PowerliftingDataRetriever
from datetime import datetime
import time

database_url = 'postgres://powerlifting_comp_user:Ow7MdhrLkOjBG7qbBvZJzNx7o6RSJOSQ@dpg-cm7otoi1hbls73au7d00-a.oregon-postgres.render.com/powerlifting_comp'
def etl_openpl_postgres(database_url):
    database_url = database_url
    postgres_instance = PowerliftingDataHandler(database_url)
    data_collector = PowerliftingDataRetriever()

    openpl_updated_dt = datetime.strptime(data_collector.retrieve_last_updated_date().rstrip('.'), '%Y-%m-%d')
    current_max_dt = datetime.strptime(postgres_instance.collect_max_dt('powerlifting_data'), '%Y-%m-%d')

    if openpl_updated_dt is not None and current_max_dt is not None:
        print(f'''Collected dates.''')
        time.sleep(1)
        print(f'''\nOpenPowerlifting has updated data for {openpl_updated_dt}. \nMost recent date in powerlifting_data Database is {current_max_dt}.''')
        time.sleep(2)

        if openpl_updated_dt > current_max_dt:

            while True:
                etl_input = input(f"""Looks like there is newer data to Ingest. Proceed with ETL to Postgres Database? (y/n)""").lower()

                if etl_input == 'y':
                    print('Ingest code here')
                    break  # Exit the loop if 'y' is entered
                elif etl_input == 'n':
                    print('Cancelling ETL. Data will not be ingested into Postgres Database')
                    break  # Exit the loop if 'n' is entered
                else:
                    print("Invalid input. Please enter 'y' or 'n'.")

        else:
            print('Data is already up to date in powerlifting_data Database.')

    else:
        print('Date values are not being returned in the proper format...')


print(etl_openpl_postgres(database_url))









