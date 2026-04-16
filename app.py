import streamlit as st
import pdfplumber
import pandas as pd
import re

# --- CONFIGURAÇÃO DE ELITE ---
st.set_page_config(page_title="Edson Medeiros | Consultoria de Ativos", layout="wide", page_icon="⚖️")

# --- CSS ARCHITECTURE (REFINAMENTO EMPRESARIAL) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600&family=Playfair+Display:wght@700&family=Inter:wght@300;400;600&family=Great+Vibes&display=swap');

    :root {
        --navy-deep: #0F172A;
        --gold-matte: #BFAF83;
        --emerald-success: #10B981;
    }

    .stApp { 
        background: radial-gradient(circle at center, #1E293B 0%, #0F172A 100%); 
        color: #F8F9FA;
    }

    .consultoria-title {
        font-family: 'Playfair Display', serif;
        font-size: 4rem;
        background: linear-gradient(180deg, #FFFFFF 0%, #BFAF83 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0px 10px 20px rgba(0,0,0,0.4);
        margin-bottom: 5px;
    }

    .impact-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(191, 175, 131, 0.2);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        transition: 0.3s;
    }

    /* Estilo para a secção Como Funciona */
    .how-it-works {
        background: rgba(15, 23, 42, 0.8);
        border-radius: 16px;
        padding: 30px;
        margin-top: 50px;
        border: 1px solid rgba(191, 175, 131, 0.1);
    }

    .step-number {
        color: var(--gold-matte);
        font-family: 'Cinzel', serif;
        font-size: 1.5rem;
        font-weight: bold;
    }

    /* Botão WhatsApp flutuante ou destaque */
    .btn-whatsapp {
        background-color: #25D366;
        color: white !important;
        padding: 15px 30px;
        border-radius: 50px;
        text-decoration: none;
        font-weight: bold;
        display: inline-block;
        transition: 0.3s;
        box-shadow: 0 4px 15px rgba(37, 211, 102, 0.3);
    }
    .btn-whatsapp:hover { transform: scale(1.05); background-color: #128C7E; }

    .footer-signature {
        position: fixed;
        bottom: 30px;
        right: 40px;
        text-align: right;
    }
    .footer-name { font-family: 'Great Vibes', cursive; color: var(--gold-matte); font-size: 2rem; margin: 0; }
    </style>
    """, unsafe_allow_html=True)

# --- CABEÇALHO E BOTÃO DE CONSULTORIA ---
col_head, col_cta = st.columns([3, 1])
with col_head:
    st.markdown('<h1 class="consultoria-title">Consultoria de Ativos</h1>', unsafe_allow_html=True)
    st.markdown("<p style='color: #BFAF83; letter-spacing: 2px; font-weight: 300;'>AUDITORIA TÉCNICA PROPRIETÁRIA</p>", unsafe_allow_html=True)

with col_cta:
    st.markdown("<br><br>", unsafe_allow_html=True)
    # Substitua pelo seu link real do WhatsApp
    st.markdown('<a href="https://wa.me/SEUNUMERO" class="btn-whatsapp">Falar com Consultor ⚖️</a>', unsafe_allow_html=True)

# --- APP INTERFACE (UPLOAD) ---
st.markdown("<br>", unsafe_allow_html=True)
upload = st.file_uploader("Submeta o arquivo PDF para certificação de auditoria", type="pdf")

# --- LÓGICA DE PROCESSAMENTO (IGUAL À ANTERIOR) ---
if upload:
    # ... (mantenha a lógica de processamento do dicionário e pdfplumber aqui) ...
    # Se precisar do código completo da lógica, ele está mantido no seu histórico
    pass

# --- SECÇÃO: COMO FUNCIONA A CONSULTORIA ---
st.markdown("""
    <div class="how-it-works">
        <h3 style="font-family: 'Cinzel', serif; color: #BFAF83; text-align: center; margin-bottom: 30px;">COMO FUNCIONA O NOSSO PROCESSO</h3>
        <div style="display: flex; justify-content: space-around; gap: 20px; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 200px; text-align: center;">
                <div class="step-number">01</div>
                <p style="font-weight: 600; margin-top: 10px;">Upload Seguro</p>
                <p style="font-size: 0.85rem; color: #94A3B8;">Submeta o seu extrato original. O processamento é feito em tempo real com sigilo total.</p>
            </div>
            <div style="flex: 1; min-width: 200px; text-align: center;">
                <div class="step-number">02</div>
                <p style="font-weight: 600; margin-top: 10px;">Varredura Técnica</p>
                <p style="font-size: 0.85rem; color: #94A3B8;">O nosso motor de IA identifica siglas e lançamentos indevidos (Tarifas, Seguros, Mora).</p>
            </div>
            <div style="flex: 1; min-width: 200px; text-align: center;">
                <div class="step-number">03</div>
                <p style="font-weight: 600; margin-top: 10px;">Laudo e Recuperação</p>
                <p style="font-size: 0.85rem; color: #94A3B8;">Receba um relatório detalhado para fundamentar o seu pedido de restituição de valores.</p>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- FOOTER ---
st.markdown(f"""
    <div class="footer-signature">
        <p class="footer-name">Edson Medeiros</p>
        <p style="font-family: 'Inter', sans-serif; font-size: 0.7rem; color: #64748B; letter-spacing: 3px;">CONSULTORIA & COMPLIANCE</p>
    </div>
    """, unsafe_allow_html=True)
