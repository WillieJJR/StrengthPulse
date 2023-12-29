import pandas as pd
from data_retrieval import PowerliftingDataRetriever
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler



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





'''Scratch Pad'''
# df = retrieve_and_process_csv()
#
# df['Date'] = pd.to_datetime(df['Date'])
# df = df[df['Date'].dt.year >= 2013]
# user_profile = df[(df['Name'] == 'Ty Evans #1') & (df['Event'] == 'SBD')]
#
# cols = ['Age', 'BodyweightKg', 'Best3SquatKg', 'Best3BenchKg', 'Best3DeadliftKg', 'Dots', 'TotalKg']
# user_profile = user_profile.dropna(subset=['TotalKg'])
# # Standardize the data
# X = StandardScaler().fit_transform(user_profile[cols])
#
# clean_df = clean_same_names(user_profile, 1)
#
# # Apply DBSCAN clustering
# dbscan = DBSCAN(eps=1.5, min_samples=2)
# user_profile['Cluster'] = dbscan.fit_predict(X)

# anomoly_check_df = user_profile.sort_values(by='Age')
# anomoly_check_df['age_diff'] = anomoly_check_df['Age'].diff()
# anomoly_check_df['date_diff'] = anomoly_check_df['Date'].dt.year.diff()
#
# age_progression_threshold = 1  # Adjust based on your dataset
#
# # Identify potential anomalies
# anomaly_mask = (anomoly_check_df['age_diff'] - anomoly_check_df['date_diff']).abs() > age_progression_threshold
# anomoly_val_df = anomoly_check_df[anomaly_mask]
#
# anomoly_check_df['check'] = 0  # Initialize with zeros
#
# # Initialize the group number
# group_number = 1
#
# group_mapping ={}
#
# # Loop through the anomalous DataFrame and assign group numbers
# for _, anomalous_record in anomoly_val_df.iterrows():
#     # Identify matching records in the original DataFrame
#     match_mask = (
#             (anomoly_check_df['Name'] == anomalous_record['Name']) &
#             (anomoly_check_df['Date'] == anomalous_record['Date'])
#     )
#
#     # Check if the group number is already assigned
#     if not anomoly_check_df.loc[match_mask, 'check'].any():
#         # If not, assign the current group number to the 'check' column for the matching record
#         anomoly_check_df.loc[match_mask, 'check'] = group_number
#
#         # Store the matching records in the group mapping
#         group_mapping[group_number] = anomoly_check_df.loc[match_mask].index.tolist()
#
#         # Increment the group number
#         group_number += 1
#
# # Fill down the group number for non-anomalous records
# non_anomalous_mask = anomoly_check_df['check'] == 0
# anomoly_check_df.loc[non_anomalous_mask, 'check'] = anomoly_check_df['check'].replace(0, method='ffill')


#user_profile = df[df['Name'] == 'Michael Peterson' & (df['Event'] == 'SBD')]
#user_profile.sort_values(by='MeetName', inplace=True)
# user_profile = user_profile.drop_duplicates(subset=['BodyweightKg', 'MeetName', 'Date'])
# grouped_user = user_profile.groupby(['BodyweightKg', 'MeetName', 'Date']).agg({'Best3SquatKg': 'sum', 'Best3BenchKg': 'sum', 'Best3DeadliftKg': 'sum'}).reset_index()

#
# closest_age_class = df_age_match.loc[
#     (df_age_match['Age'] - 17).abs().idxmin(),
#     'AgeClass'
# ]


# fed_df = df['Federation'].value_counts()
# fed_p = df['ParentFederation'].value_counts()
# equip = df['Equipment'].value_counts()
# non_tested = df[df['Tested'] != 'Yes']
# federations_with_nan_and_yes = df.groupby('Federation')['Tested'].apply(lambda x: x.isna().any() and 'Yes' in x.values)

# fed_df_raw = df[df['Federation'] == 'RAW']
# print(fed_df_raw['WeightClassKg'].value_counts())
# df_new = df
# df_new['Tested'] = df_new['Tested'].apply(lambda x: 'Not Known' if x != 'Yes' else x)
# df['Date'] = pd.to_datetime(df['Date'])
# df = df[df['Date'].dt.year >= 2013]
# # df_weight_match = df[(df['Federation'] == 'IPF') & (df['Sex'] == 'M') & (df['Date'].dt.year >= 2013)]
# #
# # closest_lower_weight_class = df_weight_match.loc[
# #     (df_weight_match['BodyweightKg'] - 72).abs().idxmin(),
# #     'WeightClassKg'
# # ]
# df_grouped = df.groupby('Name').agg(squat = ('Best3SquatKg', 'max'),
#                                                  bench = ('Best3BenchKg', 'max'),
#                                                  deadlift = ('Best3DeadliftKg', 'max'),
#                                                  wilks = ('Wilks', 'max')
#                                                  ).reset_index()

#print(df_grouped)
# df = retrieve_and_process_csv()
# df_country_cnt =df['Country'].value_counts()
# df_county_na = df[df['Country'].isna()]
# len(df)
#
# remove_special_chars(df)
# df = convert_kg_to_lbs(df)
# df = apply_business_rules(df)
#
# print(df['Sex'].unique())
# chk_records = df[df['Sex'] == 'Mx']

# filtered_df_after2k = df[df['Date'].dt.year >= 2017]

#
#
#
# filtered_df_age = df[~(df['Age'].isna() & df['AgeClass'].isna() & df['BirthYearClass'].isna())]
# filtered_df_age = filtered_df_age[filtered_df_age['Age'] >= 13]
#
# print(df['AgeClass'].unique())
#
# df['Date'] = pd.to_datetime(df['Date'])
# filtered_df_after2k = df[df['Date'].dt.year >= 2010]
# print(filtered_df_after2k['AgeClass'].unique())
# len(filtered_df_after2k)
# len(df)
# df = retrieve_and_process_csv()
# remove_special_chars(df)
# df = convert_kg_to_lbs(df)
#print(df['WeightClassKg'].unique())
# nan_records = filtered_df_age[filtered_df_age['AgeClass'].isna()]
# us_records = df[df['MeetCountry'] == 'USA']
# filtered_records = df[(df['AgeClass'].isna()) & (~df['BirthYearClass'].isna())]
# print(len(nan_records)/len(df))

#def remove_nan(df):
