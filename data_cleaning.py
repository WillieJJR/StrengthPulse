import pandas as pd
from data_retrieval import retrieve_and_process_csv



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


    if all(col in df.columns for col in ['BirthYearClass', 'AgeClass', 'Age']):
        mask = df['AgeClass'].isna() & ~df['BirthYearClass'].isna()
        df.loc[mask, 'AgeClass'] = df.loc[mask, 'BirthYearClass']

        df = df[~(df['Age'].isna() & df['AgeClass'].isna() & df['BirthYearClass'].isna()) & (df['Age'] >= 13)]

        if df['AgeClass'].isna().any():
            raise ValueError('AgeClass contains NaN values')
    else:
        raise ValueError("One or more required columns are missing")

    return df


'''Scratch Pad'''
# df = retrieve_and_process_csv()
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
