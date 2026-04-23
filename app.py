import streamlit as st
import pdfplumber
import pandas as pd
import re

# --- 1. CONFIGURAÇÃO DE INTERFACE LUXUOSA ---
st.set_page_config(page_title="Edson Medeiros | Consultoria", layout="wide")

ESTILO_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600&family=Playfair+Display:wght@700&family=Inter:wght@300;400;600&display=swap');
:root { --navy: #0F172A; --gold: #BFAF83; }
.stApp { background: radial-gradient(circle, #1E293B 0%, #0F172A 100%); color: #F8F9FA; font-family: 'Inter', sans-serif; }
.consultoria-title { 
    font-family: 'Playfair Display', serif; font-size: 4rem; 
    background: linear-gradient(180deg, #FFFFFF, #BFAF83); 
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
    text-align: center;
}
.impact-card { 
    background: rgba(255, 255, 255, 0.05); border: 1px solid var(--gold); 
    border-radius: 10px; padding: 20px; text-align: center;
}
</style>
"""
st.markdown(ESTILO_CSS, unsafe_allow_html=True)

# --- 2. PARÂMETROS DE BUSCA COMPLETOS (RESTAURADOS) ---
DICIONARIO_ALVOS = {
    "CESTA/PACOTE": r"CESTA|PACOTE|TARIFA BANCARIA|CESTA B\.EXPRESSO",
    "MORA DE OPERAÇÃO": r"MORA OPERACAO|MORA DE OPERAÇÃO",
    "MORA CREDITO PESSOAL": r"MORA CRED PESS|MORA CREDITO PESSOAL",
    "MORA OPERACAO DE CREDITO": r"MORA OPERACAO DE CREDITO|MORA OPER CRED",
    "BX": r"BX ",
    "PARCELA CREDITO PESSOAL": r"PARC CRED PESS|PARCELA CREDITO PESSOAL",
    "GASTOS CARTAO DE CREDITO": r"GASTOS CARTAO|CARTAO DE CREDITO",
    "SEGURO": r"SEGURO|SEGURADORA|SEG ",
    "ADIANT. DEPOSITANTE": r"ADIANT|ADIANTAMENTO DEPOSITANTE",
    "APLICACAO": r"APLICACAO|APLIC ",
    "ENCARGOS": r"ENCARGOS|ENC LIMITE|ENC LIM CREDITO",
    "ANUIDADE": r"ANUIDADE|CARTAO CREDITO ANUIDADE",
    "OPERACOES VENCIDAS": r"OPERACOES VENCIDAS|OPERAÇÕES VENCIDAS",
    "DIV. EM ATRASO": r"DIV\. EM ATRASO|DIVIDA EM ATRASO",
    "IOF": r"IOF S/ UTILIZACAO|IOF UTIL LIMITE"
}

# --- 3. MOTOR DE AUDITORIA (MODO 1 E MODO 2) ---
def realizar_auditoria(arquivo):
    resultados = []
    transacoes_pendentes = [] # Buffer para o MODO 1 (Data Inferior)
    
    with pdfplumber.open(arquivo) as pdf:
        for page in pdf.pages:
            tabela = page.extract_table({"vertical_strategy": "text", "horizontal_strategy": "text", "snap_tolerance": 4})
            if not tabela: continue
            
            for linha in tabela:
                if len(linha) < 4: continue
                
                col_data = str(linha[0]).strip() if linha[0] else ""
                col_hist = str(linha[1]).strip().upper() if linha[1] else ""
                # O débito no Bradesco geralmente é a penúltima coluna antes do saldo
                col_debito = str(linha[-2]).strip() if len(linha) >= 5 else ""
                col_credito = str(linha[-3]).strip() if len(linha) >= 6 else ""

                # FILTRO DE SEGURANÇA: Só processa se houver valor no DÉBITO e nada no CRÉDITO (Azul)
                if col_debito and "," in col_debito and not (col_credito and "," in col_credito):
                    for cat, regex in DICIONARIO_ALVOS.items():
                        if re.search(regex, col_hist):
                            item = {"CATEGORIA": cat, "VALOR DÉBITO (R$)": col_debito, "HISTÓRICO": col_hist}
                            
                            if col_data and re.match(r"\d{2}/\d{2}", col_data):
                                # MODO 2: Data na linha
                                item["DATA"] = col_data
                                resultados.append(item)
                            else:
                                # MODO 1: Aguardando data inferior
                                transacoes_pendentes.append(item)
                            break
                
                # GATILHO MODO 1: Encontrou uma data isolada que ancora as linhas acima
                elif col_data and re.match(r"\d{2}/\d{2}", col_data) and transacoes_pendentes:
                    for p in transacoes_pendentes:
                        p["DATA"] = col_data
                        resultados.append(p)
                    transacoes_pendentes = [] # Limpa buffer
                    
    return resultados

# --- 4. INTERFACE PRINCIPAL ---
st.markdown('<h1 class="consultoria-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)

st.sidebar.markdown("### PARÂMETROS DE AUDITORIA")
selecionados = [k for k in DICIONARIO_ALVOS.keys() if st.sidebar.checkbox(k, value=True)]

upload = st.file_uploader("📂 ARRASTE SEU PDF AQUI", type=["pdf"])

if upload:
    with st.spinner('Auditando extratos e correlacionando datas...'):
        dados = realizar_auditoria(upload)
        if dados:
            df = pd.DataFrame(dados)
            # Ordenação visual: Data primeiro
            if "DATA" in df.columns:
                df = df[['DATA', 'CATEGORIA', 'VALOR DÉBITO (R$)', 'HISTÓRICO']]
            
            c1, c2 = st.columns(2)
            total = sum([float(v.replace('.','').replace(',','.')) for v in df["VALOR DÉBITO (R$)"]])
            c1.markdown(f'<div class="impact-card"><h3>TOTAL RECUPERÁVEL</h3><h2>R$ {total:,.2f}</h2></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="impact-card"><h3>OCORRÊNCIAS</h3><h2>{len(df)}</h2></div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Nenhum débito indevido encontrado nos parâmetros selecionados.")

# --- 5. RODAPÉ 3 PASSOS ---
st.markdown("<br><hr><br>", unsafe_allow_html=True)
ca, cb, cc = st.columns(3)
ca.markdown("**I - Identificação Digital**\nVarredura inteligente de rubricas.")
cb.markdown("**II - Extração Técnica**\nIsolamento de colunas de débito e data.")
cc.markdown("**III - Certificação**\nGeração de laudo técnico especializado.")
