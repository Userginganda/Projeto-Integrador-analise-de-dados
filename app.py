import altair as alt
import pandas as pd
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Dashboard | Análise de Smartphones", page_icon="📱", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
html, body, [class*="css"], [data-testid="stApp"] {font-family:'DM Sans',sans-serif;}
[data-testid="stAppViewContainer"] {background:#f6f8fc;color:#14243b;}
.block-container {max-width:1380px;padding-top:2.1rem;padding-bottom:3rem;}
[data-testid="stHeader"] {background:transparent;}
h1,h2,h3 {color:#14243b!important;letter-spacing:-.035em;}
h1 {font-size:2.15rem!important;font-weight:750!important;}
h3 {font-size:1.13rem!important;}
.hero-sub {color:#64748b;font-size:1rem;margin:-.4rem 0 1.3rem;}
.eyebrow {color:#3167d5;font-size:.78rem;font-weight:700;letter-spacing:.11em;text-transform:uppercase;margin-bottom:.3rem;}
[data-testid="stMetric"] {background:#fff;border:1px solid #e6ebf3;border-radius:16px;padding:19px 22px;box-shadow:0 4px 18px rgba(25,45,78,.035);min-height:122px;}
[data-testid="stMetricLabel"] {color:#65758c;font-weight:600;}
[data-testid="stMetricValue"] {color:#162c4c;font-weight:750;font-size:1.75rem;}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius:16px!important;background:#fff;}
[data-testid="stSelectbox"] label, [data-testid="stRadio"] label {color:#4b5e78;font-weight:600;}
hr {border-color:#e6ebf3;}
/* Padroniza controles, tabela e botao no tema claro */
[data-testid="stDataFrame"], [data-testid="stDataFrame"] > div {background:#fff!important;border-radius:12px!important;}
[data-testid="stDataFrame"] iframe {color-scheme:light!important;}
[data-testid="stDownloadButton"] button {background:#2563eb!important;color:#fff!important;border:1px solid #2563eb!important;border-radius:10px!important;padding:.65rem 1.2rem!important;font-weight:650!important;box-shadow:0 3px 10px rgba(37,99,235,.12)!important;}
[data-testid="stDownloadButton"] button:hover {background:#1d4ed8!important;border-color:#1d4ed8!important;color:#fff!important;}
[data-testid="stDownloadButton"] button p {color:#fff!important;}
[data-testid="stSelectbox"] [data-baseweb="select"] > div {background:#fff!important;color:#182b49!important;border-color:#dbe3ef!important;}

.section-caption {color:#718096;font-size:.9rem;margin:-.5rem 0 1rem;}
.note {background:#edf4ff;border-left:3px solid #4275dc;padding:13px 17px;border-radius:8px;color:#345276;font-size:.92rem;}
</style>""", unsafe_allow_html=True)

@st.cache_data
def carregar_dados():
    arquivo = Path(__file__).resolve().parent / "smartphones.csv"
    df = pd.read_csv(arquivo, encoding="utf-8-sig")
    df.columns = df.columns.str.strip()
    numericas = ["vendas_primeiro_trimestre_unidades", "nota_avaliacao_clientes", "preco_lancamento"]
    for coluna in numericas:
        if df[coluna].dtype == "object":
            texto = df[coluna].astype(str).str.strip()
            # Preserva valores decimais com ponto e aceita vírgula decimal.
            texto = texto.str.replace(",", ".", regex=False)
            df[coluna] = pd.to_numeric(texto, errors="coerce")
        else:
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce")
    return df


def numero_br(valor, casas=0):
    return f"{valor:,.{casas}f}".replace(",", "§").replace(".", ",").replace("§", ".")

try:
    dados = carregar_dados()
except (FileNotFoundError, KeyError, pd.errors.ParserError) as erro:
    st.error(f"Não foi possível carregar smartphones.csv: {erro}")
    st.stop()

st.markdown('<div class="eyebrow">Projeto Integrador · Business Intelligence</div>', unsafe_allow_html=True)
st.title("Análise de smartphones")
st.markdown('<div class="hero-sub">Campeões de vendas × melhores avaliações dos clientes · Análise comparativa do 1º trimestre</div>', unsafe_allow_html=True)

filtro1, filtro2 = st.columns([2, 1])
with filtro1:
    marcas = sorted(dados["marca"].dropna().astype(str).unique().tolist())
    marca = st.selectbox("Filtrar por marca", ["Todas as marcas"] + marcas)
with filtro2:
    limite = st.selectbox("Modelos exibidos em cada gráfico", [5, 10, 15, "Todos"], index=1)

filtrados = dados if marca == "Todas as marcas" else dados[dados["marca"] == marca]
if filtrados.empty:
    st.warning("Nenhum modelo encontrado para este filtro.")
    st.stop()

vendas = filtrados["vendas_primeiro_trimestre_unidades"].sum()
nota = filtrados["nota_avaliacao_clientes"].mean()
preco = filtrados["preco_lancamento"].mean()
k1, k2, k3 = st.columns(3)
k1.metric("Unidades vendidas · 1º trimestre", numero_br(vendas))
k2.metric("Avaliação média dos clientes", f"{numero_br(nota, 1)} / 10")
k3.metric("Preço médio de lançamento", f"US$ {numero_br(preco, 2)}")

st.markdown("### Comparativo de desempenho")
st.markdown('<div class="section-caption">Os gráficos são ordenados do maior para o menor. Passe o mouse sobre as barras para consultar os valores.</div>', unsafe_allow_html=True)

ranking_vendas = (filtrados.groupby("modelo", as_index=False)["vendas_primeiro_trimestre_unidades"].sum().sort_values("vendas_primeiro_trimestre_unidades", ascending=False))
ranking_notas = (filtrados.groupby("modelo", as_index=False)["nota_avaliacao_clientes"].mean().sort_values("nota_avaliacao_clientes", ascending=False))
if limite != "Todos":
    ranking_vendas = ranking_vendas.head(limite)
    ranking_notas = ranking_notas.head(limite)

altura = max(280, len(ranking_vendas) * 30)

def grafico(df, campo, cor, titulo_eixo, altura_grafico):
    ordem = df["modelo"].tolist()
    return (alt.Chart(df).mark_bar(color=cor, cornerRadiusEnd=5, size=17)
        .encode(y=alt.Y("modelo:N", sort=ordem, title=None, axis=alt.Axis(labelLimit=180, labelFontSize=11, labelColor="#4c5e78", ticks=False, domain=False)),
                x=alt.X(f"{campo}:Q", title=titulo_eixo, axis=alt.Axis(grid=True, gridColor="#eaf0f6", domain=False, tickColor="#eaf0f6", labelColor="#6a7a90")),
                tooltip=[alt.Tooltip("modelo:N", title="Modelo"), alt.Tooltip(f"{campo}:Q", title=titulo_eixo, format=",.2f" if campo == "nota_avaliacao_clientes" else ",.0f")])
         .properties(height=altura_grafico, background="#FFFFFF")
        .configure_view(stroke=None, fill="#FFFFFF")
        .configure_axis(labelColor="#53647d", titleColor="#334155", gridColor="#e8edf5")
        .configure(background="#FFFFFF"))

esq, dir = st.columns(2, gap="large")
with esq:
    with st.container(border=True):
        st.subheader("Modelos mais vendidos")
        st.caption("Total de unidades comercializadas no 1º trimestre")
        st.altair_chart(grafico(ranking_vendas, "vendas_primeiro_trimestre_unidades", "#3876df", "Unidades vendidas", altura), use_container_width=True)
with dir:
    with st.container(border=True):
        st.subheader("Melhores avaliações")
        st.caption("Média das notas atribuídas pelos clientes")
        st.altair_chart(grafico(ranking_notas, "nota_avaliacao_clientes", "#12a594", "Nota média (0 a 10)", max(280, len(ranking_notas)*30)), use_container_width=True)

st.markdown("### Base de dados detalhada")
st.markdown('<div class="section-caption">Todos os modelos da marca selecionada permanecem disponíveis na tabela, independentemente do limite dos gráficos.</div>', unsafe_allow_html=True)
tabela = filtrados.sort_values("vendas_primeiro_trimestre_unidades", ascending=False)
nomes_colunas = {
    "marca": "Marca", "modelo": "Modelo", "ano_lancamento": "Ano de lançamento",
    "preco_lancamento": "Preço de lançamento (US$)", "ram_gb": "RAM (GB)",
    "armazenamento_gb_opcoes": "Armazenamento (GB)", "bateria_mah": "Bateria (mAh)",
    "camera_principal_mp": "Câmera (MP)", "tela_polegadas": "Tela (pol.)",
    "vendas_primeiro_trimestre_unidades": "Vendas (1º trimestre)",
    "nota_avaliacao_clientes": "Avaliação dos clientes"
}
st.dataframe(tabela.rename(columns=nomes_colunas), use_container_width=True, hide_index=True, height=380)
col_espaco, col_botao = st.columns([3, 1])
with col_botao:
    st.download_button("⬇ Baixar dados em CSV", tabela.to_csv(index=False).encode("utf-8-sig"), "smartphones_filtrados.csv", "text/csv", use_container_width=True)
st.caption("O arquivo contém todos os modelos do filtro selecionado, inclusive os não exibidos nos gráficos.")
st.markdown('<div class="note"><strong>Como interpretar:</strong> o gráfico azul mostra volume de vendas; o verde mostra satisfação dos clientes. Um modelo pode liderar em vendas sem ter a maior avaliação. Os filtros atualizam os indicadores, gráficos e tabela.</div>', unsafe_allow_html=True)
st.caption("Fonte: smartphones.csv · Os resultados refletem exclusivamente a base fornecida para o projeto.")
