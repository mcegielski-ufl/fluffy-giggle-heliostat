# solar_analysis/visualizations.py
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import io
import base64

def generate_chart_base64(fig):
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def plot_arrangement_comparison(results_df: pd.DataFrame, year: int):
    fig, ax = plt.subplots(figsize=(14, 8))
    results_df.plot(kind='bar', ax=ax, width=0.8)
    ax.set_title(f'Annual GHI Output Comparison for All Arrangements ({year})', fontsize=16)
    ax.set_ylabel('Total GHI (Wh/m²)', fontsize=12)
    ax.set_xlabel('Tilt Arrangement', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    return generate_chart_base64(fig)

def plot_monthly_comparison(monthly_ghi_df: pd.DataFrame, arr1_name: str, arr2_name: str, sky_condition: str, year: int):
    fig, ax = plt.subplots(figsize=(12, 7))
    monthly_ghi_df[[arr1_name, arr2_name]].plot(kind='bar', ax=ax, width=0.8)
    ax.set_title(f'Monthly GHI: {arr1_name} vs. {arr2_name} ({year}, {sky_condition.capitalize()} Sky)', fontsize=16)
    ax.set_ylabel('GHI Output (Wh/m²)', fontsize=12)
    ax.set_xlabel('Month', fontsize=12)
    plt.xticks(rotation=0)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.legend(title='Arrangement')
    return generate_chart_base64(fig)

def plot_optimal_tilts(monthly_optimal_df: pd.DataFrame, sky_condition: str, year: int):
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(monthly_optimal_df.index, monthly_optimal_df['Optimal Tilt'], marker='o', linestyle='-', color='teal')
    ax.set_title(f'Optimal Solar Panel Tilt Angle by Month ({year}, {sky_condition.capitalize()} Sky)', fontsize=16)
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('Optimal Tilt Angle (Degrees)', fontsize=12)
    ax.set_xticks(range(1, 13))
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    return generate_chart_base64(fig)

def plot_performance_improvement(results_df: pd.DataFrame, sky_condition: str):
    sky_col = f'{sky_condition.capitalize()} Sky GHI'
    base_ghi = results_df.loc['Arr. 1: 0° Fixed', sky_col]
    improvements = results_df[sky_col].apply(lambda x: (x - base_ghi) / base_ghi * 100)
    improvements = improvements[improvements > 0].drop('Arr. 1: 0° Fixed', errors='ignore')

    fig, ax = plt.subplots(figsize=(10, 10))
    if not improvements.empty:
        ax.pie(improvements, labels=improvements.index, autopct='%1.1f%%', startangle=90, wedgeprops=dict(width=0.4))
        ax.set_title(f'Performance Improvement Over 0° Fixed Tilt ({sky_condition.capitalize()} Sky)', fontsize=16)
    else:
        ax.text(0.5, 0.5, 'No improvement to display', horizontalalignment='center', verticalalignment='center')
        ax.set_title('Performance Improvement', fontsize=16)

    ax.axis('equal')
    return generate_chart_base64(fig)

