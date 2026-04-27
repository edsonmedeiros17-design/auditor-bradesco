import streamlit as st
import pdfplumber
import pandas as pd
import re
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image

# --- CONFIGURAÇÃO E IDENTIDADE VISUAL (ATEEM) ---
st.set_page_config(page_title="ATEEM - CONSULTORIAS", layout="wide", page_icon="⚖️")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    .main-title { font-family: 'Playfair Display', serif; font-size: 3rem; color: #BFAF83; text-align: center; }
    .metric-card { background: rgba(255,255,255,0.05); border: 1px solid #BFAF83; border-radius: 10px; padding: 20px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- PARÂMETROS CONGELADOS (PROTEÇÃO ATEEM) ---
RUBRICAS_MESTRE = {
    "PAGTO COBRANCA": r"PAGTO COBRANCA|BRADESCO VIDA E PREVIDENCIA|PACTO COBRANCA",
    "ENCARGOS LIMITE": r"ENC LIMITE|ENC LIM CREDITO|ENCARGO\d",
    "ANUIDADE CARTÃO": r"CART CRED ANUID|ANUIDADE",
    "CREDITO PESSOAL": r"PARC CRED PESS|PARCELA CREDITO PESSOAL",
    "CESTA BANCÁRIA": r"CESTA|TARIFA BANCARIA",
    "MORA/JUROS": r"MORA|JUROS|IOF UTIL LIMITE"
}
TERMOS_EXCLUSAO = r"TRANSF|SALDO|SDO|TRANSFERENCIA|SALARIO"

# --- MOTOR DE ALTA PERFORMANCE ---
def extrair_texto_otimizado(arquivo_bytes):
    texto_total = ""
    try:
        with pdfplumber.open(arquivo_bytes) as pdf:
            total_paginas = len(pdf.pages)
            progresso = st.progress(0)
            status_text = st.empty()

            for i, page in enumerate(pdf.pages):
                # Atualiza interface para o usuário
                percentual = (i + 1) / total_paginas
                progresso.progress(percentual)
                status_text.text(f"🚀 Analisando página {i+1} de {total_paginas}...")

                # Tenta extração digital primeiro (Ultra rápido)
                extraido = page.extract_text()
                if extraido and len(extraido.strip()) > 50:
                    texto_total += extraido + "\n"
                else:
                    # Ativa OCR Otimizado (Apenas se necessário)
                    try:
                        arquivo_bytes.seek(0)
                        # DPI 200 para equilíbrio entre velocidade e precisão
                        imagens = convert_from_bytes(arquivo_bytes.read(), first_page=i+1, last_page=i+1, dpi=200)
                        for img in imagens:
                            # Converte para tons de cinza para acelerar o Tesseract
                            img = img.convert('L')
                            texto_total += pytesseract.image_to_string(img, lang='por')
                    except:
                        continue
            
            progresso.empty()
            status_text.empty()
    except Exception as e:
        st.error(f"Erro no processamento: {e}")
    return texto_total

def realizar_auditoria(texto):
    resultados = []
    linhas = texto.split('\n')
    data_atual = "---"
    
    for linha in linhas:
        linha_up = linha.upper()
        match_data = re.search(r"(\d{2}/\d{2}(?:/\d{2,4})?)", linha)
        if match_data: data_atual = match_data.group(1)

        if re.search(TERMOS_EXCLUSAO, linha_up): continue

        # Identifica Valor e sinal de menos (-) conforme ANEXO 2
        match_valor = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})([-]?)", linha)

        if match_valor:
            valor_texto = match_valor.group(1)
            confirmado = "SIM" if match_valor.group(2) == "-" else "NÃO"
            
            for nome, regex in RUBRICAS_MESTRE.items():
                if re.search(regex, linha_up):
                    resultados.append({
                        "DATA": data_atual,
                        "DESCONTO": nome,
                        "VALOR": valor_texto,
                        "SINAL (-)": confirmado,
                        "HISTÓRICO": linha_up[:50]
                    })
                    break
    return resultados

# --- DASHBOARD ---
st.markdown('<h1 class="main-title">ATEEM - CONSULTORIAS</h1>', unsafe_allow_html=True)

upload = st.file_uploader("📂 SOLTE O EXTRATO BANCÁRIO", type=["pdf"])

if upload:
    # Inicia processamento otimizado
    texto = extrair_texto_otimizado(upload)
    
    if texto:
        dados = realizar_auditoria(texto)
        if dados:
            df = pd.DataFrame(dados)
            df['V_NUM'] = df['VALOR'].str.replace('.','', regex=False).str.replace(',','.', regex=False).astype(float)
            
            c1, c2 = st.columns(2)
            with c1: st.markdown(f'<div class="metric-card"><h4>TOTAL LOCALIZADO</h4><h2 style="color:#BFAF83;">R$ {df["V_NUM"].sum():,.2f}</h2></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="metric-card"><h4>OCORRÊNCIAS</h4><h2 style="color:#BFAF83;">{len(df)}</h2></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True)
            st.download_button("📥 BAIXAR RELATÓRIO", df.to_csv(index=False).encode('utf-8-sig'), "auditoria_ateem.csv")
        else:
            st.info("Nenhum desconto indevido encontrado neste documento.")

st.markdown("<br><br><p style='text-align:right; color:#BFAF83;'>Edson Medeiros</p>", unsafe_allow_html=True)
