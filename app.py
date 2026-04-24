import streamlit as st
import pdfplumber
import pandas as pd
import re

# --- 1. CONFIGURAÇÃO E IDENTIDADE VISUAL (PRESERVADA) ---
st.set_page_config(page_title="Edson Medeiros | Consultoria de Ativos", layout="wide", page_icon="⚖️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');
    .stApp { background-color: #0E1117; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    .main-title { font-family: 'Playfair Display', serif; font-size: 3rem; color: #BFAF83; text-align: center; margin-bottom: 0; }
    .sub-title { text-align: center; color: #64748B; letter-spacing: 2px; text-transform: uppercase; font-size: 0.8rem; margin-bottom: 40px; }
    .metric-card { background: rgba(255,255,255,0.05); border: 1px solid #BFAF83; border-radius: 10px; padding: 20px; text-align: center; }
    
    /* Estilo para as Rubricas Identificadas */
    .rubrica-badge {
        display: inline-block;
        padding: 5px 12px;
        margin: 5px;
        border-radius: 20px;
        background: rgba(191, 175, 131, 0.15);
        border: 1px solid #BFAF83;
        color: #BFAF83;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .resumo-container {
        background: rgba(255,255,255,0.02);
        border-radius: 10px;
        padding: 15px;
        margin-top: 20px;
        border-left: 4px solid #BFAF83;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. MOTOR DE BUSCA (CONGELADO - PROTEÇÃO ATEEM) ---
RUBRICAS_MESTRE = {
    "CESTA/PACOTE": r"CESTA|PACOTE|TARIFA BANCARIA",
    "MORA DE OPERAÇÃO": r"MORA OPERACAO|MORA DE OPERAÇÃO",
    "MORA CREDITO PESSOAL": r"MORA CREDITO PESSOAL|MORA CRED PESS",
    "MORA OPERACAO DE CREDITO": r"MORA OPERACAO DE CREDITO|MORA OPER CRED",
    "BX": r"\bBX\b",
    "PARCELA CREDITO PESSOAL": r"PARCELA CREDITO PESSOAL|PARC CRED PESS",
    "GASTOS CARTAO": r"GASTOS CARTAO|CARTAO DE CREDITO",
    "SEGURO": r"SEGURO|SEGURADORA|SEG\b",
    "ADIANT. DEPOSITANTE": r"ADIANT|ADIANTAMENTO DEPOSITANTE",
    "APLIC": r"APLICACAO|APLIC\b",
    "ENCARGOS": r"ENCARGOS|ENCARGO|ENC LIMITE|LIMITE DE CRED",
    "ANUIDADE": r"ANUIDADE|CARTAO CREDITO ANUIDADE",
    "OPERACOES VENCIDAS": r"OPERACOES VENCIDAS|OPERAÇÕES VENCIDAS",
    "DIV. EM ATRASO": r"DIV\. EM ATRASO|DIVIDA EM ATRASO"
}

TERMOS_EXCLUSAO = r"TRANSF|SALDO|SDO|TRANSFERENCIA|SALARIO"

def realizar_auditoria(arquivo, rubricas_alvo):
    resultados = []
    cesto_acumulador = []
    with pdfplumber.open(arquivo) as pdf:
        for page in pdf.pages:
            texto = page.extract_text(x_tolerance=3, y_tolerance=3)
            if not texto: continue
            linhas = texto.split('\n')
            for linha in linhas:
                linha_up = linha.upper()
                match_data = re.search(r"(\d{2}/\d{2}/\d{2,4})", linha)
                match_valor = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})(?!\s*%)", linha)
                
                if re.search(TERMOS_EXCLUSAO, linha_up):
                    cesto_acumulador = [item for item in cesto_acumulador if item["VALOR"] != "PENDENTE"]
                    continue 

                rubrica_detectada = None
                if "%" not in linha:
                    for nome in rubricas_alvo:
                        if re.search(RUBRICAS_MESTRE[nome], linha_up):
                            rubrica_detectada = nome
                            break
                
                if rubrica_detectada:
                    valor = match_valor.group(1) if match_valor else "PENDENTE"
                    cesto_acumulador.append({"CATEGORIA": rubrica_detectada, "VALOR": valor, "HISTÓRICO": linha_up[:65]})
                elif match_valor and cesto_acumulador:
                    if cesto_acumulador[-1]["VALOR"] == "PENDENTE":
                        cesto_acumulador[-1]["VALOR"] = match_valor.group(1)

                if match_data:
                    data_encontrada = match_data.group(1)
                    if cesto_acumulador:
                        for item in cesto_acumulador:
                            if item["VALOR"] != "PENDENTE":
                                item["DATA"] = data_encontrada
                                resultados.append(item)
                        cesto_acumulador = []
    return resultados

# --- 3. DASHBOARD ---
st.markdown('<h1 class="main-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Gestão Especializada - Edson Medeiros</p>', unsafe_allow_html=True)

st.sidebar.markdown("### 🔍 CONFIGURAÇÕES")
selecionadas = [r for r in RUBRICAS_MESTRE.keys() if st.sidebar.checkbox(r, value=True)]

upload = st.file_uploader("📂 ARRASTE O EXTRATO BANCÁRIO (PDF)", type=["pdf"])

if upload:
    with st.spinner("Auditando movimentações..."):
        dados = realizar_auditoria(upload, selecionadas)
        if dados:
            df = pd.DataFrame(dados)
            df['V_NUM'] = df['VALOR'].str.replace('.','', regex=False).str.replace(',','.', regex=False).astype(float)
            
            # --- SEÇÃO DE MÉTRICAS ---
            c1, c2 = st.columns(2)
            with c1: st.markdown(f'<div class="metric-card"><h4>VALOR TOTAL</h4><h2 style="color:#BFAF83;">R$ {df["V_NUM"].sum():,.2f}</h2></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="metric-card"><h4>DÉBITOS</h4><h2 style="color:#BFAF83;">{len(df)}</h2></div>', unsafe_allow_html=True)

            # --- SEÇÃO DE RESUMO ATUALIZADA ---
            st.markdown('<div class="resumo-container">', unsafe_allow_html=True)
            st.markdown('<p style="color: #64748B; font-size: 0.8rem; margin-bottom: 10px; font-weight: 600;">DESCONTOS ENCONTRADOS:</p>', unsafe_allow_html=True)
            
            rubricas_unicas = df['CATEGORIA'].unique()
            badge_html = "".join([f'<span class="rubrica-badge">{r}</span>' for r in rubricas_unicas])
            st.markdown(badge_html, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # --- TABELA E EXPORTAÇÃO ---
            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(df[['DATA', 'CATEGORIA', 'VALOR', 'HISTÓRICO']], use_container_width=True)
            st.download_button("📥 BAIXAR LAUDO", df[['DATA', 'CATEGORIA', 'VALOR', 'HISTÓRICO']].to_csv(index=False).encode('utf-8-sig'), "laudo_ativos.csv")
        else:
            st.info("Nenhuma rubrica identificada com os filtros atuais.")

st.markdown("<br><br><p style='text-align:right; font-family:serif; font-style:italic; color:#BFAF83;'>Edson Medeiros</p>", unsafe_allow_html=True)
