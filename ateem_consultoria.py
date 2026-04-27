import streamlit as st
import pdfplumber
import pandas as pd
import re
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image

# --- 1. CONFIGURAÇÃO E IDENTIDADE VISUAL (ATEEM) ---
st.set_page_config(page_title="ATEEM - CONSULTORIAS", layout="wide", page_icon="⚖️")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    .main-title { font-family: 'Playfair Display', serif; font-size: 2.8rem; color: #BFAF83; text-align: center; }
    .metric-card { background: rgba(255,255,255,0.05); border: 1px solid #BFAF83; border-radius: 10px; padding: 15px; text-align: center; }
    .rubrica-badge { display: inline-block; padding: 4px 10px; margin: 4px; border-radius: 15px; background: rgba(191, 175, 131, 0.1); border: 1px solid #BFAF83; color: #BFAF83; font-size: 0.7rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# --- 2. PARAMETRIZAÇÃO DE PRECISÃO (NOMENCLATURAS ATUALIZADAS) ---
RUBRICAS_MESTRE = {
    "PACTO COBRANÇA / PREVIDÊNCIA": r"PACTO COBRANCA|PAGTO COBRANCA|BRADESCO VIDA E PREVIDENCIA",
    "ENC LIM CREDITO": r"ENC LIMITE|ENC LIM CREDITO|ENCARGO",
    "CART CRED ANUID": r"CART CRED ANUID|ANUIDADE",
    "PARC CRED PESS": r"PARC CRED PESS|PARCELA CREDITO PESSOAL",
    "CESTA": r"CESTA|TARIFA BANCARIA",
    "IOF UTIL LIMITE": r"IOF UTIL LIMITE|IOF\b",  # Agora isolado para evitar o erro do Anexo 1
    "MORA/JUROS": r"MORA|JUROS" 
}

TERMOS_EXCLUSAO = r"TRANSF|SALDO|SDO|TRANSFERENCIA|SALARIO"

# --- 3. MOTOR DE VARREDURA TOP-TO-BOTTOM (ANEXO 3) ---
def realizar_auditoria_ateem(arquivo_bytes):
    resultados = []
    texto_total = ""
    
    try:
        with pdfplumber.open(arquivo_bytes) as pdf:
            total_paginas = len(pdf.pages)
            progresso = st.progress(0)
            status = st.empty()

            for i, page in enumerate(pdf.pages):
                status.text(f"🔍 Scanner Ativo: Página {i+1} de {total_paginas} (Varredura Top-to-Bottom)")
                progresso.progress((i + 1) / total_paginas)
                
                # Tenta Extração Digital
                conteudo = page.extract_text(x_tolerance=2, y_tolerance=2)
                
                # Se for imagem/escaneado (OCR), converte e lê
                if not conteudo or len(conteudo.strip()) < 30:
                    arquivo_bytes.seek(0)
                    img = convert_from_bytes(arquivo_bytes.read(), first_page=i+1, last_page=i+1, dpi=200)[0]
                    conteudo = pytesseract.image_to_string(img.convert('L'), lang='por')

                # Processamento da página linha por linha
                data_da_linha = "---"
                for linha in conteudo.split('\n'):
                    linha_up = linha.upper()
                    
                    # Captura Data
                    match_data = re.search(r"(\d{2}/\d{2}(?:/\d{2,4})?)", linha)
                    if match_data: data_da_linha = match_data.group(1)

                    # Reset por Termo de Exclusão (Transferências)
                    if re.search(TERMOS_EXCLUSAO, linha_up): continue

                    # Captura Valor e Sinal de Saída (-) conforme ANEXO 2
                    match_valor = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})([-]?)", linha)

                    if match_valor:
                        valor_str = match_valor.group(1)
                        sinal_negativo = match_valor.group(2) == "-"
                        
                        # Verificação de Rubrica (Uma por uma na linha)
                        for rubrica, regex in RUBRICAS_MESTRE.items():
                            if re.search(regex, linha_up):
                                resultados.append({
                                    "DATA": data_da_linha,
                                    "RUBRICA IDENTIFICADA": rubrica,
                                    "VALOR": valor_str,
                                    "SAÍDA (-)": "SIM" if sinal_negativo else "NÃO",
                                    "TRECHO DO EXTRATO": linha_up[:50]
                                })
                                break # Encontrou a rubrica, pula para a próxima linha

            status.empty()
            progresso.empty()
            
    except Exception as e:
        st.error(f"Erro técnico no processamento: {e}")
        
    return resultados

# --- 4. DASHBOARD DE ENTREGA ---
st.markdown('<h1 class="main-title">ATEEM - CONSULTORIAS</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; color:#64748B; letter-spacing:1px;">AUDITORIA DE DÉBITOS INDEVIDOS - MÓDULO HÍBRIDO</p>', unsafe_allow_html=True)

upload = st.file_uploader("📂 ARRASTE O EXTRATO ESCANEADO OU DIGITAL", type=["pdf"])

if upload:
    dados = realizar_auditoria_ateem(upload)
    
    if dados:
        df = pd.DataFrame(dados)
        # Conversão numérica para cálculo
        df['V_FLOAT'] = df['VALOR'].str.replace('.','', regex=False).str.replace(',','.', regex=False).astype(float)
        
        c1, c2 = st.columns(2)
        with c1: st.markdown(f'<div class="metric-card"><h4>TOTAL EM DÉBITOS</h4><h2 style="color:#BFAF83;">R$ {df["V_FLOAT"].sum():,.2f}</h2></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card"><h4>LANÇAMENTOS</h4><h2 style="color:#BFAF83;">{len(df)}</h2></div>', unsafe_allow_html=True)

        st.markdown('<p style="color: #64748B; font-weight: 600; margin-top:20px; font-size: 0.8rem;">DESCONTOS ENCONTRADOS:</p>', unsafe_allow_html=True)
        unicas = df['RUBRICA IDENTIFICADA'].unique()
        badges = "".join([f'<span class="rubrica-badge">{r}</span>' for r in unicas])
        st.markdown(badges, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        # Exibe a tabela respeitando a ordem de leitura (Top-to-Bottom)
        st.dataframe(df[['DATA', 'RUBRICA IDENTIFICADA', 'VALOR', 'SAÍDA (-)', 'TRECHO DO EXTRATO']], use_container_width=True)
        
        csv = df[['DATA', 'RUBRICA IDENTIFICADA', 'VALOR', 'SAÍDA (-)']].to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 BAIXAR LAUDO TÉCNICO", csv, "laudo_auditoria_ateem.csv")
    else:
        st.info("Varredura concluída. Nenhuma rubrica da lista foi identificada.")

st.markdown("<br><br><p style='text-align:right; font-family:serif; font-style:italic; color:#BFAF83;'>Edson Medeiros</p>", unsafe_allow_html=True)

# atualização de segurança ATEEM
