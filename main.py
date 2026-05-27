import os
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("IDESIGN_SHOW_PLOTS", "0")

from Profiles import LoadGeneratorElectricity, LoadGeneratorThermal


PROJECT_ROOT = Path(__file__).resolve().parent


# ========================
#     RUN SETTINGS
# ========================
GENERATE_ELECTRICAL_PROFILE = True
GENERATE_THERMAL_PROFILE = True

COUNTRY_CODE = "DE"
YEAR = 2018
BASE_PATH = PROJECT_ROOT

ELECTRICAL_INDUSTRY_NUMBER = 1
ELECTRICAL_WEIGHTS_MODE = "sfu"  # Available values: "summed", "unsummed", "sfu" (standard final uses)

THERMAL_INDUSTRY_NUMBER = 1


COUNTRY_CODES = {
    "AT": "Austria",
    "BE": "Belgium",
    "BG": "Bulgaria",
    "CY": "Cyprus",
    "CZ": "Czech Republic",
    "DE": "Germany",
    "DK": "Denmark",
    "EE": "Estonia",
    "EL": "Greece",
    "ES": "Spain",
    "FI": "Finland",
    "FR": "France",
    "HR": "Croatia",
    "HU": "Hungary",
    "IE": "Ireland",
    "IT": "Italy",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "LV": "Latvia",
    "MT": "Malta",
    "NL": "Netherlands",
    "PL": "Poland",
    "PT": "Portugal",
    "RO": "Romania",
    "SE": "Sweden",
    "SI": "Slovenia",
    "SK": "Slovakia",
}

ELECTRICAL_INDUSTRIES = {
    1: {"code": "ISI", "name": "Iron and steel"},
    2: {"code": "NFM", "name": "Non-ferrous metals"},
    3: {"code": "CHI", "name": "Chemicals"},
    4: {"code": "NMM", "name": "Non-metallic minerals"},
    5: {"code": "PPA", "name": "Pulp, paper and printing"},
    6: {"code": "FBT", "name": "Food, beverages and tobacco"},
    7: {"code": "TRE", "name": "Transport equipment"},
    8: {"code": "MAE", "name": "Machinery equipment"},
    9: {"code": "TEL", "name": "Textiles and leather"},
    10: {"code": "WWP", "name": "Wood and wood products"},
    11: {"code": "OIS", "name": "Other industrial sectors"},
}

THERMAL_INDUSTRIES = {
    1: {"name": "Primary Steel", "column": "Primary Steel (TWh)"},
    2: {"name": "Secondary Steel", "column": "Secondary Steel (TWh)"},
    3: {"name": "Chemicals", "column": "Chemicals (TWh)"},
    4: {"name": "Cement", "column": "Cement (TWh)"},
    5: {"name": "Pulp and Paper", "column": "Pulp and Paper (TWh)"},
    6: {"name": "Food, Beverages and Tobacco", "column": "Food, Beverages and Tobacco (TWh)"},
    7: {"name": "Transport Equipment", "column": "Transport Equipment (TWh)"},
    8: {"name": "Machinery and Equipment", "column": "Machinery and Equipment (TWh)"},
    9: {"name": "Textiles and Leather", "column": "Textiles and Leather (TWh)"},
    10: {"name": "Wood and Wood Products", "column": "Wood and Wood Products (TWh)"},
    11: {"name": "Non-ferrous Metals", "column": "Non-ferrous Metals (TWh)"},
    12: {"name": "Ceramics and Glass", "column": "Ceramics and Glass (TWh)"},
}


def main():
    base_path = PROJECT_ROOT if BASE_PATH in ("", None) else Path(BASE_PATH).expanduser().resolve()
    country_code = COUNTRY_CODE.upper()


    """ Validate the editable settings: """

    if not GENERATE_ELECTRICAL_PROFILE and not GENERATE_THERMAL_PROFILE:
        raise ValueError("At least one profile type must be enabled.")

    if country_code not in COUNTRY_CODES:
        valid_codes = ", ".join(COUNTRY_CODES)
        raise ValueError(f"Invalid COUNTRY_CODE '{COUNTRY_CODE}'. Valid codes: {valid_codes}")

    if not isinstance(YEAR, int):
        raise TypeError("YEAR must be an integer.")

    if GENERATE_ELECTRICAL_PROFILE:
        if ELECTRICAL_INDUSTRY_NUMBER not in ELECTRICAL_INDUSTRIES:
            raise ValueError("Invalid ELECTRICAL_INDUSTRY_NUMBER.")
        if ELECTRICAL_WEIGHTS_MODE not in {"summed", "unsummed", "sfu"}:
            raise ValueError("ELECTRICAL_WEIGHTS_MODE must be 'summed', 'unsummed' or 'sfu'.")

    if GENERATE_THERMAL_PROFILE and THERMAL_INDUSTRY_NUMBER not in THERMAL_INDUSTRIES:
        raise ValueError("Invalid THERMAL_INDUSTRY_NUMBER.")

    electrical_industry = ELECTRICAL_INDUSTRIES.get(ELECTRICAL_INDUSTRY_NUMBER)
    thermal_industry = THERMAL_INDUSTRIES.get(THERMAL_INDUSTRY_NUMBER)


    """ Print the selected configuration """

    print("\nConfiguration")
    print(f"  Country: {country_code} - {COUNTRY_CODES[country_code]}")
    print(f"  Year: {YEAR}")

    if GENERATE_ELECTRICAL_PROFILE:
        electrical_label = f"{electrical_industry['code']} ({electrical_industry['name']})"
        print(f"  Electrical profile: {ELECTRICAL_INDUSTRY_NUMBER} - {electrical_label}")
        print(f"  Electrical weights mode: {ELECTRICAL_WEIGHTS_MODE}")
    else:
        print("  Electrical profile: disabled")

    if GENERATE_THERMAL_PROFILE:
        thermal_label = thermal_industry["name"]
        print(f"  Thermal profile: {THERMAL_INDUSTRY_NUMBER} - {thermal_label}")
    else:
        print("  Thermal profile: disabled")

    print(f"  Output folder: {base_path / 'Generated'}")

    
    """ Run the generators """
    
    if GENERATE_ELECTRICAL_PROFILE:
        print("\nGenerating electrical profile...")
        LoadGeneratorElectricity.run(
            industry_number=ELECTRICAL_INDUSTRY_NUMBER,
            industry_code=electrical_industry["code"],
            industry_name=electrical_industry["name"],
            year=YEAR,
            base_path=base_path,
            country_code=country_code,
            weights_mode=ELECTRICAL_WEIGHTS_MODE,
        )

    if GENERATE_THERMAL_PROFILE:
        print("\nGenerating thermal profile...")
        LoadGeneratorThermal.run(
            industry_number=THERMAL_INDUSTRY_NUMBER,
            industry_name=thermal_industry["name"],
            industry_column=thermal_industry["column"],
            year=YEAR,
            base_path=base_path,
            country_code=country_code,
        )

    print("\nProcess finished.")
    print(f"  Profiles: {base_path / 'Generated' / 'load_profiles'}")
    print(f"  Diagrams: {base_path / 'Generated' / 'diagrams'}")


if __name__ == "__main__":
    main()
