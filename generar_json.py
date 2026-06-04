"""
Genera data/historico.json a partir de la Fjelstul World Cup Database
(github.com/jfjelstul/worldcup) — carpeta fuente4/.

Filtra únicamente Mundiales masculinos (1930–2022). La landing page
index_historico.html consume solo este JSON, nunca los CSV.
"""

import pandas as pd
import json
import os

BASE = 'fuente4'


# ── Cargar datasets ─────────────────────────────────────────────────────────
tournaments    = pd.read_csv(f'{BASE}/tournaments.csv')
matches_all    = pd.read_csv(f'{BASE}/matches.csv', low_memory=False)
goals_all      = pd.read_csv(f'{BASE}/goals.csv', low_memory=False)
bookings_all   = pd.read_csv(f'{BASE}/bookings.csv', low_memory=False)
player_apps_all  = pd.read_csv(f'{BASE}/player_appearances.csv', low_memory=False)
manager_apps_all = pd.read_csv(f'{BASE}/manager_appearances.csv', low_memory=False)
referee_apps_all = pd.read_csv(f'{BASE}/referee_appearances.csv', low_memory=False)
team_apps_all    = pd.read_csv(f'{BASE}/team_appearances.csv', low_memory=False)


# ── Filtrar solo Mundiales masculinos ───────────────────────────────────────
mens_ids = set(tournaments.loc[
    tournaments['tournament_name'].str.contains("Men's"), 'tournament_id'
])

def only_mens(df):
    return df[df['tournament_id'].isin(mens_ids)].copy()

tournaments  = only_mens(tournaments)
matches      = only_mens(matches_all)
goals        = only_mens(goals_all)
bookings     = only_mens(bookings_all)
player_apps  = only_mens(player_apps_all)
manager_apps = only_mens(manager_apps_all)
referee_apps = only_mens(referee_apps_all)
team_apps    = only_mens(team_apps_all)


# ── Helpers ─────────────────────────────────────────────────────────────────
def full_name(given, family):
    """Forma 'Given Family' o solo 'Family' si Given es 'not applicable'."""
    family = '' if pd.isna(family) else str(family).strip()
    given  = '' if pd.isna(given) or str(given).strip() == 'not applicable' else str(given).strip()
    return f'{given} {family}'.strip()


def add_full_name(df):
    df = df.copy()
    df['full_name'] = [full_name(g, f) for g, f in zip(df['given_name'], df['family_name'])]
    return df


def top_grouped(df, group_cols, name_field='size', n=5):
    """Devuelve top-n filas agrupadas. Retorna lista de tuplas (keys, count)."""
    s = df.groupby(group_cols).size().sort_values(ascending=False).head(n)
    return list(zip(s.index, s.values))


# Etiqueta corta de selección para los rankings (sólo nombre histórico que
# no entra en el badge — los rankings muestran solo apellido + país).
TEAM_LABELS = {
    'West Germany': 'Germany (W)',
}

def short_team(name):
    return TEAM_LABELS.get(name, name)


# ── Stats por mundial ───────────────────────────────────────────────────────
historico = {}

for _, t in tournaments.sort_values('year').iterrows():
    tid = t['tournament_id']
    year = int(t['year'])
    host = t['host_country']
    champion = t['winner']

    yr_matches  = matches[matches['tournament_id'] == tid]
    yr_goals    = goals[goals['tournament_id'] == tid]
    yr_bookings = bookings[bookings['tournament_id'] == tid]
    yr_refs     = referee_apps[referee_apps['tournament_id'] == tid]
    yr_team     = team_apps[team_apps['tournament_id'] == tid]
    yr_mgr      = manager_apps[manager_apps['tournament_id'] == tid]

    # ── PARTIDOS ─────────────────────────────────────────────────────────────
    total_matches    = len(yr_matches)
    extra_time       = int((yr_matches['extra_time'] == 1).sum())
    penalty_shootout = int((yr_matches['penalty_shootout'] == 1).sum())
    pct_extra_time   = round(extra_time / total_matches * 100, 1) if total_matches else 0.0
    pct_penalty_of_extra = round(penalty_shootout / extra_time * 100, 1) if extra_time else 0.0

    # ── GOLES ────────────────────────────────────────────────────────────────
    total_goals      = int(yr_matches['home_team_score'].sum() + yr_matches['away_team_score'].sum())
    penalty_goals    = int(yr_goals['penalty'].sum())
    pct_penalty_goals = round(penalty_goals / len(yr_goals) * 100, 1) if len(yr_goals) else 0.0

    # Goleador del torneo (excluye autogoles)
    real_goals = yr_goals[yr_goals['own_goal'] == 0]
    if len(real_goals):
        top_scorer_row = (real_goals
                          .groupby(['player_id', 'family_name', 'given_name', 'team_name'])
                          .size().sort_values(ascending=False))
        (_pid, fam, giv, team), g = top_scorer_row.index[0], top_scorer_row.iloc[0]
        tournament_top_scorer = {
            'name':  full_name(giv, fam),
            'team':  team,
            'goals': int(g),
        }
    else:
        tournament_top_scorer = None

    # ── TARJETAS ─────────────────────────────────────────────────────────────
    yellow_total    = int(yr_bookings['yellow_card'].sum())
    sending_off     = int(yr_bookings['sending_off'].sum())
    direct_red      = int(yr_bookings['red_card'].sum())
    pct_direct_red  = round(direct_red / sending_off * 100, 1) if sending_off else 0.0

    # ── ÁRBITRO TOP ──────────────────────────────────────────────────────────
    if len(yr_refs):
        ref_top = (yr_refs.groupby(['referee_id', 'family_name', 'given_name', 'country_name'])['match_id']
                   .nunique().sort_values(ascending=False))
        (_rid, fam, giv, country), n = ref_top.index[0], ref_top.iloc[0]
        top_referee = {
            'name':    full_name(giv, fam),
            'country': country,
            'matches': int(n),
        }
    else:
        top_referee = None

    # ── CAMPEÓN ──────────────────────────────────────────────────────────────
    champ_team = yr_team[yr_team['team_name'] == champion]
    champion_matches_played = len(champ_team)
    champion_matches_won    = int(champ_team['win'].sum())
    champion_goals_for      = int(champ_team['goals_for'].sum())

    # DT del campeón (el que más partidos dirigió ese torneo para el campeón)
    champ_mgrs = yr_mgr[yr_mgr['team_name'] == champion]
    if len(champ_mgrs):
        mc = (champ_mgrs.groupby(['manager_id', 'family_name', 'given_name'])['match_id']
              .nunique().sort_values(ascending=False))
        (_mid, fam, giv), _ = mc.index[0], mc.iloc[0]
        champion_manager = full_name(giv, fam)
    else:
        champion_manager = None

    # Goleador del campeón
    champ_goals = real_goals[real_goals['team_name'] == champion]
    if len(champ_goals):
        cts = (champ_goals.groupby(['player_id', 'family_name', 'given_name'])
               .size().sort_values(ascending=False))
        (_pid, fam, giv), g = cts.index[0], cts.iloc[0]
        champion_top_scorer = {
            'name':  full_name(giv, fam),
            'goals': int(g),
        }
    else:
        champion_top_scorer = None

    # ── ESTADIO MÁS USADO (mantengo para info adicional) ─────────────────────
    stad = yr_matches['stadium_name'].value_counts()
    top_stadium = stad.index[0] if len(stad) else None
    top_stadium_matches = int(stad.iloc[0]) if len(stad) else 0

    historico[str(year)] = {
        'year':                    year,
        'host':                    host,
        'champion':                champion,
        'champion_manager':        champion_manager,
        'champion_goals':          champion_goals_for,
        'champion_matches_played': champion_matches_played,
        'champion_matches_won':    champion_matches_won,
        'champion_top_scorer':     champion_top_scorer,
        'total_matches':           total_matches,
        'total_goals':             total_goals,
        'top_stadium':             top_stadium,
        'top_stadium_matches':     top_stadium_matches,

        'stats_matches': {
            'total':                total_matches,
            'extra_time':           extra_time,
            'pct_extra_time':       pct_extra_time,
            'penalty_shootout':     penalty_shootout,
            'pct_penalty_of_extra': pct_penalty_of_extra,
        },
        'stats_goals': {
            'total':         total_goals,
            'penalty_goals': penalty_goals,
            'pct_penalty':   pct_penalty_goals,
            'top_scorer':    tournament_top_scorer,
        },
        'stats_cards': {
            'yellow':         yellow_total,
            'red':            sending_off,
            'direct_red':     direct_red,
            'pct_direct_red': pct_direct_red,
        },
        'stats_referee': top_referee,
    }


# ── Stats globales ──────────────────────────────────────────────────────────

# Top países por cantidad de participaciones (mundiales distintos)
country_appearances = (team_apps.groupby('team_name')['tournament_id']
                       .nunique().sort_values(ascending=False).head(5))
top_countries = [{'country': c, 'appearances': int(v)}
                 for c, v in country_appearances.items()]

# Helper: para un grupo de filas de un mismo jugador / DT, devuelve la
# selección más reciente (por match_date) — necesario para Matthäus
# (West Germany → Germany), Milutinović, etc.
def latest_team(df, team_col='team_name', date_col='match_date'):
    if date_col not in df.columns or df.empty:
        return df[team_col].iloc[0] if not df.empty else ''
    return df.sort_values(date_col).iloc[-1][team_col]


# Top jugadores por partidos efectivamente jugados (titular o suplente que entró).
# Agrupamos por player_id para no dividir a quienes jugaron en distintas selecciones
# (ej. Matthäus en West Germany y luego Germany). En el ranking mostramos solo el
# apellido — el badge de selección distingue a homónimos (Ronaldo BRA vs Ronaldo POR).
played = player_apps[(player_apps['starter'] == 1) | (player_apps['substitute'] == 1)].copy()
pm_counts = played.groupby('player_id')['match_id'].nunique().sort_values(ascending=False).head(5)
top_players = []
for pid, n in pm_counts.items():
    rows = played[played['player_id'] == pid]
    top_players.append({
        'player':  str(rows['family_name'].iloc[0]),
        'team':    short_team(latest_team(rows)),
        'matches': int(n),
    })

# Top goleadores históricos (excluye autogoles)
real_g = goals[goals['own_goal'] == 0].copy()
sg_counts = real_g.groupby('player_id').size().sort_values(ascending=False).head(5)
top_scorers = []
for pid, n in sg_counts.items():
    rows = real_g[real_g['player_id'] == pid]
    top_scorers.append({
        'player': str(rows['family_name'].iloc[0]),
        'team':   short_team(latest_team(rows)),
        'goals':  int(n),
    })

# Top DTs por partidos dirigidos. A diferencia de los jugadores, los DTs
# cambian de selección con frecuencia (Parreira, Milutinović…), así que
# mostramos el equipo donde dirigieron más partidos, no el último.
def main_team(df, team_col='team_name'):
    return df[team_col].value_counts().index[0] if not df.empty else ''


cm_counts = manager_apps.groupby('manager_id')['match_id'].nunique().sort_values(ascending=False).head(5)
top_coaches = []
for mid, n in cm_counts.items():
    rows = manager_apps[manager_apps['manager_id'] == mid]
    top_coaches.append({
        'coach':   str(rows['family_name'].iloc[0]),
        'team':    short_team(main_team(rows)),
        'matches': int(n),
    })

# Distribución de goles por minuto (con minute_regulation, bin "90+" incluye stoppage / alargue)
mins = goals['minute_regulation'].dropna().astype(int).tolist()
bins   = list(range(0, 100, 10)) + [200]
labels = ['0-10', '10-20', '20-30', '30-40', '40-50',
          '50-60', '60-70', '70-80', '80-90', '90+']
dist = (pd.cut(mins, bins=bins, labels=labels, right=False)
        .value_counts().reindex(labels).fillna(0).astype(int))
goal_distribution = [{'range': r, 'goals': int(g)} for r, g in dist.items()]

# Totales globales — recalcular desde los datos reales
total_tournaments = len(historico)
total_matches_all = sum(h['total_matches'] for h in historico.values())
total_goals_all   = sum(h['total_goals']   for h in historico.values())


# ── Escribir JSON ───────────────────────────────────────────────────────────
output = {
    'global': {
        'total_tournaments': total_tournaments,
        'total_matches':     total_matches_all,
        'total_goals':       total_goals_all,
        'top_countries':     top_countries,
        'top_players':       top_players,
        'top_scorers':       top_scorers,
        'top_coaches':       top_coaches,
        'goal_distribution': goal_distribution,
    },
    'years': historico,
}

os.makedirs('data', exist_ok=True)
with open('data/historico.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f'JSON generado — {total_tournaments} mundiales · {total_matches_all} partidos · {total_goals_all} goles')
print(f'Top países:    {top_countries}')
print(f'Top jugadores: {top_players}')
print(f'Top goleadores: {top_scorers}')
print(f'Top DTs:       {top_coaches}')
print(f'Distribución goles: {goal_distribution}')
