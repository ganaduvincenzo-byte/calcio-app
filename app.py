import datetime
import math
import random
import pandas as pd
import requests
import streamlit as st

# Configurazione della pagina Streamlit
st.set_page_config(
    page_title="Centro Analisi Calcio Pro", page_icon="⚽", layout="wide"
)

# Stili CSS avanzati per un look moderno, pulito e curato nei dettagli
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
    /* Stile personalizzato per i container di configurazione schedina */
    .filter-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
</style>
""",
    unsafe_allow_html=True,
)

API_KEY = "16ecb66eb7f7454cad0506778fa7d041"
headers = {"X-Auth-Token": API_KEY}

# Elenco delle 12 competizioni coperte dal Free Tier dell'API
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
if "schedina_generata" not in st.session_state:
  st.session_state.schedina_generata = None

# --- CREAZIONE DELLE SCHEDE (TABS) ---
tab1, tab2, tab3 = st.tabs(
    ["📊 Analisi Turno & Giocatori", "🎟️ Schedina Vincente", "ℹ️ Info & Guide"]
)

with tab1:
  st.subheader(
      "🌍 Seleziona Più Campionati e Avvia l'Analisi Multi-Competizione"
  )

  col1, col2 = st.columns([3, 1])
  with col1:
    camp_options = [
        (code, f"{c['bandiera']} {c['nome']}") for code, c in campionati.items()
    ]
    leghe_selezionate = st.multiselect(
        "Seleziona uno o più campionati da analizzare:",
        options=[opt[0] for opt in camp_options],
        format_func=lambda x: next(opt[1] for opt in camp_options if opt[0] == x),
        default=["SA"] if "SA" in campionati else [camp_options[0][0]],
    )

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

  btn_analizza = st.button(
      "📊 Avvia Analisi Selezionati", type="primary", use_container_width=True
  )

  if btn_analizza:
    if not leghe_selezionate:
      st.warning("⚠️ Seleziona almeno un campionato prima di avviare l'analisi.")
    else:
      report_totale_sessione = []
      progress_bar = st.progress(0)
      tot_leghe = len(leghe_selezionate)

      for idx, league_code in enumerate(leghe_selezionate):
        selezionato = campionati[league_code]
        progress_bar.progress(
            (idx + 1) / tot_leghe,
            text=f"Analisi in corso per {selezionato['bandiera']} {selezionato['nome']}...",
        )

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
            tutti_corrente = resp_base.json().get("matches", [])
          if not tutti_corrente:
            resp_curr = requests.get(
                f"{url_base}?season={anno_corrente}",
                headers=headers,
                timeout=10,
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
              if g_casa + g_ospite > 1.5:
                prob_over15 += p
              if g_casa + g_ospite > 2.5:
                prob_over25 += p
              if g_casa > 0 and g_ospite > 0:
                prob_gol += p

          prob_under15 = 1.0 - prob_over15
          prob_under25 = 1.0 - prob_over25
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
              "🔍 Marcatore Probabile": f"⚽ {marcatore_casa} / {marcatore_ospite}",
              "⚠️ Rischio Cartellini": (
                  "Alto" if stima_cartellini > 4.5 else "Moderato"
              ),
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
  st.subheader("🎟️ Generatore Schedina Intelligente e Personalizzabile")

  if not st.session_state.archivio_partite_globali:
    st.info(
        "💡 Analizza almeno un campionato nella scheda 'Analisi Turno &"
        " Giocatori' per popolare la schedina."
    )
  else:
    campionati_presenti = list(
        set([p["Campionato"] for p in st.session_state.archivio_partite_globali])
    )

    # --- SEZIONE FILTRI GRAFICA RINNOVATA (CARD DESIGN) ---
    st.markdown('<div class="filter-card">', unsafe_allow_html=True)
    st.markdown("#### ⚙️ Configurazione Filtri Schedina")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
      campionati_scelti = st.multiselect(
          "🏆 Seleziona Campionati:",
          options=campionati_presenti,
          default=campionati_presenti,
      )

    tutti_i_mercati_possibili = [
        "Over 1.5",
        "Under 1.5",
        "Over 2.5",
        "Under 2.5",
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

    with col_f2:
      mercati_selezionati = st.multiselect(
          "🎯 Scegli Opzioni di Mercato:",
          options=tutti_i_mercati_possibili,
          default=["Over 1.5", "Gol"],
      )

    col_f3, col_f4 = st.columns(2)
    with col_f3:
      num_eventi = st.number_input(
          "🔢 Numero di eventi in schedina:",
          min_value=1,
          max_value=max(1, len(st.session_state.archivio_partite_globali)),
          value=min(5, len(st.session_state.archivio_partite_globali)),
      )

    with col_f4:
      budget = st.number_input(
          "💰 Budget puntata (€):",
          min_value=1.00,
          max_value=1000.00,
          value=5.00,
      )

    st.markdown("</div>", unsafe_allow_html=True)

    # --- TASTINO CENTRALE DEDICATO "GENERA SCHEDINA" ---
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
      btn_genera_schedina = st.button(
          "🚀 Genera Schedina", type="primary", use_container_width=True
      )

    if btn_genera_schedina:
      partite_filtrate = [
          p
          for p in st.session_state.archivio_partite_globali
          if p["Campionato"] in campionati_scelti
      ]

      selezioni_schedina = []
      if partite_filtrate:
        partite_campione = random.sample(
            partite_filtrate, min(num_eventi, len(partite_filtrate))
        )

        for p in partite_campione:
          mercato_scelto = None
          prob_val = 0.0

          if mercati_selezionati:
            mercati_compatibili = []
            for m in p["_tutti_i_mercati"]:
              for ms in mercati_selezionati:
                if ms.lower() in m["mercato"].lower():
                  mercati_compatibili.append(m)

            if mercati_compatibili:
              scelta_compatibile = max(
                  mercati_compatibili, key=lambda x: x["prob"]
              )
              mercato_scelto = scelta_compatibile["mercato"]
              prob_val = scelta_compatibile["prob"]

          if not mercato_scelto:
            mercato_scelto = p["_miglior_mercato"]
            prob_val = p["_miglior_prob"]

          quota_stimata = round(
              max(1.05, min(3.50, (1.0 / max(0.05, prob_val)) * 0.92)), 2
          )

          selezioni_schedina.append({
              "Incontro": p["Incontro"],
              "Data e Ora": p["📅 Data e Ora"],
              "Pronostico": mercato_scelto,
              "Probabilità": f"{prob_val * 100:.1f}%",
              "Quota Stimata": quota_stimata,
          })

      st.session_state.schedina_generata = selezioni_schedina

    # Mostra la schedina se è stata generata in questa sessione
    if st.session_state.schedina_generata is not None:
      selezioni_schedina = st.session_state.schedina_generata
      if selezioni_schedina:
        st.markdown("---")
        st.markdown("### 📋 La tua Schedina Consigliata")
        df_schedina = pd.DataFrame(selezioni_schedina)
        st.dataframe(df_schedina, use_container_width=True)

        quota_totale = 1.0
        for s in selezioni_schedina:
          quota_totale *= s["Quota Stimata"]

        vincita_potenziale = budget * quota_totale

        st.success(
            f"📊 **Quota Totale Combinata:** {quota_totale:.2f} | 💰 **Vincita"
            f" Potenziale:** {vincita_potenziale:.2f} €"
        )
      else:
        st.warning(
            "⚠️ Nessuna partita disponibile con i campionati o i mercati"
            " selezionati. Riprova modificando i filtri."
        )

with tab3:
  st.subheader("ℹ️ Guida all'Utilizzo e Informazioni")
  st.markdown("""
    Benvenuto nel **Centro Analisi Calcio Pro**. 
    * **Tab 1:** Analizza i campionati desiderati caricando i dati storici e le giornate correnti.
    * **Tab 2:** Configura la tua schedina selezionando i campionati e i mercati preferiti all'interno del pannello filtri, quindi clicca su **Genera Schedina** per visualizzare il pronostico ottimizzato.
    """)
