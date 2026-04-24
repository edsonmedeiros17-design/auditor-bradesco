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

# --- 2. OS 14 PARÂMETROS DE BUSCA SELECIONÁVEIS ---
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
    "ENCARGOS": r"ENCARGOS|ENC LIMITE|ENCARGO|LIMITE DE CRED",
    "ANUIDADE": r"ANUIDADE|CARTAO CREDITO ANUIDADE",
    "OPERACOES VENCIDAS": r"OPERACOES VENCIDAS|OPERAÇÕES VENCIDAS",
    "DIV. EM ATRASO": r"DIV\. EM ATRASO|DIVIDA EM ATRASO"
}

# --- 3. SIDEBAR COM AS RÚBRICAS SOLICITADAS ---
st.sidebar.markdown("### 🔍 PARÂMETROS DE BUSCA")
selecionadas = []
for r in RUBRICAS_MESTRE.keys():
    if st.sidebar.checkbox(r, value=True):
        selecionadas.append(r)

# --- 4. MOTOR DE AUDITORIA (LÓGICA DE BLOCO E DATA INFERIOR) ---
def realizar_auditoria(arquivo, rubricas_alvo):
    resultados = []
    cesto_acumulador = [] # Acumula débitos de um bloco antes de achar a data
    
    with pdfplumber.open(arquivo) as pdf:
        for page in pdf.pages:
            # Aumentamos a tolerância para capturar valores que o banco joga pro lado
            texto_extraido = page.extract_text(x_tolerance=3, y_tolerance=3)
            if not texto_extraido: continue
            
            linhas = texto_extraido.split('\n')
            
            for linha in linhas:
                linha_up = linha.upper()
                
                # Identifica Data e Valor
                match_data = re.search(r"(\d{2}/\d{2}/\d{2,4})", linha)
                match_valor = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})", linha)
                
                # Procura Rubrica
                rubrica_detectada = None
                for nome in rubricas_alvo:
                    if re.search(RUBRICAS_MESTRE[nome], linha_up):
                        rubrica_detectada = nome
                        break
                
                # SE ACHOU RÚBRICA: Guarda no cesto (mesmo que o valor esteja na linha de baixo)
                if rubrica_detectada:
                    valor = match_valor.group(1) if match_valor else "PENDENTE"
                    cesto_acumulador.append({
                        "CATEGORIA": rubrica_detectada,
                        "VALOR": valor,
                        "HISTÓRICO": linha_up[:65]
                    })
                
                # SE ACHOU VALOR MAS NÃO TEM RÚBRICA (Pode ser o valor da rubrica da linha de cima)
                elif match_valor and cesto_acumulador:
                    if cesto_acumulador[-1]["VALOR"] == "PENDENTE":
                        cesto_acumulador[-1]["VALOR"] = match_valor.group(1)

                # SE ACHOU DATA (O MOMENTO DA VERDADE - ANEXO 2)
                if match_data:
                    data_encontrada = match_data.group(1)
                    
                    # Se temos itens no cesto, todos pertencem a esta data (Data Inferior)
                    if cesto_acumulador:
                        for item in cesto_acumulador:
                            if item["VALOR"] != "PENDENTE":
                                item["DATA"] = data_encontrada
                                resultados.append(item)
                        cesto_acumulador = [] # Limpa para o próximo bloco

    return resultados

# --- 5. DASHBOARD ---
st.markdown('<h1 class="main-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Auditoria Técnica Especializada - Edson Medeiros</p>', unsafe_allow_html=True)

upload = st.file_uploader("📂 ARRASTE O EXTRATO BANCÁRIO (PDF)", type=["pdf"])

if upload:
    with st.spinner("Processando blocos de movimentação e validando datas..."):
        dados = realizar_auditoria(upload, selecionadas)
        
        if dados:
            df = pd.DataFrame(dados)
            df = df[['DATA', 'CATEGORIA', 'VALOR', 'HISTÓRICO']]
            
            # Cálculo de Total
            df['V_NUM'] = df['VALOR'].str.replace('.','', regex=False).str.replace(',','.', regex=False).astype(float)
            total = df['V_NUM'].sum()
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f'<div class="metric-card"><h4>TOTAL RECUPERÁVEL</h4><h2 style="color:#BFAF83;">R$ {total:,.2f}</h2></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="metric-card"><h4>DÉBITOS IDENTIFICADOS</h4><h2 style="color:#BFAF83;">{len(df)}</h2></div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(df[['DATA', 'CATEGORIA', 'VALOR', 'HISTÓRICO']], use_container_width=True)
            
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 BAIXAR LAUDO COMPLETO", csv, "auditoria_edson_medeiros.csv", "text/csv")
        else:
            st.info("Nenhuma rubrica identificada. Verifique se as opções no menu lateral estão marcadas.")

st.markdown("<br><br><p style='text-align:right; font-family:serif; font-style:italic; color:#BFAF83;'>Edson Medeiros</p>", unsafe_allow_html=True)
