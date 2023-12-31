import psycopg2
from data_retrieval import PowerliftingDataRetriever
from psycopg2 import sql
import pandas as pd
from io import StringIO

data_retriever = PowerliftingDataRetriever()

#df = data_retriever.retrieve_and_process_csv()
#database_url = 'postgres://powerlifting_comp_user:Ow7MdhrLkOjBG7qbBvZJzNx7o6RSJOSQ@dpg-cm7otoi1hbls73au7d00-a.oregon-postgres.render.com/powerlifting_comp'


def get_pg_datatype(pandas_dtype):
    # Map pandas data types to PostgreSQL data types
    dtype_mapping = {
        'int64': 'INTEGER',
        'float64': 'REAL',
        'object': 'VARCHAR(255)',
        # Add more mappings as needed
    }
    return dtype_mapping.get(str(pandas_dtype), 'VARCHAR(255)')  # Default to VARCHAR(255) for unknown types

def create_table(database_url, csv_data, table_name):
    # Establish a connection to the PostgreSQL database
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()

    # Check if the table already exists
    table_exists_query = sql.SQL("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = {});").format(sql.Literal(table_name))
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
                    [sql.SQL("{} {}").format(sql.Identifier(col), sql.SQL(get_pg_datatype(csv_data.dtypes[col]))) for
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
                [sql.SQL("{} {}").format(sql.Identifier(col), sql.SQL(get_pg_datatype(csv_data.dtypes[col]))) for col in
                 csv_data.columns])
        )

        print(f"Creating table '{table_name}' with query:")
        print(create_table_query.as_string(conn))
        cur.execute(create_table_query)
        conn.commit()

        # Close the cursor and connection
    cur.close()
    conn.close()


def insert_data(database_url, csv_data, table_name):
    # Establish a connection to the PostgreSQL database
    conn = psycopg2.connect(database_url)
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

def fetch_data(table_name, database_url):
    # Establish a connection to the PostgreSQL database
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()

    # Fetch data from the table
    query = f"SELECT * FROM {table_name} limit 50000;"
    result = pd.read_sql_query(query, conn)
    #cur.execute(query)
    #result = cur.fetchall()

    # Close the connection
    conn.close()

    return result

if __name__ == "__main__":
    create_table()
    insert_data()
    fetch_data()

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