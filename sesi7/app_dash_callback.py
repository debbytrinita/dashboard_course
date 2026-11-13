# sesi7/app_dash_callback.py — sistem callback Dash: filter -> KPI, chart, tabel
from pathlib import Path
import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc, dash_table, Input, Output, State, callback, ctx, no_update
from dash.exceptions import PreventUpdate

ROOT = Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "data" / "customer_churn.csv", parse_dates=["signup_date"])
df["status"] = df["churn"].map({0: "Bertahan", 1: "Churn"})
WARNA = {"Bertahan": "#4C72B0", "Churn": "#C44E52"}
KARTU = {"flex": 1, "padding": "14px", "borderRadius": "10px", "background": "#F4F6FA",
         "textAlign": "center"}
TABEL_COLS = ["customer_id", "region", "segment", "contract_type", "tenure_months",
              "monthly_charges", "num_complaints", "status"]
INTERNET = sorted(df.internet_service.unique())

app = Dash(__name__, title="Dash Callback")
server = app.server                                  # dipakai WSGI (PythonAnywhere/gunicorn)
app.layout = html.Div(style={"maxWidth": "1200px", "margin": "auto", "fontFamily": "Arial"}, children=[
    html.H1("Dash Callback System — Dashboard Churn"),

    # ---- Panel filter ----
    html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr 1fr 1fr", "gap": "16px"}, children=[
        html.Div([html.Label("Region"),
                  dcc.Dropdown(id="dd-region", options=sorted(df.region.unique()), multi=True,
                               placeholder="Semua region")]),
        html.Div([html.Label("Segmen (opsi bergantung region)"),
                  dcc.Dropdown(id="dd-segment", multi=True, placeholder="Semua segmen")]),
        html.Div([html.Label("Jenis kontrak"),
                  dcc.RadioItems(id="rd-kontrak", inline=True, value="Semua",
                                 options=["Semua", "Bulanan", "Tahunan", "Dua Tahun"])]),
        # Latihan 1: checklist internet_service
        html.Div([html.Label("Internet service"),
                  dcc.Checklist(id="cl-internet", options=INTERNET, value=INTERNET,
                                labelStyle={"display": "block"})]),
    ]),
    html.Div(style={"marginTop": "12px"}, children=[
        html.Label("Tenure (bulan)"),
        dcc.RangeSlider(id="rs-tenure", min=1, max=72, step=1, value=[1, 72],
                        marks={i: str(i) for i in (1, 12, 24, 36, 48, 60, 72)}),
    ]),
    html.Div(style={"display": "flex", "gap": "8px", "alignItems": "center"}, children=[
        html.Label("Minimal jumlah keluhan:"),
        dcc.Input(id="in-keluhan", type="number", min=0, max=10, value=0, style={"width": "70px"}),
        html.Button("Terapkan", id="btn-terapkan", n_clicks=0),
        html.Button("Reset filter", id="btn-reset", n_clicks=0),
        html.Span(id="info-keluhan", style={"color": "#666"}),
    ]),
    dcc.Store(id="store-keluhan", data=0),
    # Latihan 4: hasil filter disimpan sekali di sini, lalu dibaca callback tabel
    dcc.Store(id="store-data"),

    # ---- KPI ----
    html.Div(id="kpi", style={"display": "flex", "gap": "12px", "margin": "16px 0"}),

    # ---- Charts ----
    html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "12px"}, children=[
        dcc.Graph(id="g-bar"), dcc.Graph(id="g-scatter")]),
    html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "12px"}, children=[
        dcc.Graph(id="g-hist", style={"height": "380px"}),        # Latihan 2 (tinggi eksplisit)
        html.Div(id="detail-pelanggan",                           # Latihan 3
                 style={"padding": "16px", "borderRadius": "10px", "background": "#F4F6FA",
                        "alignSelf": "start"})]),
    html.P("Tip: klik batang region untuk memfilter tabel; klik satu titik scatter untuk melihat detail "
           "pelanggan; drag (box/lasso) pada scatter untuk memfilter tabel dengan titik terpilih.",
           style={"color": "#666"}),
    html.H3(id="judul-tabel"),
    dash_table.DataTable(id="tbl", page_size=10, sort_action="native",
                         columns=[{"name": c, "id": c} for c in TABEL_COLS],
                         style_cell={"padding": "6px", "textAlign": "left"},
                         style_header={"fontWeight": "bold", "background": "#E9EDF5"},
                         style_data_conditional=[{"if": {"filter_query": "{status} = 'Churn'"},
                                                  "backgroundColor": "#FBE9EA"}]),
])


def filter_df(region, segment, kontrak, tenure, min_keluhan, internet=None):
    d = df
    if region:
        d = d[d.region.isin(region)]
    if segment:
        d = d[d.segment.isin(segment)]
    if kontrak and kontrak != "Semua":
        d = d[d.contract_type == kontrak]
    if internet is not None:                      # checklist kosong -> tidak ada data
        d = d[d.internet_service.isin(internet)]
    d = d[d.tenure_months.between(tenure[0], tenure[1])]
    return d[d.num_complaints >= (min_keluhan or 0)]


# 1) Chained callback: opsi segmen bergantung pada region terpilih
@callback(Output("dd-segment", "options"), Input("dd-region", "value"))
def update_segment_options(region):
    d = df[df.region.isin(region)] if region else df
    return sorted(d.segment.unique())


# 2) State + tombol: nilai keluhan baru dipakai setelah tombol diklik; ctx untuk tombol mana
@callback(Output("store-keluhan", "data"), Output("in-keluhan", "value"),
          Output("dd-region", "value"), Output("dd-segment", "value"),
          Output("rd-kontrak", "value"), Output("rs-tenure", "value"),
          Output("cl-internet", "value"),
          Input("btn-terapkan", "n_clicks"), Input("btn-reset", "n_clicks"),
          State("in-keluhan", "value"), prevent_initial_call=True)
def terapkan_atau_reset(n_apply, n_reset, nilai):
    if ctx.triggered_id == "btn-reset":
        return 0, 0, None, None, "Semua", [1, 72], INTERNET
    if nilai is None:
        raise PreventUpdate                       # input kosong: jangan ubah apa pun
    return nilai, no_update, no_update, no_update, no_update, no_update, no_update


# 3) Callback utama: banyak input -> banyak output (kini 5 output, termasuk histogram)
@callback(Output("kpi", "children"), Output("g-bar", "figure"), Output("g-scatter", "figure"),
          Output("info-keluhan", "children"), Output("g-hist", "figure"),
          Input("dd-region", "value"), Input("dd-segment", "value"), Input("rd-kontrak", "value"),
          Input("rs-tenure", "value"), Input("store-keluhan", "data"), Input("cl-internet", "value"))
def update_dashboard(region, segment, kontrak, tenure, min_keluhan, internet):
    d = filter_df(region, segment, kontrak, tenure, min_keluhan, internet)
    info = f"Filter keluhan aktif: ≥ {min_keluhan}"
    if d.empty:
        kosong = px.scatter(title="Tidak ada data untuk filter ini")
        return [html.Div("Data kosong", style=KARTU)], kosong, kosong, info, kosong

    def kartu(j, v):
        return html.Div([html.Small(j), html.H2(v, style={"margin": "4px 0"})], style=KARTU)
    kpi = [kartu("Pelanggan", f"{len(d):,}"), kartu("Churn rate", f"{d.churn.mean():.1%}"),
           kartu("Rata-rata tagihan", f"Rp{d.monthly_charges.mean():,.0f}".replace(",", ".")),
           kartu("Rata-rata keluhan", f"{d.num_complaints.mean():.2f}")]
    reg = d.groupby("region", as_index=False)["churn"].mean().sort_values("churn", ascending=False)
    bar = px.bar(reg, x="region", y="churn", template="plotly_white", title="Churn rate per region",
                 labels={"churn": "Churn rate", "region": ""}, color_discrete_sequence=["#C44E52"])
    bar.update_yaxes(tickformat=".0%")
    sc = px.scatter(d, x="tenure_months", y="monthly_charges", color="status", opacity=0.6,
                    color_discrete_map=WARNA, template="plotly_white", hover_name="customer_id",
                    custom_data=["customer_id"],
                    title="Tenure vs tagihan", labels={"tenure_months": "Tenure (bulan)",
                                                       "monthly_charges": "Tagihan (Rp)"})
    sc.update_layout(dragmode="select")           # drag = box select (lasso ada di toolbar)
    hist = px.histogram(d, x="tenure_months", color="status", barmode="overlay", nbins=36,
                        opacity=0.7, color_discrete_map=WARNA, template="plotly_white",
                        title="Distribusi tenure (ikut terfilter)",
                        labels={"tenure_months": "Tenure (bulan)", "status": "Status"})
    hist.update_layout(height=380, margin=dict(t=60, l=50, r=20, b=50), yaxis_title="Jumlah pelanggan")
    return kpi, bar, sc, info, hist


# 4) Latihan 4: hitung hasil filter SEKALI, simpan ke dcc.Store (records)
@callback(Output("store-data", "data"),
          Input("dd-region", "value"), Input("dd-segment", "value"), Input("rd-kontrak", "value"),
          Input("rs-tenure", "value"), Input("store-keluhan", "data"), Input("cl-internet", "value"))
def simpan_hasil_filter(region, segment, kontrak, tenure, min_keluhan, internet):
    d = filter_df(region, segment, kontrak, tenure, min_keluhan, internet)
    return d[TABEL_COLS].to_dict("records")


# 5) Tabel membaca dari store; klik batang (region) atau seleksi scatter (box/lasso) menyaringnya
@callback(Output("tbl", "data"), Output("judul-tabel", "children"),
          Input("store-data", "data"), Input("g-bar", "clickData"), Input("g-scatter", "selectedData"))
def update_tabel(data, click, selected):
    d = pd.DataFrame(data or [], columns=TABEL_COLS)
    judul = "Detail pelanggan (semua hasil filter)"
    if ctx.triggered_id == "g-bar" and click:
        reg = click["points"][0]["x"]
        d = d[d.region == reg]
        judul = f"Detail pelanggan — region {reg}"
    elif ctx.triggered_id == "g-scatter" and selected and selected.get("points"):
        ids = [p["customdata"][0] for p in selected["points"]]
        d = d[d.customer_id.isin(ids)]
        judul = f"Detail pelanggan — {len(d):,} titik terpilih di scatter"
    return d.to_dict("records"), judul


# 6) Latihan 3: klik satu titik scatter -> tampilkan detail pelanggan
@callback(Output("detail-pelanggan", "children"), Input("g-scatter", "clickData"))
def detail_pelanggan(click):
    if not click:
        return html.Div("Klik satu titik pada scatter untuk melihat detail pelanggan.",
                        style={"color": "#666"})
    cid = click["points"][0]["customdata"][0]
    r = df[df.customer_id == cid].iloc[0]
    baris = [("ID pelanggan", r.customer_id), ("Region", r.region), ("Jenis kontrak", r.contract_type),
             ("Jumlah keluhan", r.num_complaints), ("Status", r.status)]
    return [html.H4("Detail pelanggan", style={"marginTop": 0})] + \
           [html.Div([html.B(f"{k}: "), str(v)]) for k, v in baris]


if __name__ == "__main__":
    app.run(debug=False, port=8052)
