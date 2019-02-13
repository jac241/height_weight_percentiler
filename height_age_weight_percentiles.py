import os
import pandas as pd
import csv
import numpy as np
import scipy.stats as stats

nsqip = '~/research/PNSQIP_CPT_abbreviated.xlsx'
wtage = os.path.expanduser('./wtagecombined.xlsx')
lnage = os.path.expanduser('./lengthstaturecombinedat24_5months.xlsx')


POUNDS_TO_KG = 2.20462262185
INCHES_TO_CM = 2.54


def main():
    nsqip_xl = pd.ExcelFile(nsqip)
    nsqip_df = nsqip_xl.parse('Sheet1')

    wtage_df = get_cdc_dataframe(wtage, 'Sheet1')
    lnage_df = get_cdc_dataframe(lnage, 'Sheet1')
    add_string_male_female(wtage_df)
    add_string_male_female(lnage_df)

    print("Calculating Weight Percentiles...")
    nsqip_df['wtpercentile'] = calculate_percentiles_for_weight(nsqip_df, wtage_df)

    print("Calculating Height Percentiles...")
    nsqip_df['htpercentile'] = calculate_percentiles_for_height(nsqip_df, lnage_df)

    return nsqip_df
    

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


def variable_for_age_in_months_and_sex(cdc_df, variable, age_in_mos, sex):
    if age_in_mos == 0:
        return cdc_df[variable][0]
    else:
        age_less_than = cdc_df[(np.floor(cdc_df.Agemos) <= np.floor(age_in_mos)) & (cdc_df.Sex_str == sex)]
        return age_less_than[variable].iloc[-1]


def zscore_for_age_in_months_and_sex(cdc_df, measurement, age_in_mos, sex):
    L = variable_for_age_in_months_and_sex(cdc_df, 'L', age_in_mos, sex)
    M = variable_for_age_in_months_and_sex(cdc_df, 'M', age_in_mos, sex)
    S = variable_for_age_in_months_and_sex(cdc_df, 'S', age_in_mos, sex)
    return zscore_for_measurement(measurement, L, M, S)


def zscore_for_measurement(measurement, L, M, S):
    return ((measurement/M)**(L) - 1) / (L*S)
    

def percentile_for_zscore(zscore):
    return stats.norm.cdf(zscore)


def calculate_percentiles_for_weight(nsqip_df, cdc_df):
    def percentile_per_row(row):
        if row['WEIGHT'] < 0:
            return row['WEIGHT']
        else:
            return percentile_for_zscore(
                zscore_for_age_in_months_and_sex(
                    cdc_df,
                    row['WEIGHT'] / POUNDS_TO_KG,
                    age_in_days_to_months(row['AGE_DAYS']),
                    row['SEX']
                )
            )

    return nsqip_df.apply(percentile_per_row, axis=1)


def calculate_percentiles_for_height(nsqip_df, cdc_df):
    def percentile_per_row(row):
        if row['HEIGHT'] < 0:
            return row['HEIGHT']
        else:
            return percentile_for_zscore(
                zscore_for_age_in_months_and_sex(
                    cdc_df,
                    row['HEIGHT'] * INCHES_TO_CM,
                    age_in_days_to_months(row['AGE_DAYS']),
                    row['SEX']
                )
            )

    return nsqip_df.apply(percentile_per_row, axis=1)


if __name__ == '__main__':
    nsqip_df = main()
