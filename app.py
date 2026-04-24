import streamlit as st
import pdfplumber
import pandas as pd
import re

# --- 1. CONFIGURAÇÃO DE INTERFACE LUXUOSA ---
st.set_page_config(page_title="Edson Medeiros | Consultoria Financeiro", layout="wide", page_icon="⚖️")

ESTILO_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600&family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@300;400;600&family=Great+Vibes&display=swap');
:root { --navy: #0F172A; --gold: #BFAF83; --off-white: #F8F9FA; }
.stApp { background: radial-gradient(circle at center, #1E293B 0%, #0F172A 100%); color: var(--off-white); font-family: 'Inter', sans-serif; }
.consultoria-title { font-family: 'Playfair Display', serif !important; font-size: 3.5rem !important; background: linear-gradient(180deg, #FFFFFF 0%, #BFAF83 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; line-height: 1.1; margin-bottom: 0px; }
.impact-card { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(191, 175, 131, 0.3); border-radius: 15px; padding: 20px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
.footer-name { font-family: 'Great Vibes', cursive; color: var(--gold); font-size: 2.2rem; text-align: right; }
</style>
"""
st.markdown(ESTILO_CSS, unsafe_allow_html=True)

# --- 2. PARÂMETROS DE BUSCA EXATOS (RESTABELECIDOS) ---
DICIONARIO_ALVOS = {
    "CESTA/PACOTE": r"CESTA|PACOTE|TARIFA BANCARIA|CESTA B\.EXPRESSO",
    "MORA DE OPERAÇÃO": r"MORA OPERACAO|MORA DE OPERAÇÃO",
    "MORA CREDITO PESSOAL": r"MORA CRED PESS|MORA CREDITO PESSOAL",
    "MORA OPERACAO DE CREDITO": r"MORA OPERACAO DE CREDITO|MORA OPER CRED",
    "BX": r"BX ",
    "PARCELA CREDITO PESSOAL": r"PARC CRED PESS|PARCELA CREDITO PESSOAL",
    "GASTOS CARTAO DE CREDITO": r"GASTOS CARTAO|CARTAO DE CREDITO|ANUIDADE",
    "SEGURO": r"SEGURO|SEGURADORA|SEG ",
    "ADIANT. DEPOSITANTE": r"ADIANT|ADIANTAMENTO DEPOSITANTE",
    "APLICACAO": r"APLICACAO|APLIC ",
    "ENCARGOS": r"ENCARGOS|ENC LIMITE|ENC LIM CREDITO|ENCARGO",
    "ANUIDADE": r"ANUIDADE|CARTAO CREDITO ANUIDADE",
    "OPERACOES VENCIDAS": r"OPERACOES VENCIDAS|OPERAÇÕES VENCIDAS",
    "DIV. EM ATRASO": r"DIV\. EM ATRASO|DIVIDA EM ATRASO",
    "IOF": r"IOF S/ UTILIZACAO|IOF UTIL LIMITE|IOF"
}

# --- 3. MOTOR DE EXTRAÇÃO POR COLUNA (PRECISÃO BRADESCO) ---
def realizar_auditoria(arquivo):
    resultados = []
    buffer_sem_data = []
    ultima_data_valida = None
    
    with pdfplumber.open(arquivo) as pdf:
        for page in pdf.pages:
            # Extração de tabela com estratégia de linhas horizontais para não misturar rubricas
            tabela = page.extract_table({
                "vertical_strategy": "lines", 
                "horizontal_strategy": "text",
                "snap_tolerance": 3,
            })
            
            if not tabela: continue
            
            for linha in tabela:
                # Filtragem de segurança: remove células nulas
                linha_limpa = [str(c).strip() if c else "" for c in linha]
                if len(linha_limpa) < 5: continue # Garante que a linha tem colunas suficientes

                # MAPEAMENTO DE COLUNAS (PADRÃO BRADESCO CELULAR)
                col_data = linha_limpa[0]
                col_historico = linha_limpa[1].upper()
                col_credito = linha_limpa[-3] # Crédito costuma ser a antepenúltima
                col_debito = linha_limpa[-2]   # Débito costuma ser a penúltima

                # 1. ATUALIZA DATA ÂNCORA
                match_data = re.search(r"(\d{2}/\d{2}/\d{2,4})", col_data)
                if match_data:
                    ultima_data_valida = match_data.group(1)

                # 2. IDENTIFICA SE É UM DÉBITO REAL
                # Ignora se houver valor no crédito e nada no débito
                valor_texto = col_debito.replace('.', '').replace(',', '.')
                try:
                    valor_num = float(valor_texto) if valor_texto else 0
                except:
                    valor_num = 0

                # Só processa se o valor de débito for maior que zero
                if valor_num > 0:
                    # 3. BUSCA RUBRICA NO HISTÓRICO
                    for cat, regex in DICIONARIO_ALVOS.items():
                        if re.search(regex, col_historico):
                            item = {
                                "DATA": ultima_data_valida,
                                "CATEGORIA": cat,
                                "VALOR DÉBITO (R$)": col_debito,
                                "HISTÓRICO": col_historico[:80]
                            }
                            
                            if ultima_data_valida:
                                resultados.append(item)
                            else:
                                buffer_sem_data.append(item)
                            break

                # 4. VINCULAÇÃO RETROATIVA (Caso a data apareça na linha seguinte)
                if ultima_data_valida and buffer_sem_data:
                    for b in buffer_sem_data:
                        b["DATA"] = ultima_data_valida
                        resultados.append(b)
                    buffer_sem_data = []

    return resultados

# --- 4. INTERFACE STREAMLIT ---
st.markdown('<h1 class="consultoria-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#BFAF83; letter-spacing:2px; margin-bottom:30px;'>SISTEMA DE AUDITORIA TÉCNICA ESPECIALIZADA</p>", unsafe_allow_html=True)

st.sidebar.markdown("### RUBRICAS DE AUDITORIA")
selecionados = [k for k in DICIONARIO_ALVOS.keys() if st.sidebar.checkbox(k, value=True)]

upload = st.file_uploader("📂 ARRASTE O EXTRATO BANCÁRIO (PDF)", type=["pdf"])

if upload:
    with st.spinner('Analisando colunas e vinculando datas...'):
        dados = realizar_auditoria(upload)
        if dados:
            df = pd.DataFrame(dados)
            df = df[df['CATEGORIA'].isin(selecionados)]
            
            if not df.empty:
                total = sum([float(str(v).replace('.','').replace(',','.')) for v in df["VALOR DÉBITO (R$)"]])
                
                c1, c2 = st.columns(2)
                c1.markdown(f'<div class="impact-card"><h4>TOTAL RECUPERÁVEL</h4><h2 style="color:#BFAF83;">R$ {total:,.2f}</h2></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="impact-card"><h4>DÉBITOS IDENTIFICADOS</h4><h2 style="color:#BFAF83;">{len(df)}</h2></div>', unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.dataframe(df[['DATA', 'CATEGORIA', 'VALOR DÉBITO (R$)', 'HISTÓRICO']], use_container_width=True)
                st.download_button("📥 BAIXAR LAUDO TÉCNICO (CSV)", df.to_csv(index=False).encode('utf-8-sig'), "laudo_auditoria.csv")
            else:
                st.info("Nenhuma rubrica selecionada foi encontrada no documento.")
        else:
            st.warning("Atenção: Não foram encontrados débitos correspondentes às rubricas neste arquivo.")

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown('<p class="footer-name">Edson Medeiros</p>', unsafe_allow_html=True)
