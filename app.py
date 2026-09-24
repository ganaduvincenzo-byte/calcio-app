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
    "Piattaforma professionale con Gol/No Gol, Gol 1° Tempo, Rigori,"
    " marcatori e cartellini."
)
st.markdown("---")

if "archivio_partite_globali" not in st.session_state:
  st.session_state.archivio_partite_globali = []
if "ultimo_report" not in st.session_state:
  st.session_state.ultimo_report = []

# --- CREAZIONE DELLE SCHEDE (TABS) ---
tab1, tab2, tab3 = st.tabs(
    ["📊 Analisi Turno & Giocatori", "🎟️ Schedina Vincente", "ℹ️ Info & Guide"]
)

with tab1:
  st.subheader("🌍 Seleziona e Analizza il Turno di Campionato")

  col1, col2 = st.columns([3, 1])
  with col1:
    camp_options = [
        (code, f"{c['bandiera']} {c['nome']}") for code, c in campionati.items()
    ]
    league_code = st.selectbox(
        "Campionato:",
        options=[opt[0] for opt in camp_options],
        format_func=lambda x: next(opt[1] for opt in camp_options if opt[0] == x),
    )

  selezionato = campionati[league_code]

  with col2:
    st.write("")
    st.write("")
    btn_analizza = st.button(
        "📊 Avvia Analisi", type="primary", use_container_width=True
    )

  if btn_analizza:
    with st.spinner(
        f"⏳ Elaborazione dati avanzati per {selezionato['bandiera']}"
        f" {selezionato['nome']}..."
    ):
      url_matches = (
          f"https://api.football-data.org/v4/competitions/{league_code}/matches"
      )
      try:
        response = requests.get(url_matches, headers=headers)
        if response.status_code == 200:
          data = response.json()
          partite_finite = [
              m for m in data.get("matches", []) if m.get("status") == "FINISHED"
          ]
          partite_future = [
              m
              for m in data.get("matches", [])
              if m.get("status") in ["TIMED", "SCHEDULED"]
          ]

          if len(partite_finite) > 0:
            media_casa = sum(
                m["score"]["fullTime"]["home"] for m in partite_finite
            ) / len(partite_finite)
            media_ospiti = sum(
                m["score"]["fullTime"]["away"] for m in partite_finite
            ) / len(partite_finite)
          else:
            media_casa, media_ospiti = 1.4, 1.1

          if len(partite_future) > 0:
            prossima_giornata = partite_future[0].get("matchday", 1)
            matchday_list = [
                m
                for m in partite_future
                if m.get("matchday") == prossima_giornata
            ]
            if not matchday_list:
              matchday_list = partite_future[:10]

            def poisson(lmbda, k):
              return (math.exp(-lmbda) * (lmbda**k)) / math.factorial(k)

            report_giornata = []
            for match in matchday_list:
              casa = match["homeTeam"]["name"]
              ospite = match["awayTeam"]["name"]

              p_casa = [
                  m for m in partite_finite if m["homeTeam"]["name"] == casa
              ]
              xg_c = (
                  sum(m["score"]["fullTime"]["home"] for m in p_casa)
                  / len(p_casa)
                  if len(p_casa) > 0
                  else media_casa
              )

              p_ospite = [
                  m for m in partite_finite if m["awayTeam"]["name"] == ospite
              ]
              xg_o = (
                  sum(m["score"]["fullTime"]["away"] for m in p_ospite)
                  / len(p_ospite)
                  if len(p_ospite) > 0
                  else media_ospiti
              )

              prob_1, prob_x, prob_2, prob_over = 0, 0, 0, 0
              prob_gol = 0
              for g_casa in range(6):
                for g_ospite in range(6):
                  p = poisson(xg_c, g_casa) * poisson(xg_o, g_ospite)
                  if g_casa > g_ospite:
                    prob_1 += p
                  elif g_casa == g_ospite:
                    prob_x += p
                  else:
                    prob_2 += p
                  if (g_casa + g_ospite) > 2.5:
                    prob_over += p
                  if g_casa > 0 and g_ospite > 0:
                    prob_gol += p

              prob_under = 1.0 - prob_over
              prob_nogol = 1.0 - prob_gol

              # Calcolo Gol 1° Tempo (basato sul 42% dei gol totali attesi nel primo tempo)
              xg_c_1t, xg_o_1t = xg_c * 0.42, xg_o * 0.42
              prob_gol_1t = 1 - (poisson(xg_c_1t, 0) * poisson(xg_o_1t, 0))

              # Stima Rigore Sì / No basata su xG e pericolosità offensiva
              # (in media circa il 28-35% delle partite in Europa ha almeno un rigore)
              stimacorner = round(8.5 + (xg_c + xg_o) * 0.8, 1)
              diff_forza = abs(xg_c - xg_o)
              stima_cartellini = max(3.8, round(5.2 - (diff_forza * 0.5), 1))
              prob_rigore_si = min(
                  0.55, max(0.22, 0.25 + (xg_c + xg_o) * 0.05)
              )

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

              mercati_disponibili = [
                  {"mercato": f"Casa ({casa})", "prob": prob_1},
                  {"mercato": f"Ospite ({ospite})", "prob": prob_2},
                  {"mercato": "Over 2.5", "prob": prob_over},
                  {"mercato": "Gol (Entrambe segnano)", "prob": prob_gol},
                  {"mercato": "Gol 1°T Sì", "prob": prob_gol_1t},
                  {
                      "mercato": "Rigore Sì",
                      "prob": prob_rigore_si,
                  },
              ]
              miglior_scelta = max(
                  mercati_disponibili, key=lambda x: x["prob"]
              )

              diz_partita = {
                  "Campionato": f"{selezionato['bandiera']} {selezionato['nome']}",
                  "Codice": league_code,
                  "Incontro": f"{casa} - {ospite}",
                  "1 (%)": f"{prob_1 * 100:.1f}%",
                  "X (%)": f"{prob_x * 100:.1f}%",
                  "2 (%)": f"{prob_2 * 100:.1f}%",
                  "Over 2.5 (%)": f"{prob_over * 100:.1f}%",
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

            st.session_state.ultimo_report = report_giornata
            st.success(
                f"✅ Analisi completata per {selezionato['bandiera']}"
                f" {selezionato['nome']} (Turno {prossima_giornata})!"
            )
          else:
            st.warning("⚠️ Nessuna partita futura trovata.")
        else:
          st.error(f"⚠️ Errore di accesso API ({response.status_code}).")
      except Exception as e:
        st.error(f"⚠️ Errore imprevisto: {e}")

  if st.session_state.get("ultimo_report"):
    df_report = pd.DataFrame(st.session_state.ultimo_report)
    display_cols = [
        c
        for c in df_report.columns
        if not c.startswith("_") and c not in ["Campionato", "Codice"]
    ]
    st.markdown("### 📋 Tabella Dettagliata & Statistiche Avanzate")
    st.dataframe(df_report[display_cols], use_container_width=True)

with tab2:
  st.subheader("🎟️ Generatore Schedina Intelligente")

  tipo_schedina = st.selectbox(
      "Seleziona modalità:",
      options=["misti", "singolo"],
      format_func=lambda x: (
          "🌍 Tutti i Campionati Analizzati"
          if x == "misti"
          else "⭐ Campionato Singolo"
      ),
  )

  schedina_code = league_code
  if tipo_schedina == "singolo":
    schedina_code = st.selectbox(
        "Scegli campionato:",
        options=[opt[0] for opt in camp_options],
        format_func=lambda x: next(opt[1] for opt in camp_options if opt[0] == x),
        key="sel_schedina_singola",
    )

  num_eventi = st.slider("Numero di eventi in schedina:", 1, 15, 4)

  if st.button("🚀 Genera Schedina Top", type="primary"):
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
        ordinate = sorted(pool, key=lambda x: x["_miglior_prob"], reverse=True)
        scelta = ordinate[:num_eventi]

        prob_totale = 1.0
        righe = ""
        for i, ev in enumerate(scelta, 1):
          p_perc = ev["_miglior_prob"] * 100
          prob_totale *= ev["_miglior_prob"]
          righe += f"<tr><td><b>#{i}</b></td><td>{ev['Campionato']}</td><td><b>{ev['Incontro']}</b></td><td><span style='color: #27ae60; font-weight: bold;'>{ev['_miglior_mercato']}</span> ({p_perc:.1f}%)</td></tr>"

        st.markdown(
            f"""
        <div style="background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-top: 4px solid #27ae60;">
            <h3 style="color: #2c3e50; text-align: center;">🎟️ Schedina Consigliata ({len(scelta)} Eventi)</h3>
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                <thead>
                    <tr style="background-color: #f1f2f6; text-align: left;">
                        <th style="padding: 8px;">N°</th>
                        <th style="padding: 8px;">Campionato</th>
                        <th style="padding: 8px;">Incontro</th>
                        <th style="padding: 8px;">Pronostico Top</th>
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
      " **Distribuzione di Poisson** per stimare i gol attesi (xG), i corner,"
      " le ammonizioni, i marcatori probabili, il Gol 1° Tempo e la stima del"
      " **Rigore Sì** per ogni match."
  )
