import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime

# --- 1. CONFIGURAÇÃO E BLINDAGEM ---
st.set_page_config(page_title="Edson Medeiros | Consultoria de Ativos", layout="wide", page_icon="⚖️")

# --- 2. CSS CUSTOMIZADO (INTACTO - SEM ALTERAÇÕES DE ESTÉTICA) ---
ESTILO_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600&family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@300;400;600&family=Great+Vibes&display=swap');
:root { --navy-deep: #0F172A; --gold-matte: #BFAF83; --emerald-success: #10B981; --off-white: #F8F9FA; }
.stApp { background: radial-gradient(circle at center, #1E293B 0%, #0F172A 100%); color: var(--off-white); font-family: 'Inter', sans-serif; }
.consultoria-title { font-family: 'Playfair Display', serif !important; font-size: 4.5rem !important; font-weight: 700 !important; background: linear-gradient(180deg, #FFFFFF 0%, #BFAF83 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0px 2px 0px #8A7650, 0px 4px 10px rgba(0,0,0,0.5); line-height: 1.1; margin-bottom: 5px; }
.btn-whatsapp { background-color: #25D366 !important; color: white !important; padding: 14px 28px !important; border-radius: 50px !important; text-decoration: none !important; font-weight: bold !important; display: inline-block !important; transition: 0.3s !important; box-shadow: 0 4px 15px rgba(37, 211, 102, 0.4) !important; text-align: center; border: none !important; }
.btn-whatsapp:hover { transform: scale(1.05); background-color: #128C7E !important; }
.impact-card { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(191, 175, 131, 0.2); border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 20px; }
.how-it-works { background: rgba(15, 23, 42, 0.6); border-radius: 16px; padding: 40px; margin-top: 60px; border: 1px solid rgba(191, 175, 131, 0.1); }
.step-number { color: var(--gold-matte); font-family: 'Cinzel', serif; font-size: 1.8rem; margin-bottom: 10px; }
.footer-signature { position: fixed; bottom: 30px; right: 40px; text-align: right; z-index: 100; }
.footer-name { font-family: 'Great Vibes', cursive; color: var(--gold-matte); font-size: 2.2rem; margin: 0; }
.footer-tech { font-family: 'Inter', sans-serif; font-size: 0.7rem; color: #64748B; letter-spacing: 3px; text-transform: uppercase; }
[data-testid="stSidebar"] { background-color: #080C14 !important; border-right: 1px solid #1E293B; }
[data-testid="stSidebar"] h3 { color: var(--gold-matte) !important; font-family: 'Cinzel', serif; }
.stFileUploader section { background-color: rgba(255,255,255,0.03) !important; border: 1px dashed var(--gold-matte) !important; }
/* Estilo para os botões de data no modo dark */
.stDateInput input { color: #FFF !important; background-color: #1E293B !important; border: 1px solid #BFAF83 !important; }
</style>
"""
st.markdown(ESTILO_CSS, unsafe_allow_html=True)

try:
    # --- 3. CABEÇALHO (INTACTO) ---
    col_head, col_cta = st.columns([2.5, 1])
    with col_head:
        st.markdown('<h1 class="consultoria-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
        st.markdown("<p style='color: #BFAF83; letter-spacing: 2px; font-weight: 300; font-size: 0.9rem;'>AUDITORIA TÉCNICA PROPRIETÁRIA DE EXTRATOS</p>", unsafe_allow_html=True)
    with col_cta:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<a href="https://contate.me/5592995087379" class="btn-whatsapp" target="_blank">Falar com Consultor ⚖️</a>', unsafe_allow_html=True)

    # --- 4. SIDEBAR (PARÂMETROS DE BUSCA) ---
    st.sidebar.markdown("### PARÂMETROS DE BUSCA")
    DICIONARIO_ALVOS = {
        "Cesta / Pacote": "CESTA|PACOTE",
        "Tarifas Bancárias": "TARIFA BANCARIA",
        "Mora": "MORA",
        "Baixas e Débitos (BX)": r"\bBX\b",
        "Crédito Pessoal": "PARCELA CREDITO PESSOAL",
        "Gastos Cartão de Crédito": "GASTOS CARTAO DE CREDITO",
        "Seguro": "SEGURO",
        "Adiantamento": "ADIANT",
        "Aplicações": "APLIC",
        "Encargos": "ENCARGOS",
        "Anuidade": "ANUIDADE",
        "Operações Vencidas": "OPERACOES VENCIDAS",
        "Dívidas em Atraso": "DIV. EM ATRASO"
    }
    selecionados = []
    for nome in DICIONARIO_ALVOS.keys():
        if st.sidebar.checkbox(nome, value=True):
            selecionados.append(nome)

    # --- INOVAÇÃO: FILTRO DE DATAS ---
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    st.sidebar.markdown("### PERÍODO DE AUDITORIA")
    usar_filtro_data = st.sidebar.checkbox("Ativar Limite de Datas (Prescrição)")
    
    if usar_filtro_data:
        data_inferior = st.sidebar.date_input("Data Inferior (Início)", format="DD/MM/YYYY")
        data_superior = st.sidebar.date_input("Data Superior (Fim)", format="DD/MM/YYYY")

    # --- 5. UPLOAD E PROCESSAMENTO ---
    st.markdown("<br>", unsafe_allow_html=True)
    upload = st.file_uploader("Submeta o arquivo PDF para certificação técnica automática", type="pdf")

    if upload and selecionados:
        with st.spinner('Analisando extrato, aplicando regras temporais e calculando valores...'):
            dados = []
            termos = [DICIONARIO_ALVOS[f] for f in selecionados]
            
            # INOVAÇÃO: MEMÓRIA DE DATA
            data_memoria_str = "---"
            
            with pdfplumber.open(upload) as pdf:
                for p in pdf.pages:
                    texto = p.extract_text()
                    if texto:
                        for linha in texto.split('\n'):
                            
                            # 1. Tenta capturar uma data nova na linha. Se achar, guarda na memória.
                            match_data = re.search(r'(\d{2}/\d{2}/\d{4})', linha)
                            data_linha_obj = None
                            
                            if match_data:
                                data_memoria_str = match_data.group(1)
                            
                            # 2. Converte a data da memória para formato real para aplicar o filtro
                            if data_memoria_str != "---":
                                try:
                                    data_linha_obj = datetime.strptime(data_memoria_str, "%d/%m/%Y").date()
                                except ValueError:
                                    pass

                            # 3. Aplica o filtro de data Superior/Inferior
                            if usar_filtro_data and data_linha_obj:
                                if data_linha_obj < data_inferior or data_linha_obj > data_superior:
                                    continue # Pula esta linha, está fora do período auditado
                            
                            # 4. Procura as tarifas/encargos na linha
                            for t in termos:
                                if re.search(t, linha, re.IGNORECASE):
                                    valor_m = re.findall(r'(\d[\d\.]*,\d{2})', linha)
                                    valor_final = valor_m[-1] if valor_m else "0,00"
                                    
                                    categoria_atual = "DESCONHECIDO"
                                    for k, v in DICIONARIO_ALVOS.items():
                                        if v == t:
                                            categoria_atual = k.upper()
                                            break
                                            
                                    dados.append({
                                        "DATA": data_memoria_str, # Injeta a data guardada
                                        "CATEGORIA": categoria_atual,
                                        "DESCRIÇÃO": linha.strip()[:100],
                                        "VALOR (R$)": valor_final
                                    })
                                    break
            
            # --- 6. EXIBIÇÃO DOS RESULTADOS (INTACTA) ---
            if dados:
                df = pd.DataFrame(dados)
                
                total_recuperavel = 0.0
                for v in df["VALOR (R$)"]:
                    try:
                        valor_limpo = v.replace('.', '').replace(',', '.')
                        total_recuperavel += float(valor_limpo)
                    except:
                        pass
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(f'<div class="impact-card"><p style="font-size: 0.7rem; color: #64748B;">OCORRÊNCIAS</p><h2 style="color: #BFAF83;">{len(df)}</h2></div>', unsafe_allow_html=True)
                with c2:
                    st.markdown(f'<div class="impact-card"><p style="font-size: 0.7rem; color: #64748B;">TOTAL RECUPERÁVEL</p><h2 style="color: #BFAF83;">R$ {total_recuperavel:,.2f}</h2></div>', unsafe_allow_html=True)
                with c3:
                    st.markdown(f'<div class="impact-card"><p style="font-size: 0.7rem; color: #64748B;">STATUS</p><h2 style="color: #10B981;">AUDITADO</h2></div>', unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True)
                
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 BAIXAR LAUDO TÉCNICO COMPLETO", csv, "laudo_medeiros.csv", "text/csv")
            else:
                st.info("Nenhuma divergência identificada nos parâmetros e datas selecionados.")

    # --- 7. RODAPÉ (INTACTO) ---
    RODAPE_HTML = """
    <div class="how-it-works">
        <h3 style="font-family: 'Cinzel', serif; color: #BFAF83; text-align: center; margin-bottom: 40px; letter-spacing: 2px;">PROCESSO DE CONSULTORIA</h3>
        <div style="display: flex; justify-content: space-around; gap: 30px; flex-wrap: wrap; text-align: center;">
            <div style="flex: 1; min-width: 250px;">
                <div class="step-number">I</div>
                <p style="font-weight: 600; color: #FFF;">Identificação Digital</p>
                <p style="font-size: 0.8rem; color: #94A3B8;">O robô cruza siglas bancárias com o banco de dados de tarifas abusivas.</p>
            </div>
            <div style="flex: 1; min-width: 250px;">
                <div class="step-number">II</div>
                <p style="font-weight: 600; color: #FFF;">Extração de Valores</p>
                <p style="font-size: 0.8rem; color: #94A3B8;">Captura precisa de cada centavo debitado indevidamente no extrato.</p>
            </div>
            <div style="flex: 1; min-width: 250px;">
                <div class="step-number">III</div>
                <p style="font-weight: 600; color: #FFF;">Certificação de Ativos</p>
                <p style="font-size: 0.8rem; color: #94A3B8;">Geração de laudo técnico com o valor total para pedido de restituição.</p>
            </div>
        </div>
    </div>
    <div class="footer-signature">
        <p class="footer-name">Edson Medeiros</p>
        <p class="footer-tech">CONSULTORIA & COMPLIANCE</p>
    </div>
    """
    st.markdown(RODAPE_HTML, unsafe_allow_html=True)

except Exception as e:
    st.error(f"⚠️ Erro de processamento. Tente novamente.")
    st.warning(f"Detalhes: {e}")
