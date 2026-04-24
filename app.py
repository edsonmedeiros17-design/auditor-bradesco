import streamlit as st
import pdfplumber
import pandas as pd
import re

# --- 1. INTERFACE EDSON MEDEIROS ---
st.set_page_config(page_title="Edson Medeiros | Consultoria de Ativos", layout="wide", page_icon="⚖️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');
    .stApp { background-color: #0E1117; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    .main-title { font-family: 'Playfair Display', serif; font-size: 3rem; color: #BFAF83; text-align: center; margin-bottom: 0; }
    .sub-title { text-align: center; color: #64748B; letter-spacing: 2px; text-transform: uppercase; font-size: 0.9rem; margin-bottom: 40px; }
    .metric-card { background: rgba(255,255,255,0.05); border: 1px solid #BFAF83; border-radius: 10px; padding: 20px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- 2. RÚBRICAS OFICIAIS ---
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

# --- 3. MOTOR DE AUDITORIA COM TRAVA DE PROXIMIDADE ---
def realizar_auditoria(arquivo, rubricas_alvo):
    resultados = []
    cesto_acumulador = []
    
    with pdfplumber.open(arquivo) as pdf:
        for page in pdf.pages:
            texto_extraido = page.extract_text(x_tolerance=3, y_tolerance=3)
            if not texto_extraido: continue
            
            linhas = texto_extraido.split('\n')
            
            # Controle de proximidade para não "pular" linhas demais buscando valor
            linha_da_ultima_rubrica = -1
            
            for i, linha in enumerate(linhas):
                linha_up = linha.upper()
                match_data = re.search(r"(\d{2}/\d{2}/\d{2,4})", linha)
                # Ignora valores com % (taxas) e foca em valores financeiros
                match_valor = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})(?!\s*%)", linha)
                
                # Identifica Rubrica
                rubrica_detectada = None
                if "%" not in linha:
                    for nome in rubricas_alvo:
                        if re.search(RUBRICAS_MESTRE[nome], linha_up):
                            # EXCEÇÃO: Se for Transferência, ignora mesmo que tenha palavra-chave
                            if "TRANSF" not in linha_up:
                                rubrica_detectada = nome
                                break
                
                # SE ACHOU RÚBRICA
                if rubrica_detectada:
                    valor = match_valor.group(1) if match_valor else "PENDENTE"
                    cesto_acumulador.append({
                        "CATEGORIA": rubrica_detectada,
                        "VALOR": valor,
                        "HISTÓRICO": linha_up[:65]
                    })
                    linha_da_ultima_rubrica = i
                
                # SE ACHOU VALOR: Só aceita se a rubrica estiver na mesma linha ou na anterior
                elif match_valor and cesto_acumulador:
                    if cesto_acumulador[-1]["VALOR"] == "PENDENTE":
                        # TRAVA: O valor deve estar no máximo 1 linha abaixo da rubrica
                        if i - linha_da_ultima_rubrica <= 1:
                            cesto_acumulador[-1]["VALOR"] = match_valor.group(1)
                        else:
                            # Se estiver longe demais, descarta a rubrica pendente (evita erro ANEXO 1)
                            cesto_acumulador.pop()

                # SELAGEM POR DATA (Data Inferior conforme ANEXO 2)
                if match_data:
                    data_encontrada = match_data.group(1)
                    if cesto_acumulador:
                        for item in cesto_acumulador:
                            if item["VALOR"] != "PENDENTE":
                                item["DATA"] = data_encontrada
                                resultados.append(item)
                        cesto_acumulador = []

    return resultados

# --- 4. DASHBOARD ---
st.markdown('<h1 class="main-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Relatório de Auditoria Técnica - Edson Medeiros</p>', unsafe_allow_html=True)

st.sidebar.markdown("### 🔍 FILTROS")
selecionadas = [r for r in RUBRICAS_MESTRE.keys() if st.sidebar.checkbox(r, value=True)]

upload = st.file_uploader("📂 ARRASTE O EXTRATO BANCÁRIO (PDF)", type=["pdf"])

if upload:
    with st.spinner("Refinando busca e validando proximidade de valores..."):
        dados = realizar_auditoria(upload, selecionadas)
        if dados:
            df = pd.DataFrame(dados)
            df = df[['DATA', 'CATEGORIA', 'VALOR', 'HISTÓRICO']]
            df['V_NUM'] = df['VALOR'].str.replace('.','', regex=False).str.replace(',','.', regex=False).astype(float)
            total = df['V_NUM'].sum()
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f'<div class="metric-card"><h4>TOTAL RECUPERÁVEL</h4><h2 style="color:#BFAF83;">R$ {total:,.2f}</h2></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="metric-card"><h4>OCORRÊNCIAS</h4><h2 style="color:#BFAF83;">{len(df)}</h2></div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(df[['DATA', 'CATEGORIA', 'VALOR', 'HISTÓRICO']], use_container_width=True)
            st.download_button("📥 BAIXAR RELATÓRIO", df.to_csv(index=False).encode('utf-8-sig'), "laudo_edson.csv", "text/csv")
        else:
            st.info("Nenhum débito encontrado com as rústicas e critérios de proximidade.")

st.markdown("<br><br><p style='text-align:right; font-family:serif; font-style:italic; color:#BFAF83;'>Edson Medeiros</p>", unsafe_allow_html=True)
