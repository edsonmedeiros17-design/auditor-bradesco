import streamlit as st
import pdfplumber
import pandas as pd
import re

# --- CONFIGURAÇÃO DA INTERFACE ---
st.set_page_config(page_title="Auditor Bradesco", layout="wide")
st.title("🏦 Robô Auditor de Extratos - Bradesco")

# --- DICIONÁRIO DE FILTROS ---
DICIONARIO_ALVOS = {
    "Mora Crédito Pessoal": "MORA CREDITO PESSOAL",
    "Encargos": "ENCARGOS",
    "Parcela Crédito Pessoal": "PARCELA CREDITO PESSOAL",
    "Gastos Cartão de Crédito": "GASTOS CARTAO DE CREDITO",
    "BX (Baixas)": r"\bBX\b",
    "APLIC (Aplicações)": r"\bAPLIC\b",
    "Tarifa Bancária": "TARIFA BANCARIA",
    "Anuidade Cartão": "CARTAO CREDITO ANUIDADE"
}

# --- BARRA LATERAL (ESTILO CAIXINHA DE SELEÇÃO) ---
st.sidebar.header("Selecione os tipos de desconto")

# Criamos uma lista vazia para armazenar o que o usuário marcar
selecionados_nomes = []

# Criamos uma caixinha para cada item do nosso dicionário
for nome_amigavel in DICIONARIO_ALVOS.keys():
    # Se o usuário marcar a caixinha, adicionamos o nome à lista
    if st.sidebar.checkbox(nome_amigavel, value=True):
        selecionados_nomes.append(nome_amigavel)

# --- LÓGICA DE PROCESSAMENTO ---
def processar_pdf(arquivo_pdf, filtros_escolhidos):
    dados_encontrados = []
    # Converte os nomes das caixinhas para os termos de busca reais
    termos_busca = [DICIONARIO_ALVOS[nome] for nome in filtros_escolhidos]
    
    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                linhas = texto.split('\n')
                for linha in linhas:
                    for termo in termos_busca:
                        if re.search(termo, linha, re.IGNORECASE):
                            data_match = re.search(r'(\d{2}/\d{2}/\d{4})', linha)
                            data = data_match.group(1) if data_match else "S/ Data"
                            
                            dados_encontrados.append({
                                "Data": data,
                                "Categoria": [k for k, v in DICIONARIO_ALVOS.items() if v == termo][0],
                                "Lançamento Completo": linha.strip()
                            })
                            break
    return pd.DataFrame(dados_encontrados)

# --- INTERFACE DE UPLOAD ---
upload = st.file_uploader("Carregue o arquivo PDF do Extrato", type="pdf")

if upload:
    if not selecionados_nomes:
        st.warning("⚠️ Marque pelo menos uma caixinha na barra lateral.")
    else:
        with st.spinner('O robô está analisando as páginas...'):
            df_final = processar_pdf(upload, selecionados_nomes)
            
            if not df_final.empty:
                st.success(f"Encontramos {len(df_final)} itens!")
                st.dataframe(df_final, use_container_width=True)
                
                csv = df_final.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 Baixar Relatório CSV", csv, "auditoria_bradesco.csv")
            else:
                st.info("Nenhum desconto encontrado com esses filtros.")
