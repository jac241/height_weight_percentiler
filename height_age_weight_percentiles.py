import os
import pandas as pd
import csv
import numpy as np
import scipy.stats as stats


POUNDS_TO_KG = 2.20462262185
INCHES_TO_CM = 2.54


def get_cdc_dataframe(path, sheet_name):
    return pd.ExcelFile(path).parse(sheet_name)


def get_nsqip_dataframe(path):
    nsqip_xl = pd.ExcelFile(nsqip)
    nsqip_df = nsqip_xl.parse('Sheet1')
    return nsqip_df


def age_in_days_to_months(age_in_days):
    return age_in_days / (365.25/12)


def add_string_male_female(df):
    df['Sex_str'] = df.Sex.apply(lambda s: 'Male' if s == 1 else 'Female')


def variables_for_age_in_months_and_sex(cdc_df, age_in_mos, sex):
    if age_in_mos == 0:
        return cdc_df.iloc[0]
    else:
        age_less_than = cdc_df[(np.floor(cdc_df.Agemos) <= np.floor(age_in_mos)) & (cdc_df.Sex_str == sex)]
        return age_less_than.iloc[-1]


def zscore_for_age_in_months_and_sex(cdc_df, measurement, age_in_mos, sex):
    v = variables_for_age_in_months_and_sex(cdc_df, age_in_mos, sex)
    return zscore_for_measurement(measurement, v['L'], v['M'], v['S'])


def zscore_for_measurement(measurement, L, M, S):
    return ((measurement/M)**(L) - 1) / (L*S)
    

def percentile_for_zscore(zscore):
    return stats.norm.cdf(zscore)


def calculate_zscore_for_weight(nsqip_df, cdc_df):
    def zscore_per_row(row):
        if row['WEIGHT'] < 0:
            return np.nan
        else:
            return zscore_for_age_in_months_and_sex(
                cdc_df,
                row['WEIGHT'] / POUNDS_TO_KG,
                age_in_days_to_months(row['AGE_DAYS']),
                row['SEX']
            )

    return nsqip_df.apply(zscore_per_row, axis=1)


def calculate_zscore_for_height(nsqip_df, cdc_df):
    def zscore_per_row(row):
        if row['HEIGHT'] < 0:
            return np.nan
        else:
            return zscore_for_age_in_months_and_sex(
                cdc_df,
                row['HEIGHT'] * INCHES_TO_CM,
                age_in_days_to_months(row['AGE_DAYS']),
                row['SEX']
            )

    return nsqip_df.apply(zscore_per_row, axis=1)


nsqip = '~/research/PNSQIP_CPT_abbreviated.xlsx'
wtage = os.path.expanduser('./wtagecombined.xlsx')
lnage = os.path.expanduser('./lengthstaturecombinedat24_5months.xlsx')

nsqip_xl = pd.ExcelFile(nsqip)
nsqip_df = nsqip_xl.parse('Sheet1')

wtage_df = get_cdc_dataframe(wtage, 'Sheet1')
lnage_df = get_cdc_dataframe(lnage, 'Sheet1')
add_string_male_female(wtage_df)
add_string_male_female(lnage_df)

print("Calculating Weight Percentiles...")
nsqip_df['wt_zscore'] = calculate_zscore_for_weight(nsqip_df, wtage_df)

print("Calculating Height Percentiles...")
nsqip_df['ht_zscore'] = calculate_zscore_for_height(nsqip_df, lnage_df)
