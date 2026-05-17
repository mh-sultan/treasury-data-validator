# data_loader.py
# Reads CSV files and loads them into the database
# Raw files are never modified - governance principle

import pandas as pd
from src.db_connector import get_connection

def load_all_data():
    """
    Load all three CSV files into the database.
    
    Business reason: Raw data is preserved on disk untouched.
    We load copies into the database for processing.
    If a regulatory question arises about what was received,
    the original CSV is the definitive record.
    """
    conn = get_connection()

    # Load transactions
    df_transactions = pd.read_csv("data/raw_transactions.csv")
    df_transactions.to_sql("transactions", conn, 
                           if_exists="replace", index=False)
    print(f"Loaded {len(df_transactions)} transaction records")

    # Load counterparty limits
    df_limits = pd.read_csv("data/counterparty_limits.csv")
    df_limits.to_sql("counterparty_limits", conn, 
                     if_exists="replace", index=False)
    print(f"Loaded {len(df_limits)} counterparty limit records")

    # Load position summary
    df_position = pd.read_csv("data/position_summary.csv")
    df_position.to_sql("position_summary", conn, 
                       if_exists="replace", index=False)
    print(f"Loaded {len(df_position)} position summary records")

    conn.commit()
    conn.close()
    print("All data loaded successfully")
    
    return df_transactions, df_limits, df_position

if __name__ == "__main__":
    load_all_data()