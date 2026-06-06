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
    st.error("Erro: A biblioteca 'openpyxl' não está instalada.")

# --- 1. CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="Edson Medeiros | Consultoria de Ativos", layout="wide", page_icon="⚖️")

st.markdown("""
<style>
    .main-title { font-family: 'Playfair Display', serif; font-size: 3rem; color: #BFAF83; text-align: center; }
    .metric-card { background: rgba(255,255,255,0.05); border: 1px solid #BFAF83; border-radius: 10px; padding: 20px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- 2. RÚBRICAS E MOTOR DE AUDITORIA ---
RUBRICAS_MESTRE = {
    "CESTA": r"CESTA", "PACOTE": r"PACOTE",
    "MORA DE OPERAÇÃO": r"MORA DE OPERAÇÃO|MORA OPERACAO",
    "MORA CREDITO PESSOAL": r"MORA CREDITO PESSOAL|MORA CRED PESS",
    "MORA OPERACAO DE CREDITO": r"MORA OPERACAO DE CREDITO|MORA OPER CRED",
    "BX": r"\bBX\b", "PARCELA CREDITO PESSOAL": r"PARCELA CREDITO PESSOAL|PARC CRED PESS",
    "GASTOS CARTAO DE CREDITO": r"GASTOS CARTAO DE CREDITO|CARTAO DE CREDITO",
    "SEGURO": r"SEGURO|SEGURADORA|SEG\b", "ADIANT": r"ADIANT|ADIANTAMENTO",
    "APLIC": r"APLICACAO|APLIC\b", "ENCARGOS": r"ENCARGOS|ENC LIMITE|LIMITE DE CRED",
    "ANUIDADE": r"ANUIDADE|CARTAO CREDITO ANUIDADE",
    "OPERACOES VENCIDAS": r"OPERACOES VENCIDAS", "DIV. EM ATRASO": r"DIV\. EM ATRASO"
}

def realizar_auditoria(arquivo, rubricas_alvo):
    resultados = []
    cesto_acumulador = []
    
    with pdfplumber.open(arquivo) as pdf:
        for page in pdf.pages:
            texto = page.extract_text(x_tolerance=3, y_tolerance=3)
            if not texto: continue
            
            for linha in texto.split('\n'):
                linha_up = linha.upper().strip()
                match_data = re.search(r"(\d{2}/\d{2}/\d{4})", linha_up)
                match_valor = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})(?!\s*%)", linha_up)
                
                # Selagem por Data Inferior
                if match_data:
                    data_encontrada = match_data.group(1)
                    for item in cesto_acumulador:
                        item["DATA"] = data_encontrada
                        resultados.append(item)
                    cesto_acumulador = []
                
                # Identificação de Rubrica
                for nome in rubricas_alvo:
                    if re.search(RUBRICAS_MESTRE[nome], linha_up):
                        cesto_acumulador.append({
                            "CATEGORIA": nome,
                            "VALOR": match_valor.group(1) if match_valor else "0,00",
                            "DATA": "PENDENTE"
                        })
                        break
    return resultados

# --- 3. GERAÇÃO DE EXCEL (CORRIGIDO) ---
def gerar_excel_calculos(df, rubrica_nome):
    df = df.copy()
    df['DT'] = pd.to_datetime(df['DATA'], format='%d/%m/%Y')
    df['ANO'] = df['DT'].dt.year
    df['MES_NUM'] = df['DT'].dt.month
    agrupado = df.groupby(['ANO', 'MES_NUM'])['V_NUM'].sum().reset_index()
    
    wb = Workbook()
    ws = wb.active
    # FIX: Cores em formato aRGB (sem # e com prefixo FF)
    fill_blue = PatternFill(start_color="FFABAAA9", end_color="FFABAAA9", fill_type="solid")
    fill_white = PatternFill(start_color="FFFFFFFF", end_color="FFFFFFFF", fill_type="solid")
    
    # ... (restante do código de formatação inalterado)
    ws.merge_cells('A1:E1')
    ws['A1'] = f"VALORES INDEVIDOS - {rubrica_nome}"
    ws['A1'].fill = fill_blue
    
    # Loop de preenchimento...
    anos = sorted(agrupado['ANO'].unique())
    for idx, ano in enumerate(anos):
        ws.cell(row=2, column=idx+2, value=ano).fill = fill_blue
        
    for m in range(1, 13):
        ws.cell(row=m+2, column=1, value=m).fill = fill_blue
        for a_idx, ano in enumerate(anos):
            val = agrupado[(agrupado['ANO'] == ano) & (agrupado['MES_NUM'] == m)]['V_NUM'].sum()
            cell = ws.cell(row=m+2, column=a_idx+2, value=val)
            cell.number_format = '"R$ " #,##0.00'
            
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()

# --- 4. DASHBOARD ---
st.markdown('<h1 class="main-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
upload = st.file_uploader("📂 ARRASTE O EXTRATO", type=["pdf"])

if upload:
    dados = realizar_auditoria(upload, list(RUBRICAS_MESTRE.keys()))
    df = pd.DataFrame(dados)
    df['V_NUM'] = df['VALOR'].str.replace('.','', regex=False).str.replace(',','.', regex=False).astype(float)
    st.dataframe(df)
    
    for cat in df['CATEGORIA'].unique():
        st.download_button(f"Baixar {cat}", gerar_excel_calculos(df[df['CATEGORIA']==cat], cat), f"{cat}.xlsx")
