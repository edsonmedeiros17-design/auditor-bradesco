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
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');
    .stApp { background-color: #0E1117; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    .main-title { font-family: 'Playfair Display', serif; font-size: 3rem; color: #BFAF83; text-align: center; }
    .sub-title { text-align: center; color: #64748B; letter-spacing: 2px; text-transform: uppercase; font-size: 0.9rem; margin-bottom: 40px; }
    .metric-card { background: rgba(255,255,255,0.05); border: 1px solid #BFAF83; border-radius: 10px; padding: 20px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- 2. RÚBRICAS E CONSTANTES ---
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

# --- 3. MOTOR DE AUDITORIA (LÓGICA DATA INFERIOR) ---
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
                
                # Procura por Data e Valor na linha
                match_data = re.search(r"(\d{2}/\d{2}/\d{4})", linha_up)
                match_valor = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})(?!\s*%)", linha_up)
                
                # Lógica de Data Inferior: Se achou data, fecha o cesto
                if match_data:
                    data_encontrada = match_data.group(1)
                    if cesto_acumulador:
                        for item in cesto_acumulador:
                            item["DATA"] = data_encontrada
                            resultados.append(item)
                        cesto_acumulador = []
                
                # Identifica Rubrica
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
                elif match_valor and cesto_acumulador and cesto_acumulador[-1]["VALOR"] == "0,00":
                    cesto_acumulador[-1]["VALOR"] = match_valor.group(1)
                    
    return resultados

# --- 4. GERAÇÃO EXCEL (CORREÇÃO DE CORES aRGB) ---
def gerar_excel_calculos(df, rubrica_nome):
    df = df.copy()
    df['DT'] = pd.to_datetime(df['DATA'], format='%d/%m/%Y')
    df['ANO'] = df['DT'].dt.year
    df['MES_NUM'] = df['DT'].dt.month
    agrupado = df.groupby(['ANO', 'MES_NUM'])['V_NUM'].sum().reset_index()
    
    wb = Workbook()
    ws = wb.active
    
    # Cores corretas aRGB (Prefixo FF, sem #)
    fill_blue = PatternFill(start_color="FFABAAA9", end_color="FFABAAA9", fill_type="solid")
    fill_peach = PatternFill(start_color="FFFFFFFF", end_color="FFFFFFFF", fill_type="solid")
    
    ws.merge_cells('A1:E1')
    ws['A1'] = f"AUDITORIA: {rubrica_nome}"
    ws['A1'].fill = fill_blue
    
    # (Restante da lógica de construção da planilha mantida...)
    meses_nomes = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]
    anos = sorted(agrupado['ANO'].unique())
    
    for idx, ano in enumerate(anos):
        ws.cell(row=2, column=idx+2, value=ano).fill = fill_blue
        
    for m_idx, mes in enumerate(meses_nomes):
        ws.cell(row=m_idx+3, column=1, value=mes).fill = fill_blue
        for a_idx, ano in enumerate(anos):
            val = agrupado[(agrupado['ANO'] == ano) & (agrupado['MES_NUM'] == m_idx + 1)]['V_NUM'].sum()
            if val > 0:
                ws.cell(row=m_idx+3, column=a_idx+2, value=val).number_format = '"R$ " #,##0.00'

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()

# --- 5. INTERFACE DASHBOARD ---
st.markdown('<h1 class="main-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
upload = st.file_uploader("📂 ARRASTE O EXTRATO", type=["pdf"])

if upload:
    dados = realizar_auditoria(upload, list(RUBRICAS_MESTRE.keys()))
    if dados:
        df = pd.DataFrame(dados)
        df['V_NUM'] = df['VALOR'].str.replace('.','', regex=False).str.replace(',','.', regex=False).astype(float)
        
        st.success(f"Total Recuperável: R$ {df['V_NUM'].sum():,.2f}")
        
        for cat in df['CATEGORIA'].unique():
            df_cat = df[df['CATEGORIA'] == cat]
            st.download_button(f"Baixar {cat}", gerar_excel_calculos(df_cat, cat), f"{cat}.xlsx")
            
        st.dataframe(df)
