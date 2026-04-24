import streamlit as st
import pdfplumber
import pandas as pd
import re

# --- 1. CONFIGURAÇÃO DE INTERFACE LUXUOSA ---
st.set_page_config(page_title="Edson Medeiros | Consultoria de Ativos", layout="wide", page_icon="⚖️")

ESTILO_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600&family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@300;400;600&family=Great+Vibes&display=swap');
:root { --navy: #0F172A; --gold: #BFAF83; --off-white: #F8F9FA; }
.stApp { background: radial-gradient(circle at center, #1E293B 0%, #0F172A 100%); color: var(--off-white); font-family: 'Inter', sans-serif; }

.consultoria-title { 
    font-family: 'Playfair Display', serif !important; 
    font-size: 4.5rem !important; 
    background: linear-gradient(180deg, #FFFFFF 0%, #BFAF83 100%); 
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
    text-shadow: 0px 4px 10px rgba(0,0,0,0.5); text-align: center; line-height: 1.1;
}

.impact-card { 
    background: rgba(255, 255, 255, 0.05); 
    border: 1px solid rgba(191, 175, 131, 0.3); 
    border-radius: 15px; padding: 25px; text-align: center;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}

.step-card {
    background: rgba(15, 23, 42, 0.6);
    border-left: 3px solid var(--gold);
    padding: 20px; border-radius: 8px; margin-bottom: 20px;
}

.footer-name { font-family: 'Great Vibes', cursive; color: var(--gold); font-size: 2.5rem; text-align: right; }
</style>
"""
st.markdown(ESTILO_CSS, unsafe_allow_html=True)

# --- 2. PARÂMETROS DE BUSCA COMPLETOS ---
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
    "ENCARGOS": r"ENCARGOS|ENC LIMITE|ENC LIM CREDITO",
    "ANUIDADE": r"ANUIDADE|CARTAO CREDITO ANUIDADE",
    "OPERACOES VENCIDAS": r"OPERACOES VENCIDAS|OPERAÇÕES VENCIDAS",
    "DIV. EM ATRASO": r"DIV\. EM ATRASO|DIVIDA EM ATRASO",
    "IOF": r"IOF S/ UTILIZACAO|IOF UTIL LIMITE"
}

# --- 3. MOTOR DE AUDITORIA INTELIGENTE ---
def realizar_auditoria(arquivo):
    resultados = []
    transacoes_pendentes = [] 
    
    with pdfplumber.open(arquivo) as pdf:
        for page in pdf.pages:
            tabela = page.extract_table({
                "vertical_strategy": "text", 
                "horizontal_strategy": "text", 
                "snap_tolerance": 4
            })
            if not tabela: continue
            
            for linha in tabela:
                if len(linha) < 3: continue
                
                col_data = str(linha[0]).strip() if linha[0] else ""
                
                # Identifica se a linha possui uma data válida
                match_data = re.search(r"\d{2}/\d{2}(?:/\d{2,4})?", col_data)
                data_encontrada = match_data.group(0) if match_data else None

                # Posições padrão do Bradesco para Débito e Crédito
                col_debito = str(linha[-2]).strip() if len(linha) >= 4 else ""
                col_credito = str(linha[-3]).strip() if len(linha) >= 5 else ""

                tem_debito = bool(re.search(r'\d+,\d{2}', col_debito))
                tem_credito = bool(re.search(r'\d+,\d{2}', col_credito))

                # ANTI-FRAGMENTAÇÃO: Junta todas as células da linha em um texto único
                texto_linha_completo = " ".join([str(c).strip() for c in linha if c]).upper()

                # 1. FILTRO DE VALORES: Tem débito e NÃO é crédito azul
                if tem_debito and not tem_credito:
                    for cat, regex in DICIONARIO_ALVOS.items():
                        # A busca agora é feita na LINHA COMPLETA unificada
                        if re.search(regex, texto_linha_completo):
                            item = {
                                "CATEGORIA": cat, 
                                "VALOR DÉBITO (R$)": col_debito, 
                                "HISTÓRICO": texto_linha_completo[:80] # Puxa todo o contexto pro usuário ver
                            }
                            
                            # Se a linha já tem data, registra na hora
                            if data_encontrada:
                                item["DATA"] = data_encontrada
                                resultados.append(item)
                                # Ancora qualquer transação anterior que estava sem data (Modo 1)
                                for p in transacoes_pendentes:
                                    p["DATA"] = data_encontrada
                                    resultados.append(p)
                                transacoes_pendentes = []
                            else:
                                # Sem data na linha: vai para a fila de espera (Modo 1)
                                transacoes_pendentes.append(item)
                            break
                
                # 2. GATILHO DE DATA ÂNCORA (Modo 1 isolado)
                # Se passou uma linha sem débito, mas com data (como "13/01/2017"), usa para carimbar as pendentes
                elif data_encontrada and transacoes_pendentes:
                    for p in transacoes_pendentes:
                        p["DATA"] = data_encontrada
                        resultados.append(p)
                    transacoes_pendentes = []
                    
    return resultados

# --- 4. INTERFACE ---
st.markdown('<h1 class="consultoria-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#BFAF83; letter-spacing:2px;'>SISTEMA DE AUDITORIA TÉCNICA ESPECIALIZADA</p>", unsafe_allow_html=True)

st.sidebar.markdown("### PARÂMETROS DE AUDITORIA")
selecionados = [k for k in DICIONARIO_ALVOS.keys() if st.sidebar.checkbox(k, value=True)]

upload = st.file_uploader("📂 ARRASTE O EXTRATO BANCÁRIO (PDF)", type=["pdf"])

if upload:
    with st.spinner('A analisar blocos de texto e sincronizar datas...'):
        dados = realizar_auditoria(upload)
        if dados:
            df = pd.DataFrame(dados)
            if "DATA" in df.columns:
                df = df[['DATA', 'CATEGORIA', 'VALOR DÉBITO (R$)', 'HISTÓRICO']]
            
            total = sum([float(v.replace('.','').replace(',','.')) for v in df["VALOR DÉBITO (R$)"]])
            
            c1, c2 = st.columns(2)
            c1.markdown(f'<div class="impact-card"><h4>TOTAL RECUPERÁVEL</h4><h2 style="color:#BFAF83;">R$ {total:,.2f}</h2></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="impact-card"><h4>OCORRÊNCIAS</h4><h2 style="color:#BFAF83;">{len(df)}</h2></div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True)
            st.download_button("📥 BAIXAR LAUDO TÉCNICO", df.to_csv(index=False).encode('utf-8-sig'), "auditoria_edson.csv")
        else:
            st.info("Nenhum débito indevido encontrado com os filtros atuais.")

# --- 5. RODAPÉ DE CREDIBILIDADE (3 PASSOS) ---
st.markdown("<br><hr style='border-color: rgba(191,175,131,0.2);'><br>", unsafe_allow_html=True)
col_a, col_b, col_c = st.columns(3)

with col_a:
    st.markdown('<div class="step-card"><strong>I - Identificação Digital</strong><br><small>Varredura por inteligência artificial em extratos nativos ou escaneados.</small></div>', unsafe_allow_html=True)
with col_b:
    st.markdown('<div class="step-card"><strong>II - Extração Técnica</strong><br><small>Isolamento de colunas de débito e correlação de datas por âncora inferior.</small></div>', unsafe_allow_html=True)
with col_c:
    st.markdown('<div class="step-card"><strong>III - Certificação de Ativos</strong><br><small>Geração de relatório técnico para instrução de processos judiciais.</small></div>', unsafe_allow_html=True)

st.markdown('<p class="footer-name">Edson Medeiros</p>', unsafe_allow_html=True)
