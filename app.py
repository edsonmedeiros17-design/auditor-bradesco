import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Edson Medeiros | Auditoria", page_icon="⚖️", layout="centered")

# --- ESTILO CSS MINIMALISTA E LUXUOSO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Inter:wght@200;400&display=swap');
    
    :root { --navy: #0F172A; --gold: #BFAF83; }

    .stApp {
        background: radial-gradient(circle at center, #1E293B 0%, #0F172A 100%);
        color: #FFFFFF;
        font-family: 'Inter', sans-serif;
    }

    .main-wrapper {
        text-align: center;
        margin-top: 15vh;
        padding: 40px;
    }

    .name-title {
        font-family: 'Cinzel', serif;
        font-size: 3.5rem;
        letter-spacing: 12px;
        color: #FFFFFF;
        margin-bottom: 5px;
        font-weight: 700;
        text-transform: uppercase;
    }

    .subtitle {
        font-family: 'Cinzel', serif;
        font-size: 1rem;
        letter-spacing: 5px;
        color: var(--gold);
        margin-bottom: 60px;
        opacity: 0.8;
    }

    .maintenance-box {
        border-top: 1px solid rgba(191, 175, 131, 0.3);
        border-bottom: 1px solid rgba(191, 175, 131, 0.3);
        padding: 30px 0;
        max-width: 500px;
        margin: 0 auto;
    }

    .maintenance-text {
        font-weight: 200;
        font-size: 1.2rem;
        letter-spacing: 2px;
        color: #CBD5E1;
        text-transform: uppercase;
    }

    /* Animação Sutil */
    .fade-in {
        animation: fadeIn 2.5s ease-in
