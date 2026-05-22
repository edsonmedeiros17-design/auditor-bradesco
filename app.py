import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
import io
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    st.error("Erro: A biblioteca 'openpyxl' não está instalada. Certifique-se de incluir 'openpyxl' no seu arquivo requirements.txt.")

# --- 1. CONFIGURAÇÃO E ESTILO QUIET LUXURY ---
st.set_page_config(page_title="Edson Medeiros | Consultoria de Ativos", layout="wide", page_icon="⚖️")

st.markdown("""
<style>
    /* Importação de Fontes Premium */
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Inter:wght@300;400;600&family=Great+Vibes&display=swap');

    /* Variáveis de Cores Quiet Luxury */
    :root {
        --navy-deep: #001F3F;
        --off-white: #F8F4E6;
        --bege-fendi: #D2B48C;
        --dourado-matte: #BFAF83;
        --cinza-chumbo: #2C3E50;
        --cinza-quente: #A8A29E;
    }

    /* Reset e Fundo */
    .stApp {
        background-color: var(--navy-deep);
        color: var(--off-white);
        font-family: 'Inter', sans-serif;
        line-height: 1.6;
    }

    /* Títulos e Tipografia Serif Pura */
    h1, h2, h3 {
        font-family: 'Playfair Display', serif !important;
        font-weight: 400 !important;
        letter-spacing: -0.02em;
    }

    .main-title {
        font-size: 3.5rem;
        color: var(--off-white);
        text-align: center;
        margin-top: 2rem;
        margin-bottom: 0.5rem;
        animation: fadeIn 1s ease-in;
    }

    .sub-title {
        text-align: center;
        color: var(--dourado-matte);
        letter-spacing: 4px;
        text-transform: uppercase;
        font-size: 0.75rem;
        font-weight: 600;
        margin-bottom: 4rem;
        opacity: 0.8;
    }

    /* Cards de Métricas (Estilo Banco Suíço) */
    .metric-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(191, 175, 131, 0.15);
        border-radius: 8px;
        padding: 2.5rem;
        text-align: center;
        transition: transform 0.4s cubic-bezier(0.165, 0.84, 0.44, 1), box-shadow 0.4s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }

    .metric-card:hover {
        transform: translateY(-4px);
        border-color: var(--dourado-matte);
        background: rgba(255, 255, 255, 0.04);
    }

    .metric-card h4 {
        color: var(--cinza-quente);
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 1rem;
    }

    .metric-card h2 {
        color: var(--dourado-matte);
        font-size: 2.2rem;
        margin: 0;
    }

    /* Botões de Luxo Discreto */
    .stButton > button {
        background-color: transparent !important;
        color: var(--dourado-matte) !important;
        border: 1px solid var(--dourado-matte) !important;
        padding: 0.6rem 2rem !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.8rem !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
        border-radius: 4px !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button:hover {
        background-color: var(--dourado-matte) !important;
        color: var(--navy-deep) !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(191, 175, 131, 0.2);
    }

    /* Estilo para Download Buttons (específico do Streamlit) */
    div[data-testid="stDownloadButton"] button {
        background-color: rgba(191, 175, 131, 0.05) !important;
        border: 1px solid var(--dourado-matte) !important;
        color: var(--dourado-matte) !important;
        width: 100%;
    }

    /* Sidebar Minimalista */
    [data-testid="stSidebar"] {
        background-color: #001830;
        border-right: 1px solid rgba(191, 175, 131, 0.1);
    }

    /* Dataframe e Tabelas */
    .stDataFrame {
        border: 1px solid rgba(191, 175, 131, 0.1) !important;
        border-radius: 8px !important;
    }

    /* Footer e Branding */
    .footer-divider {
        border-top: 1px solid rgba(191, 175, 131, 0.1);
        margin-top: 5rem;
        margin-bottom: 1.5rem;
    }

    .footer-text {
        text-align: right;
        font-family: 'Great Vibes', cursive;
        color: var(--dourado-matte);
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }

    /* Animações */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Responsividade Mobile */
    @media (max-width: 768px) {
        .main-title { font-size: 2.2rem; }
        .metric-card { padding: 1.5rem; margin-bottom: 1rem; }
    }
</style>
""", unsafe_allow_html=True)

# --- 2. RÚBRICAS ATUALIZADAS ---
RUBRICAS_MESTRE = {
    "CESTA": r"CESTA",
    "PACOTE": r"PACOTE",
    "MORA DE OPERAÇÃO": r"MORA DE OPERAÇÃO|MORA OPERACAO",
    "MORA CREDITO PESSOAL": r"MORA CREDITO PESSOAL|MORA CRED PESS",
    "MORA OPERACAO DE CREDITO": r"MORA OPERACAO DE CREDITO|MORA OPER CRED",
    "BX": r"\bBX\b",
    "PARCELA CREDITO PESSOAL": r"PARCELA CREDITO PESSOAL|PARC CRED PESS",
    "GASTOS CARTAO DE CREDITO": r"GASTOS CARTAO DE CREDITO|CARTAO DE CREDITO|GASTOS CARTAO",
    "SEGURO": r"SEGURO|SEGURADORA|SEG\b",
    "ADIANT": r"ADIANT|ADIANTAMENTO DEPOSITANTE",
    "APLIC": r"APLICACAO|APLIC\b",
    "ENCARGOS": r"ENCARGOS|ENCARGO|ENC LIMITE|LIMITE DE CRED",
    "ANUIDADE": r"ANUIDADE|CARTAO CREDITO ANUIDADE",
    "OPERACOES VENCIDAS": r"OPERACOES VENCIDAS|OPERAÇÕES VENCIDAS",
    "DIV. EM ATRASO": r"DIV\. EM ATRASO|DIVIDA EM ATRASO"
}

TERMOS_EXCLUSAO = r"TRANSF|SALDO|SDO|TRANSFERENCIA|SALARIO"

# --- 3. MOTOR COM LÓGICA DE DATA INFERIOR ---
def realizar_auditoria(arquivo, rubricas_alvo):
    resultados = []
    cesto_acumulador = []
    with pdfplumber.open(arquivo) as pdf:
        for page in pdf.pages:
            texto = page.extract_text(x_tolerance=3, y_tolerance=3)
            if not texto: continue
            linhas = texto.split('\n')
            for linha in linhas:
                linha_up = linha.upper().strip()
                if not linha_up: continue
                match_data = re.search(r"(\d{2}/\d{2}/\d{2,4})", linha_up)
                match_valor = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})(?!\s*%)", linha_up)
                if re.search(TERMOS_EXCLUSAO, linha_up):
                    cesto_acumulador = [item for item in cesto_acumulador if item["VALOR"] != "PENDENTE"]
                    continue 
                rubrica_detectada = None
                if "%" not in linha_up:
                    for nome in rubricas_alvo:
                        if re.search(RUBRICAS_MESTRE[nome], linha_up):
                            rubrica_detectada = nome
                            break
                if rubrica_detectada:
                    valor_na_linha = match_valor.group(1) if match_valor else "PENDENTE"
                    cesto_acumulador.append({"CATEGORIA": rubrica_detectada, "VALOR": valor_na_linha, "HISTÓRICO": linha_up[:80]})
                elif match_valor and cesto_acumulador:
                    if cesto_acumulador[-1]["VALOR"] == "PENDENTE":
                        cesto_acumulador[-1]["VALOR"] = match_valor.group(1)
                if match_data:
                    data_encontrada = match_data.group(1)
                    if cesto_acumulador:
                        for item in cesto_acumulador:
                            if item["VALOR"] != "PENDENTE":
                                item["DATA"] = data_encontrada
                                resultados.append(item)
                        cesto_acumulador = []
    return resultados

# --- 4. FUNÇÃO PARA GERAR PLANILHA DE CÁLCULOS ---
def gerar_excel_calculos(df, rubrica_nome):
    df = df.copy()
    def fix_date(d):
        p = d.split('/')
        if len(p[2]) == 2: p[2] = "20" + p[2]
        return "/".join(p)
    df['DT'] = pd.to_datetime(df['DATA'].apply(fix_date), format='%d/%m/%Y')
    df['ANO'] = df['DT'].dt.year
    df['MES_NUM'] = df['DT'].dt.month
    agrupado = df.groupby(['ANO', 'MES_NUM'])['V_NUM'].sum().reset_index()
    wb = Workbook()
    ws = wb.active
    ws.title = "Cálculos"
    font_header = Font(bold=True, size=11)
    fill_blue = PatternFill(start_color="BDD7EE", end_color="BDD7EE", fill_type="solid")
    fill_peach = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
    border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    ws.merge_cells('A1:E1')
    ws['A1'] = f"VALORES DESCONTADOS INDEVIDAMENTE - \"{rubrica_nome}\""
    ws['A1'].font = Font(bold=True, size=12)
    ws['A1'].fill = fill_blue
    ws['A1'].alignment = Alignment(horizontal='center')
    meses_nomes = ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
    ws['A2'] = "MESES"
    anos = sorted(agrupado['ANO'].unique()) if not agrupado.empty else [datetime.now().year]
    for idx, ano in enumerate(anos):
        col = idx + 2
        ws.cell(row=2, column=col, value=ano).font = font_header
        ws.cell(row=2, column=col).fill = fill_blue
    for m_idx, mes in enumerate(meses_nomes):
        row = m_idx + 3
        ws.cell(row=row, column=1, value=mes).fill = fill_blue
        for a_idx, ano in enumerate(anos):
            col = a_idx + 2
            val = agrupado[(agrupado['ANO'] == ano) & (agrupado['MES_NUM'] == m_idx + 1)]['V_NUM'].sum()
            cell = ws.cell(row=row, column=col, value=val if val > 0 else 0)
            cell.number_format = '"R$ " #,##0.00'
            cell.fill = fill_peach
            cell.border = border
    row_anual = 15
    ws.cell(row=row_anual, column=1, value="VALOR ANUAL:").fill = fill_blue
    for idx, ano in enumerate(anos):
        col = idx + 2
        col_letter = get_column_letter(col)
        cell = ws.cell(row=row_anual, column=col, value=f"=SUM({col_letter}3:{col_letter}14)")
        cell.number_format = '"R$ " #,##0.00'
        cell.fill = fill_peach
        cell.border = border
    row_total = 16
    ws.cell(row=row_total, column=1, value="VALOR TOTAL:").fill = fill_blue
    last_col = get_column_letter(len(anos) + 1)
    ws.merge_cells(start_row=row_total, start_column=2, end_row=row_total, end_column=len(anos)+1)
    cell_total = ws.cell(row=row_total, column=2, value=f"=SUM(B{row_anual}:{last_col}{row_anual})")
    cell_total.number_format = '"R$ " #,##0.00'
    row_dobro = 17
    ws.cell(row=row_dobro, column=1, value="VALOR EM DOBRO ART. 42 DO CDC").fill = fill_blue
    ws.merge_cells(start_row=row_dobro, start_column=2, end_row=row_dobro+1, end_column=len(anos)+1)
    cell_dobro = ws.cell(row=row_dobro, column=2, value=f"=B{row_total}*2")
    cell_dobro.number_format = '"R$ " #,##0.00'
    cell_dobro.fill = fill_peach
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()

# --- 5. DASHBOARD ---
st.markdown('<h1 class="main-title">Edson Medeiros</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Consultoria de Ativos | Auditoria Técnica</p>', unsafe_allow_html=True)

# Sidebar Minimalista
st.sidebar.markdown("<h3 style='color:#BFAF83; font-size:1rem; letter-spacing:2px;'>FILTROS</h3>", unsafe_allow_html=True)
if 'sel_all' not in st.session_state: st.session_state.sel_all = True
col_b1, col_b2 = st.sidebar.columns(2)
if col_b1.button("Marcar Todas"): st.session_state.sel_all = True
if col_b2.button("Desmarcar Todas"): st.session_state.sel_all = False

selecionadas = []
for r in RUBRICAS_MESTRE.keys():
    if st.sidebar.checkbox(r, value=st.session_state.sel_all, key=f"check_{r}"):
        selecionadas.append(r)

upload = st.file_uploader("📂 ARRASTE O EXTRATO BANCÁRIO (PDF)", type=["pdf"])

if upload:
    with st.spinner("Analisando com precisão técnica..."):
        dados = realizar_auditoria(upload, selecionadas)
        if dados:
            df = pd.DataFrame(dados)
            df['V_NUM'] = df['VALOR'].str.replace('.','', regex=False).str.replace(',','.', regex=False).astype(float)
            def fix_date(d):
                p = d.split('/')
                if len(p[2]) == 2: p[2] = "20" + p[2]
                return "/".join(p)
            df['DT_O'] = pd.to_datetime(df['DATA'].apply(fix_date), format='%d/%m/%Y', errors='coerce')
            df = df.sort_values('DT_O', ascending=True)
            
            # Métricas Elegantes
            m1, m2 = st.columns(2)
            with m1: st.markdown(f'<div class="metric-card"><h4>TOTAL RECUPERÁVEL</h4><h2>R$ {df["V_NUM"].sum():,.2f}</h2></div>', unsafe_allow_html=True)
            with m2: st.markdown(f'<div class="metric-card"><h4>OCORRÊNCIAS</h4><h2>{len(df)}</h2></div>', unsafe_allow_html=True)
            
            st.markdown('<h2 style="color:#BFAF83; text-align:center; margin-top:4rem; margin-bottom:2rem;">Tabelas de Cálculos</h2>', unsafe_allow_html=True)
            
            # Grid de Botões de Download
            cats = df['CATEGORIA'].unique()
            cols = st.columns(2)
            for idx, cat in enumerate(cats):
                with cols[idx % 2]:
                    df_cat = df[df['CATEGORIA'] == cat]
                    excel_file = gerar_excel_calculos(df_cat, cat)
                    st.download_button(label=f"Baixar Tabela: {cat}", data=excel_file, file_name=f"Calculos_{cat}.xlsx", key=f"btn_{cat}")
            
            st.markdown('<h3 style="color:#BFAF83; text-align:center; margin-top:4rem; margin-bottom:2rem;">Detalhamento de Lançamentos</h3>', unsafe_allow_html=True)
            st.dataframe(df[['DATA', 'CATEGORIA', 'VALOR', 'HISTÓRICO']], use_container_width=True)
        else:
            st.info("Nenhum débito identificado com os parâmetros atuais.")

# Footer e Branding Sutil
st.markdown('<div class="footer-divider"></div>', unsafe_allow_html=True)
st.markdown('<p class="footer-text">Fundado por Edson Medeiros</p>', unsafe_allow_html=True)
