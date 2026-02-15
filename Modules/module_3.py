import pandas as pd
import datetime
import holidays
from pathlib import Path



def build_load_type_calendar(year):
    """
    Build a calendar of daily load pattern types for a full year.

    Included holidays and special days:
    - German statutory holidays.
    - Epiphany (Jan 6), Christmas Eve (Dec 24), New Year's Eve (Dec 31).
    - Bridge days (days before/after holidays that affect working patterns).

    Scope and rules:
    - Working days are Monday-Friday that are not holidays.
    - Non-working days are weekends and holidays.

    Output classification (load pattern types):
    1. Weekday load: working day with the standard weekday profile.
    2. Holiday load: non-working day between two working days.
    3. Saturday load: non-working day after a working day and before a non-working day.
    4. Sunday load: non-working day after a non-working day and before a working day.
    5. Constant load: non-working day surrounded by non-working days.

    Steps:
    1. Build the full date range for the year and collect all holidays.
    2. Classify each day as working (1) or non-working (2).
    3. Map each day to a load pattern type (1-5) using neighbor-day rules.
    """

    """ BUILD LIST OF HOLIDAYS FOR THE YEAR  """
    # Create date range for the entire year
    year_list = pd.date_range(str(year) + "-01-01", str(year) + "-12-31", freq="D")
    year_list = list(year_list)
    
    # Collect all holidays
    dates = []
    names = []
    
    # Add German statutory holidays
    for date, name in sorted(holidays.Germany(years=year).items()):
        dates.append(date)
        names.append(name)
    
    # Add additional relevant dates
    dates.append(datetime.date(year, 1, 6))    # Epiphany
    dates.append(datetime.date(year, 12, 24))  # Christmas Eve
    dates.append(datetime.date(year, 12, 31))  # New Year's Eve
    names.append("Epiphany")
    names.append("Christmas Eve")
    names.append("New Year's Eve")
    
    # Create DataFrame with holidays
    list_holidays = pd.DataFrame({"date": dates, "name": names}, index=None)
    
    # Add "bridge days" (days adjacent to holidays that impact working patterns)
    for i in list_holidays["date"]:
        if datetime.date.weekday(i) == 1:  # Holiday on Monday
            list_holidays.loc[len(list_holidays)] = {
                "date": (i + datetime.timedelta(days=-1)),
                "name": "Bridge day",
            }
        elif datetime.date.weekday(i) == 3:  # Holiday on Wednesday
            list_holidays.loc[len(list_holidays)] = {
                "date": (i + datetime.timedelta(days=1)),
                "name": "Bridge day",
            }


    """ CLASSIFY DAYS INTO WORKING AND NON-WORKING DAYS """
    array_wd_we = []
    for i in year_list:
        # Weekday that is not a holiday
        if datetime.datetime.weekday(i) in [0, 1, 2, 3, 4] and i not in dates:
            array_wd_we.append(1)
        # Weekend or holiday
        else:
            array_wd_we.append(2)


    """ CLASSIFY DAYS INTO LOAD PATTERN TYPES (1-5) """
    array_load_type = []
    for i in range(len(array_wd_we)):
        if array_wd_we[i] == 1:
            # Working day
            array_load_type.append(1)
        
        elif array_wd_we[i] == 2 and i != 0 and i != len(array_wd_we) - 1:
            # Non-working day (not first or last day of year)
            if array_wd_we[i - 1] == 1:  # Day before is working
                if array_wd_we[i + 1] == 1:
                    # Day after is working → Holiday load pattern
                    array_load_type.append(2)
                elif array_wd_we[i + 1] == 2:
                    # Day after is non-working → Saturday load pattern
                    array_load_type.append(3)
            
            elif array_wd_we[i - 1] == 2:  # Day before is non-working
                if array_wd_we[i + 1] == 1:
                    # Day after is working → Sunday load pattern
                    array_load_type.append(4)
                elif array_wd_we[i + 1] == 2:
                    # Day after is non-working → Constant load pattern
                    array_load_type.append(5)
        
        elif i == 0:
            # First day of year
            if array_wd_we[i + 1] == 1:
                array_load_type.append(4)  # Sunday load
            elif array_wd_we[i + 1] == 2:
                array_load_type.append(5)  # Constant load
        
        elif i == len(array_wd_we) - 1:
            # Last day of year
            if array_wd_we[i - 1] == 1:
                array_load_type.append(3)  # Saturday load
            elif array_wd_we[i - 1] == 2:
                array_load_type.append(5)  # Constant load
    
    return year_list, array_load_type



def seasonality(year, year_list, array_load_type, 
                weekday_adjusted, saturday_adjusted, sunday_adjusted, holiday_adjusted, constant_adjusted, 
                path):
    """
    This function applies seasonal adjustment to space heating based on heating degree days (HDD).
    
    Heating degree days account for temperature variations throughout the year:
    - High HDD in winter → high heating demand
    - Low HDD in summer → low heating demand
    """
    # Read heating degree day factors by month
    base_path = Path(path)
    month_factor = pd.read_excel(base_path / "HeatingDegreeDays.xlsx", sheet_name="HDD")
    month_factor = month_factor.iloc[0][1:13]  # Extract 12 monthly factors
    
    # Dictionary mapping load pattern types to their respective load profiles
    profiles = []
    dict_load_type = {
        1: weekday_adjusted,
        2: holiday_adjusted,
        3: saturday_adjusted,
        4: sunday_adjusted,
        5: constant_adjusted,
    }
    
    # Apply seasonal adjustment for each day
    for i in range(len(year_list)):
        dayprofile = dict_load_type[array_load_type[i]].copy()
        # Multiply space heating by monthly HDD factor
        dayprofile["Space heating"] = dayprofile["Space heating"] * month_factor.iloc[year_list[i].month - 1]
        profiles.append(dayprofile)

    df = pd.concat(profiles, ignore_index=True)
    
    # Create continuous datetime index with 15-minute intervals
    idx = pd.date_range(datetime.datetime(year, 1, 1, 0, 0),
                        datetime.datetime(year, 12, 31, 23, 45),
                        freq="15min")
    df.index = idx
    
    return df



def normalising_1000(df):
    """
    Scales the load profile to a standard annual consumption of 1000 MWh.
    """
    # Calculate actual annual energy consumption in MWh
    energy_per_year = float(df["Total"].sum() * 0.25 / 1000)  # 0.25 = 15 min intervals in hours

    # Scale all values to reach 1000 MWh/year
    df_normalized = df / (energy_per_year / 1000)

    return df_normalized
