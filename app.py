import datetime
import math
import random
import pandas as pd
import requests
import streamlit as st

# Configurazione della pagina Streamlit
st.set_page_config(
    page_title="VIGANA Centro Analisi Calcio Pro", page_icon="⚽", layout="wide"
)

# Stili CSS avanzati per un look super moderno e accattivante
st.markdown(
    """
<style>
    .main { background-color: #0f172a; color: #f8fafc; }
    .stTabs [data-baseweb="tab-list"] { gap: 12px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1e293b;
        border-radius: 10px 10px 0px 0px;
        padding: 12px 24px;
        font-weight: 600;
        color: #94a3b8;
        border: 1px solid #334155;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
        color: white !important;
        border-bottom: none;
    }
    .dashboard-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 25px;
        border-radius: 16px;
        border: 1px solid #334155;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        margin-bottom: 25px;
    }
    .card-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #38bdf8;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
</style>
""",
    unsafe_allow_html=True,
)

API_KEY = "16ecb66eb7f7454cad0506778fa7d041"
headers = {"X-Auth-Token": API_KEY}

# Elenco delle competizioni con bandiere per i campionati e coppe per i tornei internazionali
campionati = {
    "PL": {
        "nome": "Premier League",
        "etichetta": (
            '<img src="https://flagcdn.com/w20/gb-eng.png" width="20"'
            ' style="vertical-align: middle; margin-right: 8px;"> Premier'
            " League"
        ),
    },
    "PD": {
        "nome": "La Liga",
        "etichetta": (
            '<img src="https://flagcdn.com/w20/es.png" width="20"'
            ' style="vertical-align: middle; margin-right: 8px;"> La Liga'
        ),
    },
    "SA": {
        "nome": "Serie A",
        "etichetta": (
            '<img src="https://flagcdn.com/w20/it.png" width="20"'
            ' style="vertical-align: middle; margin-right: 8px;"> Serie A'
        ),
    },
    "BL1": {
        "nome": "Bundesliga",
        "etichetta": (
            '<img src="https://flagcdn.com/w20/de.png" width="20"'
            ' style="vertical-align: middle; margin-right: 8px;"> Bundesliga'
        ),
    },
    "FL1": {
        "nome": "Ligue 1",
        "etichetta": (
            '<img src="https://flagcdn.com/w20/fr.png" width="20"'
            ' style="vertical-align: middle; margin-right: 8px;"> Ligue 1'
        ),
    },
    "CL": {
        "nome": "Champions League",
        "etichetta": (
            '<span style="font-size: 1.1rem; vertical-align: middle;'
            ' margin-right: 6px;">🏆</span> Champions League'
        ),
    },
    "EL": {
        "nome": "Europa League",
        "etichetta": (
            '<span style="font-size: 1.1rem; vertical-align: middle;'
            ' margin-right: 6px;">🏆</span> Europa League'
        ),
    },
    "DED": {
        "nome": "Eredivisie",
        "etichetta": (
            '<img src="https://flagcdn.com/w20/nl.png" width="20"'
            ' style="vertical-align: middle; margin-right: 8px;"> Eredivisie'
        ),
    },
    "PPL": {
        "nome": "Primeira Liga",
        "etichetta": (
            '<img src="https://flagcdn.com/w20/pt.png" width="20"'
            ' style="vertical-align: middle; margin-right: 8px;"> Primeira Liga'
        ),
    },
    "BSA": {
        "nome": "Brasileirão",
        "etichetta": (
            '<img src="https://flagcdn.com/w20/br.png" width="20"'
            ' style="vertical-align: middle; margin-right: 8px;"> Brasileirão'
        ),
    },
    "CLI": {
        "nome": "Copa Libertadores",
        "etichetta": (
            '<span style="font-size: 1.1rem; vertical-align: middle;'
            ' margin-right: 6px;">🏆</span> Copa Libertadores'
        ),
    },
    "WC": {
        "nome": "World Cup",
        "etichetta": (
            '<span style="font-size: 1.1rem; vertical-align: middle;'
            ' margin-right: 6px;">🏆</span> World Cup'
        ),
    },
}

st.markdown(
    """
    <div style="text-align: center; margin-bottom: 20px;">
        <h1>⚽ ⚽ ⚽ VIGANA Centro Analisi Calcio Pro ⚽ ⚽ ⚽</h1>
        <p style="color: #94a3b8; font-size: 1.1rem;">Piattaforma professionale con analisi multi-stagione (fino a 5 anni), Risultato Esatto, Over/Under, Gol/No Gol, Gol 1° Tempo, Rigori, Corner, Cartellini, Data/Ora e marcatori reali.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("---")

if "archivio_partite_globali" not in st.session_state:
  st.session_state.archivio_partite_globali = []
if "ultimo_report" not in st.session_state:
  st.session_state.ultimo_report = []
if "schedina_generata" not in st.session_state:
  st.session_state.schedina_generata = None

# --- CREAZIONE DELLE SCHEDE (TABS) ---
tab1, tab2, tab3 = st.tabs(
    ["📊 Analisi Turno & Giocatori", "🎟️ Schedina Vincente Pro", "ℹ️ Info & Guide"]
)

with tab1:
  st.subheader("🌍 Seleziona i Campionati e Avvia l'Analisi Multi-Competizione")

  st.markdown(
      '<div class="dashboard-card"><div class="card-title">🏆 Seleziona Campionati'
      " da Analizzare</div>",
      unsafe_allow_html=True,
  )

  if "leghe_selezionate_tab1" not in st.session_state:
    st.session_state.leghe_selezionate_tab1 = ["SA"]

  col_s1, col_s2, col_s3 = st.columns([1, 1, 3])
  with col_s1:
    if st.button("Seleziona Tutti", key="tutti_t1", use_container_width=True):
      st.session_state.leghe_selezionate_tab1 = list(campionati.keys())
      st.rerun()
  with col_s2:
    if st.button("Deseleziona Tutti", key="nessuno_t1", use_container_width=True):
      st.session_state.leghe_selezionate_tab1 = []
      st.rerun()

  st.markdown("<br>", unsafe_allow_html=True)

  grid_cols = st.columns(3)
  leghe_scelte_temp = []
  for i, (code, info) in enumerate(campionati.items()):
    target_col = grid_cols[i % 3]
    with target_col:
      is_checked = st.checkbox(
          info["nome"],
          value=code in st.session_state.leghe_selezionate_tab1,
          key=f"chk_t1_{code}",
          help=info["nome"],
      )
      st.markdown(
          f"""
            <div style="margin-top: -30px; margin-left: 28px; margin-bottom: 10px; pointer-events: none;">
                <span style="font-size: 0.95rem; color: #f8fafc; font-weight: 500;">{info['etichetta']}</span>
            </div>
            """,
          unsafe_allow_html=True,
      )
      if is_checked:
        leghe_scelte_temp.append(code)

  st.session_state.leghe_selezionate_tab1 = leghe_scelte_temp
  st.markdown("</div>", unsafe_allow_html=True)

  col_storico, col_btn = st.columns([2, 2])
  with col_storico:
    num_stagioni = st.selectbox(
        "Profondità storica:",
        options=[1, 2, 3, 4, 5],
        format_func=lambda x: (
            "Solo Stagione Corrente"
            if x == 1
            else f"Corrente + {x-1} Anni Prec."
        ),
        index=1,
    )

  with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    btn_analizza = st.button(
        "📊 AVVIA ANALISI SELEZIONATI", type="primary", use_container_width=True
    )

  if btn_analizza:
    leghe_selezionate = st.session_state.leghe_selezionate_tab1
    if not leghe_selezionate:
      st.warning("⚠️ Seleziona almeno un campionato prima di avviare l'analisi.")
    else:
      report_totale_sessione = []
      progress_bar = st.progress(0)
      tot_leghe = len(leghe_selezionate)

      for idx, league_code in enumerate(leghe_selezionate):
        selezionato = campionati[league_code]
        nome_pulito = selezionato["nome"]
        progress_bar.progress(
            (idx + 1) / tot_leghe,
            text=f"Analisi in corso per {nome_pulito}...",
        )

        partite_finite_totali = []
        tutti_corrente = []
        marcatori_per_squadra = {}
        anno_corrente = datetime.datetime.now().year
        url_base = f"https://api.football-data.org/v4/competitions/{league_code}/matches"

        try:
          resp_base = requests.get(url_base, headers=headers, timeout=10)
          if resp_base.status_code == 200:
            tutti_corrente = resp_base.json().get("matches", [])
          if not tutti_corrente:
            resp_curr = requests.get(
                f"{url_base}?season={anno_corrente}", headers=headers, timeout=10
            )
            if resp_curr.status_code == 200:
              tutti_corrente = resp_curr.json().get("matches", [])
          partite_finite_totali.extend(
              [m for m in tutti_corrente if m.get("status") == "FINISHED"]
          )
        except Exception:
          pass

        if num_stagioni > 1:
          for anno_p in [anno_corrente - i for i in range(1, num_stagioni)]:
            try:
              resp_season = requests.get(
                  f"https://api.football-data.org/v4/competitions/{league_code}/matches?season={anno_p}",
                  headers=headers,
                  timeout=10,
              )
              if resp_season.status_code == 200:
                m_fin_passate = [
                    m
                    for m in resp_season.json().get("matches", [])
                    if m.get("status") == "FINISHED"
                ]
                partite_finite_totali.extend(m_fin_passate)
            except Exception:
              pass

        try:
          resp_sc = requests.get(
              f"https://api.football-data.org/v4/competitions/{league_code}/scorers",
              headers=headers,
              timeout=10,
          )
          if resp_sc.status_code == 200:
            for scorer in resp_sc.json().get("scorers", []):
              p_nome = scorer.get("player", {}).get("name", "Sconosciuto")
              t_id = scorer.get("team", {}).get("id")
              if t_id:
                if t_id not in marcatori_per_squadra:
                  marcatori_per_squadra[t_id] = []
                marcatori_per_squadra[t_id].append(p_nome)
        except Exception:
          pass

        matchday_list = []
        if tutti_corrente:
          partite_future_reali = [
              m
              for m in tutti_corrente
              if m.get("status") in ["TIMED", "SCHEDULED", "LIVE", "IN_PLAY"]
          ]
          if partite_future_reali:
            primo_matchday_futuro = partite_future_reali[0].get("matchday")
            matchday_list = [
                m
                for m in tutti_corrente
                if m.get("matchday") == primo_matchday_futuro
                and m.get("status") not in ["FINISHED"]
            ]

        media_casa = (
            sum(
                m["score"]["fullTime"]["home"]
                for m in partite_finite_totali
                if m.get("score")
                and m["score"].get("fullTime")
                and m["score"]["fullTime"]["home"] is not None
            )
            / max(1, len(partite_finite_totali))
            if partite_finite_totali
            else 1.45
        )
        media_ospiti = (
            sum(
                m["score"]["fullTime"]["away"]
                for m in partite_finite_totali
                if m.get("score")
                and m["score"].get("fullTime")
                and m["score"]["fullTime"]["away"] is not None
            )
            / max(1, len(partite_finite_totali))
            if partite_finite_totali
            else 1.15
        )

        def poisson(lmbda, k):
          return (math.exp(-lmbda) * (lmbda**k)) / math.factorial(k)

        incontri_visti = set()
        for match in matchday_list:
          casa = match["homeTeam"]["name"]
          ospite = match["awayTeam"]["name"]
          home_id = match["homeTeam"].get("id")
          away_id = match["awayTeam"].get("id")

          chiave_match = f"{casa}-{ospite}"
          if chiave_match in incontri_visti:
            continue
          incontri_visti.add(chiave_match)

          utc_date_str = match.get("utcDate")
          if utc_date_str:
            try:
              dt_utc = datetime.datetime.strptime(
                  utc_date_str.replace("Z", ""), "%Y-%m-%dT%H:%M:%S"
              )
              data_ora_formattata = (
                  dt_utc + datetime.timedelta(hours=2)
              ).strftime("%d/%m/%Y %H:%M")
            except Exception:
              data_ora_formattata = "Da definire"
          else:
            data_ora_formattata = "Da definire"

          p_casa = [
              m for m in partite_finite_totali if m["homeTeam"]["name"] == casa
          ]
          valid_home_goals = [
              m["score"]["fullTime"]["home"]
              for m in p_casa
              if m.get("score")
              and m["score"].get("fullTime")
              and m["score"]["fullTime"]["home"] is not None
          ]
          xg_c = (
              sum(valid_home_goals) / len(valid_home_goals)
              if valid_home_goals
              else max(0.8, media_casa + (abs(hash(casa)) % 7) * 0.12 - 0.2)
          )

          p_ospite = [
              m for m in partite_finite_totali if m["awayTeam"]["name"] == ospite
          ]
          valid_away_goals = [
              m["score"]["fullTime"]["away"]
              for m in p_ospite
              if m.get("score")
              and m["score"].get("fullTime")
              and m["score"]["fullTime"]["away"] is not None
          ]
          xg_o = (
              sum(valid_away_goals) / len(valid_away_goals)
              if valid_away_goals
              else max(0.7, media_ospiti + (abs(hash(ospite)) % 7) * 0.12 - 0.3)
          )

          prob_1, prob_x, prob_2 = 0, 0, 0
          prob_over15, prob_over25, prob_over35, prob_over45 = 0, 0, 0, 0
          prob_gol = 0
          max_p_risultato = -1
          risultato_esatto = "1-1"

          for g_casa in range(6):
            for g_ospite in range(6):
              p = poisson(xg_c, g_casa) * poisson(xg_o, g_ospite)
              if p > max_p_risultato:
                max_p_risultato = p
                risultato_esatto = f"{g_casa} - {g_ospite}"
              if g_casa > g_ospite:
                prob_1 += p
              elif g_casa == g_ospite:
                prob_x += p
              else:
                prob_2 += p
              tot_g = g_casa + g_ospite
              if tot_g > 1.5:
                prob_over15 += p
              if tot_g > 2.5:
                prob_over25 += p
              if tot_g > 3.5:
                prob_over35 += p
              if tot_g > 4.5:
                prob_over45 += p
              if g_casa > 0 and g_ospite > 0:
                prob_gol += p

          prob_under15 = 1.0 - prob_over15
          prob_under25 = 1.0 - prob_over25
          prob_under35 = 1.0 - prob_over35
          prob_under45 = 1.0 - prob_over45
          prob_nogol = 1.0 - prob_gol
          prob_gol_1t = 1 - (
              poisson(xg_c * 0.42, 0) * poisson(xg_o * 0.42, 0)
          )
          stimacorner = round(8.5 + (xg_c + xg_o) * 0.8, 1)
          stima_cartellini = max(
              3.8, round(5.2 - (abs(xg_c - xg_o) * 0.5), 1)
          )
          prob_rigore_si = min(0.50, max(0.22, 0.25 + (xg_c + xg_o) * 0.04))
          prob_over85_corner = min(
              0.88, max(0.35, 0.50 + (stimacorner - 9.0) * 0.08)
          )
          prob_under95_corner = 1.0 - prob_over85_corner
          prob_over35_cartellini = min(
              0.90, max(0.30, 0.50 + (stima_cartellini - 4.0) * 0.10)
          )
          prob_under45_cartellini = 1.0 - prob_over35_cartellini

          marcatore_casa = (
              marcatori_per_squadra.get(home_id, ["Attaccante Casa"])[0]
              if home_id in marcatori_per_squadra
              else f"Bomber ({casa})"
          )
          marcatore_ospite = (
              marcatori_per_squadra.get(away_id, ["Attaccante Ospite"])[0]
              if away_id in marcatori_per_squadra
              else f"Bomber ({ospite})"
          )
          prob_marcatore_c = min(0.65, max(0.20, xg_c * 0.35))
          prob_marcatore_o = min(0.60, max(0.18, xg_o * 0.35))

          def clamp(val):
            return min(0.95, max(0.05, val))

          mercati_partita = [
              {"mercato": f"1X2: Casa ({casa})", "prob": clamp(prob_1)},
              {"mercato": "1X2: X (Pareggio)", "prob": clamp(prob_x)},
              {"mercato": f"1X2: Ospite ({ospite})", "prob": clamp(prob_2)},
              {"mercato": "Over 1.5", "prob": clamp(prob_over15)},
              {"mercato": "Under 1.5", "prob": clamp(prob_under15)},
              {"mercato": "Over 2.5", "prob": clamp(prob_over25)},
              {"mercato": "Under 2.5", "prob": clamp(prob_under25)},
              {"mercato": "Over 3.5", "prob": clamp(prob_over35)},
              {"mercato": "Under 3.5", "prob": clamp(prob_under35)},
              {"mercato": "Over 4.5", "prob": clamp(prob_over45)},
              {"mercato": "Under 4.5", "prob": clamp(prob_under45)},
              {"mercato": "Gol", "prob": clamp(prob_gol)},
              {"mercato": "No Gol", "prob": clamp(prob_nogol)},
              {"mercato": "Gol 1°T Sì", "prob": clamp(prob_gol_1t)},
              {"mercato": "Rigore Sì", "prob": clamp(prob_rigore_si)},
              {"mercato": "Corner Over 8.5", "prob": clamp(prob_over85_corner)},
              {"mercato": "Corner Under 9.5", "prob": clamp(prob_under95_corner)},
              {
                  "mercato": "Cartellini Over 3.5",
                  "prob": clamp(prob_over35_cartellini),
              },
              {
                  "mercato": "Cartellini Under 4.5",
                  "prob": clamp(prob_under45_cartellini),
              },
              {
                  "mercato": f"Marcatore Si: {marcatore_casa}",
                  "prob": clamp(prob_marcatore_c),
              },
              {
                  "mercato": f"Marcatore Si: {marcatore_ospite}",
                  "prob": clamp(prob_marcatore_o),
              },
          ]

          miglior_scelta = max(mercati_partita, key=lambda x: x["prob"])

          diz_partita = {
              "Campionato": nome_pulito,
              "Codice": league_code,
              "📅 Data e Ora": data_ora_formattata,
              "Incontro": f"{casa} - {ospite}",
              "🎯 Risultato Esatto": risultato_esatto,
              "1 (%)": f"{prob_1 * 100:.1f}%",
              "X (%)": f"{prob_x * 100:.1f}%",
              "2 (%)": f"{prob_2 * 100:.1f}%",
              "Over 2.5 (%)": f"{prob_over25 * 100:.1f}%",
              "Under 2.5 (%)": f"{prob_under25 * 100:.1f}%",
              "Gol (%)": f"{prob_gol * 100:.1f}%",
              "No Gol (%)": f"{prob_nogol * 100:.1f}%",
              "Corner": stimacorner,
              "Cartellini": stima_cartellini,
              "🔍 Marcatore Probabile": f"⚽ {marcatore_casa} / {marcatore_ospite}",
              "_miglior_mercato": miglior_scelta["mercato"],
              "_miglior_prob": miglior_scelta["prob"],
              "_tutti_i_mercati": mercati_partita,
          }
          report_totale_sessione.append(diz_partita)

          esistente = next(
              (
                  p
                  for p in st.session_state.archivio_partite_globali
                  if p["Incontro"] == diz_partita["Incontro"]
              ),
              None,
          )
          if esistente:
            st.session_state.archivio_partite_globali.remove(esistente)
          st.session_state.archivio_partite_globali.append(diz_partita)

      st.session_state.ultimo_report = report_totale_sessione
      progress_bar.empty()
      st.success("✅ Analisi completata!")
      st.rerun()

  if st.session_state.get("ultimo_report"):
    df_report = pd.DataFrame(st.session_state.ultimo_report)
    display_cols = [
        c for c in df_report.columns if not c.startswith("_") and c != "Codice"
    ]
    st.markdown("### 📋 Tabella Dettagliata & Risultati Esatti Stimati")
    st.dataframe(df_report[display_cols], use_container_width=True)

with tab2:
  st.markdown(
      '<p style="font-size: 1.8rem; font-weight: 800; color: #38bdf8; text-align:'
      ' center; margin-bottom: 20px;">🎟️ Schedina Vincente Pro - Generatore'
      " Intelligente</p>",
      unsafe_allow_html=True,
  )

  if not st.session_state.archivio_partite_globali:
    st.info(
        "💡 Per generare la schedina, avvia prima l'analisi dei campionati nella"
        " scheda 'Analisi Turno & Giocatori'."
    )
  else:
    campionati_disponibili = list(
        set([p["Campionato"] for p in st.session_state.archivio_partite_globali])
    )

    st.markdown(
        '<div class="dashboard-card"><div class="card-title">🏆 Seleziona i'
        " Campionati da Giocare</div>",
        unsafe_allow_html=True,
    )

    if "campionati_selezionati_pro" not in st.session_state:
      st.session_state.campionati_selezionati_pro = campionati_disponibili.copy()

    col_sel1, col_sel2, col_sel3 = st.columns([1, 1, 3])
    with col_sel1:
      if st.button("Seleziona Tutti", key="tutti_t2", use_container_width=True):
        st.session_state.campionati_selezionati_pro = (
            campionati_disponibili.copy()
        )
        st.rerun()
    with col_sel2:
      if st.button(
          "Deseleziona Tutti", key="nessuno_t2", use_container_width=True
      ):
        st.session_state.campionati_selezionati_pro = []
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    camp_cols = st.columns(3)
    campionati_scelti = []
    for i, camp in enumerate(campionati_disponibili):
      col_target = camp_cols[i % 3]
      with col_target:
        checked = st.checkbox(
            camp,
            value=camp in st.session_state.campionati_selezionati_pro,
            key=f"chk_camp_{i}",
        )
        if checked:
          campionati_scelti.append(camp)

    st.session_state.campionati_selezionati_pro = campionati_scelti
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div class="dashboard-card"><div class="card-title">⚙️ Parametri &'
        " Mercati di Gioco</div>",
        unsafe_allow_html=True,
    )

    tutti_i_mercati_possibili = [
        "Over 1.5",
        "Under 1.5",
        "Over 2.5",
        "Under 2.5",
        "Over 3.5",
        "Under 3.5",
        "Over 4.5",
        "Under 4.5",
        "Gol",
        "No Gol",
        "Gol 1°T Sì",
        "Rigore Sì",
        "1X2: 1 (Casa)",
        "1X2: X (Pareggio)",
        "1X2: 2 (Ospite)",
        "Corner Over 8.5",
        "Corner Under 9.5",
        "Cartellini Over 3.5",
        "Cartellini Under 4.5",
        "Marcatore Si",
    ]

    col_m1, col_m2 = st.columns([2, 1])
    with col_m1:
      mercati_selezionati = st.multiselect(
          "🎯 Scegli i mercati preferiti (Over, Under, Gol, 1X2, ecc.):",
          options=tutti_i_mercati_possibili,
          default=["Over 1.5", "Under 2.5", "Gol"],
      )

    with col_m2:
      num_eventi = st.slider(
          "🔢 Numero Eventi:",
          min_value=1,
          max_value=max(1, len(st.session_state.archivio_partite_globali)),
          value=min(5, len(st.session_state.archivio_partite_globali)),
      )
      col_b_bud, col_b_quot = st.columns(2)
      with col_b_bud:
        budget = st.number_input(
            "💰 Budget (€):", min_value=1.00, max_value=1000.00, value=10.00
        )
      with col_b_quot:
        quota_desiderata = st.number_input(
            "🎯 Quota Totale Desiderata:",
            min_value=1.10,
            max_value=500.00,
            value=10.00,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
    with col_b2:
      btn_genera = st.button(
          "🚀 GENERA SCHEDINA VINCENTE", type="primary", use_container_width=True
      )

    if btn_genera:
      partite_filtrate = [
          p
          for p in st.session_state.archivio_partite_globali
          if p["Campionato"] in campionati_scelti
      ]

      selezioni_schedina = []
      if partite_filtrate:
        target_singola = max(1.05, quota_desiderata ** (1.0 / num_eventi))
        pool_partite = list(partite_filtrate)
        random.shuffle(pool_partite)

        for _ in range(min(num_eventi, len(pool_partite))):
          if not pool_partite:
            break
          p = pool_partite.pop(0)

          opzioni_valide = []
          for m in p["_tutti_i_mercati"]:
            q_est = round(
                max(1.05, min(5.00, (1.0 / max(0.05, m["prob"])) * 0.92)), 2
            )
            opzioni_valide.append((m["mercato"], m["prob"], q_est))

          if mercati_selezionati:
            filtrate_utente = [
                op
                for op in opzioni_valide
                if any(ms.lower() in op[0].lower() for ms in mercati_selezionati)
            ]
            if filtrate_utente:
              opzioni_valide = filtrate_utente

          miglior_opzione = min(
              opzioni_valide, key=lambda x: abs(x[2] - target_singola)
          )

          selezioni_schedina.append({
              "Campionato": p["Campionato"],
              "Incontro": p["Incontro"],
              "Data e Ora": p["📅 Data e Ora"],
              "Pronostico": miglior_opzione[0],
              "Probabilità": f"{miglior_opzione[1] * 100:.1f}%",
              "Quota Stimata": miglior_opzione[2],
          })

      st.session_state.schedina_generata = selezioni_schedina

    if st.session_state.schedina_generata is not None:
      selezioni_schedina = st.session_state.schedina_generata
      if selezioni_schedina:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<div class="dashboard-card"><div'
            ' class="card-title">📊 Risultato Schedina Elaborata</div>',
            unsafe_allow_html=True,
        )

        df_schedina = pd.DataFrame(selezioni_schedina)
        st.dataframe(df_schedina, use_container_width=True)

        quota_totale = 1.0
        for s in selezioni_schedina:
          quota_totale *= s["Quota Stimata"]

        vincita_potenziale = budget * quota_totale

        st.markdown(
            f"""
                <div style="display: flex; justify-content: space-around; background: #0f172a; padding: 20px; border-radius: 12px; border: 1px solid #3b82f6; margin-top: 15px; text-align: center;">
                    <div>
                        <p style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 5px;">QUOTA TOTALE</p>
                        <p style="color: #38bdf8; font-size: 1.8rem; font-weight: 800; margin: 0;">{quota_totale:.2f}</p>
                    </div>
                    <div>
                        <p style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 5px;">PUNTATA</p>
                        <p style="color: #f8fafc; font-size: 1.8rem; font-weight: 800; margin: 0;">{budget:.2f} €</p>
                    </div>
                    <div>
                        <p style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 5px;">VINCITA POTENZIALE</p>
                        <p style="color: #22c55e; font-size: 1.8rem; font-weight: 800; margin: 0;">{vincita_potenziale:.2f} €</p>
                    </div>
                </div>
                """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
      else:
        st.warning(
            "⚠️ Nessuna partita trovata con i campionati o mercati selezionati."
            " Seleziona almeno un campionato e dei mercati validi."
        )

with tab3:
  st.subheader("ℹ️ Guida all'Utilizzo e Informazioni")
  st.markdown("""
    Benvenuto nel **VIGANA Centro Analisi Calcio Pro**. 
    * **Tab 1:** Seleziona i campionati con le relative bandiere e tornei internazionali con l'icona della coppa, quindi avvia l'analisi.
    * **Tab 2:** Scegli i campionati, i mercati preferiti, imposta il budget e la **Quota Totale Desiderata** per generare la schedina.
    """)
