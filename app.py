"""
NOME DO PROJETO: Edital.IA (Versão 19.48 - Conversion Ready - Professional UI)
VERSÃO: MVP 19.48 (UI Refinada & Bugfix Feedback)
AUTOR: Lucas Almeida (Rota Fácil / Açaicat)
DATA: Janeiro/2026
DEPÊNDENCIA: pip install fpdf gspread oauth2client google-generativeai pypdf2 streamlit
"""

import streamlit as st
import google.generativeai as genai
import json
import os
from PyPDF2 import PdfReader
import datetime
import time

# --- IMPORTAÇÕES OPCIONAIS ---
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    TEM_GSPREAD = True
except ImportError:
    TEM_GSPREAD = False

try:
    from fpdf import FPDF
    TEM_PDF = True
except ImportError:
    TEM_PDF = False

# ==============================================================================
# 1. CONFIGURAÇÃO VISUAL (PROFESSIONAL & MINIMALIST)
# ==============================================================================
st.set_page_config(page_title="Edital.IA | Corporate", layout="wide", page_icon="🏛️")

st.markdown("""
    <style>
    /* --- GERAL E TIPOGRAFIA --- */
    body {
        color: #1e293b;
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3 {
        color: #0f172a;
        font-weight: 700 !important;
    }

    /* --- INPUTS E FORMULÁRIOS (SOLICITAÇÃO DE COR AZUL CLARO) --- */
    /* Força o fundo azul claro nos inputs de texto, número e áreas de texto */
    .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #f0f7ff !important; /* Azul bem claro */
        border: 1px solid #cbd5e1 !important;
        color: #0f172a !important; /* Texto escuro */
        border-radius: 6px;
    }
    
    /* Foco no input */
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
    }

    /* Rótulos (Labels) dos inputs - Forçando contraste alto */
    .stMarkdown label p, div[data-testid="stWidgetLabel"] p {
        font-size: 14px !important;
        color: #334155 !important; /* Cinza escuro, quase preto */
        font-weight: 600 !important;
    }

    /* --- CARDS E BOXES (DESIGN FLAT) --- */
    
    /* Instruções */
    .instruction-box {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 8px;
        border-left: 4px solid #2563eb; /* Azul Royal */
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        color: #475569;
        font-size: 14px;
        margin-bottom: 25px;
    }
    
    /* Box Financeiro */
    .finance-box {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .finance-title {
        color: #64748b;
        font-weight: 600;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 5px;
    }
    .finance-value {
        color: #059669; /* Verde sério */
        font-weight: 700;
        font-size: 26px;
        font-family: 'Roboto Mono', monospace;
    }
    
    /* Dicas Estratégicas */
    .tip-card {
        background-color: #fefce8;
        color: #854d0e;
        border: 1px solid #fef08a;
        padding: 15px;
        margin-bottom: 10px;
        font-size: 14px;
        border-radius: 6px;
    }
    
    /* Box Especialista (WhatsApp) - Minimalista */
    .expert-box {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 25px;
        border-radius: 8px;
        text-align: center;
        margin-top: 30px;
        margin-bottom: 30px;
    }
    .expert-title {
        color: #0f172a;
        font-weight: 700;
        font-size: 18px;
        margin-bottom: 10px;
    }
    
    /* Tags de Status - Pílulas discretas */
    .status-tag-open { background-color: #dcfce7; color: #166534; padding: 4px 12px; border-radius: 6px; font-weight: 600; font-size: 12px; display: inline-block; }
    .status-tag-closed { background-color: #fee2e2; color: #991b1b; padding: 4px 12px; border-radius: 6px; font-weight: 600; font-size: 12px; display: inline-block; }
    
    .match-tag-high { background-color: #dbeafe; color: #1e40af; padding: 4px 12px; border-radius: 6px; font-weight: 600; font-size: 12px; display: inline-block; }
    .match-tag-low { background-color: #fef3c7; color: #92400e; padding: 4px 12px; border-radius: 6px; font-weight: 600; font-size: 12px; display: inline-block; }

    /* Estilos Gerais de Guias */
    .guide-box {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 15px;
        border-left: 4px solid #64748b;
    }
    .guide-title { color: #0f172a; font-weight: 700; font-size: 16px; margin-bottom: 8px; }
    .guide-suggestion { color: #334155; font-size: 15px; line-height: 1.6; }
    .guide-source { font-size: 11px; color: #94a3b8; text-align: right; margin-top: 10px; font-style: italic;}
    .guide-warning { 
        background-color: #fff1f2; color: #be123c; 
        padding: 10px; border-radius: 6px; font-size: 13px; margin-top: 10px; 
        border: 1px solid #ffe4e6; font-weight: 600;
    }
    
    .block-header {
        background-color: transparent;
        border-bottom: 1px solid #e2e8f0;
        padding-bottom: 8px;
        font-weight: 700;
        font-size: 18px;
        color: #1e293b;
        margin-top: 30px;
        margin-bottom: 20px;
    }

    .risk-card {
        background-color: #fff7ed;
        border-left: 4px solid #fb923c;
        padding: 12px;
        margin-bottom: 8px;
        color: #9a3412;
        font-size: 14px;
        border-radius: 4px;
    }
    
    /* 10 Perguntas */
    .question-box {
        background-color: #ffffff;
        padding: 18px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        margin-bottom: 12px;
    }
    .question-header {
        font-weight: 700;
        color: #64748b;
        margin-bottom: 6px;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Timeline */
    .timeline-box { position: relative; padding-left: 30px; border-left: 2px solid #e2e8f0; margin-bottom: 20px; }
    .timeline-dot { position: absolute; left: -6px; top: 0; width: 10px; height: 10px; border-radius: 50%; background-color: #3b82f6; border: 2px solid #fff; box-shadow: 0 0 0 1px #3b82f6;}
    .timeline-date { font-size: 13px; font-weight: 700; color: #3b82f6; text-transform: uppercase; margin-bottom: 4px; }
    .timeline-content { background-color: #f8fafc; color: #334155; padding: 12px; border-radius: 6px; font-size: 14px; border: 1px solid #e2e8f0; }
    
    /* Alerta Legal */
    .legal-box {
        background-color: #f8fafc;
        border: 1px solid #cbd5e1;
        padding: 12px;
        font-size: 12px;
        color: #64748b;
        border-radius: 6px;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 2. SISTEMA DE MEMÓRIA
# ==============================================================================
ARQUIVO_PERFIL = "meu_perfil.json"

def carregar_perfil():
    if os.path.exists(ARQUIVO_PERFIL):
        try:
            with open(ARQUIVO_PERFIL, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def salvar_perfil(dados):
    if dados.get('data_referencia') and isinstance(dados.get('data_referencia'), (datetime.date, datetime.datetime)):
        dados['data_referencia'] = str(dados['data_referencia'])
    elif dados.get('data_referencia') is None:
        dados['data_referencia'] = ""
    with open(ARQUIVO_PERFIL, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

# --- TRACKER ---
def registrar_evento_analytics(projeto, setor, nome_edital, resultado, feedback_score):
    if not TEM_GSPREAD or "gcp_service_account" not in st.secrets: return False
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mapa_feedback = {0: "😞", 1: "🙁", 2: "😐", 3: "🙂", 4: "🤩"}
        feedback_texto = mapa_feedback.get(feedback_score, "N/A")
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
        client = gspread.authorize(creds)
        sheet = client.open("Tracker_Edital_IA").sheet1
        sheet.append_row([timestamp, projeto, setor, nome_edital, resultado, feedback_texto])
        st.toast(f"✅ Feedback Recebido!", icon="📊")
        return True
    except: return False

# --- PDF ---
def limpar_texto_pdf(texto):
    if not texto: return ""
    if isinstance(texto, list): texto = "\n".join([f"- {str(item)}" for item in texto])
    texto = str(texto).replace("’", "'").replace("“", '"').replace("”", '"')
    return texto.encode('latin-1', 'replace').decode('latin-1')

def gerar_relatorio_pdf(dados, user_data):
    if not TEM_PDF: return None
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, limpar_texto_pdf(f"Relatório Técnico: {user_data['projeto']['nome']}"), ln=True, align='C')
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, f"Gerado em: {datetime.date.today()}", ln=True, align='C')
    pdf.ln(5)

    raio_x = dados.get("dados_do_edital", {})
    analise = dados.get("analise_compatibilidade", {})
    elig = dados.get("elegibilidade_basica", {})
    checklist = dados.get("plano_acao_cronograma", [])
    riscos = dados.get("radar_de_riscos", [])
    guia = dados.get("guia_escrita", [])
    perguntas = dados.get("perguntas_cruciais", [])
    dicas = analise.get("dicas_estrategicas", [])

    pdf.set_font("Arial", "B", 14)
    res = analise.get('resultado', 'ANÁLISE')
    pdf.cell(0, 10, limpar_texto_pdf(f"VEREDITO: {res}"), ln=True)
    
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 6, limpar_texto_pdf(f"Parecer: {analise.get('motivo_principal', '')}"))
    pdf.ln(5)

    if riscos:
        pdf.set_text_color(139, 0, 0)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, limpar_texto_pdf("RISCOS IDENTIFICADOS"), ln=True)
        pdf.set_font("Arial", "", 10)
        for r in riscos: pdf.multi_cell(0, 5, limpar_texto_pdf(f"• {r}"))
        pdf.set_text_color(0, 0, 0); pdf.ln(5)

    if dicas:
        pdf.set_text_color(0, 0, 128)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, limpar_texto_pdf("DICAS ESTRATÉGICAS"), ln=True)
        pdf.set_font("Arial", "", 10)
        for d in dicas: pdf.multi_cell(0, 5, limpar_texto_pdf(f"• {d}"))
        pdf.set_text_color(0, 0, 0); pdf.ln(5)

    # Roteiro
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, limpar_texto_pdf("ROTEIRO DO PROJETO"), ln=True, fill=True); pdf.ln(2)
    for passo in guia:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, limpar_texto_pdf(f"• {passo.get('secao')}"), ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 5, limpar_texto_pdf(f"  {passo.get('analise_do_edital')}"))
        pdf.ln(2)

    return pdf.output(dest="S").encode("latin-1", "replace")

# ==============================================================================
# 3. MOTOR DE IA
# ==============================================================================
def chamar_ia_blindada(model, prompt):
    try:
        return model.generate_content(prompt, safety_settings=[
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ])
    except Exception as e:
        return None

def limpar_json_cirurgico(texto_sujo):
    if not texto_sujo: return {"erro": "Sem resposta da IA."}
    try:
        texto_limpo = texto_sujo.replace("```json", "").replace("```", "").strip()
        inicio = texto_limpo.find("{")
        fim = texto_limpo.rfind("}")
        if inicio != -1 and fim != -1:
            return json.loads(texto_limpo[inicio : fim + 1])
        else: return {"erro": "JSON inválido."}
    except Exception as e: return {"erro": f"Erro de Formatação: {str(e)}"}

@st.cache_data 
def ler_multiplos_pdfs(files):
    text = ""; pages = 0
    for f in files:
        try:
            pdf = PdfReader(f); pages += len(pdf.pages)
            for p in pdf.pages:
                t = p.extract_text()
                if t: text += t + "\n"
        except: pass
    return text, pages

# --- ANALISADOR DETALHADO ---
def analisar_doc(texto_edital, texto_empresa, perfil, api_key):
    if not api_key: return {"erro": "Insira a API Key na barra lateral!"}
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("models/gemini-2.5-flash", generation_config={"response_mime_type": "application/json"})
        
        hoje_str = datetime.date.today().strftime("%d/%m/%Y")
        
        prompt = f"""
        ATUE COMO: Consultor Sênior em Captação de Recursos (Inovação).
        HOJE É DIA: {hoje_str}.
        
        TAREFA:
        1. PRAZOS: Verifique se está ABERTO/ENCERRADO.
        2. CRONOGRAMA MACRO: Extraia datas de início, fim e resultados.
        3. FINANCEIRO: Extraia tipo de recurso, valor máximo e rubricas (O que paga).
        4. DOCUMENTAÇÃO (CRUCIAL): Separe PF e PJ.
        5. PERGUNTAS DE OURO: 10 critérios de eliminação.
        6. ROTEIRO DE ESCRITA: Com referências ("Item X.Y").
        7. DICAS ESTRATÉGICAS: 3 sugestões para aumentar a nota neste edital.
        8. CRUZAMENTO: Valide PF/PJ e TRL com os documentos da empresa.

        CONTEXTO:
        PERFIL: {json.dumps(perfil, indent=2, ensure_ascii=False)}
        DOCS EMPRESA: {texto_empresa[:20000]}
        EDITAL: {texto_edital[:700000]}
        
        SAÍDA JSON:
        {{
            "elegibilidade_basica": {{
                "data_limite_inscricao": "DD/MM/AAAA",
                "status_prazo": "ABERTO" ou "ENCERRADO",
                "publico_alvo": "Texto...",
                "exige_cnpj": true/false,
                "motivo_inelegibilidade": "Texto se houver"
            }},
            "analise_fomento": {{
                "tipo_recurso": "Subvenção/Reembolsável",
                "valor_maximo_projeto": "R$ Teto",
                "contrapartida_exigida": "Texto",
                "itens_financiáveis_detalhado": ["Item 1", "Item 2"],
                "itens_proibidos_resumo": ["Proibido A"]
            }},
            "dados_do_edital": {{
                "objetivo_resumido": "Texto...",
                "cronograma_macro": {{
                    "inicio_inscricoes": "Data",
                    "fim_inscricoes": "Data",
                    "resultado_preliminar": "Data",
                    "resultado_final": "Data"
                }}
            }},
            "documentacao_exigida": {{
                "pf_inscricao": ["Doc A", "Doc B"],
                "pf_se_aprovado": ["Abrir CNPJ", "Contrato Social"],
                "pj_ja_constituida": ["CNPJ", "CNDs"]
            }},
            "plano_acao_cronograma": [{{"data": "DD/MM", "tarefa": "Ação...", "status": "Pendente"}}],
            "perguntas_cruciais": ["1. Pergunta...", "2. ...", "3. ...", "4. ...", "5. ...", "6. ...", "7. ...", "8. ...", "9. ...", "10. ..."],
            "analise_compatibilidade": {{
                "resultado": "ALTA ADERÊNCIA" ou "MÉDIA" ou "INELEGÍVEL",
                "motivo_principal": "Texto...",
                "dicas_estrategicas": ["Dica 1", "Dica 2", "Dica 3"],
                "alerta_cnae": "Alerta ou N/A",
                "match_trl_status": "COMPATÍVEL/INCOMPATÍVEL",
                "match_trl_explicacao": "Explicação..."
            }},
            "radar_de_riscos": ["Risco 1", "Risco 2"],
            "guia_escrita": [
                {{
                    "secao": "Problema",
                    "analise_do_edital": "Instrução...",
                    "exemplo_aplicado": "Exemplo...",
                    "citacao_edital": "Item X.Y"
                }},
                {{
                    "secao": "Metodologia",
                    "analise_do_edital": "Instrução...",
                    "exemplo_aplicado": "Exemplo...",
                    "citacao_edital": "Item W.Z"
                }},
                 {{
                    "secao": "Orçamento",
                    "analise_do_edital": "Instrução...",
                    "exemplo_aplicado": "N/A",
                    "citacao_edital": "Item A.B"
                }}
            ]
        }}
        """
        res = chamar_ia_blindada(model, prompt)
        if not res: return {"erro": "Erro de conexão API."}
        return limpar_json_cirurgico(res.text)
    except Exception as e:
        return {"erro": f"Erro crítico: {str(e)}"}

# ==============================================================================
# 4. FRONT-END
# ==============================================================================
perfil = carregar_perfil()

# --- SIDEBAR: CONTROLE GERAL ---
st.sidebar.title("Edital.IA")
st.sidebar.caption("Sua API Key e o Edital ficam aqui.")

try:
    if "GOOGLE_API_KEY" in st.secrets: api_key = st.secrets["GOOGLE_API_KEY"]
    else: api_key = st.sidebar.text_input("API Key", value=perfil.get('api_key', ''), type="password")
except: api_key = st.sidebar.text_input("API Key", value=perfil.get('api_key', ''), type="password")

st.sidebar.markdown("---")
st.sidebar.subheader("O EDITAL (Regras)")
uploaded_files = st.sidebar.file_uploader("Suba o PDF do Edital", accept_multiple_files=True)

# --- ÁREA PRINCIPAL ---
st.title("Painel de Captação")

# --- GUIA RÁPIDO (Minimalista) ---
with st.expander("COMO USAR", expanded=False):
    st.markdown("""
    1. **Preencha seus dados na Aba 1:** A IA precisa saber quem você é.
    2. **(Opcional) Suba documentos na Aba 1:** Pitch ou Plano de Negócios ajudam muito.
    3. **Suba o Edital na Esquerda:** O arquivo com as regras.
    4. **Vá na Aba 2 (Raio-X):** Clique em 'Analisar' para ver o veredito.
    5. **Siga as Abas 3, 4 e 5:** Para validar e escrever o projeto.
    """)

# --- ABAS ---
tab_perfil, tab_analise, tab_questions, tab_crono, tab_gps = st.tabs(["Meu Projeto", "Raio-X & Match", "Checklist (10 Itens)", "Timeline", "Roteiro (GPS)"])

# --- ABA 1: MEU PROJETO ---
with tab_perfil:
    st.markdown("""
    <div class="instruction-box">
        <strong>INSTRUÇÕES DE PREENCHIMENTO:</strong><br>
        1. <strong>Pitch:</strong> Descreva o problema e a solução. A IA cruza isso com o "Objeto do Edital".<br>
        2. <strong>Pessoa Física:</strong> Se selecionar esta opção, o faturamento será zerado automaticamente.<br>
        3. <strong>Documentos da Empresa:</strong> Suba seu Pitch Deck ou CNPJ abaixo para uma análise mais profunda.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("##### Seus Documentos (Opcional)")
    arquivos_empresa = st.file_uploader("Arraste seu Pitch, CNPJ ou Plano de Negócios (PDF)", accept_multiple_files=True, key="upload_empresa")
    if arquivos_empresa: st.success(f"✅ {len(arquivos_empresa)} documento(s) carregado(s).")

    st.markdown("---")
    st.markdown("##### Defina seu Perfil")
    
    btn_save = False
    with st.form("form_cadastro_full"):
        col_a, col_b = st.columns(2)
        with col_a:
            nome_projeto = st.text_input("Nome do Projeto", value=perfil.get('nome_projeto', 'Minha Startup'))
            tipo_perfil = st.radio("Entidade Jurídica", ["Pessoa Física (CPF)", "Empresa (CNPJ)"], index=1 if perfil.get('tipo_entidade') == "Empresa (CNPJ)" else 0)
            setor = st.selectbox("Setor Principal", ["Bioeconomia", "Agritech", "Healthtech", "Edtech", "SaaS/TI", "Indústria", "Outros"], index=0)
            modelo = st.selectbox("Modelo de Negócio", ["B2B", "B2C", "SaaS", "Hardware", "Serviços", "Marketplace"], index=0)
        with col_b:
            trl_num = st.slider("TRL (Maturidade 1-9)", 1, 9, value=perfil.get('trl', 1), help="1=Ideia, 9=Escala")
            equipe = st.number_input("Tamanho da Equipe", min_value=1, value=int(perfil.get('tamanho_equipe', 1)))
            ip = st.selectbox("Propriedade Intelectual", ["Sem IP", "Patente Depositada", "Patente Concedida", "Software Registrado"], index=0)
            if tipo_perfil == "Pessoa Física (CPF)":
                faturamento = "Zero/Pré-operacional"
                st.caption("ℹ️ Pessoa Física: Faturamento definido como Zero.")
            else:
                faturamento = st.selectbox("Faturamento Anual", ["Zero/Pré-operacional", "Até R$ 360k", "Até R$ 4.8M", "+ R$ 4.8M"], index=0)

        pitch = st.text_area("Pitch (Obrigatório)", value=perfil.get('resumo_projeto', ''), height=120, help="Descreva o problema, solução e tecnologia.")
        c3, c4 = st.columns(2)
        with c3: mulher = st.checkbox("Liderança Feminina?", value=perfil.get('mulher', False))
        with c4: doutor = st.checkbox("Possui Doutores?", value=perfil.get('doutor', False))
        
        st.markdown("---")
        st.markdown("""<div class="legal-box"><strong>AVISO DE RESPONSABILIDADE (BETA)</strong><br>O Edital.IA é uma ferramenta de apoio. A responsabilidade pelo envio, prazos e conteúdo é do proponente.</div>""", unsafe_allow_html=True)
        aceite_termos = st.checkbox("Declaro que li e concordo com o aviso acima.")
        btn_save = st.form_submit_button("Salvar Perfil")
    
    if btn_save:
        if not aceite_termos: st.error("Você precisa aceitar os termos de responsabilidade para continuar.")
        else:
            d = {"api_key": api_key, "nome_projeto": nome_projeto, "resumo_projeto": pitch, "tipo_entidade": tipo_perfil, "trl": trl_num, "tamanho_equipe": equipe, "setor": setor, "modelo_negocio": modelo, "propriedade_intelectual": ip, "mulher": mulher, "doutor": doutor, "tecnico": {"trl": trl_num}, "faixa_faturamento": faturamento}
            salvar_perfil(d)
            st.success("Perfil Salvo com Sucesso.")

# --- ABA 2: ANÁLISE ---
with tab_analise:
    st.markdown("### Raio-X & Deep Match")
    if 'resultado' not in st.session_state: st.session_state['resultado'] = None

    if st.session_state['resultado']:
        if st.button("Nova Análise"): st.session_state['resultado'] = None; st.rerun()
    
    if uploaded_files and api_key and st.session_state['resultado'] is None:
        if st.button("Iniciar Análise Cruzada"):
            if len(pitch) < 5: st.error("Volte na aba 'Meu Projeto' e preencha o Pitch!")
            else:
                with st.spinner("Processando edital e documentos..."):
                    texto_edital, pags = ler_multiplos_pdfs(uploaded_files)
                    texto_empresa_extra = ""
                    if arquivos_empresa:
                        texto_empresa_extra, p_emp = ler_multiplos_pdfs(arquivos_empresa)
                    user_data = {"projeto": {"nome": nome_projeto, "resumo": pitch, "setor": setor}, "tecnico": {"trl": trl_num, "equipe": equipe, "ip": ip}, "juridico": {"tipo": tipo_perfil, "faturamento": faturamento}, "bonus": {"mulher": mulher, "doutor": doutor}}
                    analise = analisar_doc(texto_edital, texto_empresa_extra, user_data, api_key)
                    if "erro" in analise: st.error(f"Erro: {analise['erro']}")
                    else:
                        st.session_state['resultado'] = analise
                        st.session_state['user_data'] = user_data
                        st.rerun()

    if st.session_state['resultado']:
        dados = st.session_state['resultado']
        comp = dados.get('analise_compatibilidade', {})
        elig = dados.get('elegibilidade_basica', {})
        fin = dados.get('analise_fomento', {})
        riscos = dados.get('radar_de_riscos', [])
        raio_x = dados.get('dados_do_edital', {})
        docs = dados.get('documentacao_exigida', {})
        dicas = comp.get('dicas_estrategicas', [])

        # Tags de Status
        cols_tags = st.columns([1, 1, 3])
        with cols_tags[0]:
            if elig.get('status_prazo') == "ENCERRADO": st.markdown('<div class="status-tag-closed">ENCERRADO</div>', unsafe_allow_html=True)
            else: st.markdown('<div class="status-tag-open">ABERTO</div>', unsafe_allow_html=True)
        with cols_tags[1]:
            res = comp.get('resultado', 'ANÁLISE')
            if "ALTA" in res.upper(): st.markdown('<div class="match-tag-high">ALTO MATCH</div>', unsafe_allow_html=True)
            else: st.markdown('<div class="match-tag-low">BAIXO MATCH</div>', unsafe_allow_html=True)
        
        st.write("")
        st.write(f"**Parecer:** {comp.get('motivo_principal')}")

        # FINANCEIRO
        st.markdown('<div class="block-header">1. DINHEIRO & RECURSOS</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="finance-box">
            <div class="finance-title">Modalidade</div>
            <div>{fin.get('tipo_recurso', 'N/A')}</div>
            <br>
            <div class="finance-title">Teto de Fomento</div>
            <div class="finance-value">{fin.get('valor_maximo_projeto', 'N/A')}</div>
            <br>
            <div class="finance-title">Contrapartida</div>
            <div>{fin.get('contrapartida_exigida', 'N/A')}</div>
            <hr style="border-top: 1px solid #eee; margin: 15px 0;">
            <div class="finance-title">Itens Financiáveis</div>
            <div>{', '.join(fin.get('itens_financiáveis_detalhado', ['Verificar Edital']))}</div>
        </div>
        """, unsafe_allow_html=True)

        if fin.get('itens_proibidos_resumo'):
            st.markdown(f"**Proibido:** {', '.join(fin.get('itens_proibidos_resumo'))}")

        # CRONOGRAMA & DOCUMENTOS
        st.markdown('<div class="block-header">2. PRAZOS & DOCUMENTOS</div>', unsafe_allow_html=True)
        c_dates, c_docs = st.columns(2)
        with c_dates:
            st.markdown("##### Datas Chave")
            crono = raio_x.get('cronograma_macro', {})
            st.write(f"**Início:** {crono.get('inicio_inscricoes', 'N/A')}")
            st.write(f"**Fim:** {crono.get('fim_inscricoes', 'N/A')}")
            st.write(f"**Resultado:** {crono.get('resultado_final', 'N/A')}")
        with c_docs:
            st.markdown("##### Documentação Exigida")
            tab_pf, tab_pj = st.tabs(["Pessoa Física", "Pessoa Jurídica"])
            with tab_pf:
                st.caption("**Para Inscrição:**")
                for d in docs.get('pf_inscricao', []): st.markdown(f"- {d}")
                st.caption("**Se Aprovado:**")
                for d in docs.get('pf_se_aprovado', []): st.markdown(f"- {d}")
            with tab_pj:
                st.caption("**Empresa Constituída:**")
                for d in docs.get('pj_ja_constituida', []): st.markdown(f"- {d}")

        # TRL & RISCOS
        st.markdown('<div class="block-header">3. ANÁLISE TÉCNICA & RISCOS</div>', unsafe_allow_html=True)
        if "INCOMPATÍVEL" in comp.get('match_trl_status', '').upper():
            st.markdown(f'<div class="risk-card">ALERTA TRL: {comp.get("match_trl_explicacao")}</div>', unsafe_allow_html=True)
        else:
            st.success(f"TRL OK: {comp.get('match_trl_explicacao')}")

        for r in riscos: st.markdown(f'<div class="risk-card">{r}</div>', unsafe_allow_html=True)

        # DICAS ESTRATÉGICAS
        if dicas:
            st.markdown('<div class="block-header">4. DICAS ESTRATÉGICAS</div>', unsafe_allow_html=True)
            for d in dicas: st.markdown(f'<div class="tip-card">{d}</div>', unsafe_allow_html=True)

        # WHATSAPP CTA
        st.markdown("---")
        st.markdown("""
        <div class="expert-box">
            <div class="expert-title">Precisa de suporte profissional?</div>
            <p style="color: #64748b; margin-bottom: 20px;">Nossa consultoria especializada pode revisar seu projeto.</p>
            <a href="https://wa.me/556294847289?text=Olá!%20Fiz%20a%20análise%20no%20Edital.IA%20e%20quero%20ajuda." target="_blank">
                <button style="background-color:#25D366; color:white; border:none; padding:12px 24px; border-radius:6px; font-weight:600; cursor:pointer; font-size: 14px;">FALAR COM ESPECIALISTA</button>
            </a>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### Baixar Relatório (PDF)")
        fb = st.feedback("faces")
        if fb is not None:
            # CORREÇÃO AQUI: Mudamos 'res_txt' para 'res'
            registrar_evento_analytics(nome_projeto, setor, "Edital", res, fb)
            if TEM_PDF:
                pdf_data = gerar_relatorio_pdf(dados, st.session_state['user_data'])
                st.download_button("BAIXAR RELATÓRIO", data=pdf_data, file_name="analise.pdf", mime="application/pdf", type="primary")

# --- ABA 3: PERGUNTAS DE OURO ---
with tab_questions:
    st.markdown("### Checklist de Eliminação")
    if st.session_state['resultado']:
        perguntas = st.session_state['resultado'].get('perguntas_cruciais', [])
        score = 0
        for i, p in enumerate(perguntas):
            st.markdown(f"""<div class="question-box"><div class="question-header">CRITÉRIO {i+1}</div>{p}</div>""", unsafe_allow_html=True)
            if st.checkbox("Atendo este requisito.", key=f"q_{i}"): score += 1
        st.divider()
        st.metric("Seu Score", f"{score}/10")
        if score == 10: st.success("EXCELENTE!")
        elif score >= 7: st.warning("Atenção: Faltam itens importantes.")
        else: st.error("Risco alto de inabilitação.")
    else: st.info("Realize a análise primeiro.")

# --- ABA 4: TIMELINE ---
with tab_crono:
    st.markdown("### Linha do Tempo")
    if st.session_state['resultado']:
        for item in st.session_state['resultado'].get('plano_acao_cronograma', []):
            st.markdown(f"""<div class="timeline-box"><div class="timeline-dot"></div><div class="timeline-date">{item.get('data')}</div><div class="timeline-content">{item.get('tarefa')}</div></div>""", unsafe_allow_html=True)
    else: st.info("Aguardando análise...")

# --- ABA 5: ROTEIRO ---
with tab_gps:
    st.markdown("### Roteiro do Projeto")
    if st.session_state['resultado']:
        for passo in st.session_state['resultado'].get('guia_escrita', []):
            alerta = passo.get('alerta_proibicao', 'Nenhum')
            html_alerta = f'<div class="guide-warning">CUIDADO: {alerta}</div>' if alerta and alerta != "Nenhum" else ""
            st.markdown(f"""
            <div class="guide-box">
                <div class="guide-title">{passo.get('secao')}</div>
                <div class="guide-suggestion">{passo.get('analise_do_edital')}</div>
                <div class="guide-source">Fonte: {passo.get('citacao_edital')}</div>
                {html_alerta}
            </div>
            """, unsafe_allow_html=True)
    else: st.info("Faça a análise na Aba 2 para gerar o Roteiro.")

