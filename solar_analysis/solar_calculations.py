import numpy as np
import pandas as pd

def calculate_ghi_for_tilt(data, tilt_degrees: float, months: list, sky_condition: str, latitude_radians: float) -> float:
    if data is None:
        return 0.0

    dhi_col, dni_col = ('DHI', 'DNI') if sky_condition == 'cloudy' else ('Clearsky DHI', 'Clearsky DNI')
    df_period = data[data['Month'].isin(months)].copy()
    df_period = df_period[~((df_period[dhi_col] == 0) & (df_period[dni_col] == 0))]

    if df_period.empty:
        return 0.0

    panel_tilt_rad = np.radians(tilt_degrees)
    declination_rad = df_period['Declination Angle Rad'].values
    dhi, dni = df_period[dhi_col].values, df_period[dni_col].values
    cos_theta = np.cos(latitude_radians - panel_tilt_rad - declination_rad)
    dni_contribution = np.where(cos_theta > 0, cos_theta * dni, 0)
    return np.sum(dhi + dni_contribution)

def find_optimal_tilt(data, months: list, sky_condition: str, latitude_radians: float) -> tuple:
    max_ghi, best_tilt = -1, -1
    for tilt in range(0, 91):
        ghi = calculate_ghi_for_tilt(data, tilt, months, sky_condition, latitude_radians)
        if ghi > max_ghi:
            max_ghi, best_tilt = ghi, tilt
    return best_tilt, max_ghi

def calculate_monthly_optimal_data(data, sky_condition: str, latitude_radians: float) -> pd.DataFrame:
    monthly_data = []
    for month in range(1, 13):
        tilt, ghi = find_optimal_tilt(data, [month], sky_condition, latitude_radians)
        monthly_data.append({'Month': month, 'Optimal Tilt': tilt, 'Max GHI': ghi})
    return pd.DataFrame(monthly_data).set_index('Month')
