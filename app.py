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

API_KEY = "10ecb5beb7f7454cad0500778fa7d841"
headers = {"X-Auth-Token": API_KEY}

campionati = {
    "SA": {"nome": "Campionato Italiano (Serie A)", "bandiera": "🇮🇹"},
    "PL": {"nome": "Campionato Inglese (Premier League)", "bandiera": "🇬🇧"},
    "PD": {"nome": "Campionato Spagnolo (La Liga)", "bandiera": "🇪🇸"},
    "BL1": {"nome": "Campionato Tedesco (Bundesliga)", "bandiera": "🇩🇪"},
    "FL1": {"nome": "Campionato Francese (Ligue 1)", "bandiera": "🇫🇷"},
    "CL": {"nome": "UEFA Champions League", "bandiera": "🇪🇺"},
}

st.title("⚽ Centro Analisi Calcio Pro")
st.markdown(
    "Piattaforma professionale con analisi multi-stagione, Risultato Esatto,"
    " Over/Under, Gol/No Gol, Gol 1° Tempo, Rigori e marcatori."
)
st.markdown("---")

if "archivio_partite_globali" not in st.session_state:
  st.session_state.archivio_partite_globali = []
if "ultimo_report" not in st.session_state:
  st.session_state.ultimo_report = []
if "campionati_analizzati" not in st.session_state:
  st.session_state.campionati_analizzati = set()

# --- CREAZIONE DELLE SCHEDE (TABS) ---
tab1, tab2, tab3 = st.tabs(
    ["📊 Analisi Turno & Giocatori", "🎟️ Schedina Vincente", "ℹ️ Info & Guide"]
)

with tab1:
  st.subheader("🌍 Seleziona e Analizza il Turno di Campionato")

  col1, col2, col3 = st.columns([2, 1, 1])
  with col1:
    camp_options = []
    for code, c in campionati.items():
      prefix = "✔️ " if code in st.session_state.campionati_analizzati else ""
      camp_options.append((code, f"{prefix}{c['bandiera']} {c['nome']}"))

    league_code = st.selectbox(
        "Campionato:",
        options=[opt[0] for opt in camp_options],
        format_func=lambda x: next(opt[1] for opt in camp_options if opt[0] == x),
    )

  selezionato = campionati[league_code]

  with col2:
    num_stagioni = st.selectbox(
        "Profondità storica:",
        options=[1, 2, 3],
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

  if btn_analizza:
    with st.spinner(
        f"⏳ Caricamento calendario e storico ({num_stagioni} stagioni) per"
        f" {selezionato['bandiera']} {selezionato['nome']}..."
    ):
      partite_finite_totali = []
      partite_future = []
      tutti_corrente = []

      # 1. Chiamata principale per le partite correnti
      url_base = (
          f"https://api.football-data.org/v4/competitions/{league_code}/matches"
      )
      try:
        resp_base = requests.get(url_base, headers=headers)
        if resp_base.status_code == 200:
          data_base = resp_base.json()
          tutti_corrente = data_base.get("matches", [])
          partite_finite_totali.extend(
              [m for m in tutti_corrente if m.get("status") == "FINISHED"]
          )
          partite_future = [
              m
              for m in tutti_corrente
              if m.get("status") in ["TIMED", "SCHEDULED", "LIVE", "IN_PLAY"]
          ]
      except Exception:
        pass

      # 2. Caricamento stagioni passate per lo storico (2025, 2024, ecc.)
      if num_stagioni > 1:
        anni_passati = [2025, 2024, 2023]
        for idx in range(num_stagioni - 1):
          anno_p = anni_passati[idx]
          url_season = f"https://api.football-data.org/v4/competitions/{league_code}/matches?season={anno_p}"
          try:
            resp_season = requests.get(url_season, headers=headers)
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

      # Sicurezza: Se l'API non restituisce partite future (es. pausa o fine/inizio giornata),
      # prendiamo le ultime 10 partite giocate o disponibili come turno di simulazione/analisi
      matchday_list = []
      if len(partite_future) > 0:
        prossima_giornata = partite_future[0].get("matchday", 1)
        matchday_list = [
            m for m in partite_future if m.get("matchday") == prossima_giornata
        ]
        if not matchday_list:
          matchday_list = partite_future[:10]
      else:
        # Fallback: se non ci sono match futuri nell'immediato, prendiamo le ultime 10 della lista corrente
        if tutti_corrente:
          matchday_list = [
              m for m in tutti_corrente if m.get("status") == "FINISHED"
          ][-10:]
        if not matchday_list and partite_finite_totali:
          matchday_list = partite_finite_totali[-10:]

      # Calcolo medie gol complessive dallo storico unito
      if partite_finite_totali:
        media_casa = sum(
            m["score"]["fullTime"]["home"]
            for m in partite_finite_totali
            if m["score"]["fullTime"]["home"] is not None
        ) / max(1, len(partite_finite_totali))
        media_ospiti = sum(
            m["score"]["fullTime"]["away"]
            for m in partite_finite_totali
            if m["score"]["fullTime"]["away"] is not None
        ) / max(1, len(partite_finite_totali))
      else:
        media_casa, media_ospiti = 1.4, 1.1

      if len(matchday_list) > 0:

        def poisson(lmbda, k):
          return (math.exp(-lmbda) * (lmbda**k)) / math.factorial(k)

        report_giornata = []
        for match in matchday_list:
          casa = match["homeTeam"]["name"]
          ospite = match["awayTeam"]["name"]

          # Statistiche storiche specifiche della squadra di casa (su tutte le stagioni caricate)
          p_casa = [
              m for m in partite_finite_totali if m["homeTeam"]["name"] == casa
          ]
          valid_home_goals = [
              m["score"]["fullTime"]["home"]
              for m in p_casa
              if m["score"]["fullTime"]["home"] is not None
          ]
          xg_c = (
              sum(valid_home_goals) / len(valid_home_goals)
              if len(valid_home_goals) > 0
              else media_casa
          )

          # Statistiche storiche specifiche della squadra ospite (su tutte le stagioni caricate)
          p_ospite = [
              m for m in partite_finite_totali if m["awayTeam"]["name"] == ospite
          ]
          valid_away_goals = [
              m["score"]["fullTime"]["away"]
              for m in p_ospite
              if m["score"]["fullTime"]["away"] is not None
          ]
          xg_o = (
              sum(valid_away_goals) / len(valid_away_goals)
              if len(valid_away_goals) > 0
              else media_ospiti
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
          prob_rigore_si = min(0.55, max(0.22, 0.25 + (xg_c + xg_o) * 0.05))

          marcatore_casa = (
              f"Top Attaccante ({casa})"
              if xg_c > 1.3
              else f"Esterno/Centrocampista ({casa})"
          )
          marcatore_ospite = (
              f"Top Attaccante ({ospite})"
              if xg_o > 1.2
              else f"Punta Centrale ({ospite})"
          )
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
              {"mercato": "Gol (Entrambe segnano)", "prob": prob_gol},
              {"mercato": "No Gol", "prob": prob_nogol},
              {"mercato": "Gol 1°T Sì", "prob": prob_gol_1t},
              {"mercato": "Rigore Sì", "prob": prob_rigore_si},
          ]

          miglior_scelta = max(mercati_partita, key=lambda x: x["prob"])

          diz_partita = {
              "Campionato": f"{selezionato['bandiera']} {selezionato['nome']}",
              "Codice": league_code,
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
              "🔍 Marcatore Probabile": (
                  f"{marcatore_casa} / {marcatore_ospite}"
              ),
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
            f" {selezionato['nome']} (Analizzate {len(matchday_list)} partite"
            f" usando {len(partite_finite_totali)} incontri storici totali)!"
        )
        st.rerun()
      else:
        st.warning(
            "⚠️ Nessuna partita disponibile per l'analisi in questo momento."
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

  col_s1, col_s2 = st.columns(2)

  with col_s1:
    tipo_schedina = st.selectbox(
        "Seleziona ambito campionati:",
        options=["misti", "singolo"],
        format_func=lambda x: (
            "🌍 Tutti i Campionati Analizzati"
            if x == "misti"
            else "⭐ Campionato Singolo"
        ),
    )

  schedina_code = league_code
  if tipo_schedina == "singolo":
    with col_s2:
      schedina_code = st.selectbox(
          "Scegli campionato:",
          options=[opt[0] for opt in camp_options],
          format_func=lambda x: next(
              opt[1] for opt in camp_options if opt[0] == x
          ),
          key="sel_schedina_singola",
      )

  st.markdown("#### 🎯 Scegli i mercati da includere nella schedina:")
  opzioni_mercato = st.multiselect(
      "Seleziona una o più categorie di scommessa (lascia vuoto per includere"
      " tutto):",
      options=[
          "1X2",
          "Over/Under 1.5",
          "Over/Under 2.5",
          "Gol / No Gol",
          "Gol 1° Tempo",
          "Rigore",
      ],
      default=["1X2", "Over/Under 1.5", "Over/Under 2.5", "Gol / No Gol"],
  )

  num_eventi = st.slider("Numero di eventi in schedina:", 1, 15, 4)

  if st.button("🚀 Genera Schedina Personalizzata", type="primary"):
    if not st.session_state.archivio_partite_globali:
      st.warning(
          "⚠️ Analizza prima almeno un campionato nella scheda precedente!"
      )
    else:
      pool = st.session_state.archivio_partite_globali
      if tipo_schedina == "singolo":
        pool = [p for p in pool if p["Codice"] == schedina_code]

      if not pool:
        st.warning("⚠️ Nessun dato disponibile per i filtri selezionati.")
      else:
        eventi_filtrati = []
        for partita in pool:
          for m in partita.get("_tutti_i_mercati", []):
            nome_m = m["mercato"]
            prob_m = m["prob"]

            Includi = False
            if not opzioni_mercato:
              Includi = True
            else:
              if "1X2" in opzioni_mercato and "1X2:" in nome_m:
                Includi = True
              if "Over/Under 1.5" in opzioni_mercato and (
                  "Over 1.5" in nome_m or "Under 1.5" in nome_m
              ):
                Includi = True
              if "Over/Under 2.5" in opzioni_mercato and (
                  "Over 2.5" in nome_m or "Under 2.5" in nome_m
              ):
                Includi = True
              if "Gol / No Gol" in opzioni_mercato and (
                  "Gol (Entrambe segnano)" in nome_m or "No Gol" in nome_m
              ):
                Includi = True
              if "Gol 1° Tempo" in opzioni_mercato and "Gol 1°T" in nome_m:
                Includi = True
              if "Rigore" in opzioni_mercato and "Rigore" in nome_m:
                Includi = True

            if Includi:
              eventi_filtrati.append({
                  "Campionato": partita["Campionato"],
                  "Incontro": partita["Incontro"],
                  "Mercato": nome_m,
                  "Prob": prob_m,
              })

        if not eventi_filtrati:
          st.warning(
              "⚠️ Nessun evento trovato con i filtri di mercato selezionati."
          )
        else:
          eventi_filtrati = sorted(
              eventi_filtrati, key=lambda x: x["Prob"], reverse=True
          )

          scelta = []
          partite_aggiunte = set()
          for ev in eventi_filtrati:
            if ev["Incontro"] not in partite_aggiunte:
              scelta.append(ev)
              partite_aggiunte.add(ev["Incontro"])
            if len(scelta) >= num_eventi:
              break

          scelta = scelta[:num_eventi]

          prob_totale = 1.0
          righe = ""
          for i, ev in enumerate(scelta, 1):
            p_perc = ev["Prob"] * 100
            prob_totale *= ev["Prob"]
            righe += f"<tr><td><b>#{i}</b></td><td>{ev['Campionato']}</td><td><b>{ev['Incontro']}</b></td><td><span style='color: #27ae60; font-weight: bold;'>{ev['Mercato']}</span> ({p_perc:.1f}%)</td></tr>"

          st.markdown(
              f"""
            <div style="background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-top: 4px solid #27ae60;">
                <h3 style="color: #2c3e50; text-align: center;">🎟️ Schedina Personalizzata ({len(scelta)} Eventi)</h3>
                <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                    <thead>
                        <tr style="background-color: #f1f2f6; text-align: left;">
                            <th style="padding: 8px;">N°</th>
                            <th style="padding: 8px;">Campionato</th>
                            <th style="padding: 8px;">Incontro</th>
                            <th style="padding: 8px;">Pronostico Selezionato</th>
                        </tr>
                    </thead>
                    <tbody>
                        {righe}
                    </tbody>
                </table>
                <div style="margin-top: 20px; padding: 12px; background-color: #e8f8f5; color: #117a65; border-radius: 8px; text-align: center; font-size: 1.1em; font-weight: bold;">
                    📊 Probabilità Matematica Combinata: {prob_totale * 100:.1f}%
                </div>
            </div>
            """,
              unsafe_allow_html=True,
          )

with tab3:
  st.subheader("ℹ️ Informazioni sull'applicazione")
  st.write(
      "Questa applicazione utilizza modelli statistici avanzati basati sulla"
      " **Distribuzione di Poisson** uniti all'analisi storica multi-stagione"
      " per stimare con maggiore precisione il Risultato Esatto, i gol attesi"
      " (xG), i corner, le ammonizioni, i marcatori, gli Over/Under e la stima"
      " del **Rigore Sì**."
  )
