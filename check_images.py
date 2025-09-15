import pandas as pd
from pathlib import Path

# Read the Excel file
excel_path = Path("./data/jugadores.xlsx")
df = pd.read_excel(excel_path)

# Filter for our team
team_name = "LUJISA GUADALAJARA BASKET"
team_df = df[df['EQUIPO'].str.contains(team_name, case=False, na=False)]

print(f"Players from {team_name} with IMAGEN info:")
print("="*80)

for idx, row in team_df.iterrows():
    imagen_value = row['IMAGEN'] if pd.notna(row['IMAGEN']) else "No imagen"
    print(f"{row['JUGADOR']} (#{row['DORSAL']}) -> IMAGEN: {imagen_value}")

print(f"\n" + "="*80)
print("Sample IMAGEN values:")
imagen_samples = df['IMAGEN'].dropna().unique()[:10]
for sample in imagen_samples:
    print(f"  - {sample}")