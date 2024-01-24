import psycopg2
from data_retrieval import PowerliftingDataRetriever
from psycopg2 import sql
import pandas as pd
from io import StringIO
from data_cleaning import remove_special_chars, convert_kg_to_lbs, apply_business_rules

class PowerliftingDataHandler:
    """
    A class to handle data operations between a PostgreSQL database and Powerlifting data.

    Attributes:
    - database_url (str): The URL of the PostgreSQL database.
    - data_retriever (PowerliftingDataRetriever): An instance of PowerliftingDataRetriever for data retrieval.
    """

    def __init__(self, database_url):
        """
        Constructor for PowerliftingDataHandler.

        Parameters:
        - database_url (str): The URL of the PostgreSQL database.
        """

        self.database_url = database_url
        self.data_retriever = PowerliftingDataRetriever()
    @staticmethod
    def get_pg_datatype(pandas_dtype):
        """
        Doesn't depend on any instance calls so making it a static method
        Map pandas data types to PostgreSQL data types.

        Parameters:
        - pandas_dtype: The pandas data type.

        Returns:
        - str: Corresponding PostgreSQL data type.
        """

        dtype_mapping = {
            'int64': 'INTEGER',
            'float64': 'REAL',
            'object': 'VARCHAR(255)',
            # Add more mappings as needed
        }
        return dtype_mapping.get(str(pandas_dtype), 'VARCHAR(255)')  # Default to VARCHAR(255) for unknown types

    def create_table(self, csv_data, table_name)-> None:
        """
         Create a PostgreSQL table based on the structure of a DataFrame.

         Parameters:
         - csv_data (pd.DataFrame): The DataFrame containing the data structure.
         - table_name (str): The name of the table to be created.

         Returns:
         None
         """

        # Establish a connection to the PostgreSQL database
        conn = psycopg2.connect(self.database_url)
        cur = conn.cursor()

        # Check if the table already exists
        table_exists_query = sql.SQL(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = {});").format(
            sql.Literal(table_name))
        cur.execute(table_exists_query)
        table_exists = cur.fetchone()[0]

        if table_exists:
            # Table already exists, ask the user if they want to drop it
            record_count_query = sql.SQL("SELECT COUNT(*) FROM {};").format(sql.Identifier(table_name))
            cur.execute(record_count_query)
            total_records = cur.fetchone()[0]
            drop_table_input = input(
                f"Table '{table_name}' already exists with {total_records} records. Do you want to drop and recreate it? (y/n): ").lower()

            if drop_table_input == 'y':
                # Drop the table if the user says yes
                drop_table_query = sql.SQL("DROP TABLE IF EXISTS {} CASCADE;").format(sql.Identifier(table_name))
                cur.execute(drop_table_query)
                conn.commit()

                # Create the table with the same structure as the DataFrame
                create_table_query = sql.SQL("CREATE TABLE {} ({});").format(
                    sql.Identifier(table_name),
                    sql.SQL(', ').join(
                        [sql.SQL("{} {}").format(sql.Identifier(col),
                                                 sql.SQL(self.get_pg_datatype(csv_data.dtypes[col]))) for
                         col in csv_data.columns])
                )

                print(f"Creating table '{table_name}' with query:")
                print(create_table_query.as_string(conn))
                cur.execute(create_table_query)
                conn.commit()
            elif drop_table_input == 'n':
                # User chose not to drop the table, print a message and return
                print(f"Table '{table_name}' already exists. Leaving it as is.")
            else:
                print('Not a valid option. Please type y/n.')
        else:
            # Table doesn't exist, proceed with creating it
            create_table_query = sql.SQL("CREATE TABLE {} ({});").format(
                sql.Identifier(table_name),
                sql.SQL(', ').join(
                    [sql.SQL("{} {}").format(sql.Identifier(col), sql.SQL(self.get_pg_datatype(csv_data.dtypes[col])))
                     for col in
                     csv_data.columns])
            )

            print(f"Creating table '{table_name}' with query:")
            print(create_table_query.as_string(conn))
            cur.execute(create_table_query)
            conn.commit()


    def insert_data(self, csv_data, table_name)-> None:
        """
        Insert data into a PostgreSQL table.

        Parameters:
        - csv_data (pd.DataFrame): The DataFrame containing the data to be inserted.
        - table_name (str): The name of the table.

        Returns:
        None
        """

        conn = psycopg2.connect(self.database_url)
        cur = conn.cursor()

        # Insert data into the table
        csv_data_string = StringIO()
        csv_data.to_csv(csv_data_string, index=False, header=False)
        csv_data_string.seek(0)

        copy_query = f"COPY {table_name} FROM STDIN WITH CSV DELIMITER ','"
        cur.copy_expert(copy_query, csv_data_string)

        # Commit the transaction
        conn.commit()

        # Close the cursor and connection
        cur.close()
        conn.close()


    def fetch_data(self, table_name):
        """
        Fetch data from a PostgreSQL table.

        Parameters:
        - table_name (str): The name of the table.

        Returns:
        - pd.DataFrame: The fetched data.
        """

        conn = psycopg2.connect(self.database_url)
        cur = conn.cursor()

        # Fetch data from the table
        query = f"""SELECT "Name", "Sex", "Event", "Age", "BirthYearClass", "AgeClass", "Division", "BodyweightKg",
         "WeightClassKg", "Best3SquatKg", "Best3BenchKg", "Best3DeadliftKg", "Wilks", "Place", "Tested", "Country", "Federation",
         "Date", "MeetName", "MeetState" FROM {table_name} WHERE "Age" IS NOT NULL AND CAST(SUBSTRING("Date" FROM 1 FOR 4) AS INTEGER) > 2017 AND "Place" != 'DQ' AND "MeetCountry" = 'USA';"""
        chunk_size = 1000  # Adjust as needed
        result_chunks = pd.read_sql_query(query, conn, chunksize=chunk_size)

        # Apply custom functions to each chunk
        processed_chunks = []
        for chunk in result_chunks:
            # Apply your custom functions to the chunk
            remove_special_chars(chunk)
            chunk = convert_kg_to_lbs(chunk)
            chunk = apply_business_rules(chunk)

            # Append the processed chunk to the list
            processed_chunks.append(chunk)

        # Concatenate the processed chunks into a single DataFrame
        result = pd.concat(processed_chunks, ignore_index=True)

        # Close the connection
        conn.close()
        return result

    def collect_max_dt(self, table_name) -> str:
        """
        Collect the maximum date from a PostgreSQL table.

        Parameters:
        - table_name (str): The name of the table.

        Returns:
        - str: The maximum date in string format.
        """

        conn = psycopg2.connect(self.database_url)
        cur = conn.cursor()

        query = f"""SELECT MAX("Date") FROM {table_name};"""
        cur.execute(query)

        # Fetch the result
        max_date_str = cur.fetchone()[0]

        cur.close
        conn.close()

        return max_date_str


    def collect_cnt_records(self, table_name) -> int:
        """
        Collect the count of records from a PostgreSQL table.

        Parameters:
        - table_name (str): The name of the table.

        Returns:
        - int: The count of records.
        """

        conn = psycopg2.connect(self.database_url)
        cur = conn.cursor()

        query = f"""SELECT count(*) FROM {table_name};"""
        cur.execute(query)

        # Fetch the result
        current_cnt = cur.fetchone()[0]

        cur.close
        conn.close()

        return current_cnt





if __name__ == '__main__':
    postgres_instance = PowerliftingDataHandler
    postgres_instance.create_table()
    postgres_instance.insert_data()
    postgres_instance.fetch_data()
    postgres_instance.collect_max_dt()
    postgres_instance.collect_cnt_records()

















































# data_retriever = PowerliftingDataRetriever()
#
# #df = data_retriever.retrieve_and_process_csv()
# #database_url = 'postgres://powerlifting_comp_user:Ow7MdhrLkOjBG7qbBvZJzNx7o6RSJOSQ@dpg-cm7otoi1hbls73au7d00-a.oregon-postgres.render.com/powerlifting_comp'
#
#
# def get_pg_datatype(pandas_dtype):
#     # Map pandas data types to PostgreSQL data types
#     dtype_mapping = {
#         'int64': 'INTEGER',
#         'float64': 'REAL',
#         'object': 'VARCHAR(255)',
#         # Add more mappings as needed
#     }
#     return dtype_mapping.get(str(pandas_dtype), 'VARCHAR(255)')  # Default to VARCHAR(255) for unknown types
#
# def create_table(database_url, csv_data, table_name):
#     # Establish a connection to the PostgreSQL database
#     conn = psycopg2.connect(database_url)
#     cur = conn.cursor()
#
#     # Check if the table already exists
#     table_exists_query = sql.SQL("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = {});").format(sql.Literal(table_name))
#     cur.execute(table_exists_query)
#     table_exists = cur.fetchone()[0]
#
#     if table_exists:
#         # Table already exists, ask the user if they want to drop it
#         record_count_query = sql.SQL("SELECT COUNT(*) FROM {};").format(sql.Identifier(table_name))
#         cur.execute(record_count_query)
#         total_records = cur.fetchone()[0]
#         drop_table_input = input(
#             f"Table '{table_name}' already exists with {total_records} records. Do you want to drop and recreate it? (y/n): ").lower()
#
#         if drop_table_input == 'y':
#             # Drop the table if the user says yes
#             drop_table_query = sql.SQL("DROP TABLE IF EXISTS {} CASCADE;").format(sql.Identifier(table_name))
#             cur.execute(drop_table_query)
#             conn.commit()
#
#             # Create the table with the same structure as the DataFrame
#             create_table_query = sql.SQL("CREATE TABLE {} ({});").format(
#                 sql.Identifier(table_name),
#                 sql.SQL(', ').join(
#                     [sql.SQL("{} {}").format(sql.Identifier(col), sql.SQL(get_pg_datatype(csv_data.dtypes[col]))) for
#                      col in csv_data.columns])
#             )
#
#             print(f"Creating table '{table_name}' with query:")
#             print(create_table_query.as_string(conn))
#             cur.execute(create_table_query)
#             conn.commit()
#         elif drop_table_input == 'n':
#             # User chose not to drop the table, print a message and return
#             print(f"Table '{table_name}' already exists. Leaving it as is.")
#         else:
#             print('Not a valid option. Please type y/n.')
#     else:
#         # Table doesn't exist, proceed with creating it
#         create_table_query = sql.SQL("CREATE TABLE {} ({});").format(
#             sql.Identifier(table_name),
#             sql.SQL(', ').join(
#                 [sql.SQL("{} {}").format(sql.Identifier(col), sql.SQL(get_pg_datatype(csv_data.dtypes[col]))) for col in
#                  csv_data.columns])
#         )
#
#         print(f"Creating table '{table_name}' with query:")
#         print(create_table_query.as_string(conn))
#         cur.execute(create_table_query)
#         conn.commit()
#
#         # Close the cursor and connection
#     cur.close()
#     conn.close()
#
#
# def insert_data(database_url, csv_data, table_name):
#     # Establish a connection to the PostgreSQL database
#     conn = psycopg2.connect(database_url)
#     cur = conn.cursor()
#
#     # Insert data into the table
#     csv_data_string = StringIO()
#     csv_data.to_csv(csv_data_string, index=False, header=False)
#     csv_data_string.seek(0)
#
#     copy_query = f"COPY {table_name} FROM STDIN WITH CSV DELIMITER ','"
#     cur.copy_expert(copy_query, csv_data_string)
#
#     # Commit the transaction
#     conn.commit()
#
#     # Close the cursor and connection
#     cur.close()
#     conn.close()
#
# def fetch_data(table_name, database_url):
#     # Establish a connection to the PostgreSQL database
#     conn = psycopg2.connect(database_url)
#     cur = conn.cursor()
#
#     # Fetch data from the table
#     query = f"""SELECT "Name", "Sex", "Event", "Age", "BirthYearClass", "AgeClass", "Division", "BodyweightKg",
#      "WeightClassKg", "Best3SquatKg", "Best3BenchKg", "Best3DeadliftKg", "Wilks", "Place", "Tested", "Country", "Federation",
#      "Date", "MeetName" FROM {table_name} WHERE "Age" IS NOT NULL AND CAST(SUBSTRING("Date" FROM 1 FOR 4) AS INTEGER) > 2017 AND "Place" != 'DQ';"""
#     #result = pd.read_sql_query(query, conn)
#     chunk_size = 1000  # Adjust as needed
#     result_chunks = pd.read_sql_query(query, conn, chunksize=chunk_size)
#
#     # Apply custom functions to each chunk
#     processed_chunks = []
#     for chunk in result_chunks:
#         # Apply your custom functions to the chunk
#         remove_special_chars(chunk)
#         chunk = convert_kg_to_lbs(chunk)
#         chunk = apply_business_rules(chunk)
#
#         # Append the processed chunk to the list
#         processed_chunks.append(chunk)
#
#     # Concatenate the processed chunks into a single DataFrame
#     result = pd.concat(processed_chunks, ignore_index=True)
#
#     # Close the connection
#     conn.close()
#     return result
#
# # def distinct_federation(table_name, database_url):
# #     conn = psycopg2.connect(database_url)
# #     cur = conn.cursor()
# #     query = f"""SELECT DISTINCT "Federation" FROM {table_name} ;"""
# #     cur.execute(query)
# #     rows = cur.fetchall()
# #
# #     cur.close()
# #     conn.close()
# #
# #     # Convert the tuples to a list of dictionaries
# #     result_list = [{'label': federation, 'value': federation} for federation, in rows]
# #
# #     return result_list
#
#
# if __name__ == "__main__":
#     create_table()
#     insert_data()
#     fetch_data()
#     #distinct_federation()

# create_table(database_url, csv_data=df, table_name='powerlifting_data')
# insert_data(database_url, csv_data=df, table_name='powerlifting_data')
# result_df = fetch_data(table_name='powerlifting_data', database_url=database_url)



# database_url = 'postgres://powerlifting_comp_user:Ow7MdhrLkOjBG7qbBvZJzNx7o6RSJOSQ@dpg-cm7otoi1hbls73au7d00-a.oregon-postgres.render.com/powerlifting_comp'
#
# conn = psycopg2.connect(database_url)
#
# cur = conn.cursor()
#
# table_creation_query = """
# CREATE TABLE IF NOT EXISTS example_table (
#     id SERIAL PRIMARY KEY,
#     name VARCHAR(100),
#     age INT
# );
# """
#
# cur.execute(table_creation_query)
# conn.commit()
#
# data_to_insert = ("John Doe", 25)
# insert_query = """
# INSERT INTO example_table (name, age) VALUES (%s, %s);
# """
# cur.execute(insert_query, data_to_insert)
# conn.commit()
#
# # Close the cursor and connection
# cur.close()
# conn.close()
#
#
# conn = psycopg2.connect(database_url)
#
# # Create a cursor
# cur = conn.cursor()
#
# # Example: Select data from the table
# select_query = "SELECT * FROM example_table;"
# cur.execute(select_query)
# result = cur.fetchall()
#
# # Print the result
# print("Data in the table:")
# for row in result:
#     print(row)
#
# # Close the cursor and connection
# cur.close()
# conn.close()
#
# conn = psycopg2.connect(database_url)
#
# # Create a cursor
# cur = conn.cursor()
#
# # Example: Drop the table
# drop_table_query = "DROP TABLE IF EXISTS example_table;"
# cur.execute(drop_table_query)
# conn.commit()
#
# # Close the cursor and connection
# cur.close()
# conn.close()