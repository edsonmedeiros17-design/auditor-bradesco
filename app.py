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
    .relatorio-titulo { font-family: 'Playfair Display', serif; font-size: 1.8rem; color: #BFAF83; text-align: center; margin-top: 40px; margin-bottom: 20px; }
    .relatorio-subtitulo { text-align: center; color: #64748B; font-size: 0.95rem; margin-bottom: 20px; }
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

# --- 3. MOTOR COM RESET DE MEMÓRIA ---
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
                
                # 1. Identifica Data e Valor
                match_data = re.search(r"(\d{2}/\d{2}/\d{2,4})", linha)
                match_valor = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})(?!\s*%)", linha)
                
                # 2. Reset por Termos de Exclusão
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
                
                # 4. Lógica de Captura
                if rubrica_detectada:
                    valor = match_valor.group(1) if match_valor else "PENDENTE"
                    cesto_acumulador.append({
                        "CATEGORIA": rubrica_detectada,
                        "VALOR": valor,
                        "HISTÓRICO": linha_up[:65]
                    })
                
                elif match_valor and cesto_acumulador:
                    if cesto_acumulador[-1]["VALOR"] == "PENDENTE":
                        cesto_acumulador[-1]["VALOR"] = match_valor.group(1)

                # 5. Selagem por Data (Correção de Ano para 4 dígitos se necessário)
                if match_data:
                    data_str = match_data.group(1)
                    if cesto_acumulador:
                        for item in cesto_acumulador:
                            if item["VALOR"] != "PENDENTE":
                                item["DATA"] = data_str
                                resultados.append(item)
                        cesto_acumulador = []

    return resultados

# --- 4. TRATAMENTO E ORDENAÇÃO DE DADOS ---
def processar_dataframe(dados):
    if not dados:
        return None
    
    df = pd.DataFrame(dados)
    
    # 1. Limpeza e Conversão de Valores
    df['V_NUM'] = df['VALOR'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
    
    # 2. Conversão de Datas para Ordenação Real
    # Tenta lidar com anos de 2 ou 4 dígitos
    def formatar_data(d):
        partes = d.split('/')
        if len(partes[2]) == 2:
            partes[2] = "20" + partes[2] # Assume século 21
        return "/".join(partes)

    df['DATA_OBJ'] = pd.to_datetime(df['DATA'].apply(formatar_data), format='%d/%m/%Y')
    
    # 3. Ordenação Cronológica Crescente
    df = df.sort_values(by='DATA_OBJ', ascending=True).drop(columns=['DATA_OBJ'])
    
    return df

def gerar_relatorio_consolidado(df):
    # Re-adicionar objeto de data temporariamente para garantir ordem no pivot
    def formatar_data(d):
        partes = d.split('/')
        if len(partes[2]) == 2: partes[2] = "20" + partes[2]
        return "/".join(partes)
    
    df_temp = df.copy()
    df_temp['DATA_SORT'] = pd.to_datetime(df_temp['DATA'].apply(formatar_data), format='%d/%m/%Y')
    
    # Pivot Table
    relatorio = df_temp.pivot_table(
        index=['DATA_SORT', 'DATA'],
        columns='CATEGORIA',
        values='V_NUM',
        aggfunc='sum',
        fill_value=0
    )
    
    # Remover o índice de ordenação, mantendo apenas a string da DATA
    relatorio = relatorio.reset_index(level=0, drop=True)
    
    # Adicionar Totais
    relatorio['TOTAL POR DATA'] = relatorio.sum(axis=1)
    totais = relatorio.sum()
    totais.name = 'TOTAL POR CATEGORIA'
    relatorio = pd.concat([relatorio, totais.to_frame().T])
    
    return relatorio

# --- 5. DASHBOARD ---
st.markdown('<h1 class="main-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Auditoria Técnica Especializada - Edson Medeiros</p>', unsafe_allow_html=True)

st.sidebar.markdown("### 🔍 FILTROS")
selecionadas = [r for r in RUBRICAS_MESTRE.keys() if st.sidebar.checkbox(r, value=True)]

upload = st.file_uploader("📂 ARRASTE O EXTRATO BANCÁRIO (PDF)", type=["pdf"])

if upload:
    with st.spinner("Analisando extrato cronologicamente..."):
        dados_brutos = realizar_auditoria(upload, selecionadas)
        df = processar_dataframe(dados_brutos)
        
        if df is not None and not df.empty:
            total = df['V_NUM'].sum()
            
            # Métricas
            c1, c2 = st.columns(2)
            with c1: st.markdown(f'<div class="metric-card"><h4>TOTAL RECUPERÁVEL</h4><h2 style="color:#BFAF83;">R$ {total:,.2f}</h2></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="metric-card"><h4>OCORRÊNCIAS</h4><h2 style="color:#BFAF83;">{len(df)}</h2></div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Relatório Consolidado
            st.markdown('<h2 class="relatorio-titulo">📊 Relatório Consolidado</h2>', unsafe_allow_html=True)
            st.markdown('<p class="relatorio-subtitulo">Visualização por categorias em ordem cronológica</p>', unsafe_allow_html=True)
            
            relatorio = gerar_relatorio_consolidado(df)
            
            # Formatação para exibição
            relatorio_formatado = relatorio.copy()
            for col in relatorio_formatado.columns:
                relatorio_formatado[col] = relatorio_formatado[col].apply(lambda x: f"R$ {x:,.2f}" if x > 0 else "-")
            
            st.dataframe(relatorio_formatado, use_container_width=True)
            
            # Detalhamento por Abas
            st.markdown('<h3 style="color:#BFAF83; text-align:center; margin-top:30px;">📋 Detalhamento por Categoria</h3>', unsafe_allow_html=True)
            categorias = df['CATEGORIA'].unique()
            tabs = st.tabs([f"📌 {cat}" for cat in categorias])
            
            for tab, categoria in zip(tabs, categorias):
                with tab:
                    df_categoria = df[df['CATEGORIA'] == categoria][['DATA', 'VALOR', 'HISTÓRICO']]
                    st.dataframe(df_categoria, use_container_width=True)
                    total_cat = df_categoria['V_NUM'].sum()
                    st.markdown(f"<p style='text-align:right; color:#BFAF83; font-weight:bold;'>Total {categoria}: R$ {total_cat:,.2f}</p>", unsafe_allow_html=True)
            
            # Exportação
            st.markdown('<h3 style="color:#BFAF83; text-align:center; margin-top:30px;">📥 Exportar Laudo</h3>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.download_button("📊 Baixar Consolidado (CSV)", relatorio.to_csv().encode('utf-8-sig'), "relatorio_consolidado.csv", "text/csv")
            with col2:
                st.download_button("📋 Baixar Detalhado (CSV)", df[['DATA', 'CATEGORIA', 'VALOR', 'HISTÓRICO']].to_csv(index=False).encode('utf-8-sig'), "laudo_detalhado.csv", "text/csv")
        else:
            st.info("Nenhum débito encontrado com as rubricas selecionadas.")

st.markdown("<br><br><p style='text-align:right; font-family:serif; font-style:italic; color:#BFAF83;'>Edson Medeiros</p>", unsafe_allow_html=True)
