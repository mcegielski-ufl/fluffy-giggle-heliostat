import pandas as pd
import numpy as np

def load_and_prepare_data(data_df: pd.DataFrame):
    try:
        df = data_df.copy()
        
        numeric_cols = ['DHI', 'DNI', 'Clearsky DHI', 'Clearsky DNI', 'Declination Angle', 'Month']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df.dropna(subset=numeric_cols, inplace=True)
        
        df['Declination Angle Rad'] = np.radians(df['Declination Angle'])
        
        return df
    except Exception as e:
        print(f"An error occurred while preparing the data: {e}")
        return None

