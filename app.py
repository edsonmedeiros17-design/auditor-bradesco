import streamlit as st
import pdfplumber
import pandas as pd
import re
from pdf2image import convert_from_bytes
import pytesseract
import PIL.Image

# --- 1. CONFIGURAÇÃO E IDENTIDADE VISUAL ---
st.set_page_config(page_title="ATEEM - CONSULTORIAS", layout="wide", page_icon="⚖️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');
    .stApp { background-color: #0E1117; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    .main-title { font-family: 'Playfair Display', serif; font-size: 3rem; color: #BFAF83; text-align: center; margin-bottom: 0; }
    .sub-title { text-align: center; color: #64748B; letter-spacing: 2px; text-transform: uppercase; font-size: 0.8rem; margin-bottom: 40px; }
    .metric-card { background: rgba(255,255,255,0.05); border: 1px solid #BFAF83; border-radius: 10px; padding: 20px; text-align: center; }
    .rubrica-badge { display: inline-block; padding: 5px 12px; margin: 5px; border-radius: 20px; background: rgba(191, 175, 131, 0.15); border: 1px solid #BFAF83; color: #BFAF83; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)

# --- 2. NOVOS PARÂMETROS (INCLUINDO NOMENCLATURAS ESCANEADAS) ---
RUBRICAS_MESTRE = {
    "PAGTO COBRANCA": r"PAGTO COBRANCA|BRADESCO VIDA E PREVIDENCIA|PACTO COBRANCA",
    "ENCARGOS LIMITE": r"ENC LIMITE|ENC LIM CREDITO|ENCARGO\d",
    "ANUIDADE CARTÃO": r"CART CRED ANUID|ANUIDADE",
    "CREDITO PESSOAL": r"PARC CRED PESS|PARCELA CREDITO PESSOAL",
    "CESTA BANCÁRIA": r"CESTA|TARIFA BANCARIA",
    "MORA/JUROS": r"MORA|JUROS|IOF UTIL LIMITE"
}

# --- 3. MOTOR DE INTELIGÊNCIA HÍBRIDA (DIGITAL + OCR) ---
def extrair_texto_pdf(arquivo_bytes):
    texto_total = ""
    with pdfplumber.open(arquivo_bytes) as pdf:
        for page in pdf.pages:
            extraido = page.extract_text()
            if extraido: # É digital
                texto_total += extraido + "\n"
            else: # É escaneado/imagem (Ativa OCR)
                # Nota: Em ambiente local, requer instalação do Tesseract OCR
                imagens = convert_from_bytes(arquivo_bytes.read())
                for img in imagens:
                    texto_total += pytesseract.image_to_string(img, lang='por')
    return texto_total

def realizar_auditoria_avancada(texto, rubricas_alvo):
    resultados = []
    linhas = texto.split('\n')
    data_atual = "Não Identificada"
    
    # Termos de reset preservados (ATEEM lock)
    TERMOS_EXCLUSAO = r"TRANSF|SALDO|SDO|TRANSFERENCIA|SALARIO"

    for linha in linhas:
        linha_up = linha.upper()
        
        # 1. Identifica Data (Padrão de extrato impresso costuma ser DD/MM)
        match_data = re.search(r"(\d{2}/\d{2}(?:/\d{2,4})?)", linha)
        if match_data: data_atual = match_data.group(1)

        # 2. Reset de segurança (conforme sua regra)
        if re.search(TERMOS_EXCLUSAO, linha_up): continue

        # 3. Identifica Valor com sinal de menos (Ex: 16,75-) conforme ANEXO 2
        # A regex busca o valor seguido opcionalmente por um "-"
        match_valor = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})[- ]?", linha)

        if match_valor:
            valor_texto = match_valor.group(1)
            # Verifica se a rubrica está na linha
            for nome in rubricas_alvo:
                if re.search(RUBRICAS_MESTRE[nome], linha_up):
                    resultados.append({
                        "DATA": data_atual,
                        "CATEGORIA": nome,
                        "VALOR": valor_texto,
                        "HISTÓRICO": linha_up[:50]
                    })
                    break
    return resultados

# --- 4. INTERFACE ---
st.markdown('<h1 class="main-title">ATEEM - CONSULTORIAS</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Inovação em Auditoria de Extratos Escaneados</p>', unsafe_allow_html=True)

upload = st.file_uploader("📂 SOLTE O EXTRATO AQUI (DIGITAL OU ESCANEADO)", type=["pdf", "png", "jpg"])

if upload:
    with st.spinner("O Robô está 'lendo' o documento impresso..."):
        # Processamento
        texto_completo = extrair_texto_pdf(upload)
        dados = realizar_auditoria_avancada(texto_completo, list(RUBRICAS_MESTRE.keys()))
        
        if dados:
            df = pd.DataFrame(dados)
            df['V_NUM'] = df['VALOR'].str.replace('.','', regex=False).str.replace(',','.', regex=False).astype(float)
            
            # Métricas
            c1, c2 = st.columns(2)
            with c1: st.markdown(f'<div class="metric-card"><h4>TOTAL IDENTIFICADO</h4><h2 style="color:#BFAF83;">R$ {df["V_NUM"].sum():,.2f}</h2></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="metric-card"><h4>DESCONTOS</h4><h2 style="color:#BFAF83;">{len(df)}</h2></div>', unsafe_allow_html=True)

            # Badges de Descontos Encontrados
            st.markdown('<p style="color: #64748B; font-weight: 600; margin-top:20px;">DESCONTOS ENCONTRADOS:</p>', unsafe_allow_html=True)
            for r in df['CATEGORIA'].unique():
                st.markdown(f'<span class="rubrica-badge">{r}</span>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(df[['DATA', 'CATEGORIA', 'VALOR', 'HISTÓRICO']], use_container_width=True)
        else:
            st.warning("Nenhum débito indevido identificado. Verifique a qualidade do escaneamento.")

st.markdown("<br><br><p style='text-align:right; font-family:serif; font-style:italic; color:#BFAF83;'>Edson Medeiros</p>", unsafe_allow_html=True)
