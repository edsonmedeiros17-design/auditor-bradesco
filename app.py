import streamlit as st
import pdfplumber
import pandas as pd
import re

# --- CONFIGURAÇÃO MASTER (Onde o Prestígio Começa) ---
st.set_page_config(
    page_title="Edson Medeiros | Auditoria Proprietária de Ativos",
    layout="wide",
    page_icon="🏦",
    initial_sidebar_state="collapsed" # Começa fechado para focar no Hero
)

# --- CSS SIGNATURE DESIGN (CORREÇÃO DE CONTRASTE E EFEITO 3D SOFISTICADO) ---
st.markdown("""
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Inter:wght@300;400;600&family=Great+Vibes&display=swap" rel="stylesheet">
    
    <style>
        /* RESET STREAMLIT PARA FOCO TOTAL NO DESIGN */
        .block-container { padding: 0rem !important; max-width: 100% !important; }
        footer, #MainMenu, header { visibility: hidden !important; height: 0px !important; }
        
        /* VARIÁVEIS DE CORES: BLACK TIE FINANCE (ALTO CONTRASTE) */
        :root {
            --bg-deep-navy: #050A18; /* Fundo Sombrio e Profundo */
            --text-ivory: #F8F4E6;    /* Texto Principal Claro e Suave */
            --accent-gold-matte: #BFAF83;   /* Dourado Matte Sofisticado */
            --accent-gold-bright: #D4AF37;  /* Dourado Matte Brilhante (Accent) */
            --emerald-matte: #1A5F3A;   /* Sucesso Matte */
            --sidebar-dark: #02050A; /* Sidebar Quase Preta */
        }

        body, .stApp {
            background-color: var(--bg-deep-navy) !important;
            color: var(--text-ivory) !important;
            font-family: 'Inter', sans-serif;
        }

        /* FONTE DOS TÍTULOS (ESTILO 'CINZEL' ROMANO CLÁSSICO) */
        .font-cinzel { font-family: 'Cinzel', serif; }
        .font-signature { font-family: 'Great Vibes', cursive; }

        /* -----------------------------------------------------------
           CORREÇÃO PRIORITÁRIA: EFEITO 3D NAS LETRAS (TITULO)
           Utiliza text-shadow complexo para volume e profundidade.
           Cores escuras no fundo fazem o dourado brilhar.
        ----------------------------------------------------------- */
        .effect-3d-gold {
            color: var(--accent-gold-matte);
            background: linear-gradient(135deg, #BFAF83 0%, #D4AF37 40%, #D2B48C 60%, #A68A5D 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            
            /* MULTI-CAMADAS DE SOMBRA PARA EFEITO 3D SOFISTICADO */
            text-shadow: 
                0px 1px 0px rgba(212, 175, 55, 0.4), /* Sombra de brilho interno superior */
                0px 2px 1px rgba(0, 0, 0, 0.7),     /* Sombra de volume 1 */
                0px 3px 2px rgba(0, 0, 0, 0.6),     /* Sombra de volume 2 */
                0px 4px 3px rgba(0, 0, 0, 0.5),     /* Sombra de volume 3 */
                1px 5px 6px rgba(0, 0, 0, 0.8),     /* Sombra de profundidade suave */
                0px 8px 12px rgba(0, 0, 0, 0.6);    /* Sombra projetada no fundo */
                
            letter-spacing: 2px;
            transform: skewY(-1deg); /* Leve inclinação para dinâmica */
        }

        /* HERO SECTION IMERSIVA: ALTO CONTRASTE */
        .hero-section {
            min-height: 80vh;
            display: flex;
            align-items: center;
            padding: 0 8%;
            position: relative;
            overflow: hidden;
            background: radial-gradient(circle at 10% 10%, #0A152A 0%, #050A18 70%);
        }

        .hero-subtitle {
            font-family: 'Inter', sans-serif;
            text-transform: uppercase;
            letter-spacing: 5px;
            color: var(--text-ivory);
            font-size: 0.9rem;
            font-weight: 300;
            opacity: 0.8;
        }

        /* INICIAIS 'EM' GIGANTES (EFEITO DE FAIXA DE SEGURANÇA) */
        .em-background {
            position: absolute;
            right: -5%;
            top: 10%;
            font-family: 'Cinzel', serif;
            font-size: 35rem;
            font-weight: 700;
            line-height: 1;
            color: rgba(191, 175, 131, 0.05); /* Dourado Matte Quase Transparente */
            pointer-events: none;
            z-index: 1;
            transform: rotate(-5deg);
        }

        /* CONTAINER DA APLICAÇÃO (WEBAPP) */
        .webapp-container {
            max-width: 1200px;
            margin: -100px auto 100px auto;
            position: relative;
            z-index: 10;
        }

        .premium-card {
            background: rgba(10, 21, 42, 0.9); /* Navy Levemente Transparente */
            backdrop-filter: blur(20px);
            border: 1px solid rgba(212, 175, 55, 0.2);
            border-radius: 4px; /* Quadrado Clássico */
            padding: 50px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        }

        /* INPUTS E TABELAS ESTILIZADAS */
        .stFileUploader section {
            background-color: transparent !important;
            border: 1px dashed rgba(212, 175, 55, 0.4) !important;
            border-radius: 0px !important;
            color: var(--text-ivory) !important;
        }

        div[data-testid="stDataFrame"] {
            background-color: #02050A; /* Fundo da Tabela Super Escuro */
            border: 1px solid rgba(212, 175, 55, 0.3);
            border-radius: 2px;
            padding: 5px;
        }
        
        div[data-testid="stDataFrame"] * {
            color: var(--text-ivory) !important;
            font-size: 0.85rem !important;
        }

        /* BOTÃO DE EXPORTAÇÃO (GRADIENTE DOURADO 3D) */
        .stButton>button {
            background: linear-gradient(135deg, #BFAF83 0%, #D4AF37 100%) !important;
            color: #050A18 !important; /* Texto Escuro sobre o Dourado Bright */
            font-weight: 700 !important;
            font-family: 'Cinzel', serif !important;
            letter-spacing: 2px !important;
            border: none !important;
            border-radius: 0px !important;
            padding: 15px 40px !important;
            transition: 0.3s !important;
            box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3) !important;
        }
        .stButton>button:hover {
            background: var(--text-ivory) !important;
            color: #050A18 !important;
            transform: translateY(-2px) scale(1.02);
            box-shadow: 0 8px 25px rgba(212, 175, 55, 0.5) !important;
        }

        /* SIDEBAR PROFISSIONAL (ALTO CONTRASTE) */
        [data-testid="stSidebar"] {
            background-color: var(--sidebar-dark) !important;
            border-right: 1px solid rgba(212, 175, 55, 0.3);
        }
        
        [data-testid="stSidebar"] .stMarkdown h3 {
            color: var(--accent-gold-bright) !important;
            font-family: 'Cinzel', serif;
            font-size: 1rem;
            letter-spacing: 2px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(212, 175, 55, 0.2);
        }

        [data-testid="stSidebar"] label p {
            color: #E0E0E0 !important;
            font-size: 0.85rem !important;
        }

        /* FOOTER DE PRESTÍGIO */
        .footer {
            position: fixed;
            bottom: 30px;
            right: 40px;
            text-align: right;
            z-index: 100;
        }
        .footer-line { border-top: 1px solid var(--accent-gold-matte); width: 100px; margin-left: auto; margin-bottom: 10px; opacity: 0.5; }
        .footer-text { font-family: 'Great Vibes', cursive; color: var(--accent-gold-bright); font-size: 1.8rem; margin: 0; }
        .footer-sub { font-family: 'Inter', sans-serif; font-size: 0.6rem; color: var(--text-ivory); letter-spacing: 3px; text-transform: uppercase; opacity: 0.7; }
    </style>
    """, unsafe_allow_html=True)

# --- CABEÇALHO HERO IMERSIVO (CORRIGIDO E SOFISTICADO) ---
st.markdown(f"""
    <section class="hero-section">
        <div class="max-w-5xl relative z-10 fade-in">
            <p class="hero-subtitle mb-3">Tecnologia Proprietária de Compliance</p>
            <h1 class="text-7xl font-cinzel leading-tight mb-8 effect-3d-gold">
                Robô Leitor <br> de Extratos
            </h1>
            <p class="text-xl text-ivory max-w-xl leading-relaxed opacity-90">
                Auditoria inteligente e elegante. Transformamos dados bancários sombrios em clareza estratégica para seu negócio.
            </p>
        </div>
        <div class="em-background">EM</div>
    </section>
""", unsafe_allow_html=True)

# --- DICIONÁRIO DE FILTROS ---
DICIONARIO_ALVOS = {
    "Mora Crédito Pessoal": "MORA CREDITO PESSOAL",
    "Encargos": "ENCARGOS",
    "Parcela Crédito Pessoal": "PARCELA CREDITO PESSOAL",
    "Gastos Cartão de Crédito": "GASTOS CARTAO DE CREDITO",
    "BX (Baixas)": r"\bBX\b",
    "APLIC (Aplicações)": r"\bAPLIC\b",
    "Tarifa Bancária": "TARIFA BANCARIA",
    "Anuidade Cartão": "CARTAO CREDITO ANUIDADE",
    "Título de Capitalização": "TITULO DE CAPITALIZACAO",
    "Pacote de Serviços": "PACOTE DE SERVIÇOS",
    "Vida e Previdência": "VIDA E PREV",
    "Seguros": "SEGURO",
    "Serviço de Cartão": "SERVICO CARTAO",
    "Adiantamento (ADIANT)": "ADIANT",
    "Parcelas Vencidas": "VENCIDAS",
    "Tarifa 2ª Via": "TAR 2 VIA"
}

# --- SIDEBAR PROFISSIONAL (ALTO CONTRASTE) ---
# Forçamos a sidebar a estar visível agora para os filtros técnicos
st.sidebar.markdown("<br><br><br>", unsafe_allow_html=True)
st.sidebar.markdown("### PARÂMETROS TÉCNICOS")
st.sidebar.markdown("<br>", unsafe_allow_html=True)
selecionados = []
for nome in DICIONARIO_ALVOS.keys():
    # Usamos upper() nos rótulos para sobriedade técnica
    if st.sidebar.checkbox(nome.upper(), value=True):
        selecionados.append(nome)

# --- LÓGICA DE AUDITORIA ---
def executar_auditoria_premium(file, filtros_nomes, dicionario):
    dados = []
    # Criamos a lista de termos técnicos para busca
    termos_busca = [dicionario[f] for f in filtros_nomes]
    
    with pdfplumber.open(file) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                linhas = texto.split('\n')
                for linha in linhas:
                    for termo in termos_busca:
                        if re.search(termo, linha, re.IGNORECASE):
                            # Tenta capturar a data
                            data_match = re.search(r'(\d{2}/\d{2}/\d{4})', linha)
                            
                            # Identifica qual categoria foi achada
                            cat = [k for k, v in dicionario.items() if v == termo][0].upper()
                            
                            dados.append({
                                "DATA": data_match.group(1) if data_match else "---",
                                "CATEGORIA": cat,
                                "DETALHAMENTO DO LANÇAMENTO": linha.strip()
                            })
                            break # Evita duplicar a mesma linha
    return pd.DataFrame(dados)

# --- WEBAPP AREA (CONTAINER FLUTUANTE) ---
st.markdown('<div class="webapp-container">', unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    
    # Grid de Entrada
    col1, col2 = st.columns([1.5, 1])
    with col1:
        st.markdown('<p class="font-cinzel text-2xl text-ivory mb-6">Área de Processamento de Arquivos</p>', unsafe_allow_html=True)
        # Upload com estilo clássico/quadrado
        upload = st.file_uploader("UPLOAD DE EXTRATO BRADESCO (PDF)", type="pdf")
        
    with col2:
        st.markdown(f"""
            <div style="background: rgba(191, 175, 131, 0.05); padding: 20px; border-radius: 2px; border: 1px solid rgba(191, 175, 131, 0.1);">
                <p class="text-xs text-ivory font-bold uppercase tracking-widest mb-3" style="color: var(--accent-gold-bright);">Protocolo de Segurança</p>
                <p class="text-xs text-ivory opacity-80 leading-relaxed">
                    Processamento técnico em tempo real. Arquivos não são armazenados. Compliance total com diretrizes de sigilo bancário.
                </p>
            </div>
        """, unsafe_allow_html=True)

    # Área de Resultados
    if upload:
        if not selecionados:
            st.markdown('<hr style="border: 0; border-top: 1px solid rgba(212, 175, 55, 0.1); margin: 30px 0;">', unsafe_allow_html=True)
            st.warning("⚠️ Selecione ao menos um parâmetro técnico no menu lateral.")
        else:
            with st.spinner('O robô proprietário está auditando o documento...'):
                df_resultado = executar_auditoria_premium(upload, selecionados, DICIONARIO_ALVOS)
                
                if not df_resultado.empty:
                    st.markdown('<hr style="border: 0; border-top: 1px solid rgba(212, 175, 55, 0.1); margin: 30px 0;">', unsafe_allow_html=True)
                    st.success(f"Análise finalizada: {len(df_resultado)} lançamentos técnicos identificados.")
                    
                    # Tabela com o estilo super escuro
                    st.dataframe(df_resultado, use_container_width=True, hide_index=True)
                    
                    # Botão de Exportação Elegante e 3D
                    csv = df_resultado.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        "EXPORTAR PARA RELATÓRIO OFICIAL",
                        csv,
                        f"auditoria_premium_{upload.name}.csv",
                        "text/csv"
                    )
                else:
                    st.markdown('<hr style="border: 0; border-top: 1px solid rgba(212, 175, 55, 0.1); margin: 30px 0;">', unsafe_allow_html=True)
                    st.info("Nenhuma divergência identificada para os filtros selecionados.")
    
    st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- FOOTER DE PRESTÍGIO (ASSINATURA DE AUTORIDADE) ---
st.markdown(f"""
    <div class="footer">
        <div class="footer-line"></div>
        <p class="footer-text">Edson Medeiros</p>
        <p class="footer-sub">Proprietary Audit Technology</p>
    </div>
    """, unsafe_allow_html=True)
