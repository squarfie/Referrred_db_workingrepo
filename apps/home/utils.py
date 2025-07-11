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

