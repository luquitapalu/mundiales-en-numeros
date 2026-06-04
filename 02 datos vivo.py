# ============================================================
# MUNDIAL 2026 — Etapa 2: Datos en vivo (football-data.org)
# ============================================================
# ANTES DE CORRER:
# 1. Registrate gratis en https://www.football-data.org/
# 2. Copiá tu API key y pegala abajo donde dice TU_API_KEY
# ============================================================

import requests
import pandas as pd

API_KEY = "TU_API_KEY"  # <-- reemplazá esto
BASE_URL = "https://api.football-data.org/v4"

headers = {"X-Auth-Token": API_KEY}

# ── Función base para hacer requests ────────────────────────
def get_data(endpoint):
    url = f"{BASE_URL}/{endpoint}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

# ── Traer competiciones disponibles ─────────────────────────
competiciones = get_data("competitions")
if competiciones:
    df_comp = pd.DataFrame(competiciones["competitions"])
    print("=== COMPETICIONES DISPONIBLES ===")
    print(df_comp[["id", "name", "code", "area"]].to_string())

# ── Traer partidos del Mundial 2026 ─────────────────────────
# Código del Mundial: "WC" — cuando arranque el torneo esto devuelve resultados
mundial = get_data("competitions/WC/matches")
if mundial:
    matches = mundial.get("matches", [])
    df_partidos = pd.json_normalize(matches)
    print(f"\n=== PARTIDOS MUNDIAL 2026: {len(df_partidos)} ===")
    
    # Columnas útiles
    cols = ["utcDate", "stage", "group",
            "homeTeam.name", "awayTeam.name",
            "score.fullTime.home", "score.fullTime.away",
            "status"]
    cols_disponibles = [c for c in cols if c in df_partidos.columns]
    print(df_partidos[cols_disponibles].head(20).to_string())
    
    # Guardar a CSV para usar en etapa 3
    df_partidos.to_csv("partidos_2026.csv", index=False)
    print("\nGuardado: partidos_2026.csv")

# ── Tabla de posiciones por grupo ───────────────────────────
standings = get_data("competitions/WC/standings")
if standings:
    for grupo in standings.get("standings", []):
        nombre_grupo = grupo.get("group", "GRUPO")
        print(f"\n=== {nombre_grupo} ===")
        tabla = pd.DataFrame(grupo["table"])
        print(tabla[["position", "team", "playedGames",
                      "won", "draw", "lost", "goalsFor",
                      "goalsAgainst", "goalDifference", "points"]].to_string())
