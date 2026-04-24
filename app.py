import streamlit as st
import pdfplumber
import pandas as pd
import re

# --- 1. CONFIGURAÇÃO DE INTERFACE LUXUOSA ---
st.set_page_config(page_title="Edson Medeiros | Consultoria de Extratos Bancários", layout="wide", page_icon="⚖️")

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

# --- 2. PARÂMETROS DE BUSCA (RESTAURADOS E COMPLETOS) ---
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
   

# --- 3. MOTOR DE AUDITORIA INTELIGENTE ---
def realizar_auditoria(arquivo):
    resultados = []
    transacoes_pendentes = [] 
    
    with pdfplumber.open(arquivo) as pdf:
        for page in pdf.pages:
            tabela = page.extract_table({
                "vertical_strategy": "text", 
                "horizontal_strategy": "text", 
                "snap_tolerance": 5
            })
            if not tabela: continue
            
            for linha in tabela:
                # UNE TODA A LINHA EM UMA STRING SÓ E LIMPA ESPAÇOS EXTRAS
                texto_cru = " ".join([str(c).strip() for c in linha if c and str(c).strip()])
                texto_linha_completo = re.sub(r'\s+', ' ', texto_cru).upper()
                if not texto_linha_completo: continue
                
                # Procura a data em qualquer lugar da linha
                match_data = re.search(r"(\d{2}/\d{2}(?:/\d{2,4})?)", texto_linha_completo)
                data_encontrada = match_data.group(1) if match_data else None

                # Procura valores monetários (Ex: 9,58)
                valores_monetarios = re.findall(r"\b\d{1,3}(?:\.\d{3})*,\d{2}\b", texto_linha_completo)

                # Busca cada rubrica individualmente
                rubrica_encontrada = None
                for cat, regex in DICIONARIO_ALVOS.items():
                    if re.search(regex, texto_linha_completo):
                        rubrica_encontrada = cat
                        break
                
                # Se achou rubrica e tem valor, processa:
                if rubrica_encontrada and not re.search(r"ESTORNO|RESSARCIMENTO", texto_linha_completo):
                    # Filtra valores para não pegar o 0,00 que às vezes o leitor gera por erro
                    valores_validos = [v for v in valores_monetarios if v != "0,00"]
                    
                    if valores_validos:
                        valor_transacao = valores_validos[0] # Pega o valor do débito
                        
                        item = {
                            "CATEGORIA": rubrica_encontrada,
                            "VALOR DÉBITO (R$)": valor_transacao,
                            "HISTÓRICO": texto_linha_completo[:85]
                        }
                        
                        if data_encontrada:
                            item["DATA"] = data_encontrada
                            resultados.append(item)
                            # Sincroniza itens que estavam aguardando data
                            for p in transacoes_pendentes:
                                p["DATA"] = data_encontrada
                                resultados.append(p)
                            transacoes_pendentes = []
                        else:
                            transacoes_pendentes.append(item)

                # Gatilho de Data Âncora
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
# Permite ao Edson escolher quais rubricas quer buscar
selecionados = []
for k in DICIONARIO_ALVOS.keys():
    if st.sidebar.checkbox(k, value=True):
        selecionados.append(k)

upload = st.file_uploader("📂 ARRASTE O EXTRATO BANCÁRIO (PDF)", type=["pdf"])

if upload:
    with st.spinner('Realizando varredura detalhada em todas as rubricas...'):
        dados = realizar_auditoria(upload)
        if dados:
            df = pd.DataFrame(dados)
            # Filtra apenas o que o usuário selecionou no sidebar
            df = df[df['CATEGORIA'].isin(selecionados)]
            
            if not df.empty:
                if "DATA" in df.columns:
                    df = df[['DATA', 'CATEGORIA', 'VALOR DÉBITO (R$)', 'HISTÓRICO']]
                
                total = sum([float(v.replace('.','').replace(',','.')) for v in df["VALOR DÉBITO (R$)"]])
                
                c1, c2 = st.columns(2)
                c1.markdown(f'<div class="impact-card"><h4>TOTAL RECUPERÁVEL</h4><h2 style="color:#BFAF83;">R$ {total:,.2f}</h2></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="impact-card"><h4>OCORRÊNCIAS</h4><h2 style="color:#BFAF83;">{len(df)}</h2></div>', unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True)
                st.download_button("📥 BAIXAR LAUDO TÉCNICO", df.to_csv(index=False).encode('utf-8-sig'), "auditoria_edson_completa.csv")
            else:
                st.info("Nenhuma das rubricas selecionadas foi encontrada.")
        else:
            st.info("Nenhum débito indevido encontrado.")

# --- 5. RODAPÉ ---
st.markdown("<br><hr style='border-color: rgba(191,175,131,0.2);'><br>", unsafe_allow_html=True)
st.markdown('<p class="footer-name">Edson Medeiros</p>', unsafe_allow_html=True)
