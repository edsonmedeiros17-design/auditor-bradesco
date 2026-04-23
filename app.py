import streamlit as st
import pdfplumber
import pandas as pd
import re

# --- CONFIGURAÇÃO DE DESIGN (Mantida conforme padrão luxo) ---
st.set_page_config(page_title="Edson Medeiros | Auditoria Pro", layout="wide")

# --- DICIONÁRIO DE PARÂMETROS ---
DICIONARIO_ALVOS = {
    "CESTA/PACOTE": r"CESTA|PACOTE|TARIFA BANC",
    "MORA CREDITO PESSOAL": r"MORA CRED PESS|MORA CRÉDITO",
    "MORA OPERACAO": r"MORA OPER|MORA DE OPERAÇÃO",
    "ENCARGOS LIMITE": r"ENC LIM CREDITO|ENCARGOS",
    "PARCELA CREDITO": r"PARC CRED PESS|PARCELA CRÉDITO",
    "GASTOS CARTAO": r"CART CRED ANUID|ANUIDADE",
    "SEGURO": r"SEGURO|SEGURADORA",
    "IOF": r"IOF UTIL LIMITE|IOF S/ UTIL",
    "BX": r"BX ",
}

# --- MOTOR DE AUDITORIA COM DOIS MODOS DE LEITURA ---
def auditoria_inteligente(arquivo):
    resultados = []
    transacoes_pendentes = [] # Para o MODO 1 (Data Inferior)
    
    with pdfplumber.open(arquivo) as pdf:
        for page in pdf.pages:
            tabela = page.extract_table({
                "vertical_strategy": "text", 
                "horizontal_strategy": "text",
                "snap_tolerance": 4
            })
            
            if not tabela: continue
            
            for linha in tabela:
                if len(linha) < 4: continue
                
                # Limpeza de dados das colunas
                col_data = str(linha[0]).strip() if linha[0] else ""
                col_hist = str(linha[1]).strip().upper() if linha[1] else ""
                col_debito = str(linha[-2]).strip() if len(linha) >= 5 else str(linha[-1]).strip()
                
                # 1. IDENTIFICAÇÃO DE VALOR DE DÉBITO VÁLIDO
                valor_valido = None
                if col_debito and "," in col_debito:
                    # Verifica se não é um crédito (azul/vazio na coluna correta)
                    # No Bradesco, se houver valor na coluna anterior à de débito, é crédito.
                    col_credito = str(linha[-3]).strip() if len(linha) >= 6 else ""
                    if col_credito and "," in col_credito:
                        continue # Pula se for crédito
                    valor_valido = col_debito

                # 2. SE TEM VALOR MAS NÃO TEM DATA (Potencial MODO 1)
                if valor_valido:
                    encontrou_alvo = False
                    for cat, regex in DICIONARIO_ALVOS.items():
                        if re.search(regex, col_hist):
                            temp_item = {
                                "CATEGORIA": cat,
                                "VALOR DÉBITO (R$)": valor_valido,
                                "HISTÓRICO": col_hist[:50]
                            }
                            
                            if col_data and re.match(r"\d{2}/\d{2}", col_data):
                                # MODO 2: Data na mesma linha
                                temp_item["DATA"] = col_data
                                resultados.append(temp_item)
                            else:
                                # MODO 1: Sem data ainda, vai para a "sala de espera"
                                transacoes_pendentes.append(temp_item)
                            encontrou_alvo = True
                            break
                
                # 3. SE ENCONTROU UMA DATA SOZINHA (Âncora do MODO 1)
                # Se a linha tem data mas as outras colunas estão vazias ou é o fim do bloco
                if col_data and re.match(r"\d{2}/\d{2}", col_data) and transacoes_pendentes:
                    for item in transacoes_pendentes:
                        item["DATA"] = col_data # Atribui a data encontrada às linhas de cima
                        resultados.append(item)
                    transacoes_pendentes = [] # Limpa a fila

    return resultados

# --- INTERFACE ---
st.title("🏛️ Consultoria de Ativos")
st.subheader("Auditoria Técnica de Alta Precisão (Modo 1 e 2)")

upload = st.file_uploader("Suba o Extrato PDF para Auditoria Combinada", type=["pdf"])

if upload:
    with st.spinner('Processando memória de datas e filtrando débitos...'):
        dados = auditoria_inteligente(upload)
        
        if dados:
            df = pd.DataFrame(dados)
            # Reorganizar colunas para a data vir primeiro
            df = df[['DATA', 'CATEGORIA', 'VALOR DÉBITO (R$)', 'HISTÓRICO']]
            
            st.success(f"Auditoria Concluída! {len(df)} débitos identificados.")
            
            # Cards de resumo
            total = sum([float(v.replace('.','').replace(',','.')) for v in df["VALOR DÉBITO (R$)"]])
            c1, c2 = st.columns(2)
            c1.metric("Transações Recuperáveis", len(df))
            c2.metric("Total Estimado", f"R$ {total:,.2f}")
            
            st.dataframe(df, use_container_width=True)
            st.download_button("Baixar Laudo Técnico", df.to_csv(index=False).encode('utf-8-sig'), "laudo_edson.csv")
        else:
            st.error("Nenhum débito encontrado com os parâmetros selecionados.")
