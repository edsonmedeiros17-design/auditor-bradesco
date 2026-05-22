import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime

# --- 1. CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="Edson Medeiros | Auditoria de Precisão", layout="wide", page_icon="⚖️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');
    .stApp { background-color: #0E1117; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    .main-title { font-family: 'Playfair Display', serif; font-size: 2.8rem; color: #BFAF83; text-align: center; margin-bottom: 0; }
    .sub-title { text-align: center; color: #64748B; letter-spacing: 2px; text-transform: uppercase; font-size: 0.85rem; margin-bottom: 40px; }
    .metric-card { background: rgba(255,255,255,0.03); border: 1px solid #BFAF83; border-radius: 8px; padding: 20px; text-align: center; }
    .status-ok { color: #2ecc71; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 2. DEFINIÇÕES TÉCNICAS (RUBRICAS) ---
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

TERMOS_EXCLUSAO = r"TRANSF|SALDO|SDO|TRANSFERENCIA|SALARIO|EXTRATO|CONTA"

# --- 3. MOTOR DE AUDITORIA DE RIGOR MÁXIMO ---
def realizar_auditoria_rigorosa(arquivo, rubricas_alvo):
    resultados = []
    cesto_temporario = []
    
    # Regex ultra-específicas para evitar falsos positivos
    # Valor: deve ter vírgula e dois decimais, opcionalmente pontos de milhar
    regex_valor = r"(\d{1,3}(?:\.\d{3})*,\d{2})(?!\s*%)"
    # Data: formato DD/MM/AA ou DD/MM/AAAA
    regex_data = r"(\d{2}/\d{2}/\d{2,4})"

    with pdfplumber.open(arquivo) as pdf:
        for page in pdf.pages:
            texto = page.extract_text(x_tolerance=2, y_tolerance=2)
            if not texto: continue
            
            linhas = texto.split('\n')
            for linha in linhas:
                linha_up = linha.upper().strip()
                if not linha_up: continue

                # A. BUSCA POR DATA (SINALIZADOR DE FECHAMENTO DE BLOCO)
                match_data = re.search(regex_data, linha_up)
                
                # B. SE ENCONTRAR DATA: SELAR O QUE ESTÁ NO CESTO
                if match_data:
                    data_confirmada = match_data.group(1)
                    if cesto_temporario:
                        for item in cesto_temporario:
                            # Só valida se tiver um valor real associado
                            if item["VALOR_BRUTO"] != "0,00":
                                item["DATA"] = data_confirmada
                                resultados.append(item)
                        # RESET ABSOLUTO APÓS ENCONTRAR DATA
                        cesto_temporario = []
                    
                    # Importante: A linha com data também pode conter uma rubrica/valor
                    # Mas geralmente a data no extrato "data inferior" confirma o que está ACIMA dela.
                    # Continuamos o processamento da linha para ver se há novas rubricas iniciando.

                # C. FILTRO DE EXCLUSÃO (Limpa lixo)
                if re.search(TERMOS_EXCLUSAO, linha_up):
                    # Se for uma linha de saldo/transf, descartamos rubricas pendentes sem valor
                    cesto_temporario = [i for i in cesto_temporario if i["VALOR_BRUTO"] != "0,00"]
                    continue

                # D. BUSCA POR RUBRICA
                rubrica_encontrada = None
                if "%" not in linha_up:
                    for nome in rubricas_alvo:
                        if re.search(RUBRICAS_MESTRE[nome], linha_up):
                            rubrica_encontrada = nome
                            break
                
                # E. BUSCA POR VALOR
                match_valor = re.search(regex_valor, linha_up)
                valor_linha = match_valor.group(1) if match_valor else "0,00"

                # F. LÓGICA DE CAPTURA
                if rubrica_encontrada:
                    cesto_temporario.append({
                        "CATEGORIA": rubrica_encontrada,
                        "VALOR_BRUTO": valor_linha,
                        "HISTÓRICO": linha_up[:80] # Histórico mais longo para prova
                    })
                elif valor_linha != "0,00" and cesto_temporario:
                    # Se achou um valor numa linha sem rubrica, associa à última rubrica pendente
                    if cesto_temporario[-1]["VALOR_BRUTO"] == "0,00":
                        cesto_temporario[-1]["VALOR_BRUTO"] = valor_linha

    return resultados

# --- 4. TRATAMENTO DE DADOS ---
def preparar_dados(dados):
    if not dados: return None
    
    df = pd.DataFrame(dados)
    
    # Conversão numérica rigorosa
    df['V_NUM'] = df['VALOR_BRUTO'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
    
    # Ordenação Cronológica Real
    def fix_date(d):
        pts = d.split('/')
        if len(pts[2]) == 2: pts[2] = "20" + pts[2]
        return "/".join(pts)
    
    df['DT_OBJ'] = pd.to_datetime(df['DATA'].apply(fix_date), format='%d/%m/%Y', errors='coerce')
    df = df.sort_values('DT_OBJ').drop(columns=['DT_OBJ'])
    
    return df

def criar_pivot(df):
    # Criar pivot garantindo a ordem cronológica
    df_temp = df.copy()
    def fix_date(d):
        pts = d.split('/')
        if len(pts[2]) == 2: pts[2] = "20" + pts[2]
        return "/".join(pts)
    
    df_temp['DT_SORT'] = pd.to_datetime(df_temp['DATA'].apply(fix_date), format='%d/%m/%Y')
    
    pivot = df_temp.pivot_table(
        index=['DT_SORT', 'DATA'],
        columns='CATEGORIA',
        values='V_NUM',
        aggfunc='sum',
        fill_value=0
    ).reset_index(level=0, drop=True)
    
    pivot['TOTAL DIA'] = pivot.sum(axis=1)
    
    totais = pivot.sum()
    totais.name = 'TOTAL GERAL'
    pivot = pd.concat([pivot, totais.to_frame().T])
    
    return pivot

# --- 5. INTERFACE DO USUÁRIO ---
st.markdown('<h1 class="main-title">Edson Medeiros</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Consultoria de Ativos | Auditoria de Precisão Impecável</p>', unsafe_allow_html=True)

st.sidebar.markdown("### 🛠️ PARÂMETROS DE RIGOR")
selecionadas = [r for r in RUBRICAS_MESTRE.keys() if st.sidebar.checkbox(r, value=True)]

arquivo_pdf = st.file_uploader("📂 CARREGAR EXTRATO BANCÁRIO (PDF)", type=["pdf"])

if arquivo_pdf:
    with st.spinner("Executando Protocolo de Rigor Máximo..."):
        dados_brutos = realizar_auditoria_rigorosa(arquivo_pdf, selecionadas)
        df_final = preparar_dados(dados_brutos)
        
        if df_final is not None and not df_final.empty:
            # Painel de Métricas
            v_total = df_final['V_NUM'].sum()
            m1, m2 = st.columns(2)
            with m1: st.markdown(f'<div class="metric-card"><h4>TOTAL IDENTIFICADO</h4><h2 style="color:#BFAF83;">R$ {v_total:,.2f}</h2><p class="status-ok">✓ Verificado</p></div>', unsafe_allow_html=True)
            with m2: st.markdown(f'<div class="metric-card"><h4>LANÇAMENTOS</h4><h2 style="color:#BFAF83;">{len(df_final)}</h2><p class="status-ok">✓ Auditados</p></div>', unsafe_allow_html=True)
            
            # Relatório Consolidado
            st.markdown('<h2 style="color:#BFAF83; text-align:center; margin-top:40px;">📊 Relatório Consolidado por Categoria</h2>', unsafe_allow_html=True)
            tabela_pivot = criar_pivot(df_final)
            
            # Formatação para o usuário
            tabela_fmt = tabela_pivot.copy()
            for col in tabela_fmt.columns:
                tabela_fmt[col] = tabela_fmt[col].apply(lambda x: f"R$ {x:,.2f}" if x != 0 else "-")
            
            st.dataframe(tabela_fmt, use_container_width=True)
            
            # Detalhamento por Abas
            st.markdown('<h3 style="color:#BFAF83; text-align:center; margin-top:30px;">📋 Prova Documental (Histórico do PDF)</h3>', unsafe_allow_html=True)
            categorias = df_final['CATEGORIA'].unique()
            abas = st.tabs([f"📍 {c}" for c in categorias])
            
            for aba, cat in zip(abas, categorias):
                with aba:
                    df_cat = df_final[df_final['CATEGORIA'] == cat][['DATA', 'VALOR_BRUTO', 'HISTÓRICO']]
                    st.dataframe(df_cat, use_container_width=True)
                    s_cat = df_final[df_final['CATEGORIA'] == cat]['V_NUM'].sum()
                    st.markdown(f"<p style='text-align:right; color:#BFAF83; font-weight:bold;'>Subtotal {cat}: R$ {s_cat:,.2f}</p>", unsafe_allow_html=True)
            
            # Exportação Excel Compatível
            st.markdown('<h3 style="color:#BFAF83; text-align:center; margin-top:30px;">📥 Exportar Laudo de Auditoria</h3>', unsafe_allow_html=True)
            d1, d2 = st.columns(2)
            with d1:
                csv_p = tabela_pivot.to_csv(sep=';').encode('utf-8-sig')
                st.download_button("📊 Baixar Resumo Consolidado (Excel)", csv_p, "auditoria_consolidada.csv", "text/csv")
            with d2:
                csv_d = df_final[['DATA', 'CATEGORIA', 'VALOR_BRUTO', 'HISTÓRICO']].to_csv(index=False, sep=';').encode('utf-8-sig')
                st.download_button("📋 Baixar Laudo Detalhado (Excel)", csv_d, "laudo_detalhado_edson.csv", "text/csv")
        else:
            st.warning("Nenhum débito foi validado com os critérios de rigor máximo. Verifique as rubricas selecionadas ou o formato do PDF.")

st.markdown("<br><br><p style='text-align:right; font-family:serif; font-style:italic; color:#BFAF83;'>Edson Medeiros</p>", unsafe_allow_html=True)
