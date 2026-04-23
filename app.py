import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Edson Medeiros | Manutenção", page_icon="⚖️", layout="centered")

# --- ESTILO CSS PARA O MODO MANUTENÇÃO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600&family=Playfair+Display:wght@700&family=Inter:wght@300;400&display=swap');
    
    :root { --navy: #0F172A; --gold: #BFAF83; }

    .stApp {
        background: radial-gradient(circle, #1E293B 0%, #0F172A 100%);
        color: #F8F9FA;
        font-family: 'Inter', sans-serif;
    }

    .container {
        text-align: center;
        padding: 50px;
        border: 1px solid rgba(191, 175, 131, 0.2);
        border-radius: 20px;
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(10px);
        margin-top: 100px;
    }

    .title {
        font-family: 'Playfair Display', serif;
        font-size: 3.5rem;
        background: linear-gradient(180deg, #FFFFFF 0%, #BFAF83 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }

    .subtitle {
        color: var(--gold);
        letter-spacing: 3px;
        font-size: 0.9rem;
        text-transform: uppercase;
        margin-bottom: 40px;
    }

    .message {
        font-size: 1.2rem;
        line-height: 1.6;
        color: #CBD5E1;
        max-width: 500px;
        margin: 0 auto;
    }

    .loader {
        margin: 30px auto;
        border: 2px solid rgba(191, 175, 131, 0.1);
        border-top: 2px solid var(--gold);
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 2s linear infinite;
    }

    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
    """, unsafe_allow_html=True)

# --- CONTEÚDO DA PÁGINA ---
st.markdown(f"""
    <div class="container">
        <div class="title">Edson Medeiros</div>
        <div class="subtitle">Consultoria de Ativos</div>
        
        <div class="loader"></div>
        
        <div class="message">
            Estamos realizando uma <b>atualização técnica</b> em nosso motor de auditoria para garantir a máxima precisão nos seus laudos.
            <br><br>
            O sistema retornará em instantes com novas funcionalidades de processamento.
        </div>
        
        <p style="margin-top: 50px; font-family: 'Cinzel', serif; color: #BFAF83; font-size: 0.8rem;">
            Aguarde, estamos otimizando sua experiência.
        </p>
    </div>
    """, unsafe_allow_html=True)

# Oculta o menu e o footer padrão do Streamlit para um visual mais limpo
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
