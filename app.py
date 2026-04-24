import streamlit as st
import pdfplumber
import pandas as pd
import re

# --- 1. INTERFACE PERSONALIZADA EDSON MEDEIROS ---
st.set_page_config(page_title="Edson Medeiros | Auditoria Pro", layout="wide", page_icon="⚖️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');
    .stApp { background-color: #0E1117; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    .main-title { font-family: 'Playfair Display', serif; font-size: 3rem; color: #BFAF83; text-align: center; margin-bottom: 0; }
    .sub-title { text-align: center; color: #64748B; letter-spacing: 2px; text-transform: uppercase; font-size: 0.9rem; margin-bottom: 40px; }
    .metric-card { background: rgba(255,255,255,0.05); border: 1px solid #BFAF83; border-radius: 10px; padding: 20px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- 2. PARÂMETROS DE BUSCA (AS 14 RUBRICAS SOLICITADAS) ---
DICIONARIO_ALVOS = {
    "CESTA/PACOTE": r"CESTA|PACOTE|TARIFA BANCARIA",
    "MORA DE OPERAÇÃO": r"MORA OPERACAO|MORA DE OPERAÇÃO",
    "MORA CREDITO PESSOAL": r"MORA CREDITO PESSOAL|MORA CRED PESS",
    "MORA OPERACAO DE CREDITO": r"MORA OPERACAO DE CREDITO|MORA OPER CRED",
    "BX": r"BX ",
    "PARCELA CREDITO PESSOAL": r"PARCELA CREDITO PESSOAL|PARC CRED PESS",
    "GASTOS CARTAO DE CREDITO": r"GASTOS CARTAO|CARTAO DE CREDITO",
    "SEGURO": r"SEGURO|SEGURADORA|SEG ",
    "ADIANT": r"ADIANT|ADIANTAMENTO DEPOSITANTE",
    "APLIC": r"APLICACAO|APLIC ",
    "ENCARGOS": r"ENCARGOS|ENC LIMITE|ENCARGO",
    "ANUIDADE": r"ANUIDADE|CARTAO CREDITO ANUIDADE",
    "OPERACOES VENCIDAS": r"OPERACOES VENCIDAS|OPERAÇÕES VENCIDAS",
    "DIV. EM ATRASO": r"DIV\. EM ATRASO|DIVIDA EM ATRASO"
}

# --- 3. MOTOR COM LÓGICA DE DATA INFERIOR (ANEXO 2 e 3) ---
def auditoria_inteligente(arquivo):
    final_data = []
    cesto_espera = [] # Guarda rubricas que estão esperando a data aparecer abaixo
    
    with pdfplumber.open(arquivo) as pdf:
        for page in pdf.pages:
            # Extração focada em texto para lidar com scans (ANEXO 3)
            linhas = page.extract_text().split('\n')
            
            for linha in linhas:
                linha_up = linha.upper()
                
                # Identifica se a linha contém uma data (Ex: 08/02/2017)
                match_data = re.search(r"(\d{2}/\d{2}/\d{2,4})", linha)
                
                # Identifica se a linha possui valor monetário (Débito)
                # Procura padrões como 116,11 ou 19,31
                match_valor = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})", linha)
                
                # BUSCA DE RUBRICAS
                rubrica_detectada = None
                for nome, regex in DICIONARIO_ALVOS.items():
                    if re.search(regex, linha_up):
                        rubrica_detectada = nome
                        break
                
                # LÓGICA DE VINCULAÇÃO (LENDO PARA BAIXO)
                if rubrica_detectada and match_valor:
                    # Encontrou a rubrica e o valor, mas não tem data na linha? 
                    # Vai para o cesto aguardar a "Data Inferior" (ANEXO 2)
                    item = {
                        "CATEGORIA": rubrica_detectada,
                        "VALOR": match_valor.group(1),
                        "HISTÓRICO": linha_up[:60]
                    }
                    
                    if match_data:
                        item["DATA"] = match_data.group(1)
                        final_data.append(item)
                    else:
                        cesto_espera.append(item)
                
                # SE ENCONTRAR UMA DATA SOZINHA OU EM LINHA DE FECHAMENTO
                elif match_data and cesto_espera:
                    data_ancora = match_data.group(1)
                    # Descarrega o cesto aplicando a data encontrada abaixo (ANEXO 2)
                    for pendente in cesto_espera:
                        pendente["DATA"] = data_ancora
                        final_data.append(pendente)
                    cesto_espera = []

    return final_data

# --- 4. DASHBOARD ---
st.markdown('<h1 class="main-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Auditoria de Débitos Indevidos - Edson Medeiros</p>', unsafe_allow_html=True)

upload = st.file_uploader("📂 Faça o upload do extrato (PDF)", type=["pdf"])

if upload:
    with st.spinner("Aplicando lógica de Data Inferior e Processando Rubricas..."):
        resultados = auditoria_inteligente(upload)
        
        if resultados:
            df = pd.DataFrame(resultados)
            
            # Formatação de Valores
            df['NUM'] = df['VALOR'].str.replace('.','').str.replace(',','.').astype(float)
            total_recuperavel = df['NUM'].sum()
            
            # Métricas
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f'<div class="metric-card"><h4>TOTAL RECUPERÁVEL</h4><h2 style="color:#BFAF83;">R$ {total_recuperavel:,.2f}</h2></div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div class="metric-card"><h4>DÉBITOS IDENTIFICADOS</h4><h2 style="color:#BFAF83;">{len(df)}</h2></div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(df[['DATA', 'CATEGORIA', 'VALOR', 'HISTÓRICO']], use_container_width=True)
            
            # Exportação
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Baixar Laudo de Auditoria", csv, "auditoria_edson_medeiros.csv", "text/csv")
        else:
            st.warning("Nenhum débito foi identificado com os parâmetros atuais. Verifique se o PDF possui camada de texto.")

st.markdown("<br><br><p style='text-align:right; font-family:serif; font-style:italic;'>Edson Medeiros</p>", unsafe_allow_html=True)
