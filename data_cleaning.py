import pandas as pd
from postgres_ingestion import fetch_data
import psycopg2
from psycopg2 import sql
from data_retrieval import PowerliftingDataRetriever
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import numpy as np



#df = retrieve_and_process_csv()

def remove_special_chars(df):
    if df is not None:
        df['WeightClassKg'] = df['WeightClassKg'].str.replace(r'\+', '', regex=True)
    else:
        print('Dataframe is empty')


def convert_kg_to_lbs(df):
    kg = 'Kg'
    lb = 'Lb'
    for name in df.columns:
        if kg in name:
            if name == 'WeightClassKg':
                pass
            else:
                try:
                    modified_col_name = name.replace(kg,lb)
                    df[modified_col_name] = df[name]*2.2
                except ValueError as e:
                    pass

    return df


def apply_business_rules(df):

    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df = df[df['Date'].dt.year >= 2013] #will make this more dynamic later
    else:
        raise ValueError('There is no column Date')

    if 'WeightClassKg' in df.columns:
        df = df.dropna(subset=['WeightClassKg'])

    if 'Tested' in df.columns:
        df['Tested'] = df['Tested'].apply(lambda x: 'Not Known' if x != 'Yes' else x)


    if all(col in df.columns for col in ['BirthYearClass', 'AgeClass', 'Age']):
        mask = df['AgeClass'].isna() & ~df['BirthYearClass'].isna()
        df.loc[mask, 'AgeClass'] = df.loc[mask, 'BirthYearClass']

        df = df[~(df['Age'].isna() & df['AgeClass'].isna() & df['BirthYearClass'].isna()) & (df['Age'] >= 13)]

        if df['AgeClass'].isna().any():
            raise ValueError('AgeClass contains NaN values')
    else:
        raise ValueError("One or more required columns are missing")

    return df

def clean_same_names(df, threshold: int): #assumes a df is cleaned and filtered down to a name

    if df is not None:
        if df['Name'].nunique() == 1:
            sorted_df = df.sort_values(by='Age')
            sorted_df['age_diff'] = sorted_df['Age'].diff()
            sorted_df['date_diff'] = sorted_df['Date'].dt.year.diff()

            #assign threshold
            threshold = threshold

            # Identify potential anomalies
            mask = (sorted_df['age_diff'] - sorted_df['date_diff']).abs() > threshold
            validation_df = sorted_df[mask]

            #assign initial value
            sorted_df['persona'] = 0

            #Initialize the group number
            group_number = 1

            #Initialize dict
            group_mapping = {}

            for _, record in validation_df.iterrows():
                match = (
                        (sorted_df['Name'] == record['Name']) &
                        (sorted_df['Date'] == record['Date'])
                )

                if not sorted_df.loc[match, 'persona'].any():
                    # If not, assign the current group number to the 'check' column for the matching record
                    sorted_df.loc[match, 'persona'] = group_number
                    # Store the matching records in the group mapping
                    group_mapping[group_number] = sorted_df.loc[match].index.tolist()

                    # Increment the group number
                    group_number += 1

            non_mask = sorted_df['persona'] == 0
            sorted_df.loc[non_mask, 'persona'] = sorted_df['persona'].replace(0, method='ffill')

            return sorted_df

        else:
            print('''There are multiple name values present in the dataframe''')
    else:
        print('''Dataframe is empty''')


def reduce_mem_usage(df, verbose=True):
    numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
    start_mem = df.memory_usage(deep=True).sum() / 1024**2
    for col in df.columns:
        col_type = df[col].dtypes
        if col_type in numerics:
            c_min = df[col].min()
            c_max = df[col].max()
            if str(col_type)[:3] == 'int':  # for integers
                if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                    df[col] = df[col].astype(np.int8)
                elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                    df[col] = df[col].astype(np.int16)
                elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                    df[col] = df[col].astype(np.int32)
                elif c_min > np.iinfo(np.int64).min and c_max < np.iinfo(np.int64).max:
                    df[col] = df[col].astype(np.int64)
            else:  # for floats.
                if c_min > np.finfo(np.float16).min and c_max < np.finfo(np.float16).max:
                    df[col] = df[col].astype(np.float16)
                elif c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                    df[col] = df[col].astype(np.float32)
                else:
                    df[col] = df[col].astype(np.float64)
    end_mem = df.memory_usage(deep=True).sum() / 1024**2
    if verbose: print('Mem. usage decreased to {:5.2f} Mb ({:.1f}% reduction)'.format(end_mem, 100 * (start_mem - end_mem) / start_mem))
    return df


'''Scratch Pad'''
# database_url = 'postgres://powerlifting_comp_user:Ow7MdhrLkOjBG7qbBvZJzNx7o6RSJOSQ@dpg-cm7otoi1hbls73au7d00-a.oregon-postgres.render.com/powerlifting_comp'
# df = fetch_data(table_name='powerlifting_data', database_url=database_url)
# memory_usage = df.memory_usage(deep=True)
# total_memory_usage = memory_usage.sum() / (1024**2)  # Convert bytes to megabytes
# print(f'Total memory usage: {total_memory_usage:.2f} MB')
# data_retriever = PowerliftingDataRetriever()
# df = data_retriever.retrieve_and_process_csv()
# # datatype_column1 = df['Date'].dtype
# df['Date'] = pd.to_datetime(df['Date'])
# #
# #
# #
# df = df[df['Date'].dt.year >= 2013]
# user_profile = df[(df['Name'] == 'Ty Evans #1') & (df['Event'] == 'SBD')]
# cols = ['BodyweightKg', 'MeetName', 'Date']
# df_user_profile = user_profile.drop_duplicates(subset=cols)
#
# unique_lifter_validation = clean_same_names(df_user_profile, 1)
# if unique_lifter_validation['persona'].nunique() > 1:
#     cols.append('persona')
#     df_user_profile = clean_same_names(df_user_profile, 1)
#
#
# lifter_stats_df_agg = df_user_profile.groupby(cols).agg({'Best3SquatKg': 'sum', 'Best3BenchKg': 'sum', 'Best3DeadliftKg': 'sum'}).reset_index()
#
# unique_lifter_validation = clean_same_names(df_user_profile_2, 1)
# if unique_lifter_validation['persona'].nunique() > 1:
#     cols.append('persona')
#     lifter_stats_df = clean_same_names(df_user_profile_2, 1)
