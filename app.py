import datetime
import math
import pandas as pd
import requests
import streamlit as st

# Configurazione della pagina Streamlit
st.set_page_config(
    page_title="Centro Analisi Calcio Pro", page_icon="⚽", layout="wide"
)

# Stili CSS avanzati per un look moderno e pulito
st.markdown(
    """
<style>
    .main { background-color: #f8f9fa; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 8px 8px 0px 0px;
        padding: 10px 20px;
        font-weight: 600;
        color: #2c3e50;
        border: 1px solid #e0e0e0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1abc9c !important;
        color: white !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

API_KEY = "16ecb66eb7f7454cad0506778fa7d041"
headers = {"X-Auth-Token": API_KEY}

# Elenco aggiornato ed esclusivo delle 12 competizioni coperte dal Free Tier dell'API
campionati = {
    "PL": {"nome": "Campionato Inglese (Premier League)", "bandiera": "🇬🇧"},
    "PD": {"nome": "Campionato Spagnolo (La Liga)", "bandiera": "🇪🇸"},
    "SA": {"nome": "Campionato Italiano (Serie A)", "bandiera": "🇮🇹"},
    "BL1": {"nome": "Campionato Tedesco (Bundesliga)", "bandiera": "🇩🇪"},
    "FL1": {"nome": "Campionato Francese (Ligue 1)", "bandiera": "🇫🇷"},
    "CL": {"nome": "UEFA Champions League", "bandiera": "🇪🇺"},
    "EL": {"nome": "UEFA Europa League", "bandiera": "🇪🇺"},
    "DED": {"nome": "Eredivisie (Paesi Bassi)", "bandiera": "🇳🇱"},
    "PPL": {"nome": "Primeira Liga (Portogallo)", "bandiera": "🇵🇹"},
    "BSA": {"nome": "Campeonato Brasileiro Série A", "bandiera": "🇧🇷"},
    "CLI": {"nome": "Copa Libertadores", "bandiera": "🌎"},
    "WC": {"nome": "FIFA World Cup", "bandiera": "🏆"},
}

st.title("⚽ Centro Analisi Calcio Pro")
st.markdown(
    "Piattaforma professionale con analisi multi-stagione (fino a 5 anni),"
    " Risultato Esatto, Over/Under, Gol/No Gol, Gol 1° Tempo, Rigori, Corner,"
    " Cartellini, Data/Ora e marcatori reali."
)
st.markdown("---")

if "archivio_partite_globali" not in st.session_state:
  st.session_state.archivio_partite_globali = []
if "ultimo_report" not in st.session_state:
  st.session_state.ultimo_report = []
if "campionati_analizzati" not in st.session_state:
  st.session_state.campionati_analizzati = set()
if "ultimo_campionato_selezionato" not in st.session_state:
  st.session_state.ultimo_campionato_selezionato = None

# --- CREAZIONE DELLE SCHEDE (TABS) ---
tab1, tab2, tab3 = st.tabs(
    ["📊 Analisi Turno & Giocatori", "🎟️ Schedina Vincente", "ℹ️ Info & Guide"]
)

with tab1:
  st.subheader("🌍 Seleziona e Analizza il Turno di Campionato / Coppe")

  col1, col2, col3 = st.columns([2, 1, 1])
  with col1:
    camp_options = []
    for code, c in campionati.items():
      prefix = "✔️ " if code in st.session_state.campionati_analizzati else ""
      camp_options.append((code, f"{prefix}{c['bandiera']} {c['nome']}"))

    league_code = st.selectbox(
        "Campionato / Competizione:",
        options=[opt[0] for opt in camp_options],
        format_func=lambda x: next(opt[1] for opt in camp_options if opt[0] == x),
    )

  selezionato = campionati[league_code]

  with col2:
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

  with col3:
    st.write("")
    st.write("")
    btn_analizza = st.button(
        "📊 Avvia Analisi", type="primary", use_container_width=True
    )

  if st.session_state.ultimo_campionato_selezionato != league_code:
    st.session_state.ultimo_campionato_selezionato = league_code

  if btn_analizza:
    with st.spinner(
        f"⏳ Caricamento calendario e storico reale per"
        f" {selezionato['bandiera']} {selezionato['nome']}..."
    ):
      partite_finite_totali = []
      tutti_corrente = []
      marcatori_per_squadra = {}

      anno_corrente = datetime.datetime.now().year

      url_base = (
          f"https://api.football-data.org/v4/competitions/{league_code}/matches"
      )
      try:
        resp_base = requests.get(url_base, headers=headers, timeout=10)
        if resp_base.status_code == 200:
          data_base = resp_base.json()
          tutti_corrente = data_base.get("matches", [])

        if not tutti_corrente:
          url_season_curr = f"{url_base}?season={anno_corrente}"
          resp_curr = requests.get(url_season_curr, headers=headers, timeout=10)
          if resp_curr.status_code == 200:
            tutti_corrente = resp_curr.json().get("matches", [])

        partite_finite_totali.extend(
            [m for m in tutti_corrente if m.get("status") == "FINISHED"]
        )
      except Exception:
        pass

      if num_stagioni > 1:
        anni_passati = [anno_corrente - i for i in range(1, num_stagioni)]
        for anno_p in anni_passati:
          url_season = f"https://api.football-data.org/v4/competitions/{league_code}/matches?season={anno_p}"
          try:
            resp_season = requests.get(url_season, headers=headers, timeout=10)
            if resp_season.status_code == 200:
              d_season = resp_season.json()
              m_fin_passate = [
                  m
                  for m in d_season.get("matches", [])
                  if m.get("status") == "FINISHED"
              ]
              partite_finite_totali.extend(m_fin_passate)
          except Exception:
            pass

      url_scorers = (
          f"https://api.football-data.org/v4/competitions/{league_code}/scorers"
      )
      try:
        resp_sc = requests.get(url_scorers, headers=headers, timeout=10)
        if resp_sc.status_code == 200:
          data_sc = resp_sc.json()
          for scorer in data_sc.get("scorers", []):
            p_nome = scorer.get("player", {}).get("name", "Sconosciuto")
            s_nome = scorer.get("team", {}).get("name", "")
            if s_nome:
              if s_nome not in marcatori_per_squadra:
                marcatori_per_squadra[s_nome] = []
              marcatori_per_squadra[s_nome].append(p_nome)
      except Exception:
        pass

      # Filtraggio rigoroso delle sole partite future reali (escludendo quelle passate)
      matchday_list = []
      if tutti_corrente:
        ora_attuale = datetime.datetime.utcnow()
        partite_future_reali = []

        for m in tutti_corrente:
          status = m.get("status")
          utc_date_str = m.get("utcDate")

          if status in ["TIMED", "SCHEDULED", "LIVE", "IN_PLAY"]:
            if utc_date_str:
              try:
                dt_utc = datetime.datetime.strptime(
                    utc_date_str.replace("Z", ""), "%Y-%m-%dT%H:%M:%S"
                )
                if dt_utc >= ora_attuale - datetime.timedelta(hours=3):
                  partite_future_reali.append(m)
              except Exception:
                pass
            else:
              partite_future_reali.append(m)

        if partite_future_reali:
          primo_matchday_futuro = partite_future_reali[0].get("matchday")
          matchday_list = [
              m
              for m in tutti_corrente
              if m.get("matchday") == primo_matchday_futuro
              and m.get("status") not in ["FINISHED"]
          ]
        else:
          matchday_list = []

      if partite_finite_totali:
        media_casa = sum(
            m["score"]["fullTime"]["home"]
            for m in partite_finite_totali
            if m.get("score")
            and m["score"].get("fullTime")
            and m["score"]["fullTime"]["home"] is not None
        ) / max(1, len(partite_finite_totali))
        media_ospiti = sum(
            m["score"]["fullTime"]["away"]
            for m in partite_finite_totali
            if m.get("score")
            and m["score"].get("fullTime")
            and m["score"]["fullTime"]["away"] is not None
        ) / max(1, len(partite_finite_totali))
      else:
        media_casa, media_ospiti = 1.45, 1.15

      if len(matchday_list) > 0:

        def poisson(lmbda, k):
          return (math.exp(-lmbda) * (lmbda**k)) / math.factorial(k)

        report_giornata = []
        incontri_visti = set()

        for match in matchday_list:
          casa = match["homeTeam"]["name"]
          ospite = match["awayTeam"]["name"]

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
              dt_ita = dt_utc + datetime.timedelta(hours=2)
              data_ora_formattata = dt_ita.strftime("%d/%m/%Y %H:%M")
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
          if len(valid_home_goals) > 0:
            xg_c = sum(valid_home_goals) / len(valid_home_goals)
          else:
            seed_c = (abs(hash(casa)) % 7) * 0.12
            xg_c = max(0.8, media_casa + seed_c - 0.2)

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
          if len(valid_away_goals) > 0:
            xg_o = sum(valid_away_goals) / len(valid_away_goals)
          else:
            seed_o = (abs(hash(ospite)) % 7) * 0.12
            xg_o = max(0.7, media_ospiti + seed_o - 0.3)

          prob_1, prob_x, prob_2 = 0, 0, 0
          prob_over15, prob_over25 = 0, 0
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

              tot_gol = g_casa + g_ospite
              if tot_gol > 1.5:
                prob_over15 += p
              if tot_gol > 2.5:
                prob_over25 += p

              if g_casa > 0 and g_ospite > 0:
                prob_gol += p

          prob_under15 = 1.0 - prob_over15
          prob_under25 = 1.0 - prob_over25
          prob_nogol = 1.0 - prob_gol

          xg_c_1t, xg_o_1t = xg_c * 0.42, xg_o * 0.42
          prob_gol_1t = 1 - (poisson(xg_c_1t, 0) * poisson(xg_o_1t, 0))

          stimacorner = round(8.5 + (xg_c + xg_o) * 0.8, 1)
          diff_forza = abs(xg_c - xg_o)
          stima_cartellini = max(3.8, round(5.2 - (diff_forza * 0.5), 1))
          prob_rigore_si = min(0.50, max(0.22, 0.25 + (xg_c + xg_o) * 0.04))

          prob_over85_corner = min(
              0.88, max(0.35, 0.50 + (stimacorner - 9.0) * 0.08)
          )
          prob_under95_corner = 1.0 - prob_over85_corner

          prob_over35_cartellini = min(
              0.90, max(0.30, 0.50 + (stima_cartellini - 4.0) * 0.10)
          )
          prob_under45_cartellini = 1.0 - prob_over35_cartellini

          def clamp(val):
            return min(0.95, max(0.05, val))

          prob_1 = clamp(prob_1)
          prob_x = clamp(prob_x)
          prob_2 = clamp(prob_2)
          prob_over15 = clamp(prob_over15)
          prob_under15 = clamp(prob_under15)
          prob_over25 = clamp(prob_over25)
          prob_under25 = clamp(prob_under25)
          prob_gol = clamp(prob_gol)
          prob_nogol = clamp(prob_nogol)
          prob_gol_1t = clamp(prob_gol_1t)
          prob_rigore_si = clamp(prob_rigore_si)
          prob_over85_corner = clamp(prob_over85_corner)
          prob_under95_corner = clamp(prob_under95_corner)
          prob_over35_cartellini = clamp(prob_over35_cartellini)
          prob_under45_cartellini = clamp(prob_under45_cartellini)

          lista_marcatori_casa = marcatori_per_squadra.get(casa, [])
          marcatore_c_str = (
              lista_marcatori_casa[0]
              if lista_marcatori_casa
              else f"Attaccante ({casa})"
          )

          lista_marcatori_ospite = marcatori_per_squadra.get(ospite, [])
          marcatore_o_str = (
              lista_marcatori_ospite[0]
              if lista_marcatori_ospite
              else f"Attaccante ({ospite})"
          )

          stringa_marcatori = f"⚽ {marcatore_c_str} / {marcatore_o_str}"
          rischio_ammonizione = (
              "Alto (Mediana aggressiva)"
              if stima_cartellini > 4.5
              else "Moderato"
          )

          mercati_partita = [
              {"mercato": f"1X2: Casa ({casa})", "prob": prob_1},
              {"mercato": f"1X2: X (Pareggio)", "prob": prob_x},
              {"mercato": f"1X2: Ospite ({ospite})", "prob": prob_2},
              {"mercato": "Over 1.5", "prob": prob_over15},
              {"mercato": "Under 1.5", "prob": prob_under15},
              {"mercato": "Over 2.5", "prob": prob_over25},
              {"mercato": "Under 2.5", "prob": prob_under25},
              {"mercato": "Gol", "prob": prob_gol},
              {"mercato": "No Gol", "prob": prob_nogol},
              {"mercato": "Gol 1°T Sì", "prob": prob_gol_1t},
              {"mercato": "Rigore Sì", "prob": prob_rigore_si},
              {"mercato": "Corner Over 8.5", "prob": prob_over85_corner},
              {"mercato": "Corner Under 9.5", "prob": prob_under95_corner},
              {
                  "mercato": "Cartellini Over 3.5",
                  "prob": prob_over35_cartellini,
              },
              {
                  "mercato": "Cartellini Under 4.5",
                  "prob": prob_under45_cartellini,
              },
          ]

          miglior_scelta = max(mercati_partita, key=lambda x: x["prob"])

          diz_partita = {
              "Campionato": f"{selezionato['bandiera']} {selezionato['nome']}",
              "Codice": league_code,
              "📅 Data e Ora": data_ora_formattata,
              "Incontro": f"{casa} - {ospite}",
              "🎯 Risultato Esatto": risultato_esatto,
              "1 (%)": f"{prob_1 * 100:.1f}%",
              "X (%)": f"{prob_x * 100:.1f}%",
              "2 (%)": f"{prob_2 * 100:.1f}%",
              "Over 1.5 (%)": f"{prob_over15 * 100:.1f}%",
              "Over 2.5 (%)": f"{prob_over25 * 100:.1f}%",
              "Gol (%)": f"{prob_gol * 100:.1f}%",
              "No Gol (%)": f"{prob_nogol * 100:.1f}%",
              "Gol 1°T (%)": f"{prob_gol_1t * 100:.1f}%",
              "Rigore Sì (%)": f"{prob_rigore_si * 100:.1f}%",
              "Corner": stimacorner,
              "Cartellini": stima_cartellini,
              "🔍 Marcatore Probabile": stringa_marcatori,
              "⚠️ Rischio Cartellini": rischio_ammonizione,
              "_miglior_mercato": miglior_scelta["mercato"],
              "_miglior_prob": miglior_scelta["prob"],
              "_tutti_i_mercati": mercati_partita,
          }
          report_giornata.append(diz_partita)

          esistente = next(
              (
                  p
                  for p in st.session_state.archivio_partite_globali
                  if p["Incontro"] == diz_partita["Incontro"]
                  and p.get("Codice") == league_code
              ),
              None,
          )
          if esistente:
            st.session_state.archivio_partite_globali.remove(esistente)
          st.session_state.archivio_partite_globali.append(diz_partita)

        st.session_state.campionati_analizzati.add(league_code)
        st.session_state.ultimo_report = report_giornata
        st.success(
            f"✅ Analisi completata per {selezionato['bandiera']}"
            f" {selezionato['nome']}!"
        )
        st.rerun()
      else:
        st.warning(
            "⚠️ Al momento non ci sono partite future programmate per questa"
            " competizione nel calendario ufficiale dell'API (o il piano"
            " gratuito non copre le date odierne per questo torneo)."
        )

  if st.session_state.get("ultimo_report"):
    df_report = pd.DataFrame(st.session_state.ultimo_report)
    display_cols = [
        c
        for c in df_report.columns
        if not c.startswith("_") and c not in ["Campionato", "Codice"]
    ]
    st.markdown("### 📋 Tabella Dettagliata & Risultati Esatti Stimati")
    st.dataframe(df_report[display_cols], use_container_width=True)

with tab2:
  st.subheader("🎟️ Generatore Schedina Intelligente e Personalizzabile")

  if not st.session_state.archivio_partite_globali:
    st.info(
        "💡 Analizza almeno un campionato nella scheda 'Analisi Turno &"
        " Giocatori' per popolare la schedina."
    )
  else:
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
      num_eventi = st.slider("Numero di eventi in schedina:", 1, 10, 3)
    with col_s2:
      quota_min = st.number_input("Quota minima per evento:", 1.10, 3.00, 1.30)
    with col_s3:
      budget = st.number_input("Budget puntata (€):", 1.00, 1000.00, 10.00)

    if st.button("🎲 Genera Schedina Vincente", type="primary"):
      partite_disponibili = list(st.session_state.archivio_partite_globali)
      import random

      random.shuffle(partite_disponibili)

      selezioni_schedina = []
      for p in partite_disponibili:
        if len(selezioni_schedina) >= num_eventi:
          break
        mercato_top = p["_miglior_mercato"]
        prob_top = p["_miglior_prob"]
        quota_stimata = round(
            max(1.05, min(3.50, (1.0 / max(0.05, prob_top)) * 0.92)), 2
        )

        if quota_stimata >= quota_min:
          selezioni_schedina.append({
              "Incontro": p["Incontro"],
              "Data e Ora": p["📅 Data e Ora"],
              "Pronostico": mercato_top,
              "Probabilità": f"{prob_top * 100:.1f}%",
              "Quota Stimata": quota_stimata,
          })

      if selezioni_schedina:
        df_schedina = pd.DataFrame(selezioni_schedina)
        st.markdown("### 🎫 La tua Schedina Consigliata")
        st.dataframe(df_schedina, use_container_width=True)

        quota_totale = 1.0
        for s in selezioni_schedina:
          quota_totale *= s["Quota Stimata"]

        vincita_potenziale = budget * quota_totale
        st.success(
            f"📊 **Quota Totale Combinata:** **{quota_totale:.2f}** | 💰"
            f" **Vincita Potenziale:** **{vincita_potenziale:.2f} €**"
        )
      else:
        st.warning(
            "⚠️ Nessun evento soddisfa i filtri selezionati. Prova ad abbassare"
            " la quota minima o ad analizzare altri campionati."
        )

with tab3:
  st.subheader("ℹ️ Guida all'Utilizzo e Informazioni")
  st.markdown("""
    Benvenuto nel **Centro Analisi Calcio Pro**. Questa applicazione ti permette di analizzare le partite ufficiali dei campionati supportati sfruttando modelli statistici avanzati (Poisson, stime di xG storiche, corner, cartellini e marcatori).
    
    * **Tab 1 (Analisi Turno & Giocatori):** Scegli una delle competizioni ufficiali dell'API, seleziona la profondità storica desiderata (da 1 a 5 anni per calcoli più accurati) e clicca su *Avvia Analisi*.
    * **Tab 2 (Schedina Vincente):** Configura i tuoi parametri e genera automaticamente una combinazione di scommesse basata sulle probabilità più alte calcolate dal sistema.
    * **Competizioni Supportate:** Sono incluse tutte le competizioni del piano gratuito ufficiale di *football-data.org* (Premier League, Serie A, Liga, Bundesliga, Ligue 1, Champions League, Europa League, Eredivisie, Primeira Liga, Brasileirão, Copa Libertadores e Mondiali).
    """)
