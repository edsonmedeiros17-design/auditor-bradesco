import streamlit as st
import pdfplumber
import pandas as pd
import re

# Configuração da página
st.set_page_config(page_title="Auditor Bradesco", layout="wide")

st.title("🏦 Robô de Auditoria de Extratos")

# 1. Dicionário de Alvos
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

# 2. Seleção na Barra Lateral
st.sidebar.header("Filtros de Busca")
opcoes_selecionadas = st.sidebar.multiselect(
    "Selecione os tipos de desconto:",
    options=list(DICIONARIO_ALVOS.keys()),
    default=list(DICIONARIO_ALVOS.keys())
)

def analisar_pdf(file, filtros):
    dados = []
    termos = [DICIONARIO_ALVOS[f] for f in filtros]
    
    with pdfplumber.open(file) as pdf:
        for p in pdf.pages:
            texto = p.extract_text()
            if texto:
                for linha in texto.split('\n'):
                    for termo in termos:
                        if re.search(termo, linha, re.IGNORECASE):
                            # Tenta pegar a data
                            data = re.search(r'(\d{2}/\d{2}/\d{4})', linha)
                            dados.append({
                                "Data": data.group(1) if data else "---",
                                "Categoria": [k for k, v in DICIONARIO_ALVOS.items() if v == termo][0],
                                "Lançamento": linha.strip()
                            })
                            break
    return pd.DataFrame(dados)

# 3. Interface principal
arquivo = st.file_uploader("Arraste o PDF do Extrato aqui", type="pdf")

if arquivo and opcoes_selecionadas:
    with st.spinner("Processando..."):
        df = analisar_pdf(arquivo, opcoes_selecionadas)
        if not df.empty:
            st.success(f"Sucesso! Encontramos {len(df)} itens.")
            st.dataframe(df, use_container_width=True)
            
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Baixar Relatório", csv, "auditoria.csv")
        else:
            st.info("Nenhum item encontrado com os filtros selecionados.")