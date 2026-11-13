# sesi6/app_dash_plotly.py — menampilkan chart Plotly di aplikasi Dash 
from pathlib import Path 
import pandas as pd 
import plotly.express as px 
import plotly.graph_objects as go 
from dash import Dash, html, dcc 
  
ROOT = Path(__file__).resolve().parents[1] 
df = pd.read_csv(ROOT / "data" / "customer_churn.csv", parse_dates=["signup_date"]) 
df["status"] = df["churn"].map({0: "Bertahan", 1: "Churn"}) 
WARNA = {"Bertahan": "#4C72B0", "Churn": "#C44E52"} 
  
hist = px.histogram(df, x="tenure_months", color="status", nbins=36, barmode="overlay", 
                    opacity=0.7, color_discrete_map=WARNA, template="plotly_white", 
                    labels={"tenure_months": "Tenure (bulan)", "status": "Status"}, 
                    title="Churn terkonsentrasi pada tenure pendek") 
  
# Latihan 2: scatter -> bubble chart (ukuran gelembung = jumlah panggilan ke CS)
scatter = px.scatter(df, x="tenure_months", y="monthly_charges", color="status", size="support_calls",
                     size_max=14, color_discrete_map=WARNA, opacity=0.5, template="plotly_white",
                     hover_name="customer_id",
                     hover_data=["region", "contract_type", "num_complaints", "support_calls"],
                     labels={"tenure_months": "Tenure (bulan)", "monthly_charges": "Tagihan (Rp)",
                             "support_calls": "Panggilan CS", "status": "Status"},
                     title="Bubble chart: ukuran = jumlah panggilan ke CS")

# Filter visual tanpa callback: tombol dropdown bawaan Plotly (updatemenus) 
bar_df = df.groupby(["region", "contract_type"], as_index=False)["churn"].mean() 
bar = px.bar(bar_df, x="region", y="churn", color="contract_type", barmode="group", 
             template="plotly_white", labels={"churn": "Churn rate", "region": "Region", 
                                              "contract_type": "Kontrak"}, 
             title="Churn rate per region dan kontrak") 
bar.update_yaxes(tickformat=".0%")
# px.bar memberi tiap trace "offsetgroup" yang memaksa batang tetap berdampingan walau barmode="stack".
# Dihapus supaya tombol Grouped/Stacked benar-benar mengubah bentuk batang.
bar.update_traces(offsetgroup=None, alignmentgroup=None)
bar.update_layout(updatemenus=[dict(type="buttons", direction="right", x=1, y=1.15, buttons=[ 
    # method="update" (bukan "relayout") agar Plotly menggambar ulang batang & menghitung ulang sumbu Y
    dict(label="Grouped", method="update", args=[{}, {"barmode": "group", "yaxis.autorange": True}]),
    dict(label="Stacked", method="update", args=[{}, {"barmode": "stack", "yaxis.autorange": True}]),
])]) 
  

# Latihan 1: bar horizontal churn rate per payment_method, urut dari tertinggi + garis rata-rata nasional
rata2 = df["churn"].mean()
pay = (df.groupby("payment_method", as_index=False)["churn"].mean()
         .sort_values("churn", ascending=True))        # ascending=True -> batang tertinggi tampil paling atas
bar_pay = px.bar(pay, x="churn", y="payment_method", orientation="h", text_auto=".1%",
                 template="plotly_white", color_discrete_sequence=["#eb6834"],
                 labels={"churn": "Churn rate", "payment_method": "Metode pembayaran"},
                 title="Churn rate per metode pembayaran")
bar_pay.update_traces(textposition="inside", insidetextanchor="start")   # label di pangkal batang, tidak menabrak garis
bar_pay.add_vline(x=rata2, line_dash="dot", line_color="#555",
                  annotation_text=f"rata-rata nasional {rata2:.1%}", annotation_position="top")
bar_pay.update_xaxes(tickformat=".0%", range=[0, max(pay["churn"].max() * 1.2, rata2 * 1.2)])

# Latihan 3: sunburst jumlah pelanggan region -> segmen -> kontrak
sun = px.sunburst(df.assign(pelanggan=1), path=["region", "segment", "contract_type"],
                  values="pelanggan", color="region", template="plotly_white",
                  title="Sunburst: jumlah pelanggan per region > segmen > kontrak")
sun.update_traces(textinfo="label+percent parent", insidetextorientation="radial")
sun.update_layout(height=520, margin=dict(t=60, l=10, r=10, b=10))

# Latihan 4: gauge churn rate keseluruhan
gauge = go.Figure(go.Indicator(
    mode="gauge+number", value=rata2 * 100, number={"suffix": "%", "valueformat": ".1f"},
    title={"text": "Churn rate keseluruhan"},
    gauge={"axis": {"range": [0, 100], "ticksuffix": "%"}, "bar": {"color": "#C44E52"},
           "steps": [{"range": [0, 20], "color": "#d6f0e4"},
                     {"range": [20, 40], "color": "#fbeec5"},
                     {"range": [40, 100], "color": "#f7d3d0"}]}))
gauge.update_layout(height=320, template="plotly_white", margin=dict(t=80, l=40, r=60, b=10))

app = Dash(__name__, title="Plotly di Dash") 
app.layout = html.Div(style={"maxWidth": "1150px", "margin": "auto", "fontFamily": "Arial"}, children=[ 
    html.H1("Interactive Visualization with Plotly"), 
    html.P("Arahkan kursor (hover), zoom dengan drag, double-click untuk reset, klik legenda untuk filter."), 
    html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "12px"}, children=[ 
        dcc.Graph(figure=hist), dcc.Graph(figure=scatter)]), 
    dcc.Graph(figure=bar, config={"displaylogo": False, 
                                  "toImageButtonOptions": {"format": "png", "scale": 2}}), 
    html.H2("Latihan"), 
    html.Div(style={"display": "grid", "gridTemplateColumns": "3fr 2fr", "gap": "12px"}, children=[ 
        dcc.Graph(id="bar-pay", figure=bar_pay), dcc.Graph(id="gauge", figure=gauge)]), 
    dcc.Graph(id="sunburst", figure=sun), 
    html.Div(style={"background": "#f7f7f5", "padding": "12px 16px", "borderRadius": "8px"}, children=[ 
        html.B("Cara membaca sunburst"), 
        html.Ul([ 
            html.Li("Lingkaran dalam = region, cincin tengah = segmen, cincin luar = jenis kontrak."), 
            html.Li("Persen pada label = porsi irisan terhadap induknya (mis. Retail 63% = 63% pelanggan Jawa adalah Retail)."), 
            html.Li("Besar sudut sebuah irisan = jumlah pelanggan di kelompok itu; hover untuk melihat angkanya."), 
            html.Li("Irisan di cincin luar selalu berada di dalam sudut induknya, jadi totalnya selalu sama dengan induk."), 
            html.Li("Klik sebuah irisan untuk zoom ke cabang itu; klik bagian tengah untuk kembali."), 
        ]), 
    ]), 
]) 
  
if __name__ == "__main__": 
    app.run(debug=False, port=8051) 