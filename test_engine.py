import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import NoSuchModuleError
import configparser # To read directly from ini

print("--- Starting Direct SQLAlchemy Engine Test ---")

# Read URL directly from alembic.ini to be certain
config = configparser.ConfigParser()
try:
    config.read('alembic.ini')
    DATABASE_URL = config['alembic']['sqlalchemy.url']
    print(f"Read URL from alembic.ini: {DATABASE_URL}")
    if 'psycopg2' not in DATABASE_URL:
         print("WARNING: URL does not contain 'psycopg2'. Check alembic.ini again.")
    if 'pyscopg2' in DATABASE_URL:
        print("ERROR: URL contains typo 'pyscopg2'. Fix alembic.ini!")

except Exception as e:
    print(f"ERROR: Could not read URL from alembic.ini: {e}")
    # Fallback or exit if needed, but ensure URL is correct below if manually setting
    DATABASE_URL = "postgresql+psycopg2://dev_user:dev_password@localhost:5432/gemini_dev" # Ensure correct spelling if using fallback
    print(f"Using manually defined URL (CHECK SPELLING): {DATABASE_URL}")


print(f"\nAttempting to create engine directly with URL: {DATABASE_URL}")

try:
    # Create engine directly using the URL read from ini
    engine = create_engine(DATABASE_URL, echo=True) # echo=True for more SQL debug
    print("Engine creation successful (dialect loaded).")

    # Try a simple connection and query
    print("\nAttempting to connect and run simple query...")
    with engine.connect() as connection:
        print("Connection successful.")
        result = connection.execute(text("SELECT 1"))
        print("Query execution successful.")
        print(f"Query result: {result.scalar_one()}")

    print("\n--- Test Completed Successfully ---")

except NoSuchModuleError as e:
    print(f"\nERROR: Caught NoSuchModuleError: {e}")
    print("This means SQLAlchemy failed to find the dialect plugin based on the URL.")
    if "pyscopg2" in str(e):
        print(">>> Error specifically mentions 'pyscopg2'. This is very strange if the URL printed above is correct.")
        print(">>> Possible causes: SQLAlchemy bug, environment issue, subtle config override.")
    elif "psycopg2" in str(e):
         print(">>> Error mentions 'psycopg2'. Check if psycopg2 package (via Conda) is correctly installed and importable.")
    else:
        print(f">>> Unexpected dialect mentioned in error: {e}")

except Exception as e:
    print(f"\nERROR: Caught other exception: {e}")
    import traceback
    traceback.print_exc() # Print full traceback for other errors

print("\n--- End of Test ---")