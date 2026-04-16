import streamlit as st
import pdfplumber
import pandas as pd
import re

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Edson Medeiros | Auditoria Inteligente", layout="wide", page_icon="🏦")

# --- INJEÇÃO DE ESTILO (TAILWIND + CUSTOM CSS) ---
st.markdown("""
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@300;400;600&family=Great+Vibes&display=swap" rel="stylesheet">
    
    <style>
        /* Reset Streamlit */
        .block-container { padding-top: 0rem; padding-bottom: 0rem; max-width: 100% !important; }
        footer {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        
        /* Fontes */
        .font-serif { font-family: 'Playfair Display', serif; }
        .font-sans { font-family: 'Inter', sans-serif; }
        .font-signature { font-family: 'Great Vibes', cursive; }

        /* Gradiente Hero Quiet Luxury */
        .hero-gradient {
            background: radial-gradient(circle at 0% 0%, #F8F9FA 0%, #E8F5E9 50%, #0F172A 100%);
            min-height: 80vh;
        }

        /* Animações Sutilíssimas */
        .fade-in { animation: fadeIn 1.2s ease-out; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

        /* Cards e Inputs */
        .premium-card {
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(26, 95, 58, 0.1);
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.05);
            transition: all 0.3s ease;
        }
        .premium-card:hover { transform: translateY(-5px); box-shadow: 0 20px 40px rgba(0,0,0,0.08); }

        /* Custom Streamlit Elements */
        .stButton>button {
            background: #1A5F3A !important;
            color: white !important;
            border-radius: 50px !important;
            padding: 0.75rem 2.5rem !important;
            border: none !important;
            font-weight: 600 !important;
            transition: all 0.3s !important;
        }
        .stButton>button:hover { transform: scale(1.05); background: #0F172A !important; }
        
        /* Sidebar Fix */
        [data-testid="stSidebar"] { background-color: #0F172A !important; color: white; }
        [data-testid="stSidebar"] * { color: white !important; }
    </style>

    <nav class="flex justify-between items-center py-6 px-12 bg-white/80 sticky top-0 z-50 backdrop-blur-md">
        <div class="text-2xl font-serif text-slate-900 tracking-tighter">Edson Medeiros<span class="text-emerald-700">.</span></div>
        <div class="hidden md:flex space-x-8 font-sans text-sm uppercase tracking-widest text-slate-600">
            <a href="#" class="hover:text-emerald-700 transition">Início</a>
            <a href="#" class="hover:text-emerald-700 transition">Funcionalidades</a>
            <a href="#" class="hover:text-emerald-700 transition">Privacidade</a>
        </div>
    </nav>

    <section class="hero-gradient flex items-center px-12 relative overflow-hidden">
        <div class="max-w-4xl fade-in relative z-10">
            <span class="text-emerald-700 font-sans font-bold uppercase tracking-widest text-xs mb-4 block">Tecnologia Proprietária</span>
            <h1 class="text-6xl md:text-7xl font-serif text-slate-900 leading-tight mb-6">
                Robô Leitor de Extratos <br>
                <span class="italic text-slate-700">Análise Inteligente e Elegante.</span>
            </h1>
            <p class="text-lg text-slate-600 font-sans max-w-xl mb-10 leading-relaxed">
                Transformamos dados bancários complexos em clareza estratégica. Auditoria de alta precisão com a sofisticação que seu negócio exige.
            </p>
        </div>
        <div class="absolute right-[-10%] top-20 opacity-10 pointer-events-none">
             <h1 style="font-size: 30rem;" class="font-serif">EM</h1>
        </div>
    </section>
""", unsafe_allow_html=True)

# --- CONFIGURAÇÃO SIDEBAR (PARÂMETROS) ---
st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
st.sidebar.title("Configurações")
DICIONARIO_ALVOS = {
    "Mora Crédito Pessoal": "MORA CREDITO PESSOAL",
    "Encargos": "ENCARGOS",
    "Parcela Crédito Pessoal": "PARCELA CREDITO PESSOAL",
    "BX (Baixas)": r"\bBX\b",
    "Tarifa Bancária": "TARIFA BANCARIA",
    "Título de Capitalização": "TITULO DE CAPITALIZACAO",
    "Pacote de Serviços": "PACOTE DE SERVIÇOS",
    "Seguros": "SEGURO",
    "Adiantamento (ADIANT)": "ADIANT"
}

selecionados = []
for nome in DICIONARIO_ALVOS.keys():
    if st.sidebar.checkbox(nome, value=True):
        selecionados.append(nome)

# --- CONTAINER DE APLICAÇÃO (WEBAPP) ---
st.markdown('<div class="px-12 -mt-20 relative z-20">', unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="premium-card p-10 bg-white">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        st.markdown('<h3 class="font-serif text-2xl mb-4">Área de Auditoria</h3>', unsafe_allow_html=True)
        upload = st.file_uploader("Arraste seu arquivo PDF aqui", type="pdf", label_visibility="collapsed")
        
    with col2:
        st.markdown('<div class="text-sm text-slate-500 mt-8">Os arquivos são processados em tempo real e não são armazenados em nossos servidores. Segurança e sigilo total.</div>', unsafe_allow_html=True)

    if upload and selecionados:
        def processar(file, filtros):
            dados = []
            with pdfplumber.open(file) as pdf:
                for p in pdf.pages:
                    text = p.extract_text()
                    if text:
                        for linha in text.split('\n'):
                            for f in filtros:
                                if re.search(DICIONARIO_ALVOS[f], linha, re.IGNORECASE):
                                    data_match = re.search(r'(\d{2}/\d{2}/\d{4})', linha)
                                    dados.append({
                                        "Data": data_match.group(1) if data_match else "---",
                                        "Categoria": f,
                                        "Lançamento": linha.strip()
                                    })
                                    break
            return pd.DataFrame(dados)

        df = processar(upload, selecionados)
        
        if not df.empty:
            st.markdown('<hr class="my-8 opacity-20">', unsafe_allow_html=True)
            st.success(f"Identificamos {len(df)} registros passíveis de análise.")
            st.dataframe(df, use_container_width=True)
            
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("Gerar Relatório Oficial", csv, "auditoria_edson_medeiros.csv")
    
    st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- FOOTER PREMIUM ---
st.markdown("""
    <footer class="bg-slate-900 text-white mt-24 py-16 px-12">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-12">
            <div>
                <div class="text-2xl font-serif mb-6">Edson Medeiros<span class="text-emerald-500">.</span></div>
                <p class="text-slate-400 text-sm leading-relaxed">
                    Especialista em inteligência de dados aplicada ao setor financeiro e jurídico. 
                    Desenvolvendo soluções que unem tecnologia e exclusividade.
                </p>
            </div>
            <div>
                <h4 class="font-sans font-bold uppercase tracking-widest text-xs mb-6 text-emerald-500">Navegação</h4>
                <ul class="text-slate-400 text-sm space-y-4">
                    <li><a href="#" class="hover:text-white transition">Privacidade e Termos</a></li>
                    <li><a href="#" class="hover:text-white transition">Suporte Técnico</a></li>
                    <li><a href="#" class="hover:text-white transition">LinkedIn</a></li>
                </ul>
            </div>
            <div class="text-right flex flex-col justify-end">
                <div class="font-signature text-3xl text-emerald-500 mb-2">Edson Medeiros</div>
                <div class="text-[10px] uppercase tracking-[0.3em] text-slate-500">© 2026 Proprietary Technology</div>
            </div>
        </div>
    </footer>
""", unsafe_allow_html=True)
