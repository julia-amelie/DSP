import csv
import os
import random
import collections
from collections import defaultdict
import shutil
from datetime import date, datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pandas import ExcelWriter

fileDir = os.path.dirname(os.path.realpath('__file__'))
currentdate = date.today().strftime('%Y.%m.%d')
# currentdate = '2019.04.02'
# Import our other files
from recommendations import top_ten_random
# from analytics import run_all_analytics
print('joe')

from create_validation_clients import get_dataframe
print('joe')

from import_rules import vector_df, df_rules_overview
print('joe')

SYMBOLS = [' ', '/', '-', '&', ',', '\’','\‘', '\'', "'"]
global user_id_list
user_id_list = []

print('joe')
# df_rules_overview = df_rules_overview.astype(int)
# df_rules_overview.replace(1.0, value=1, inplace=True)
# df_rules_overview.replace(0.0, value=0, inplace=True)
# df_rules_overview.replace(1, value=True, inplace=True)
# df_rules_overview.replace(0, value=False, inplace=True)

feature_df = pd.read_csv("featurelist.csv")
all_features_list = feature_df['Name'].to_list()

df_x = pd.read_csv(f"{fileDir}/musea.csv", header=0)
museum_df = df_x[['translationSetId','publicName']]
museum_df = museum_df.drop_duplicates(subset=['publicName'])
museum_df = museum_df.sort_values('translationSetId')
museum_df = museum_df.reset_index(drop=True)
all_museums_list = museum_df['translationSetId'].to_list()

def move_files(filename):
    shutil.move("%s/%s" %(fileDir, filename), "%s/RESULTS/%s" %(fileDir, filename))

def create_file(filename, df):
    df.to_excel(filename, index=False)
    move_files(filename)

def clean_column(df, column):
    for symbol in SYMBOLS:
        df["%s" %column] = df["%s" %column].astype(str).str.replace(r'%s' % symbol,'')
    return df

''' STANDAARD '''
from ast import literal_eval
def create_excel_list():
    excel_client_list = []
    with open('excel_clients.txt', 'r') as f:
        for x in f:
            clients_for_excel = x.split(';')

    return clients_for_excel
def convert_museumid_to_name(vector):
    ''' HIER MUSEUM DF UIT HALEN EN ERGENS BOVEN GLOBAL ERIN FIXEN'''

    recomm_amount = 10
    ind = np.argpartition(vector, -10)[-10:]
    idx = (-vector).argsort()[:recomm_amount]
    idx = idx.tolist()

    museum_name_list = []
    museum_id_list = []
    for x in idx:
        ''' MOET DE MUSEUM DATAFRAMES NOG CHECKEN - SORTEN OP MUSEUM NAAM OF ID?? ZODAT INDEX ALTIJD HETZELFDE IS'''
        museum_id_list.append(museum_df.loc[x].at['translationSetId'])
        museum_name_list.append(museum_df.loc[x].at['publicName'])
    return museum_name_list, museum_id_list

def update_vectors(new, old, count):

    myarray = np.array(new.values[0])
    myarray *= count
    new_array = np.transpose(myarray)
    myarray = old*new_array
    return myarray

def prepare_excel_file(mydict):
    with ExcelWriter("validation_excel.xlsx") as writer:
        for k, v in mydict.items():
            v.to_excel(writer, sheet_name=k)

def create_excel_sheet(row):
    museum_list = row['museum_id'].values[0]
    features = row['features'].values[0]
    df = create_validation(museum_list, features)

    return df

def create_statistical(df, museum_list, features, feature_correct_dict, feature_wrong_dict):
    museum_total = len(museum_list)
    feature_total = len(features)

    threshold = 7
    if len(features) == 2:
        threshold = 5
    if len(features) > 2:
        threshold = 4
    correct_total = 0
    for feature in features:
        data = df.loc['feature total', feature]

        if feature == 'educative' or feature == 'art_galleries' or feature == 'science':
            threshold = 3
        if feature == 'military' or feature == 'churches' or feature == 'gardens' or feature == 'audiotour':
            threshold = 1

        if data >= threshold:
            feature_correct_dict[feature] += 1
            correct_total += 1
        else:
            feature_wrong_dict[feature] += 1

        # if len(features) == 1 and data >= 7:
            # feature_dict[feature]['correct'] += 1
            # feature_correct_dict[feature] += 1
            # correct_total += 1
        # elif len(features) == 1 and data < 7:
        #     # feature_dict[feature]['wrong'] += 1
        #     feature_wrong_dict[feature] += 1
        # elif len(features) > 1 and data >= 4:
        #     correct_total += 1
        #     # feature_dict[feature]['correct'] += 1
        # else:
        #     # feature_dict[feature]['wrong'] += 1
        #     feature_wrong_dict[feature] += 1

        # print(feature_dict)
    pass_fail = correct_total-feature_total
    return pass_fail

def create_validation(museum_list, features):
    new_df = df_rules_overview['translationSetId']
    new_df = new_df.to_frame()
    for feature in features:
        correct_column = df_rules_overview[f'{feature}']
        new_df[f'{feature}'] = correct_column
    total_df_list = []
    for museum in museum_list:
        row = new_df.loc[(new_df['translationSetId'] == museum)]
        df_temp = pd.DataFrame()
        df_temp['museumname'] = museum_df.loc[museum_df.translationSetId == museum]['publicName']
        row.insert(1, 'museumname', df_temp['museumname'])
        total_df_list.append(row)
    total_df = pd.concat(total_df_list)
    total_df.loc['feature total']= total_df.sum(numeric_only=True, axis=0)
    total_df.loc[:,'museum total'] = total_df.sum(numeric_only=True, axis=1)
    return total_df
def create_output_dataframes(correct_dict, incorrect_dict):
    print(correct_dict)
    combined_df = pd.DataFrame()
    for k, v in correct_dict.items():
        correct = v
        wrong = incorrect_dict.get(k)
        total = correct + wrong
        if total == 0:
            total += 1
        percentage = correct/total
        combined_df = combined_df.append({'feature': k, 'correct': correct, 'wrong':wrong , 'percentage': percentage}, ignore_index=True)

    combined_df.to_csv('results validation.csv')

def run_all_validation():
    client_vector_dict = {}
    client_features_dict = {}
    client_id_list = []
    museum_count_dict = {}
    input_df, clients_for_excel = get_dataframe()
    print(clients_for_excel)
    for index, row in input_df.iterrows():

        client = row['clientid']
        museum = row['translationSetId']

        ''' MOET NOG WAT DOEN MET DE COUNT VAN HIERONDER - VERWERKEN IN VECTOR MULTIPLICATION'''
        count = row['count']

        if client in client_id_list:
            vector = client_vector_dict.get(client)
        else:
            client_id_list.append(client)
            vector = np.ones(496, dtype=object)
            features = row['features']
            client_features_dict[client] = features

        museum_vector = vector_df[(vector_df['translationSetId'] == museum)].vector
        calculated_vector = update_vectors(museum_vector, vector, count)
        client_vector_dict[client] = calculated_vector

    df_vectors = pd.DataFrame()
    for k, v in client_vector_dict.items():
        museum_name_list, museum_id_list = convert_museumid_to_name(v)
        df_vectors = df_vectors.append({'clientid': k, 'museum_list': museum_name_list, 'museum_id': museum_id_list}, ignore_index=True)
    df_features = pd.DataFrame()
    for k, v in client_features_dict.items():
        df_features = df_features.append({'clientid': k, 'features': v}, ignore_index=True)

    df_total = df_vectors.merge(df_features, how='inner', on='clientid')

    print('\n\n\nFROM HERE--------------\n')

    # museum_validation_dict = dict.fromkeys(all_museums_list, {'correct': 0, 'wrong': 0})
    # feature_validation_dict = dict.fromkeys(all_features_list, {'correct': 0, 'wrong': 0})
    feature_correct_dict = dict.fromkeys(all_features_list, 0)
    feature_wrong_dict = dict.fromkeys(all_features_list, 0)

    correct_wrong_list = []
    for index, row in df_total.iterrows():
        museum_list = row['museum_id']
        features = row['features']
        result_df = create_validation(museum_list, features)
        correct_wrong_list.append(create_statistical(result_df, museum_list, features, feature_correct_dict, feature_wrong_dict))



    correct= correct_wrong_list.count(0)
    wrong= len(correct_wrong_list)-correct
    total = wrong + correct
    print(f'Total correct recommendations: {correct}')
    print(f'Total wrong recommendations: {wrong}')
    print(f'Percentage correct: {correct/total}')

    create_output_dataframes(feature_correct_dict, feature_wrong_dict)
    dataframe_dict = {}
    # clients_for_excel = get_clients()
    for client_x in clients_for_excel:
        row = df_total[(df_total['clientid'] == client_x)]
        temp_df = create_excel_sheet(row)
        dataframe_dict[client_x] = temp_df
        prepare_excel_file(dataframe_dict)

    df_total.to_csv('result_client_museums.csv')

def run_all_train():
    client_vector_dict = {}
    client_id_list = []
    '''HIER INPUT VAN ANALYTICS DATA IN GIEREN'''
    input_df = get_dataframe()
    print(input_df)

    for index, row in input_df.iterrows():
        client = row['clientid']
        museum = row['translationSetId']
        count = row['count']


        if client in client_id_list:
            vector = client_vector_dict.get(client)
        else:
            client_id_list.append(client)
            vector = np.ones(496, dtype=object)

        museum_vector = vector_df[(vector_df['translationSetId'] == museum)].vector
        calculated_vector = update_vectors(museum_vector, vector)
        client_vector_dict[client] = calculated_vector

    df = pd.DataFrame()
    for k, v in client_vector_dict.items():
        museum_name_list, museum_id_list = convert_museumid_to_name(v)
        df = df.append({'clientid': k, 'museum_list': museum_name_list, 'museum_id': museum_id_list}, ignore_index=True)
    df.to_csv('result_client_museums.csv')

# run_all_train()
run_all_validation()
