# ============================================================
# MUNDIAL 2026 — Etapa 1: Datos históricos
# Fuente: Kaggle (archivo local) + Wikipedia (scraping simple)
# ============================================================
# ANTES DE CORRER:
# 1. Bajate este dataset de Kaggle y guardalo en la misma carpeta:
#    https://www.kaggle.com/datasets/abecklas/fifa-world-cup
#    Archivos: WorldCupMatches.csv, WorldCups.csv
# ============================================================

import pandas as pd

# ── Cargar datos históricos ──────────────────────────────────
partidos = pd.read_csv("WorldCupMatches.csv")
mundiales = pd.read_csv("WorldCups.csv")
jugadores = pd.read_csv("WorldCupPlayers.csv")

print("=== PARTIDOS HISTÓRICOS ===")
print(f"Total partidos: {len(partidos)}")
print(f"Columnas: {list(partidos.columns)}")
print(partidos.head(3))

print("\n=== MUNDIALES ===")
print(mundiales[["Year", "Winner", "Runners-Up", "Third", "GoalsScored", "QualifiedTeams"]])

# ── Análisis: rendimiento de campeones de grupo ──────────────
# Filtramos solo fase de grupos
grupos = partidos[partidos["Stage"] == "Group A"]  # ejemplo, luego generalizamos
print("\n=== EJEMPLO FASE DE GRUPOS ===")
print(grupos[["Year", "Home Team Name", "Away Team Name",
              "Home Team Goals", "Away Team Goals"]].head(10))

# ── Análisis base: goles por mundial ────────────────────────
goles_por_mundial = partidos.groupby("Year").agg(
    partidos_jugados=("MatchID", "count"),
    goles_totales=("Home Team Goals", "sum"),  # suma aprox
).reset_index()
goles_por_mundial["promedio_goles"] = (
    goles_por_mundial["goles_totales"] / goles_por_mundial["partidos_jugados"]
).round(2)

print("\n=== GOLES POR MUNDIAL ===")
print(goles_por_mundial)
