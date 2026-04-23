import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Edson Medeiros | Excelência em Auditoria", page_icon="⚖️", layout="centered")

# --- ESTILO CSS AVANÇADO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600&family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Inter:wght@200;400&display=swap');
    
    :root { --navy: #0F172A; --gold: #BFAF83; --white: #FFFFFF; }

    .stApp {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        color: var(--white);
        font-family: 'Inter', sans-serif;
    }

    .main-container {
        text-align: center;
        padding: 80px 40px;
        border: 1px solid rgba(191, 175, 131, 0.15);
        background: rgba(15, 23, 42, 0.4);
        backdrop-filter: blur(20px);
        border-radius: 4px;
        margin-top: 100px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    }

    .brand-name {
        font-family: 'Cinzel', serif;
        font-size: 0.8rem;
        letter-spacing: 6px;
        color: var(--gold);
        text-transform: uppercase;
        margin-bottom: 20px;
    }

    .headline {
        font-family: 'Playfair Display', serif;
        font-size: 3rem;
        font-weight: 700;
        line-height: 1.2;
        margin-bottom: 30px;
        background: linear-gradient(to right, #FFFFFF, #BFAF83, #FFFFFF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .divider {
        width: 60px;
        height: 1px;
        background: var(--gold);
        margin: 30px auto;
        opacity: 0.6;
    }

    .status-msg {
        font-family: 'Inter', sans-serif;
        font-weight: 200;
        font-size: 1.1rem;
        line-height: 1.8;
        color: #94A3B8;
        max-width: 600px;
        margin: 0 auto;
        font-style: italic;
    }

    .highlight { color: var(--gold); font-weight: 400; }

    /* Loader Minimalista */
    .pulse {
        width: 8px;
        height: 8px;
        background-color: var(--gold);
        border-radius: 50%;
        display: inline-block;
        margin: 40px 5px;
        animation: pulse 1.5s infinite ease-in-out;
    }
    .pulse:nth-child(2) { animation-delay: 0.2s; }
    .pulse:nth-child(3) { animation-delay: 0.4s; }

    @keyframes pulse {
        0%, 80%, 100% { opacity: 0; transform: scale(0.8); }
        40% { opacity: 1; transform: scale(1.2); }
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONTEÚDO DA PÁGINA ---
st.markdown(f"""
    <div class="main-container">
        <div class="brand-name">Consultoria de Ativos</div>
        <div class="headline">Aprimorando a Precisão da sua Auditoria</div>
        
        <div class="divider"></div>
        
        <div class="status-msg">
            No momento, nossa plataforma passa por uma <span class="highlight">calibragem técnica rigorosa</span>. 
            Estamos refinando os algoritmos de extração para assegurar que cada centavo de desconto indevido seja identificado com clareza absoluta.
            <br><br>
            A excelência requer tempo. Retornaremos em breve sob o comando de <span class="highlight">Edson Medeiros</span>.
        </div>
        
        <div>
            <div class="pulse"></div>
            <div class="pulse"></div>
            <div class="pulse"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Ocultar elementos padrão
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
