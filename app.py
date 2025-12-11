import requests
import zipfile
import io
import pandas as pd
import numpy as np
from datetime import datetime
import json
import os
import time
from flask import Flask, request, jsonify, render_template

from solar_analysis.data_loader import load_and_prepare_data
from solar_analysis.arrangements import (
    analyze_arrangement_1, analyze_arrangement_2, analyze_arrangement_3,
    analyze_arrangement_4, analyze_arrangement_5, analyze_arrangement_6
)
from solar_analysis.solar_calculations import calculate_ghi_for_tilt, calculate_monthly_optimal_data
from solar_analysis.visualizations import (
    plot_arrangement_comparison, plot_monthly_comparison,
    plot_optimal_tilts, plot_performance_improvement
)

app = Flask(__name__)

BASE_URL = "https://developer.nrel.gov/api/nsrdb/v2/solar/nsrdb-GOES-full-disc-v4-0-0-download.json?"


def handle_api_errors(response: requests.Response) -> dict:
    try:
        response_json = response.json()
    except json.JSONDecodeError:
        raise ValueError(f"Server Error: Invalid response from NREL API. Status: {response.status_code}")
    if response.status_code != 200 or len(response_json.get('errors', [])) > 0:
        errors = '\n'.join(response_json.get('errors', [f'Unknown API Error: {response.status_code} {response.reason}']))
        raise ConnectionError(f"NREL API Error: {errors}")
    return response_json

def request_nrel_data_url(year, lat, lon, email, api_key):
    wkt_point = f'POINT({lon} {lat})'
    input_data = {
        'attributes': 'clearsky_dni,clearsky_dhi,clearsky_ghi,dhi,dni,ghi', 'interval': '60',
        'utc': 'false', 'email': email, 'full_name': 'Helio WebApp User',
        'affiliation': 'UF Dept. of Construction and Planning', 'reason': 'Research',
        'names': [year], 'wkt': wkt_point,
    }
    request_url = f"{BASE_URL}api_key={api_key}"
    response = requests.post(request_url, data=input_data)
    data = handle_api_errors(response)
    if 'outputs' in data and 'downloadUrl' in data['outputs']:
        return data['outputs']['downloadUrl']
    raise ValueError("Could not find download URL in NREL API response.")

def get_dataframe_from_zip_url(zip_url):
    print("Waiting for 20 seconds for NREL to prepare the data file...")
    time.sleep(20)
    print("Attempting to download the data file...")
    
    response = requests.get(zip_url, timeout=120)
    response.raise_for_status()
    print("Download successful.")
    
    with zipfile.ZipFile(io.BytesIO(response.content)) as thezip:
        csv_filename = next((name for name in thezip.namelist() if name.endswith('.csv')), None)
        if not csv_filename:
            raise FileNotFoundError("No CSV file found in the zip archive from NREL.")
        with thezip.open(csv_filename) as thefile:
            return pd.read_csv(thefile, skiprows=2)

def add_declination_to_dataframe(df):
    def calculate_declination_angle(date):
        day_of_year = date.timetuple().tm_yday
        return -23.45 * np.cos(np.radians(360/365 * (day_of_year + 10)))
    df['datetime'] = pd.to_datetime(df[['Year', 'Month', 'Day', 'Hour', 'Minute']])
    df['Declination Angle'] = df['datetime'].apply(calculate_declination_angle)
    df = df.drop(columns=['datetime'])
    return df


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/process-data', methods=['POST'])
def process_data_endpoint():
    try:
        form_data = request.form
        lat, lon, year, email, api_key = (
            float(form_data['latitude']), float(form_data['longitude']),
            int(form_data['year']), form_data['email'], form_data['api_key']
        )
        sky_condition = form_data.get('sky_condition', 'cloudy')
        generate_charts = form_data.get('generate_charts')
        lat_rad = np.radians(lat)

        download_url = request_nrel_data_url(year, lat, lon, email, api_key)
        solar_df = get_dataframe_from_zip_url(download_url)
        final_df = add_declination_to_dataframe(solar_df)
        
        prepared_data = load_and_prepare_data(final_df)
        if prepared_data is None:
            raise ValueError("Failed to prepare the data for analysis.")

        analysis_args = (prepared_data, lat, lat_rad)
        cloudy_results = {
            "Arr. 1: 0° Fixed": analyze_arrangement_1(*analysis_args, sky_condition='cloudy'),
            f"Arr. 2: {lat:.1f}° Fixed (Lat)": analyze_arrangement_2(*analysis_args, sky_condition='cloudy'),
            "Arr. 3: Two Fixed (Lat±11.7°)": analyze_arrangement_3(*analysis_args, sky_condition='cloudy'),
            "Arr. 4: Monthly Optimal": analyze_arrangement_4(*analysis_args, sky_condition='cloudy'),
            "Arr. 5: Summer/Winter Optimal": analyze_arrangement_5(*analysis_args, sky_condition='cloudy'),
            "Arr. 6: Annual Optimal": analyze_arrangement_6(*analysis_args, sky_condition='cloudy'),
        }
        clear_results = {
            "Arr. 1: 0° Fixed": analyze_arrangement_1(*analysis_args, sky_condition='clear'),
            f"Arr. 2: {lat:.1f}° Fixed (Lat)": analyze_arrangement_2(*analysis_args, sky_condition='clear'),
            "Arr. 3: Two Fixed (Lat±11.7°)": analyze_arrangement_3(*analysis_args, sky_condition='clear'),
            "Arr. 4: Monthly Optimal": analyze_arrangement_4(*analysis_args, sky_condition='clear'),
            "Arr. 5: Summer/Winter Optimal": analyze_arrangement_5(*analysis_args, sky_condition='clear'),
            "Arr. 6: Annual Optimal": analyze_arrangement_6(*analysis_args, sky_condition='clear'),
        }
        
        results_df = pd.DataFrame({'Cloudy Sky GHI': cloudy_results, 'Clear Sky GHI': clear_results})
        results_table_html = results_df.map('{:,.0f}'.format).to_html(classes='w-full text-sm text-left text-gray-500', border=0)

        chart_data = {}
        if generate_charts:
            chart_data['comparison'] = plot_arrangement_comparison(results_df, year)
            
            monthly_ghi_arr1 = [calculate_ghi_for_tilt(prepared_data, 0, [m], sky_condition, lat_rad) for m in range(1, 13)]
            monthly_ghi_arr2 = [calculate_ghi_for_tilt(prepared_data, lat, [m], sky_condition, lat_rad) for m in range(1, 13)]
            arr2_name = f'Arr. 2: {lat:.1f}° Fixed'
            monthly_df = pd.DataFrame({'Arr. 1: 0° Fixed': monthly_ghi_arr1, arr2_name: monthly_ghi_arr2}, index=range(1, 13))
            chart_data['monthly'] = plot_monthly_comparison(monthly_df, 'Arr. 1: 0° Fixed', arr2_name, sky_condition, year)

            monthly_optimal_df = calculate_monthly_optimal_data(prepared_data, sky_condition, lat_rad)
            chart_data['tilts'] = plot_optimal_tilts(monthly_optimal_df, sky_condition, year)

            chart_data['pie'] = plot_performance_improvement(results_df, sky_condition)

        return jsonify({
            "message": "Successfully processed data and generated analysis.",
            "results_table": results_table_html,
            "chart_data": chart_data
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

