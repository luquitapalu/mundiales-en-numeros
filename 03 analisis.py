# ============================================================
# MUNDIAL 2026 — Etapa 3: Análisis histórico vs actual
# Pregunta central: ¿los campeones de grupo llegaron lejos?
# ============================================================
# Requiere haber corrido etapa 1 (WorldCupMatches.csv disponible)
# ============================================================

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ── Cargar datos ─────────────────────────────────────────────
partidos = pd.read_csv("WorldCupMatches.csv")
partidos.columns = partidos.columns.str.strip()
partidos["Year"] = partidos["Year"].astype(int)

# ── Limpieza básica ──────────────────────────────────────────
partidos["Home Team Goals"] = pd.to_numeric(partidos["Home Team Goals"], errors="coerce")
partidos["Away Team Goals"] = pd.to_numeric(partidos["Away Team Goals"], errors="coerce")
partidos.dropna(subset=["Home Team Goals", "Away Team Goals"], inplace=True)

# ── Análisis 1: ¿En qué etapa llegan los campeones de grupo? ─
# (simplificado: contamos apariciones por Stage)
etapas = partidos["Stage"].value_counts().reset_index()
etapas.columns = ["Etapa", "Partidos"]
print("=== PARTIDOS POR ETAPA (histórico) ===")
print(etapas.to_string())

# ── Análisis 2: Promedio de goles por etapa ──────────────────
partidos["goles_partido"] = partidos["Home Team Goals"] + partidos["Away Team Goals"]
goles_etapa = (partidos.groupby("Stage")["goles_partido"]
               .mean().round(2)
               .sort_values(ascending=False)
               .reset_index())
goles_etapa.columns = ["Etapa", "Promedio goles"]
print("\n=== PROMEDIO GOLES POR ETAPA ===")
print(goles_etapa.to_string())

# ── Análisis 3: Campeones históricos y su rendimiento ────────
mundiales = pd.read_csv("WorldCups.csv")
campeones = mundiales["Winner"].value_counts().reset_index()
campeones.columns = ["País", "Títulos"]
print("\n=== CAMPEONES HISTÓRICOS ===")
print(campeones.to_string())

# ── Análisis 4: Goles a favor de campeones vs resto ──────────
# Por cada mundial, cuántos goles hizo el campeón
resultados = []
for _, row in mundiales.iterrows():
    year = row["Year"]
    campeon = row["Winner"]
    p_año = partidos[partidos["Year"] == year]
    
    # Goles del campeón como local
    gf_local = p_año[p_año["Home Team Name"].str.strip() == campeon]["Home Team Goals"].sum()
    # Goles del campeón como visitante
    gf_visita = p_año[p_año["Away Team Name"].str.strip() == campeon]["Away Team Goals"].sum()
    
    resultados.append({
        "Año": year,
        "Campeón": campeon,
        "Goles del campeón": gf_local + gf_visita,
        "Total goles torneo": p_año["goles_partido"].sum()
    })

df_camp = pd.DataFrame(resultados).dropna()
df_camp["% goles del campeón"] = (
    df_camp["Goles del campeón"] / df_camp["Total goles torneo"] * 100
).round(1)
print("\n=== GOLES DEL CAMPEÓN POR MUNDIAL ===")
print(df_camp.to_string())

# ── Gráficos ─────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle("Análisis Histórico Mundiales FIFA", fontsize=14, fontweight="bold")

# Gráfico 1: Títulos por país
axes[0].barh(campeones["País"], campeones["Títulos"], color="#1A5C38")
axes[0].set_title("Títulos por país")
axes[0].set_xlabel("Títulos")
axes[0].xaxis.set_major_locator(mticker.MultipleLocator(1))

# Gráfico 2: Goles del campeón a lo largo de los años
axes[1].plot(df_camp["Año"], df_camp["Goles del campeón"],
             marker="o", color="#C0392B", linewidth=2)
axes[1].set_title("Goles del campeón por mundial")
axes[1].set_xlabel("Año")
axes[1].set_ylabel("Goles")
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("analisis_mundial.png", dpi=150, bbox_inches="tight")
plt.show()
print("\nGráfico guardado: analisis_mundial.png")
