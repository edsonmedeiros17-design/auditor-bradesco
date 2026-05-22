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
    .relatorio-titulo { font-family: 'Playfair Display', serif; font-size: 1.8rem; color: #BFAF83; text-align: center; margin-top: 40px; margin-bottom: 20px; }
    .relatorio-subtitulo { text-align: center; color: #64748B; font-size: 0.95rem; margin-bottom: 20px; }
    .tabela-relatorio { width: 100%; border-collapse: collapse; }
    .tabela-relatorio th { background-color: rgba(191, 175, 131, 0.2); color: #BFAF83; padding: 12px; text-align: left; border-bottom: 2px solid #BFAF83; font-weight: 600; }
    .tabela-relatorio td { padding: 10px 12px; border-bottom: 1px solid rgba(255,255,255,0.1); }
    .tabela-relatorio tr:hover { background-color: rgba(191, 175, 131, 0.05); }
    .total-row { background-color: rgba(191, 175, 131, 0.15); font-weight: 600; }
    .total-row td { border-top: 2px solid #BFAF83; border-bottom: 2px solid #BFAF83; }
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

# --- 3. MOTOR COM RESET DE MEMÓRIA (SOLUÇÃO ANEXO 2) ---
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
                    # Só preenche se o último item for realmente uma rubrica esperando valor
                    if cesto_acumulador[-1]["VALOR"] == "PENDENTE":
                        cesto_acumulador[-1]["VALOR"] = match_valor.group(1)

                # 5. Selagem por Data Inferior
                if match_data:
                    data_encontrada = match_data.group(1)
                    if cesto_acumulador:
                        for item in cesto_acumulador:
                            if item["VALOR"] != "PENDENTE":
                                item["DATA"] = data_encontrada
                                resultados.append(item)
                        cesto_acumulador = [] # Limpa para o próximo bloco

    return resultados

# --- 4. FUNÇÃO PARA GERAR RELATÓRIO CONSOLIDADO ---
def gerar_relatorio_consolidado(df):
    """
    Gera um relatório consolidado com datas nas linhas e categorias nas colunas.
    """
    # Converter valores para numérico
    df['V_NUM'] = df['VALOR'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
    
    # Criar pivot table com datas nas linhas e categorias nas colunas
    relatorio = df.pivot_table(
        index='DATA',
        columns='CATEGORIA',
        values='V_NUM',
        aggfunc='sum',
        fill_value=0
    )
    
    # Adicionar coluna de total por data
    relatorio['TOTAL POR DATA'] = relatorio.sum(axis=1)
    
    # Adicionar linha de total por categoria
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
    with st.spinner("Limpando ruídos e validando transferências..."):
        dados = realizar_auditoria(upload, selecionadas)
        if dados:
            df = pd.DataFrame(dados)
            df['V_NUM'] = df['VALOR'].str.replace('.','', regex=False).str.replace(',','.', regex=False).astype(float)
            total = df['V_NUM'].sum()
            
            c1, c2 = st.columns(2)
            with c1: st.markdown(f'<div class="metric-card"><h4>TOTAL RECUPERÁVEL</h4><h2 style="color:#BFAF83;">R$ {total:,.2f}</h2></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="metric-card"><h4>OCORRÊNCIAS</h4><h2 style="color:#BFAF83;">{len(df)}</h2></div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- EXIBIR RELATÓRIO CONSOLIDADO ---
            st.markdown('<h2 class="relatorio-titulo">📊 Relatório Consolidado</h2>', unsafe_allow_html=True)
            st.markdown('<p class="relatorio-subtitulo">Análise detalhada por categoria e data</p>', unsafe_allow_html=True)
            
            # Gerar relatório consolidado
            relatorio = gerar_relatorio_consolidado(df)
            
            # Formatar valores para exibição em reais
            relatorio_formatado = relatorio.copy()
            for col in relatorio_formatado.columns:
                if col != 'TOTAL POR DATA':
                    relatorio_formatado[col] = relatorio_formatado[col].apply(lambda x: f"R$ {x:,.2f}" if x > 0 else "-")
                else:
                    relatorio_formatado[col] = relatorio_formatado[col].apply(lambda x: f"R$ {x:,.2f}")
            
            # Exibir tabela formatada
            st.dataframe(relatorio_formatado, use_container_width=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- EXIBIR DETALHAMENTO POR CATEGORIA ---
            st.markdown('<h3 style="color:#BFAF83; text-align:center; margin-top:30px;">📋 Detalhamento por Categoria</h3>', unsafe_allow_html=True)
            
            # Criar abas para cada categoria
            categorias = df['CATEGORIA'].unique()
            tabs = st.tabs([f"📌 {cat}" for cat in categorias])
            
            for tab, categoria in zip(tabs, categorias):
                with tab:
                    df_categoria = df[df['CATEGORIA'] == categoria][['DATA', 'VALOR', 'HISTÓRICO']].sort_values('DATA')
                    st.dataframe(df_categoria, use_container_width=True)
                    
                    # Total da categoria
                    total_categoria = df_categoria['VALOR'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float).sum()
                    st.markdown(f"<p style='text-align:right; color:#BFAF83; font-weight:bold;'>Total: R$ {total_categoria:,.2f}</p>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- OPÇÃO DE DOWNLOAD ---
            st.markdown('<h3 style="color:#BFAF83; text-align:center;">📥 Exportar Dados</h3>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Download do relatório consolidado
                relatorio_csv = relatorio.to_csv()
                st.download_button(
                    label="📊 Baixar Relatório Consolidado (CSV)",
                    data=relatorio_csv.encode('utf-8-sig'),
                    file_name="relatorio_consolidado.csv",
                    mime="text/csv"
                )
            
            with col2:
                # Download dos dados detalhados
                st.download_button(
                    label="📋 Baixar Dados Detalhados (CSV)",
                    data=df[['DATA', 'CATEGORIA', 'VALOR', 'HISTÓRICO']].to_csv(index=False).encode('utf-8-sig'),
                    file_name="laudo_edson_detalhado.csv",
                    mime="text/csv"
                )
        else:
            st.info("Nenhum débito encontrado com as rubricas selecionadas.")

st.markdown("<br><br><p style='text-align:right; font-family:serif; font-style:italic; color:#BFAF83;'>Edson Medeiros</p>", unsafe_allow_html=True)
