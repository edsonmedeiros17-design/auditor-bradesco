import streamlit as st
import pdfplumber
import pandas as pd
import re
from pdf2image import convert_from_bytes
import pytesseract
import PIL.Image

# --- CONFIGURAÇÃO TÉCNICA (AJUSTE LOCAL) ---
# Se você instalou no Windows, descomente a linha abaixo e coloque o seu caminho:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# --- 1. CONFIGURAÇÃO E IDENTIDADE VISUAL (ATEEM PRESERVADA) ---
st.set_page_config(page_title="ATEEM - CONSULTORIAS", layout="wide", page_icon="⚖️")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    .main-title { font-family: 'Playfair Display', serif; font-size: 3rem; color: #BFAF83; text-align: center; }
    .metric-card { background: rgba(255,255,255,0.05); border: 1px solid #BFAF83; border-radius: 10px; padding: 20px; text-align: center; }
    .rubrica-badge { display: inline-block; padding: 5px 12px; margin: 5px; border-radius: 20px; background: rgba(191, 175, 131, 0.15); border: 1px solid #BFAF83; color: #BFAF83; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# --- 2. MOTOR DE INTELIGÊNCIA (PROTEÇÃO ATEEM LOCK) ---
RUBRICAS_MESTRE = {
    "PAGTO COBRANCA": r"PAGTO COBRANCA|BRADESCO VIDA E PREVIDENCIA|PACTO COBRANCA",
    "ENCARGOS LIMITE": r"ENC LIMITE|ENC LIM CREDITO|ENCARGO\d",
    "ANUIDADE CARTÃO": r"CART CRED ANUID|ANUIDADE",
    "CREDITO PESSOAL": r"PARC CRED PESS|PARCELA CREDITO PESSOAL",
    "CESTA BANCÁRIA": r"CESTA|TARIFA BANCARIA",
    "MORA/JUROS": r"MORA|JUROS|IOF UTIL LIMITE"
}

TERMOS_EXCLUSAO = r"TRANSF|SALDO|SDO|TRANSFERENCIA|SALARIO"

def extrair_texto_hibrido(arquivo_bytes):
    texto_total = ""
    try:
        with pdfplumber.open(arquivo_bytes) as pdf:
            for page in pdf.pages:
                extraido = page.extract_text()
                if extraido and len(extraido.strip()) > 50:
                    texto_total += extraido + "\n"
                else:
                    # Se falhar a leitura digital, tenta OCR
                    try:
                        arquivo_bytes.seek(0)
                        imagens = convert_from_bytes(arquivo_bytes.read())
                        for img in imagens:
                            texto_total += pytesseract.image_to_string(img, lang='por')
                    except Exception as e:
                        st.error(f"⚠️ Motor de Visão (OCR) não configurado: {e}")
                        return "ERRO_OCR"
    except Exception as e:
        st.error(f"Erro ao abrir PDF: {e}")
    return texto_total

def realizar_auditoria_avancada(texto, rubricas_alvo):
    resultados = []
    if texto == "ERRO_OCR": return []
    
    linhas = texto.split('\n')
    data_atual = "---"
    
    for linha in linhas:
        linha_up = linha.upper()
        
        # Identifica Data
        match_data = re.search(r"(\d{2}/\d{2}(?:/\d{2,4})?)", linha)
        if match_data: data_atual = match_data.group(1)

        # Reset de segurança (Regra ATEEM)
        if re.search(TERMOS_EXCLUSAO, linha_up): continue

        # Identifica Valor com sinal de menos (Ex: 16,75-) conforme seu ANEXO 2
        # Captura o valor e o sinal de menos se existir
        match_valor = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})([-]?)", linha)

        if match_valor:
            valor_texto = match_valor.group(1)
            tem_sinal_menos = match_valor.group(2) == "-"
            
            for nome in rubricas_alvo:
                if re.search(RUBRICAS_MESTRE[nome], linha_up):
                    # Se for extrato impresso, priorizamos os que têm o sinal de menos
                    status = "DÉBITO CONFIRMADO" if tem_sinal_menos else "VERIFICAR"
                    
                    resultados.append({
                        "DATA": data_atual,
                        "CATEGORIA": nome,
                        "VALOR": valor_texto,
                        "STATUS": status,
                        "HISTÓRICO": linha_up[:50]
                    })
                    break
    return resultados

# --- 3. DASHBOARD ---
st.markdown('<h1 class="main-title">ATEEM - CONSULTORIAS</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; color:#64748B;">Módulo de Auditoria Híbrida (Digital + Escaneado)</p>', unsafe_allow_html=True)

upload = st.file_uploader("📂 SOLTE O EXTRATO AQUI (PDF OU IMAGEM)", type=["pdf"])

if upload:
    with st.spinner("O Robô está processando as imagens do extrato..."):
        texto = extrair_texto_hibrido(upload)
        if texto != "ERRO_OCR":
            dados = realizar_auditoria_avancada(texto, list(RUBRICAS_MESTRE.keys()))
            
            if dados:
                df = pd.DataFrame(dados)
                df['V_NUM'] = df['VALOR'].str.replace('.','', regex=False).str.replace(',','.', regex=False).astype(float)
                
                c1, c2 = st.columns(2)
                with c1: st.markdown(f'<div class="metric-card"><h4>TOTAL IDENTIFICADO</h4><h2 style="color:#BFAF83;">R$ {df["V_NUM"].sum():,.2f}</h2></div>', unsafe_allow_html=True)
                with c2: st.markdown(f'<div class="metric-card"><h4>DESCONTOS</h4><h2 style="color:#BFAF83;">{len(df)}</h2></div>', unsafe_allow_html=True)

                st.markdown('<p style="color: #64748B; font-weight: 600; margin-top:20px;">DESCONTOS ENCONTRADOS:</p>', unsafe_allow_html=True)
                badges = "".join([f'<span class="rubrica-badge">{r}</span>' for r in df['CATEGORIA'].unique()])
                st.markdown(badges, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.dataframe(df[['DATA', 'CATEGORIA', 'VALOR', 'STATUS', 'HISTÓRICO']], use_container_width=True)
            else:
                st.warning("Nenhum débito identificado. Certifique-se de que o extrato está legível.")

st.markdown("<br><br><p style='text-align:right; font-family:serif; font-style:italic; color:#BFAF83;'>Edson Medeiros</p>", unsafe_allow_html=True)
