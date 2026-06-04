from pathlib import Path

if __name__ == "__main__":
    raise SystemExit("This module cannot be executed directly. Run python main.py instead.")

import pandas as pd

from Modules import module_1, module_2, module_3, module_4, module_plot


def run(industry_number, industry_code, industry_name, year, base_path, country_code, weights_mode):
    country_code = str(country_code).upper()
    base_path = Path(base_path)


    """Module 1: build base daily profiles by day type. """

    weekday_profiles, saturday_profiles, sunday_profiles, holiday_profiles, constant_profiles, data_industry_type = (
        module_1.build_electric_daily_profiles(
            industry_number,
            industry_code,
            year,
            country_code,
            str(base_path),
            weights_mode=weights_mode,
        )
    )


    """ Module 2: apply peak/base factors to the daily profiles. """

    weekday_adjusted, saturday_adjusted, sunday_adjusted, holiday_adjusted, constant_adjusted = (
        module_2.apply_peak_base_factors(
            year,
            industry_number,
            data_industry_type,
            weekday_profiles,
            saturday_profiles,
            sunday_profiles,
            holiday_profiles,
            constant_profiles,
        )
    )


    """ Module 3: expand daily profiles to the full year and normalize to 1000 MWh. """

    year_list, array_load_type = module_3.build_load_type_calendar(year)
    seasonal_profile = module_3.seasonality(
        year,
        year_list,
        array_load_type,
        weekday_adjusted,
        saturday_adjusted,
        sunday_adjusted,
        holiday_adjusted,
        constant_adjusted,
        str(base_path),
    )
    normalized_profile = module_3.normalising_1000(seasonal_profile)


    """ Module 4: scale to annual consumption and add electrical fluctuations. """

    scaled_profile = module_4.upscale_yearly(
        year,
        normalized_profile,
        data_industry_type,
    )
    final_profile = module_4.add_fluctuations(
        industry_number,
        scaled_profile,
        data_industry_type,
    )


    """ Plot and save the profile """

    # Save the annual diagram
    diagrams_dir = base_path / "Generated" / "diagrams"
    diagrams_dir.mkdir(parents=True, exist_ok=True)

    if weights_mode == "unsummed":
        module_plot.year_electrical_unsummed(
            final_profile,
            industry_name,
            industry_code,
            country_code,
            year,
            base_path,
        )
    elif weights_mode == "sfu":
        module_plot.year_electrical_sfu(
            final_profile,
            industry_name,
            industry_code,
            country_code,
            year,
            base_path,
        )
    else:
        module_plot.year_electrical_summed(
            final_profile,
            industry_name,
            industry_code,
            country_code,
            year,
            base_path,
        )

    # Save the annual profile
    load_profiles_dir = base_path / "Generated" / "load_profiles"
    load_profiles_dir.mkdir(parents=True, exist_ok=True)

    # Reorder to have 'Total' at last place
    application_columns = [column for column in final_profile.columns if column != "Total"]
    ordered_columns = application_columns + ["Total"]
    # Generate two-level headers (application name + unit)
    output_columns = pd.MultiIndex.from_arrays(
        [ordered_columns, ["in kW"] * len(ordered_columns)],
        names=("Application", "Unit"),
    )

    output_profile = final_profile[ordered_columns].copy()
    output_profile.columns = output_columns
    output_profile.index.name = "Time"

    output_file = load_profiles_dir / f"iDesign_RES_{industry_name}_{industry_code}-{country_code}.xlsx"
    output_profile.to_excel(output_file, index=True)
    return output_profile
