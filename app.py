import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime

# --- 1. CONFIGURAÇÃO E ESTILO ---
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

# --- 2. RÚBRICAS ATUALIZADAS (CONFORME SOLICITADO) ---
RUBRICAS_MESTRE = {
    "CESTA": r"CESTA",
    "PACOTE": r"PACOTE",
    "MORA DE OPERAÇÃO": r"MORA DE OPERAÇÃO|MORA OPERACAO",
    "MORA CREDITO PESSOAL": r"MORA CREDITO PESSOAL|MORA CRED PESS",
    "MORA OPERACAO DE CREDITO": r"MORA OPERACAO DE CREDITO|MORA OPER CRED",
    "BX": r"\bBX\b",
    "PARCELA CREDITO PESSOAL": r"PARCELA CREDITO PESSOAL|PARC CRED PESS",
    "GASTOS CARTAO DE CREDITO": r"GASTOS CARTAO DE CREDITO|CARTAO DE CREDITO|GASTOS CARTAO",
    "SEGURO": r"SEGURO|SEGURADORA|SEG\b",
    "ADIANT": r"ADIANT|ADIANTAMENTO DEPOSITANTE",
    "APLIC": r"APLICACAO|APLIC\b",
    "ENCARGOS": r"ENCARGOS|ENCARGO|ENC LIMITE|LIMITE DE CRED",
    "ANUIDADE": r"ANUIDADE|CARTAO CREDITO ANUIDADE",
    "OPERACOES VENCIDAS": r"OPERACOES VENCIDAS|OPERAÇÕES VENCIDAS",
    "DIV. EM ATRASO": r"DIV\. EM ATRASO|DIVIDA EM ATRASO"
}

TERMOS_EXCLUSAO = r"TRANSF|SALDO|SDO|TRANSFERENCIA|SALARIO"

# --- 3. MOTOR COM LÓGICA DE DATA INFERIOR (MODELO ANEXO 2) ---
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
                
                # 1. Identifica Data e Valor (Trava de %)
                match_data = re.search(r"(\d{2}/\d{2}/\d{2,4})", linha)
                match_valor = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})(?!\s*%)", linha)
                
                # 2. Se a linha for uma transferência ou saldo, limpamos o cesto (RESET)
                # Isso impede que rubricas sem valor sejam associadas erroneamente
                if re.search(TERMOS_EXCLUSAO, linha_up):
                    cesto_acumulador = [item for item in cesto_acumulador if item["VALOR"] != "PENDENTE"]
                    continue 

                # 3. Busca Rubrica
                rubrica_detectada = None
                if "%" not in linha:
                    for nome in rubricas_alvo:
                        if re.search(RUBRICAS_MESTRE[nome], linha_up):
                            rubrica_detectada = nome
                            break
                
                # 4. Lógica de Captura (Acúmulo no Cesto)
                if rubrica_detectada:
                    valor = match_valor.group(1) if match_valor else "PENDENTE"
                    cesto_acumulador.append({
                        "CATEGORIA": rubrica_detectada,
                        "VALOR": valor,
                        "HISTÓRICO": linha_up[:65]
                    })
                
                elif match_valor and cesto_acumulador:
                    # Só preenche se o último item for realmente uma rubrica esperando valor
                    if cesto_acumulador[-1]["VALOR"] == "PENDENTE":
                        cesto_acumulador[-1]["VALOR"] = match_valor.group(1)

                # 5. SELAGEM POR DATA INFERIOR (A LÓGICA DO ANEXO 2)
                # Quando uma data é encontrada, ela carimba todos os itens que estão no cesto acima dela
                if match_data:
                    data_encontrada = match_data.group(1)
                    if cesto_acumulador:
                        for item in cesto_acumulador:
                            # Só selamos se o item tiver um valor capturado
                            if item["VALOR"] != "PENDENTE":
                                item["DATA"] = data_encontrada
                                resultados.append(item)
                        cesto_acumulador = [] # Limpa para o próximo bloco

    return resultados

# --- 4. DASHBOARD ---
st.markdown('<h1 class="main-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Auditoria Técnica Especializada - Edson Medeiros</p>', unsafe_allow_html=True)

# --- BARRA LATERAL COM BOTÕES DE SELEÇÃO EM MASSA ---
st.sidebar.markdown("### 🔍 RUBRICAS DE AUDITORIA")

col_btn1, col_btn2 = st.sidebar.columns(2)
if col_btn1.button("Marcar Todas"):
    for r in RUBRICAS_MESTRE.keys():
        st.session_state[f"cb_{r}"] = True

if col_btn2.button("Desmarcar Todas"):
    for r in RUBRICAS_MESTRE.keys():
        st.session_state[f"cb_{r}"] = False

selecionadas = []
for r in RUBRICAS_MESTRE.keys():
    if f"cb_{r}" not in st.session_state:
        st.session_state[f"cb_{r}"] = True
    if st.sidebar.checkbox(r, key=f"cb_{r}"):
        selecionadas.append(r)

upload = st.file_uploader("📂 ARRASTE O EXTRATO BANCÁRIO (PDF)", type=["pdf"])

if upload:
    with st.spinner("Limpando ruídos e validando transferências..."):
        dados = realizar_auditoria(upload, selecionadas)
        if dados:
            df = pd.DataFrame(dados)
            
            # Tratamento numérico para cálculos
            df['V_NUM'] = df['VALOR'].str.replace('.','', regex=False).str.replace(',','.', regex=False).astype(float)
            
            # Ordenação Cronológica Real
            def fix_date(d):
                p = d.split('/')
                if len(p[2]) == 2: p[2] = "20" + p[2]
                return "/".join(p)
            df['DT_OBJ'] = pd.to_datetime(df['DATA'].apply(fix_date), format='%d/%m/%Y', errors='coerce')
            df = df.sort_values('DT_OBJ', ascending=True)
            
            total = df['V_NUM'].sum()
            
            c1, c2 = st.columns(2)
            with c1: st.markdown(f'<div class="metric-card"><h4>TOTAL RECUPERÁVEL</h4><h2 style="color:#BFAF83;">R$ {total:,.2f}</h2></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="metric-card"><h4>OCORRÊNCIAS</h4><h2 style="color:#BFAF83;">{len(df)}</h2></div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- RELATÓRIO CONSOLIDADO (CATEGORIAS EM COLUNAS) ---
            st.markdown('<h2 style="color:#BFAF83; text-align:center;">📊 Relatório Consolidado</h2>', unsafe_allow_html=True)
            
            # Pivot Table para colocar categorias em colunas
            pivot = df.pivot_table(
                index=['DT_OBJ', 'DATA'],
                columns='CATEGORIA',
                values='V_NUM',
                aggfunc='sum',
                fill_value=0
            ).reset_index(level=0, drop=True)
            
            pivot['TOTAL DIA'] = pivot.sum(axis=1)
            
            # Linha de Totais Gerais
            totais_gerais = pivot.sum()
            totais_gerais.name = 'TOTAL GERAL'
            pivot = pd.concat([pivot, totais_gerais.to_frame().T])
            
            # Formatação para exibição
            pivot_fmt = pivot.copy()
            for col in pivot_fmt.columns:
                pivot_fmt[col] = pivot_fmt[col].apply(lambda x: f"R$ {x:,.2f}" if x != 0 else "-")
            
            st.dataframe(pivot_fmt, use_container_width=True)
            
            # --- EXPORTAÇÃO EXCEL COMPATÍVEL ---
            st.markdown("<br>", unsafe_allow_html=True)
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.download_button("📊 Baixar Tabela Consolidada (Excel)", pivot.to_csv(sep=';').encode('utf-8-sig'), "relatorio_consolidado.csv", "text/csv")
            with col_d2:
                st.download_button("📋 Baixar Laudo Detalhado (Excel)", df[['DATA', 'CATEGORIA', 'VALOR', 'HISTÓRICO']].to_csv(index=False, sep=';').encode('utf-8-sig'), "laudo_detalhado.csv", "text/csv")
        else:
            st.info("Nenhum débito encontrado com as rubricas selecionadas.")

st.markdown("<br><br><p style='text-align:right; font-family:serif; font-style:italic; color:#BFAF83;'>Edson Medeiros</p>", unsafe_allow_html=True)
