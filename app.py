import streamlit as st
import pdfplumber
import pandas as pd
import re

# --- 1. CONFIGURAÇÃO DE INTERFACE (PADRÃO EDSON MEDEIROS) ---
st.set_page_config(page_title="Edson Medeiros | Auditoria de Ativos", layout="wide", page_icon="⚖️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');
    .stApp { background-color: #0E1117; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    .main-title { font-family: 'Playfair Display', serif; font-size: 3rem; color: #BFAF83; text-align: center; margin-bottom: 0; }
    .sub-title { text-align: center; color: #64748B; letter-spacing: 2px; text-transform: uppercase; font-size: 0.9rem; margin-bottom: 40px; }
    .metric-card { background: rgba(255,255,255,0.05); border: 1px solid #BFAF83; border-radius: 10px; padding: 20px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- 2. AS 14 RÚBRICAS SOLICITADAS (DEFINIÇÃO DE REGEX) ---
# Adicionei variações comuns para garantir que o robô não ignore abreviações bancárias
RUBRICAS_MESTRE = {
    "CESTA/PACOTE": r"CESTA|PACOTE|TARIFA BANCARIA",
    "MORA DE OPERAÇÃO": r"MORA OPERACAO|MORA DE OPERAÇÃO",
    "MORA CREDITO PESSOAL": r"MORA CREDITO PESSOAL|MORA CRED PESS",
    "MORA OPERACAO DE CREDITO": r"MORA OPERACAO DE CREDITO|MORA OPER CRED",
    "BX": r"\bBX\b",
    "PARCELA CREDITO PESSOAL": r"PARCELA CREDITO PESSOAL|PARC CRED PESS",
    "GASTOS CARTAO DE CREDITO": r"GASTOS CARTAO|CARTAO DE CREDITO",
    "SEGURO": r"SEGURO|SEGURADORA|SEG\b",
    "ADIANT": r"ADIANT|ADIANTAMENTO DEPOSITANTE",
    "APLIC": r"APLICACAO|APLIC\b",
    "ENCARGOS": r"ENCARGOS|ENC LIMITE|ENCARGO",
    "ANUIDADE": r"ANUIDADE|CARTAO CREDITO ANUIDADE",
    "OPERACOES VENCIDAS": r"OPERACOES VENCIDAS|OPERAÇÕES VENCIDAS|OP VENC",
    "DIV. EM ATRASO": r"DIV\. EM ATRASO|DIVIDA EM ATRASO"
}

# --- 3. SIDEBAR - PARÂMETROS DE BUSCA SELECIONÁVEIS ---
st.sidebar.markdown("### 🔍 SELECIONAR RÚBRICAS")
st.sidebar.info("Marque as rúbricas que deseja incluir na auditoria atual.")

selecionadas = []
for rubrica in RUBRICAS_MESTRE.keys():
    if st.sidebar.checkbox(rubrica, value=True):
        selecionadas.append(rubrica)

# --- 4. MOTOR DE AUDITORIA COM LÓGICA DE DATA INFERIOR ---
def realizar_auditoria(arquivo, rubricas_alvo):
    resultados = []
    cesto_pendente = []
    
    with pdfplumber.open(arquivo) as pdf:
        for page in pdf.pages:
            linhas = page.extract_text().split('\n')
            
            for linha in linhas:
                linha_up = linha.upper()
                
                # Identifica Data (Ex: 08/02/2017)
                match_data = re.search(r"(\d{2}/\d{2}/\d{2,4})", linha)
                
                # Identifica Valor (Ex: 116,11)
                match_valor = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})", linha)
                
                # Busca apenas as rubricas que o Edson selecionou no Sidebar
                rubrica_encontrada = None
                for nome in rubricas_alvo:
                    if re.search(RUBRICAS_MESTRE[nome], linha_up):
                        rubrica_encontrada = nome
                        break
                
                # Se achou rubrica e valor (mas pode não ter data na linha)
                if rubrica_encontrada and match_valor:
                    item = {
                        "CATEGORIA": rubrica_encontrada,
                        "VALOR": match_valor.group(1),
                        "HISTÓRICO": linha_up[:70]
                    }
                    
                    if match_data:
                        item["DATA"] = match_data.group(1)
                        resultados.append(item)
                    else:
                        # Vai para o "Cesto" aguardar a Data Inferior (Conforme ANEXO 2)
                        cesto_pendente.append(item)
                
                # Se encontrar uma data em uma linha sem rubrica (Data de Fechamento do Bloco)
                elif match_data and cesto_pendente:
                    data_inferior = match_data.group(1)
                    for pendente in cesto_pendente:
                        pendente["DATA"] = data_inferior
                        resultados.append(pendente)
                    cesto_pendente = []

    return resultados

# --- 5. EXECUÇÃO E DASHBOARD ---
st.markdown('<h1 class="main-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Gestão Especializada - Edson Medeiros</p>', unsafe_allow_html=True)

upload = st.file_uploader("📂 ARRASTE O EXTRATO BANCÁRIO (PDF)", type=["pdf"])

if upload:
    if not selecionadas:
        st.warning("⚠️ Por favor, selecione pelo menos uma rúbrica no menu lateral.")
    else:
        with st.spinner("Auditando movimentações com lógica de data inferior..."):
            dados = realizar_auditoria(upload, selecionadas)
            
            if dados:
                df = pd.DataFrame(dados)
                
                # Conversão para cálculo
                df['V_NUM'] = df['VALOR'].str.replace('.','').str.replace(',','.').astype(float)
                total = df['V_NUM'].sum()
                
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f'<div class="metric-card"><h4>VALOR RECUPERÁVEL</h4><h2 style="color:#BFAF83;">R$ {total:,.2f}</h2></div>', unsafe_allow_html=True)
                with c2:
                    st.markdown(f'<div class="metric-card"><h4>OCORRÊNCIAS</h4><h2 style="color:#BFAF83;">{len(df)}</h2></div>', unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.dataframe(df[['DATA', 'CATEGORIA', 'VALOR', 'HISTÓRICO']], use_container_width=True)
                
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 BAIXAR LAUDO TÉCNICO", csv, "auditoria_ativos.csv", "text/csv")
            else:
                st.info("Nenhum débito correspondente às rúbricas selecionadas foi encontrado.")

st.markdown("<br><br><p style='text-align:right; font-family:serif; font-style:italic; color:#BFAF83;'>Edson Medeiros</p>", unsafe_allow_html=True)
