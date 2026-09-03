import pandas as pd
from pathlib import Path
import os

def create_excel():
    desktop = Path(os.environ['USERPROFILE']) / 'Desktop' / 'סגולי בדיקות לוקאלי'
    desktop.mkdir(parents=True, exist_ok=True)
    excel_path = desktop / 'Local_Form939_Research.xlsx'
    
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        for csv_file in Path('logs').glob('*.csv'):
            df = pd.read_csv(csv_file)
            sheet_name = csv_file.stem[:31] # Excel limits sheet name to 31 chars
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
    print(f"Excel saved to {excel_path}")

if __name__ == '__main__':
    create_excel()
