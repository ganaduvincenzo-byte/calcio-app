import requests
import pandas as pd
import math
import ipywidgets as widgets
from IPython.display import display, HTML

API_KEY = "16ecb66eb7f7454cad0506778fa7d041"
headers = {"X-Auth-Token": API_KEY}

campionati = {
    "SA": {"nome": "Campionato Italiano (Serie A)", "bandiera": "🇮🇹"},
    "PL": {"nome": "Campionato Inglese (Premier League)", "bandiera": "🇬🇧"},
    "PD": {"nome": "Campionato Spagnolo (La Liga)", "bandiera": "🇪🇸"},
    "BL1": {"nome": "Campionato Tedesco (Bundesliga)", "bandiera": "🇩🇪"},
    "FL1": {"nome": "Campionato Francese (Ligue 1)", "bandiera": "🇫🇷"},
    "CL": {"nome": "UEFA Champions League", "bandiera": "🇪🇺"}
}

archivio_partite_globali = []

# --- CREAZIONE DEI COMPONENTI GRAFICI (WIDGETS) ---
out_output = widgets.Output()

# Dropdown Campionati
camp_options = [(f"{c['bandiera']} {c['nome']}", code) for code, c in campionati.items()]
dropdown_campionati = widgets.Dropdown(
    options=camp_options,
    description='<b>Campionato:</b>',
    style={'description_width': 'initial'},
    layout=widgets.Layout(width='100%', max_width='400px')
)

btn_analizza = widgets.Button(
    description='📊 Analizza Turno',
    button_style='success',
    layout=widgets.Layout(width='200px', height='40px')
)

# Sezione Schedina
dropdown_tipo_schedina = widgets.Dropdown(
    options=[('🌍 Tutti i Campionati Misti', 'misti'), ('⭐ 1 Solo Campionato Specifico', 'singolo')],
    value='misti',
    description='<b>Tipo Schedina:</b>',
    style={'description_width': 'initial'},
    layout=widgets.Layout(width='100%', max_width='400px')
)

dropdown_schedina_singola = widgets.Dropdown(
    options=camp_options,
    description='<b>Scegli Campionato:</b>',
    style={'description_width': 'initial'},
    layout=widgets.Layout(width='100%', max_width='400px')
)

slider_eventi = widgets.IntSlider(
    value=5,
    min=1,
    max=20,
    step=1,
    description='<b>N° Eventi:</b>',
    style={'description_width': 'initial'},
    layout=widgets.Layout(width='100%', max_width='400px')
)

btn_crea_schedina = widgets.Button(
    description='🎟️ Genera Schedina',
    button_style='primary',
    layout=widgets.Layout(width='200px', height='40px')
)

# Funzione per gestire la visibilità del filtro singolo campionato nella schedina
def on_tipo_schedina_change(change):
    if change['new'] == 'singolo':
        box_schedina.children = [dropdown_tipo_schedina, dropdown_schedina_singola, slider_eventi, btn_crea_schedina]
    else:
        box_schedina.children = [dropdown_tipo_schedina, slider_eventi, btn_crea_schedina]

dropdown_tipo_schedina.observe(on_tipo_schedina_change, names='value')

# --- LOGICA DI ANALISI CAMPIONATO ---
def on_button_analizza_clicked(b):
    with out_output:
        out_output.clear_output()
        league_code = dropdown_campionati.value
        selezionato = campionati[league_code]
        
        print(f"⏳ Caricamento dati per {selezionato['bandiera']} {selezionato['nome']}...")
        url_matches = f"https://api.football-data.org/v4/competitions/{league_code}/matches"
        
        try:
            response = requests.get(url_matches, headers=headers)
            if response.status_code == 200:
                data = response.json()
                partite_finite = [m for m in data.get("matches", []) if m.get('status') == 'FINISHED']
                partite_future = [m for m in data.get("matches", []) if m.get('status') in ['TIMED', 'SCHEDULED']]
                
                if len(partite_finite) > 0:
                    media_globale_casa = sum(m['score']['fullTime']['home'] for m in partite_finite) / len(partite_finite)
                    media_globale_ospiti = sum(m['score']['fullTime']['away'] for m in partite_finite) / len(partite_finite)
                else:
                    media_globale_casa, media_globale_ospiti = 1.4, 1.1

                if len(partite_future) > 0:
                    prossima_giornata = partite_future[0].get('matchday', 1)
                    matchday_list = [m for m in partite_future if m.get('matchday') == prossima_giornata]
                    if not matchday_list:
                        matchday_list = partite_future[:10]
                    
                    def poisson(lmbda, k):
                        return (math.exp(-lmbda) * (lmbda ** k)) / math.factorial(k)
                        
                    report_giornata = []
                    for match in matchday_list:
                        casa = match['homeTeam']['name']
                        ospite = match['awayTeam']['name']
                        
                        p_casa = [m for m in partite_finite if m['homeTeam']['name'] == casa]
                        xg_c = (sum(m['score']['fullTime']['home'] for m in p_casa) / len(p_casa)) if len(p_casa) > 0 else media_globale_casa
                        
                        p_ospite = [m for m in partite_finite if m['awayTeam']['name'] == ospite]
                        xg_o = (sum(m['score']['fullTime']['away'] for m in p_ospite) / len(p_ospite)) if len(p_ospite) > 0 else media_globale_ospiti
                        
                        prob_1, prob_x, prob_2, prob_over = 0, 0, 0, 0
                        for g_casa in range(6):
                            for g_ospite in range(6):
                                p = poisson(xg_c, g_casa) * poisson(xg_o, g_ospite)
                                if g_casa > g_ospite: prob_1 += p
                                elif g_casa == g_ospite: prob_x += p
                                else: prob_2 += p
                                if (g_casa + g_ospite) > 2.5: prob_over += p
                        
                        prob_under = 1.0 - prob_over
                        xg_c_1t, xg_o_1t = xg_c * 0.42, xg_o * 0.42
                        prob_0_gol_1t = poisson(xg_c_1t, 0) * poisson(xg_o_1t, 0)
                        prob_gol_1t = (1 - prob_0_gol_1t)
                        
                        stimacorner = round(8.5 + (xg_c + xg_o) * 0.8, 1)
                        diff_forza = abs(xg_c - xg_o)
                        stima_cartellini = max(3.8, round(5.2 - (diff_forza * 0.5), 1))

                        mercati_disponibili = [
                            {"mercato": f"Casa ({casa})", "prob": prob_1},
                            {"mercato": f"Ospite ({ospite})", "prob": prob_2},
                            {"mercato": "Under 2.5", "prob": prob_under},
                            {"mercato": "Over 2.5", "prob": prob_over},
                            {"mercato": "Gol 1°T", "prob": prob_gol_1t}
                        ]
                        miglior_scelta = max(mercati_disponibili, key=lambda x: x['prob'])

                        diz_partita = {
                            "Campionato": f"{selezionato['bandiera']} {selezionato['nome']}",
                            "Codice": league_code,
                            "Incontro": f"{casa} - {ospite}",
                            "1 (%)": f"{prob_1 * 100:.1f}%",
                            "X (%)": f"{prob_x * 100:.1f}%",
                            "2 (%)": f"{prob_2 * 100:.1f}%",
                            "Over 2.5 (%)": f"{prob_over * 100:.1f}%",
                            "Gol 1T (%)": f"{prob_gol_1t * 100:.1f}%",
                            "Corner": stimacorner,
                            "Cartellini": stima_cartellini,
                            "_miglior_mercato": miglior_scelta['mercato'],
                            "_miglior_prob": miglior_scelta['prob']
                        }
                        report_giornata.append(diz_partita)
                        
                        # Aggiorna archivio globale
                        esistente = next((p for p in archivio_partite_globali if p["Incontro"] == diz_partita["Incontro"] and p.get("Codice") == league_code), None)
                        if esistente: archivio_partite_globali.remove(esistente)
                        archivio_partite_globali.append(diz_partita)
                        
                    df_report = pd.DataFrame(report_giornata)
                    display_cols = [c for c in df_report.columns if not c.startswith('_') and c != 'Campionato' and c != 'Codice']
                    html_table = df_report[display_cols].to_html(index=False, classes='modern-table', escape=False)
                    
                    styled_html = f"""
                    <div style="font-family: 'Segoe UI', sans-serif; padding: 12px; background-color: #fdfefe; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-top: 10px; overflow-x: auto;">
                        <h3 style="color: #2c3e50; border-bottom: 2px solid #1abc9c; padding-bottom: 6px; margin-top: 0;">🔥 Report {selezionato['bandiera']} {selezionato['nome']} - Turno N. {prossima_giornata}</h3>
                        {html_table}
                    </div>
                    """
                    display(HTML(styled_html))
                    print(f"\n✅ Dati caricati con successo e salvati in memoria!")
                else:
                    print("⚠️ Nessuna partita futura trovata.")
            else:
                print(f"⚠️ Errore di accesso API ({response.status_code}).")
        except Exception as e:
            print(f"⚠️ Errore imprevisto: {e}")

btn_analizza.on_click(on_button_analizza_clicked)

# --- LOGICA DI CREAZIONE SCHEDINA ---
def on_button_schedina_clicked(b):
    with out_output:
        out_output.clear_output()
        if not archivio_partite_globali:
            print("⚠️ Nessun campionato analizzato in questa sessione! Carica prima almeno un campionato.")
            return

        partite_pool = archivio_partite_globali
        if dropdown_tipo_schedina.value == 'singolo':
            cod_scelto = dropdown_schedina_singola.value
            partite_pool = [p for p in archivio_partite_globali if p['Codice'] == cod_scelto]

        if not partite_pool:
            print("⚠️ Nessuna partita disponibile per i filtri selezionati.")
            return

        num_eventi = slider_eventi.value
        partite_ordinate = sorted(partite_pool, key=lambda x: x['_miglior_prob'], reverse=True)
        schedina_scelta = partite_ordinate[:num_eventi]

        righe_html = ""
        prob_totale_combinata = 1.0
        for i, ev in enumerate(schedina_scelta, 1):
            p_perc = ev['_miglior_prob'] * 100
            prob_totale_combinata *= ev['_miglior_prob']
            righe_html += f"<tr><td><b>#{i}</b></td><td>{ev['Campionato']}</td><td><b>{ev['Incontro']}</b></td><td><span style='color: #27ae60; font-weight: bold;'>{ev['_miglior_mercato']}</span> ({p_perc:.1f}%)</td></tr>"

        html_schedina = f"""
        <div style="font-family: 'Segoe UI', sans-serif; padding: 15px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); border-radius: 12px; box-shadow: 0 6px 15px rgba(0,0,0,0.1); margin-top: 15px; overflow-x: auto;">
            <h2 style="color: #2c3e50; text-align: center; margin-bottom: 5px;">🎟️ LA TUA SCHEDINA CONSIGLIATA</h2>
            <p style="text-align: center; color: #7f8c8d; font-size: 0.9em;">Analisi di massima sicurezza ({len(schedina_scelta)} Eventi)</p>
            <table class="modern-table" style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; margin-top: 10px;">
                <thead>
                    <tr style="background-color: #2c3e50; color: white; text-align: left;">
                        <th style="padding: 8px;">N°</th>
                        <th style="padding: 8px;">Campionato</th>
                        <th style="padding: 8px;">Incontro</th>
                        <th style="padding: 8px;">Puntata Top</th>
                    </tr>
                </thead>
                <tbody>
                    {righe_html}
                </tbody>
            </table>
            <div style="margin-top: 12px; padding: 10px; background-color: #27ae60; color: white; border-radius: 6px; text-align: center; font-size: 1.1em; font-weight: bold;">
                📊 Probabilità Matematica Combinata: {prob_totale_combinata * 100:.1f}%
            </div>
        </div>
        """
        display(HTML(html_schedina))

btn_crea_schedina.on_click(on_button_schedina_clicked)

# --- STILI CSS RESPONSIVE SOTTO FORMA DI WIDGET HTML ---
css_widget = widgets.HTML("""
<style>
    .modern-table {
        border-collapse: collapse;
        width: 100%;
        font-size: 0.85em;
        background-color: white;
        border-radius: 8px;
        overflow: hidden;
    }
    .modern-table thead tr {
        background-color: #1abc9c;
        color: white;
        text-align: left;
        font-weight: 600;
    }
    .modern-table th, .modern-table td {
        padding: 8px 10px;
        border-bottom: 1px solid #edf2f7;
    }
    .modern-table tbody tr:hover {
        background-color: #f1f8f6;
    }
</style>
""")

# --- ASSEMBLAGGIO FINALE DELL'INTERFACCIA ---
box_analisi = widgets.VBox([
    widgets.HTML("<h3 style='color: #2c3e50; margin-bottom: 5px;'>🌍 1. Seleziona e Analizza Campionato</h3>"),
    dropdown_campionati,
    btn_analizza
], layout=widgets.Layout(padding='10px', border='1px solid #e2e8f0', borderRadius='8px', marginBottom='15px', backgroundColor='#fafbfc'))

box_schedina = widgets.VBox([
    widgets.HTML("<h3 style='color: #2c3e50; margin-bottom: 5px;'>🎟️ 2. Genera Schedina Personalizzata</h3>"),
    dropdown_tipo_schedina,
    slider_eventi,
    btn_crea_schedina
], layout=widgets.Layout(padding='10px', border='1px solid #e2e8f0', borderRadius='8px', backgroundColor='#fafbfc'))

interfaccia_completa = widgets.VBox([
    css_widget,
    widgets.HTML("<h2 style='color: #2c3e50; text-align: center;'>⚽ Centro Analisi Calcio - Pannello Visivo</h2>"),
    box_analisi,
    box_schedina,
    out_output
])

# Mostra l'interfaccia nella pagina
display(interfaccia_completa)
