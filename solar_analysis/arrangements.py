
import numpy as np
from .solar_calculations import calculate_ghi_for_tilt, find_optimal_tilt

EARTH_AXIAL_TILT = 23.45
WINTER_MONTHS = [10, 11, 12, 1, 2, 3]
SUMMER_MONTHS = [4, 5, 6, 7, 8, 9]


def analyze_arrangement_1(data, latitude_degrees: float, latitude_radians: float, sky_condition: str) -> float:
    """Arrangement 1: Fixed 0 degrees all year."""
    return calculate_ghi_for_tilt(data, 0, list(range(1, 13)), sky_condition, latitude_radians)

def analyze_arrangement_2(data, latitude_degrees: float, latitude_radians: float, sky_condition: str) -> float:
    """Arrangement 2: Fixed at the user-provided latitude all year."""
    return calculate_ghi_for_tilt(data, latitude_degrees, list(range(1, 13)), sky_condition, latitude_radians)

def analyze_arrangement_3(data, latitude_degrees: float, latitude_radians: float, sky_condition: str) -> float:
    """Arrangement 3: Two fixed tilts based on latitude +/- half of Earth's axial tilt."""
    adjustment = EARTH_AXIAL_TILT / 2
    summer_tilt = latitude_degrees - adjustment
    winter_tilt = latitude_degrees + adjustment
    ghi_summer = calculate_ghi_for_tilt(data, summer_tilt, SUMMER_MONTHS, sky_condition, latitude_radians)
    ghi_winter = calculate_ghi_for_tilt(data, winter_tilt, WINTER_MONTHS, sky_condition, latitude_radians)
    return ghi_summer + ghi_winter

def analyze_arrangement_4(data, latitude_degrees: float, latitude_radians: float, sky_condition: str) -> float:
    """Arrangement 4: Monthly optimal tilts."""
    return sum(find_optimal_tilt(data, [m], sky_condition, latitude_radians)[1] for m in range(1, 13))

def analyze_arrangement_5(data, latitude_degrees: float, latitude_radians: float, sky_condition: str) -> float:
    """Arrangement 5: Optimized tilt for summer and winter periods."""
    _, ghi_summer = find_optimal_tilt(data, SUMMER_MONTHS, sky_condition, latitude_radians)
    _, ghi_winter = find_optimal_tilt(data, WINTER_MONTHS, sky_condition, latitude_radians)
    return ghi_summer + ghi_winter

def analyze_arrangement_6(data, latitude_degrees: float, latitude_radians: float, sky_condition: str) -> float:
    """Arrangement 6: Single optimal tilt for the entire year."""
    return find_optimal_tilt(data, list(range(1, 13)), sky_condition, latitude_radians)[1]

