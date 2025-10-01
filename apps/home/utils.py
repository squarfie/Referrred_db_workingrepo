# apps/your_app/utils.py


from sqlalchemy import create_engine
import pandas as pd


#creating a connection to postgresql
try:
    # Create SQLAlchemy engine
    engine = create_engine('postgresql+psycopg2://postgres:admin123@localhost:5432/test_db')

    # SQL query to fetch data
    breakpoints_query = "SELECT * FROM home_breakpointstable"
    antibiotic_query = "SELECT * FROM home_antibioticentry"
    # Use pandas to fetch data via SQLAlchemy engine
    breakpoint_data = pd.read_sql_query(breakpoints_query, engine)
    antibiotic_data = pd.read_sql_query(antibiotic_query, engine)


    # Display the data
    print(breakpoint_data)
    print(antibiotic_data)


    


except Exception as error:
    print("Error while fetching data from PostgreSQL:", error)


# finally:
#     print("Execution completed")


# generate codes for handling generation of accession numbers
def generate_codes(site_code, referral_date_obj, ref_no_raw, batch_no, total_batch, site_name):
    """
    Generates accession numbers, batch code, and batch name.
    
    Handles multi-accession ranges like '0001-0002' and returns a list of dictionaries.
    """
    # Ensure referral date is valid
    if not referral_date_obj or not site_code or not ref_no_raw:
        return []

    # Parse the ref_no range
    ref_parts = ref_no_raw.split('-')
    if len(ref_parts) == 2 and ref_parts[0].isdigit() and ref_parts[1].isdigit():
        start_ref = int(ref_parts[0])
        end_ref = int(ref_parts[1])
        ref_numbers = range(start_ref, end_ref + 1)
    else:
        ref_numbers = [int(ref_parts[0])]  # single number

    year_short = referral_date_obj.strftime('%y')
    year_long = referral_date_obj.strftime('%m%d%Y')

    result_list = []

    for ref in ref_numbers:
        padded_ref = str(ref).zfill(4)
        accession_number = f"{year_short}ARS_{site_code}{padded_ref}"
        batch_codegen = f"{site_code}_{year_long}_{batch_no}.{total_batch}_{padded_ref}"
        auto_batch_name = batch_codegen  # identical format

        result_list.append({
            "accession_number": accession_number,
            "batch_codegen": batch_codegen,
            "auto_batch_name": auto_batch_name,
            "site_name": site_name,
        })

    return result_list




