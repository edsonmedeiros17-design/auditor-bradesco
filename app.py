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

# --- 1. CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="Edson Medeiros | Consultoria de Ativos", layout="wide", page_icon="⚖️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');
    .stApp { background-color: #0E1117; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    .main-title { font-family: 'Playfair Display', serif; font-size: 3rem; color: #BFAF83; text-align: center; margin-bottom: 0; }
    .sub-title { text-align: center; color: #64748B; letter-spacing: 2px; text-transform: uppercase; font-size: 0.9rem; margin-bottom: 40px; }
    .metric-card { background: rgba(255,255,255,0.05); border: 1px solid #BFAF83; border-radius: 10px; padding: 20px; text-align: center; }
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

                # 1. Identifica Data e Valor
                match_data = re.search(r"(\d{2}/\d{2}/\d{4})", linha_up)
                match_valor = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})(?!\s*%)", linha_up)
                
                # 2. Se encontrou uma DATA, selamos o cesto acumulador
                if match_data:
                    data_encontrada = match_data.group(1)
                    if cesto_acumulador:
                        for item in cesto_acumulador:
                            item["DATA"] = data_encontrada
                            resultados.append(item)
                        cesto_acumulador = [] 
                
                # 3. Se encontrou uma RUBRICA, adicionamos ao cesto
                rubrica_detectada = None
                for nome in rubricas_alvo:
                    if re.search(RUBRICAS_MESTRE[nome], linha_up):
                        rubrica_detectada = nome
                        break
                
                if rubrica_detectada:
                    cesto_acumulador.append({
                        "CATEGORIA": rubrica_detectada,
                        "VALOR": match_valor.group(1) if match_valor else "0,00",
                        "HISTÓRICO": linha_up[:80],
                        "DATA": "PENDENTE" 
                    })
                
                # 4. Caso a linha não tenha rubrica, mas tenha valor, tenta atualizar o último item do cesto
                elif match_valor and cesto_acumulador and cesto_acumulador[-1]["VALOR"] == "0,00":
                    cesto_acumulador[-1]["VALOR"] = match_valor.group(1)

    return resultados

# --- 4. FUNÇÃO PARA GERAR PLANILHA (CORREÇÃO DE CORES aRGB) ---
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
    ws.title = "Tabela de Cálculos"
    
    # CORES EM aRGB (Prefixado com FF e sem #)
    fill_blue = PatternFill(start_color="FFABAAA9", end_color="FFABAAA9", fill_type="solid")
    fill_peach = PatternFill(start_color="FFFFFFFF", end_color="FFFFFFFF", fill_type="solid")
    font_header = Font(bold=True, size=11)
    font_title = Font(bold=True, size=12)
    border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    align_center = Alignment(horizontal='center', vertical='center')
    
    # Cabeçalho
    ws.merge_cells('A1:E1')
    ws['A1'] = f"VALORES DESCONTADOS INDEVIDAMENTE - \"{rubrica_nome}\""
    ws['A1'].font = font_title
    ws['A1'].fill = fill_blue
    ws['A1'].alignment = align_center
    
    meses_nomes = ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", 
                   "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
    
    ws['A2'] = "MESES"
    ws['A2'].font = font_header
    ws['A2'].alignment = align_center
    
    anos = sorted(agrupado['ANO'].unique())
    if not anos: anos = [datetime.now().year]
    
    for idx, ano in enumerate(anos):
        col = idx + 2
        ws.cell(row=2, column=col, value=ano).font = font_header
        ws.cell(row=2, column=col).alignment = align_center
        ws.cell(row=2, column=col).fill = fill_blue
    
    for m_idx, mes in enumerate(meses_nomes):
        row = m_idx + 3
        ws.cell(row=row, column=1, value=mes).font = font_header
        ws.cell(row=row, column=1).fill = fill_blue
        for a_idx, ano in enumerate(anos):
            col = a_idx + 2
            val = agrupado[(agrupado['ANO'] == ano) & (agrupado['MES_NUM'] == m_idx + 1)]['V_NUM'].sum()
            if val > 0:
                cell = ws.cell(row=row, column=col, value=val)
                cell.number_format = '"R$ " #,##0.00'
            ws.cell(row=row, column=col).fill = fill_peach
            ws.cell(row=row, column=col).border = border

    # Fórmulas
    row_anual = 15
    ws.cell(row=row_anual, column=1, value="VALOR ANUAL:").font = font_header
    ws.cell(row=row_anual, column=1).fill = fill_blue
    for idx, ano in enumerate(anos):
        col = idx + 2
        col_letter = get_column_letter(col)
        formula = f"=SUM({col_letter}3:{col_letter}14)"
        cell = ws.cell(row=row_anual, column=col, value=formula)
        cell.number_format = '"R$ " #,##0.00'
        cell.font = font_header
        cell.fill = fill_peach
        cell.border = border

    row_total = 16
    ws.cell(row=row_total, column=1, value="VALOR TOTAL:").font = font_header
    ws.cell(row=row_total, column=1).fill = fill_blue
    last_col_letter = get_column_letter(len(anos) + 1)
    formula_total = f"=SUM(B{row_anual}:{last_col_letter}{row_anual})"
    ws.merge_cells(start_row=row_total, start_column=2, end_row=row_total, end_column=len(anos)+1)
    cell_total = ws.cell(row=row_total, column=2, value=formula_total)
    cell_total.number_format = '"R$ " #,##0.00'
    cell_total.font = font_header
    cell_total.alignment = Alignment(horizontal='right')
    
    row_dobro = 17
    ws.merge_cells(start_row=row_dobro, start_column=1, end_row=row_dobro+1, end_column=1)
    ws.cell(row=row_dobro, column=1, value="VALOR EM DOBRO ART. 42 DO CDC").font = font_header
    ws.cell(row=row_dobro, column=1).fill = fill_blue
    ws.merge_cells(start_row=row_dobro, start_column=2, end_row=row_dobro+1, end_column=len(anos)+1)
    formula_dobro = f"=B{row_total}*2"
    cell_dobro = ws.cell(row=row_dobro, column=2, value=formula_dobro)
    cell_dobro.number_format = '"R$ " #,##0.00'
    cell_dobro.font = font_header
    cell_dobro.fill = fill_peach

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()

# --- 5. DASHBOARD ---
st.markdown('<h1 class="main-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Auditoria Técnica Especializada - Edson Medeiros</p>', unsafe_allow_html=True)

st.sidebar.markdown("### 🔍 RUBRICAS DE AUDITORIA")
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
    with st.spinner("Analisando..."):
        dados = realizar_auditoria(upload, selecionadas)
        if dados:
            df = pd.DataFrame(dados)
            df['V_NUM'] = df['VALOR'].str.replace('.','', regex=False).str.replace(',','.', regex=False).astype(float)
            st.success("Auditoria concluída com sucesso!")
            
            cats = df['CATEGORIA'].unique()
            for cat in cats:
                df_cat = df[df['CATEGORIA'] == cat]
                excel_file = gerar_excel_calculos(df_cat, cat)
                st.download_button(label=f"📊 Baixar Tabela: {cat}", data=excel_file, file_name=f"Tabela_{cat}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
            st.dataframe(df, use_container_width=True)
