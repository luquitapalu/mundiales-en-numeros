import pandas as pd

# ── Cargar datos históricos ──────────────────────────────────
partidos = pd.read_csv("WorldCupMatches.csv", encoding="latin-1")

print("=== PARTIDOS HISTÓRICOS ===")
print(f"Total partidos: {len(partidos)}")
print(f"Columnas: {list(partidos.columns)}")
print(partidos.head(3))