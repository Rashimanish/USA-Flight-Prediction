import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import StandardScaler
import datetime

def feature_engineering_classification(df):
    df['FL_DATE'] = pd.to_datetime(df['FL_DATE'])
    df['CRS_DEP_TIME'] = pd.to_numeric(df['CRS_DEP_TIME'], errors='coerce')
    df['CRS_ARR_TIME'] = pd.to_numeric(df['CRS_ARR_TIME'], errors='coerce')

    #  new features
    df['DAY_OF_WEEK'] = df['FL_DATE'].dt.dayofweek
    df['MONTH'] = df['FL_DATE'].dt.month
    df['HOUR_DEP'] = df['CRS_DEP_TIME'] // 100
    df['MIN_DEP'] = df['CRS_DEP_TIME'] % 100
    df['HOUR_ARR'] = df['CRS_ARR_TIME'] // 100
    df['MIN_ARR'] = df['CRS_ARR_TIME'] % 100
    df['DISTANCE_BIN'] = pd.cut(df['DISTANCE'], bins=[0, 500, 1000, 1500, 2000, 3000], labels=[1, 2, 3, 4, 5])

    # interaction features
    df['DISTANCE_DAY_INTERACTION'] = df['DISTANCE'] * df['DAY_OF_WEEK']
    df['HOUR_DEP_ARR_INTERACTION'] = df['HOUR_DEP'] * df['HOUR_ARR']
    df['MONTH_DAY_INTERACTION'] = df['MONTH'] * df['DAY_OF_WEEK']

    # Drop columns 
    cols_to_drop = ['FL_DATE', 'CRS_DEP_TIME', 'CRS_ARR_TIME']
    df = df.drop(columns=cols_to_drop, errors='ignore')

     # Convert categorical features to numeric using label encoding
    label_encoder = LabelEncoder()
    categorical_columns = ['ORIGIN', 'DEST', 'ORIGIN_CARRIER','DISTANCE_BIN']
    for col in categorical_columns:
        df[col] = label_encoder.fit_transform(df[col])
    return df

def feature_engineering_mcl(df):
    df['CRS_DEP_TIME'] = pd.to_numeric(df['CRS_DEP_TIME'], errors='coerce')
    df['FL_DATE'] = pd.to_datetime(df['FL_DATE'])


    df['DAY_OF_WEEK'] = df['FL_DATE'].dt.dayofweek
    df['MONTH'] = df['FL_DATE'].dt.month
    df['HOUR_DEP'] = df['CRS_DEP_TIME'] // 100
    df['MIN_DEP'] = df['CRS_DEP_TIME'] % 100
    df['DISTANCE_BIN'] = pd.cut(df['DISTANCE'], bins=[0, 500, 1000, 1500, 2000, 3000], labels=[1, 2, 3, 4, 5])

    #  interaction features
    df['DISTANCE_DAY_INTERACTION'] = df['DISTANCE'] * df['DAY_OF_WEEK']
    df['MONTH_DAY_INTERACTION'] = df['MONTH'] * df['DAY_OF_WEEK']

    # Drop columns no longer needed
    cols_to_drop = ['FL_DATE', 'CRS_DEP_TIME']
    df = df.drop(columns=cols_to_drop, errors='ignore')

     # Convert categorical features to numeric using label encoding
    label_encoder = LabelEncoder()
    categorical_columns = ['ORIGIN', 'DEST', 'ORIGIN_CARRIER','DISTANCE_BIN']
    for col in categorical_columns:
        df[col] = label_encoder.fit_transform(df[col])

    return df



