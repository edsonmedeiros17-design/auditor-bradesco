import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime

# --- 1. CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="Edson Medeiros | Auditoria de Alta Fidelidade", layout="wide", page_icon="⚖️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');
    .stApp { background-color: #0E1117; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    .main-title { font-family: 'Playfair Display', serif; font-size: 2.8rem; color: #BFAF83; text-align: center; margin-bottom: 0; }
    .sub-title { text-align: center; color: #64748B; letter-spacing: 2px; text-transform: uppercase; font-size: 0.85rem; margin-bottom: 40px; }
    .metric-card { background: rgba(255,255,255,0.03); border: 1px solid #BFAF83; border-radius: 8px; padding: 20px; text-align: center; }
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

# Termos que forçam a limpeza imediata da memória para evitar vazamento de datas/valores
TERMOS_LIMPEZA = r"TRANSF|SALDO|SDO|TRANSFERENCIA|SALARIO|EXTRATO|CONTA|SALDO ANTERIOR|SALDO ATUAL"

# --- 3. MOTOR DE AUDITORIA DE ALTA FIDELIDADE ---
def realizar_auditoria_fiel(arquivo, rubricas_alvo):
    resultados = []
    # O cesto armazena rubricas que aguardam confirmação por uma data inferior
    cesto_pendente = []
    
    regex_valor = r"(\d{1,3}(?:\.\d{3})*,\d{2})(?!\s*%)"
    regex_data = r"(\d{2}/\d{2}/\d{2,4})"

    with pdfplumber.open(arquivo) as pdf:
        for page in pdf.pages:
            texto = page.extract_text(x_tolerance=2, y_tolerance=2)
            if not texto: continue
            
            linhas = texto.split('\n')
            for linha in linhas:
                linha_up = linha.upper().strip()
                if not linha_up: continue

                # 1. BUSCA POR DATA (Gatilho de Selagem)
                match_data = re.search(regex_data, linha_up)
                
                if match_data:
                    data_encontrada = match_data.group(1)
                    # Se temos itens no cesto, eles pertencem a esta data (lógica de data inferior)
                    if cesto_pendente:
                        for item in cesto_pendente:
                            # SÓ ADICIONA SE TIVER VALOR REAL. Se for 0,00, foi erro de leitura.
                            if item["VALOR_NUM"] > 0:
                                item["DATA"] = data_encontrada
                                resultados.append(item)
                        # LIMPEZA TOTAL: Os itens foram selados com a data encontrada.
                        cesto_pendente = []
                    
                    # Após encontrar uma data, a linha atual pode iniciar um novo bloco.
                    # Mas se a linha contém termos de saldo/transferência, ignoramos o resto dela.
                    if re.search(TERMOS_LIMPEZA, linha_up):
                        continue

                # 2. BUSCA POR RUBRICA
                rubrica_detectada = None
                if "%" not in linha_up:
                    for nome in rubricas_alvo:
                        if re.search(RUBRICAS_MESTRE[nome], linha_up):
                            rubrica_detectada = nome
                            break
                
                # 3. BUSCA POR VALOR
                match_valor = re.search(regex_valor, linha_up)
                valor_str = match_valor.group(1) if match_valor else None
                
                # 4. LÓGICA DE ASSOCIAÇÃO RÍGIDA
                if rubrica_detectada:
                    # Se achou rubrica, cria o registro. Se tiver valor na mesma linha, já guarda.
                    v_num = 0.0
                    if valor_str:
                        v_num = float(valor_str.replace('.', '').replace(',', '.'))
                    
                    cesto_pendente.append({
                        "CATEGORIA": rubrica_detectada,
                        "VALOR_STR": valor_str if valor_str else "0,00",
                        "VALOR_NUM": v_num,
                        "HISTÓRICO": linha_up[:80]
                    })
                
                elif valor_str and cesto_pendente:
                    # Se não tem rubrica mas tem valor, associa ao último item do cesto que está sem valor
                    if cesto_pendente[-1]["VALOR_NUM"] == 0:
                        v_num = float(valor_str.replace('.', '').replace(',', '.'))
                        cesto_pendente[-1]["VALOR_STR"] = valor_str
                        cesto_pendente[-1]["VALOR_NUM"] = v_num
                
                # 5. TRAVA DE SEGURANÇA: Se a linha for de saldo ou transferência, limpa o cesto de qualquer lixo
                if re.search(TERMOS_LIMPEZA, linha_up):
                    # Remove do cesto itens que não conseguiram capturar um valor antes de chegar num saldo/transf
                    cesto_pendente = [i for i in cesto_pendente if i["VALOR_NUM"] > 0]

    return resultados

# --- 4. TRATAMENTO E EXIBIÇÃO ---
def processar_df(dados):
    if not dados: return None
    df = pd.DataFrame(dados)
    
    def fix_date(d):
        p = d.split('/')
        if len(p[2]) == 2: p[2] = "20" + p[2]
        return "/".join(p)
    
    df['DT_OBJ'] = pd.to_datetime(df['DATA'].apply(fix_date), format='%d/%m/%Y', errors='coerce')
    df = df.sort_values('DT_OBJ')
    return df

def gerar_pivot(df):
    # Garantir ordenação no pivot
    df_t = df.copy()
    def fix_date(d):
        p = d.split('/')
        if len(p[2]) == 2: p[2] = "20" + p[2]
        return "/".join(p)
    df_t['DT_S'] = pd.to_datetime(df_t['DATA'].apply(fix_date), format='%d/%m/%Y')
    
    pivot = df_t.pivot_table(
        index=['DT_S', 'DATA'],
        columns='CATEGORIA',
        values='VALOR_NUM',
        aggfunc='sum',
        fill_value=0
    ).reset_index(level=0, drop=True)
    
    pivot['TOTAL DIA'] = pivot.sum(axis=1)
    totais = pivot.sum()
    totais.name = 'TOTAL GERAL'
    pivot = pd.concat([pivot, totais.to_frame().T])
    return pivot

# --- 5. INTERFACE ---
st.markdown('<h1 class="main-title">Edson Medeiros</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Consultoria de Ativos | Auditoria de Alta Fidelidade</p>', unsafe_allow_html=True)

st.sidebar.markdown("### 🔍 FILTROS")
selecionadas = [r for r in RUBRICAS_MESTRE.keys() if st.sidebar.checkbox(r, value=True)]

upload = st.file_uploader("📂 CARREGAR EXTRATO BANCÁRIO (PDF)", type=["pdf"])

if upload:
    with st.spinner("Auditando extrato com precisão absoluta..."):
        dados = realizar_auditoria_fiel(upload, selecionadas)
        df = processar_df(dados)
        
        if df is not None and not df.empty:
            # Métricas
            total_recuperavel = df['VALOR_NUM'].sum()
            c1, c2 = st.columns(2)
            with c1: st.markdown(f'<div class="metric-card"><h4>TOTAL IDENTIFICADO</h4><h2 style="color:#BFAF83;">R$ {total_recuperavel:,.2f}</h2></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="metric-card"><h4>LANÇAMENTOS</h4><h2 style="color:#BFAF83;">{len(df)}</h2></div>', unsafe_allow_html=True)
            
            # Relatório Consolidado
            st.markdown('<h2 style="color:#BFAF83; text-align:center; margin-top:40px;">📊 Relatório Consolidado</h2>', unsafe_allow_html=True)
            pivot = gerar_pivot(df)
            pivot_fmt = pivot.copy()
            for col in pivot_fmt.columns:
                pivot_fmt[col] = pivot_fmt[col].apply(lambda x: f"R$ {x:,.2f}" if x != 0 else "-")
            st.dataframe(pivot_fmt, use_container_width=True)
            
            # Detalhamento
            st.markdown('<h3 style="color:#BFAF83; text-align:center; margin-top:30px;">📋 Detalhamento por Categoria</h3>', unsafe_allow_html=True)
            categorias = df['CATEGORIA'].unique()
            tabs = st.tabs([f"📌 {c}" for c in categorias])
            for tab, cat in zip(tabs, categorias):
                with tab:
                    df_c = df[df['CATEGORIA'] == cat][['DATA', 'VALOR_STR', 'HISTÓRICO']]
                    st.dataframe(df_c, use_container_width=True)
                    s_c = df[df['CATEGORIA'] == cat]['VALOR_NUM'].sum()
                    st.markdown(f"<p style='text-align:right; color:#BFAF83; font-weight:bold;'>Total {cat}: R$ {s_c:,.2f}</p>", unsafe_allow_html=True)
            
            # Exportação
            st.markdown('<h3 style="color:#BFAF83; text-align:center; margin-top:30px;">📥 Exportar Laudos</h3>', unsafe_allow_html=True)
            d1, d2 = st.columns(2)
            with d1:
                st.download_button("📊 Baixar Consolidado (Excel)", pivot.to_csv(sep=';').encode('utf-8-sig'), "relatorio_consolidado.csv", "text/csv")
            with d2:
                st.download_button("📋 Baixar Laudo Detalhado (Excel)", df[['DATA', 'CATEGORIA', 'VALOR_STR', 'HISTÓRICO']].to_csv(index=False, sep=';').encode('utf-8-sig'), "laudo_detalhado.csv", "text/csv")
        else:
            st.warning("Nenhum débito validado encontrado. O sistema ignorou dados incompletos para garantir precisão.")

st.markdown("<br><br><p style='text-align:right; font-family:serif; font-style:italic; color:#BFAF83;'>Edson Medeiros</p>", unsafe_allow_html=True)
