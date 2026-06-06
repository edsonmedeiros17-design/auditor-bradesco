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
    .stApp { background-color: #0E1117; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    .main-title { font-family: 'Playfair Display', serif; font-size: 3rem; color: #BFAF83; text-align: center; }
    .metric-card { background: rgba(255,255,255,0.05); border: 1px solid #BFAF83; border-radius: 10px; padding: 20px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- 2. RÚBRICAS E CONFIGURAÇÕES ---
RUBRICAS_MESTRE = {
    "CESTA": r"CESTA", "PACOTE": r"PACOTE", "MORA DE OPERAÇÃO": r"MORA DE OPERAÇÃO|MORA OPERACAO",
    "MORA CREDITO PESSOAL": r"MORA CREDITO PESSOAL|MORA CRED PESS", "MORA OPERACAO DE CREDITO": r"MORA OPERACAO DE CREDITO|MORA OPER CRED",
    "BX": r"\bBX\b", "PARCELA CREDITO PESSOAL": r"PARCELA CREDITO PESSOAL|PARC CRED PESS",
    "GASTOS CARTAO DE CREDITO": r"GASTOS CARTAO DE CREDITO|CARTAO DE CREDITO|GASTOS CARTAO",
    "SEGURO": r"SEGURO|SEGURADORA|SEG\b", "ADIANT": r"ADIANT|ADIANTAMENTO DEPOSITANTE",
    "APLIC": r"APLICACAO|APLIC\b", "ENCARGOS": r"ENCARGOS|ENCARGO|ENC LIMITE|LIMITE DE CRED",
    "ANUIDADE": r"ANUIDADE|CARTAO CREDITO ANUIDADE", "OPERACOES VENCIDAS": r"OPERACOES VENCIDAS|OPERAÇÕES VENCIDAS",
    "DIV. EM ATRASO": r"DIV\. EM ATRASO|DIVIDA EM ATRASO"
}

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

                # Regex para encontrar datas e valores
                match_data = re.search(r"(\d{2}/\d{2}/\d{4})", linha_up)
                match_valor = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})(?!\s*%)", linha_up)
                
                # LÓGICA DE DATA INFERIOR: Se encontrar data, aplica ao acumulador
                if match_data:
                    data_encontrada = match_data.group(1)
                    if cesto_acumulador:
                        for item in cesto_acumulador:
                            item["DATA"] = data_encontrada
                            resultados.append(item)
                        cesto_acumulador = []
                
                # Busca por Rubrica
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

# --- 4. GERAÇÃO DE EXCEL (CORRIGIDO) ---
def gerar_excel_calculos(df, rubrica_nome):
    df = df.copy()
    df['V_NUM'] = df['VALOR'].str.replace('.','', regex=False).str.replace(',','.', regex=False).astype(float)
    
    wb = Workbook()
    ws = wb.active
    
    # CORREÇÃO aRGB: Prefixo FF, sem #
    fill_blue = PatternFill(start_color="FFABAAA9", end_color="FFABAAA9", fill_type="solid")
    
    ws.merge_cells('A1:D1')
    ws['A1'] = f"AUDITORIA: {rubrica_nome}"
    ws['A1'].fill = fill_blue
    
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()

# --- 5. DASHBOARD ---
st.markdown('<h1 class="main-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
upload = st.file_uploader("📂 ARRASTE O EXTRATO BANCÁRIO (PDF)", type=["pdf"])

if upload:
    dados = realizar_auditoria(upload, list(RUBRICAS_MESTRE.keys()))
    if dados:
        df = pd.DataFrame(dados)
        st.dataframe(df)
        st.success(f"Análise concluída: {len(df)} movimentos processados.")
