import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime

# --- 1. INTERFACE EDSON MEDEIROS ---
st.set_page_config(page_title="Edson Medeiros | Consultoria de Ativos", layout="wide", page_icon="⚖️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');
    .stApp { background-color: #0E1117; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    .main-title { font-family: 'Playfair Display', serif; font-size: 3rem; color: #BFAF83; text-align: center; margin-bottom: 0; }
    .sub-title { text-align: center; color: #64748B; letter-spacing: 2px; text-transform: uppercase; font-size: 0.9rem; margin-bottom: 40px; }
    .metric-card { background: rgba(255,255,255,0.05); border: 1px solid #BFAF83; border-radius: 10px; padding: 20px; text-align: center; }
    .relatorio-titulo { font-family: 'Playfair Display', serif; font-size: 1.8rem; color: #BFAF83; text-align: center; margin-top: 40px; margin-bottom: 10px; }
    .relatorio-subtitulo { text-align: center; color: #64748B; font-size: 0.95rem; margin-bottom: 30px; }
</style>
""", unsafe_allow_html=True)

# --- 2. RÚBRICAS E TERMOS DE EXCLUSÃO ---
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

# --- 3. MOTOR DE AUDITORIA ---
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
                
                # Identifica Data e Valor
                match_data = re.search(r"(\d{2}/\d{2}/\d{2,4})", linha)
                match_valor = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})(?!\s*%)", linha)
                
                # Reset por Termos de Exclusão
                if re.search(TERMOS_EXCLUSAO, linha_up):
                    cesto_acumulador = [item for item in cesto_acumulador if item["VALOR"] != "PENDENTE"]
                    continue 

                # Busca Rubrica
                rubrica_detectada = None
                if "%" not in linha:
                    for nome in rubricas_alvo:
                        if re.search(RUBRICAS_MESTRE[nome], linha_up):
                            rubrica_detectada = nome
                            break
                
                # Lógica de Captura
                if rubrica_detectada:
                    valor = match_valor.group(1) if match_valor else "0,00" # Evita "PENDENTE" para não quebrar cálculos
                    cesto_acumulador.append({
                        "CATEGORIA": rubrica_detectada,
                        "VALOR": valor,
                        "HISTÓRICO": linha_up[:65]
                    })
                
                elif match_valor and cesto_acumulador:
                    if cesto_acumulador[-1]["VALOR"] == "0,00":
                        cesto_acumulador[-1]["VALOR"] = match_valor.group(1)

                # Selagem por Data
                if match_data:
                    data_str = match_data.group(1)
                    if cesto_acumulador:
                        for item in cesto_acumulador:
                            item["DATA"] = data_str
                            resultados.append(item)
                        cesto_acumulador = []

    return resultados

# --- 4. PROCESSAMENTO DE DADOS ---
def processar_dataframe(dados):
    if not dados:
        return None
    
    df = pd.DataFrame(dados)
    
    # Conversão de Valores (Garante que seja numérico)
    df['V_NUM'] = df['VALOR'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
    
    # Padronização de Datas para Ordenação
    def normalizar_data(d):
        p = d.split('/')
        if len(p[2]) == 2: p[2] = "20" + p[2]
        return "/".join(p)
    
    df['DATA_OBJ'] = pd.to_datetime(df['DATA'].apply(normalizar_data), format='%d/%m/%Y', errors='coerce')
    df = df.sort_values(by='DATA_OBJ', ascending=True)
    
    return df

def gerar_relatorio_consolidado(df):
    # Pivot Table usando a data original (string) mas mantendo a ordem do DATA_OBJ
    relatorio = df.pivot_table(
        index=['DATA_OBJ', 'DATA'],
        columns='CATEGORIA',
        values='V_NUM',
        aggfunc='sum',
        fill_value=0
    )
    
    # Limpa o índice multinível para ficar apenas com a DATA formatada
    relatorio = relatorio.reset_index(level=0, drop=True)
    
    # Adiciona Totais
    relatorio['TOTAL POR DATA'] = relatorio.sum(axis=1)
    
    # Linha de Totais Finais
    totais_finais = relatorio.sum()
    totais_finais.name = 'TOTAL POR CATEGORIA'
    relatorio = pd.concat([relatorio, totais_finais.to_frame().T])
    
    return relatorio

# --- 5. DASHBOARD ---
st.markdown('<h1 class="main-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Auditoria Técnica Especializada - Edson Medeiros</p>', unsafe_allow_html=True)

st.sidebar.markdown("### 🔍 FILTROS")
selecionadas = [r for r in RUBRICAS_MESTRE.keys() if st.sidebar.checkbox(r, value=True)]

upload = st.file_uploader("📂 ARRASTE O EXTRATO BANCÁRIO (PDF)", type=["pdf"])

if upload:
    with st.spinner("Analisando dados..."):
        dados_brutos = realizar_auditoria(upload, selecionadas)
        df = processar_dataframe(dados_brutos)
        
        if df is not None and not df.empty:
            total_geral = df['V_NUM'].sum()
            
            # Métricas no Topo
            c1, c2 = st.columns(2)
            with c1: st.markdown(f'<div class="metric-card"><h4>TOTAL RECUPERÁVEL</h4><h2 style="color:#BFAF83;">R$ {total_geral:,.2f}</h2></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="metric-card"><h4>OCORRÊNCIAS</h4><h2 style="color:#BFAF83;">{len(df)}</h2></div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Relatório Consolidado (Tabela Dinâmica)
            st.markdown('<h2 class="relatorio-titulo">📊 Relatório Consolidado</h2>', unsafe_allow_html=True)
            st.markdown('<p class="relatorio-subtitulo">Categorias em colunas organizadas cronologicamente</p>', unsafe_allow_html=True)
            
            relatorio = gerar_relatorio_consolidado(df)
            
            # Exibição Formatada
            relatorio_display = relatorio.copy()
            for col in relatorio_display.columns:
                relatorio_display[col] = relatorio_display[col].apply(lambda x: f"R$ {x:,.2f}" if x != 0 else "-")
            
            st.dataframe(relatorio_display, use_container_width=True)
            
            # Detalhamento por Abas
            st.markdown('<h3 style="color:#BFAF83; text-align:center; margin-top:30px;">📋 Detalhamento por Categoria</h3>', unsafe_allow_html=True)
            cats_encontradas = df['CATEGORIA'].unique()
            tabs = st.tabs([f"📌 {c}" for c in cats_encontradas])
            
            for tab, categoria in zip(tabs, cats_encontradas):
                with tab:
                    df_cat = df[df['CATEGORIA'] == categoria][['DATA', 'VALOR', 'HISTÓRICO']]
                    st.dataframe(df_cat, use_container_width=True)
                    # Soma segura do valor numérico já processado
                    soma_cat = df[df['CATEGORIA'] == categoria]['V_NUM'].sum()
                    st.markdown(f"<p style='text-align:right; color:#BFAF83; font-weight:bold;'>Subtotal {categoria}: R$ {soma_cat:,.2f}</p>", unsafe_allow_html=True)
            
            # Botões de Download
            st.markdown('<h3 style="color:#BFAF83; text-align:center; margin-top:30px;">📥 Baixar Laudos Técnicos</h3>', unsafe_allow_html=True)
            col_down1, col_down2 = st.columns(2)
            
            with col_down1:
                csv_consolidado = relatorio.to_csv().encode('utf-8-sig')
                st.download_button("📊 Baixar Tabela Consolidada (CSV)", csv_consolidado, "relatorio_consolidado.csv", "text/csv")
            
            with col_down2:
                csv_detalhado = df[['DATA', 'CATEGORIA', 'VALOR', 'HISTÓRICO']].to_csv(index=False).encode('utf-8-sig')
                st.download_button("📋 Baixar Lista Detalhada (CSV)", csv_detalhado, "laudo_detalhado.csv", "text/csv")
        else:
            st.info("Nenhum débito encontrado com os critérios selecionados.")

st.markdown("<br><br><p style='text-align:right; font-family:serif; font-style:italic; color:#BFAF83;'>Edson Medeiros</p>", unsafe_allow_html=True)
