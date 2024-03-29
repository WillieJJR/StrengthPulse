import pandas as pd
#from postgres_ingestion import PowerliftingDataHandler
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

def clean_same_names_test(df, threshold: int): #assumes a df is cleaned and filtered down to a name

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

def clean_same_names(df):

    # Sort the DataFrame by 'Age' and 'Date'
    filtered_df = df.sort_values(by=['Age', 'Date'])

    # Calculate prev_date, new_lifter_flag, and personas columns
    filtered_df['prev_date'] = filtered_df.groupby('Name')['Date'].shift().fillna(filtered_df['Date'])
    filtered_df['new_lifter_flag'] = (filtered_df['prev_date'] > filtered_df['Date']) | filtered_df['prev_date'].isnull()
    filtered_df['persona'] = filtered_df.groupby('Name')['new_lifter_flag'].cumsum() + 1

    # Add identifier column
    filtered_df['identifier'] = filtered_df['new_lifter_flag'].apply(lambda x: 'New Lifter' if x else 'Current Lifter')

    # Create a new column that concatenates Name with persona
    filtered_df['name_with_persona'] = filtered_df['Name'] + ' #' + filtered_df['persona'].astype(str)

    return filtered_df


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

def calculate_wilks(gender: str, bodyweight: float, total: float, lbs: bool) -> float:
    if lbs:
        bodyweight = bodyweight / 2.2
        total = total / 2.2

    coefficients = {
        'm': [-216.0475144, 16.2606339, -0.002388645, -0.00113732, 7.01863e-6, -1.291e-8],
        'f': [594.31747775582, -27.23842536447, 0.82112226871, -0.00930733913, 4.731582e-5, -9.054e-8]
    }

    gender = gender.lower()

    if gender not in coefficients:
        raise ValueError("Invalid gender. Use 'male' or 'female'.")

    b0, b1, b2, b3, b4, b5 = coefficients[gender]

    wilks_coefficient = 500 / (
            b0 + (b1 * bodyweight) + (b2 * bodyweight ** 2) + (b3 * bodyweight ** 3) + (b4 * bodyweight ** 4) + (
            b5 * bodyweight ** 5)
    )

    return wilks_coefficient * total

def classify_wilks(wilks):
    if wilks is not None and not pd.isna(wilks):
        if wilks < 300:
            return 'Beginner'
        elif 300 <= wilks < 400:
            return 'Intermediate'
        elif 400 <= wilks < 500:
            return 'Advanced'
        else:
            return 'Elite'
    else:
        return None
