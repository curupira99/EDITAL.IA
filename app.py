"""
NOME DO PROJETO: Edital.IA (Versão 19.14 - Expanded Profile)
VERSÃO: MVP 19.14 (Novas Naturezas Jurídicas + Lista Expandida de Tecnologias)
AUTOR: Lucas Almeida (Rota Fácil / Açaicat)
DATA: Janeiro/2026
DEPÊNDENCIA: python -m pip install fpdf
"""

import streamlit as st
import google.generativeai as genai
import json
import os
from PyPDF2 import PdfReader
import datetime
import time
import re
import unicodedata

# Tenta importar FPDF
try:
    from fpdf import FPDF
    TEM_PDF = True
except ImportError:
    TEM_PDF = False

# ==============================================================================
# 1. CONFIGURAÇÃO VISUAL
# ==============================================================================
st.set_page_config(page_title="Edital.IA", layout="wide", page_icon="🚀")

# --- BANNER BETA ---
st.markdown("""
<div style="background-color: #d1e7dd; color: #0f5132; padding: 12px; border-radius: 8px; border: 1px solid #badbcc; margin-bottom: 20px; text-align: center; font-family: sans-serif;">
    <strong>🚀 FASE BETA PÚBLICA:</strong> Funcionalidades Premium (Auditoria de Risco, Timeline e Deep Match) liberadas gratuitamente.
</div>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
    /* Cards Gerais */
    .tip-card { background-color: #fff3cd; color: #856404; border-left: 5px solid #ffc107; padding: 10px; margin-bottom: 5px; font-size: 14px; }
    .doc-card { background-color: #e2e3e5; color: #383d41; border-radius: 5px; padding: 8px; margin-bottom: 5px; border-left: 5px solid #6c757d; font-size: 14px; }
    .date-card { background-color: #cfe2ff; color: #084298; padding: 8px; border-radius: 5px; margin-bottom: 5px; border: 1px solid #b6d4fe; font-weight: bold; }
    .money-card { background-color: #e6f9e6; color: #155724; padding: 15px; border-radius: 8px; border: 1px solid #c3e6cb; font-weight: bold; font-size: 16px; margin-bottom: 10px; }
    .smart-doc-card { background-color: #f0f8ff; border-left: 5px solid #007bff; padding: 10px; margin-bottom: 8px; color: #004085; font-size: 14px; }
    
    /* CARD DE RISCO */
    .risk-card {
        background-color: #fff5f5;
        border-left: 5px solid #dc3545; /* Vermelho */
        padding: 12px;
        margin-bottom: 8px;
        color: #842029;
        font-size: 14px;
    }

    /* TIMELINE STYLES */
    .timeline-box { position: relative; padding-left: 30px; border-left: 3px solid #007bff; margin-bottom: 20px; }
    .timeline-dot { position: absolute; left: -9px; top: 0; width: 15px; height: 15px; border-radius: 50%; background-color: #007bff; border: 2px solid #fff; }
    .timeline-date { font-size: 14px; font-weight: bold; color: #007bff; text-transform: uppercase; margin-bottom: 5px; }
    .timeline-content { background-color: #f8f9fa; color: #212529; padding: 10px; border-radius: 5px; font-size: 15px; border: 1px solid #dee2e6; }

    /* Status */
    .status-aprovado { background-color: #d1e7dd; color: #0f5132; padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 18px; border: 1px solid #c3e6cb; }
    .status-reprovado { background-color: #f8d7da; color: #842029; padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 18px; border: 1px solid #f5c6cb; }
    .forbidden-box { background-color: #ffe6e6; border: 2px solid #ff0000; border-radius: 8px; padding: 15px; color: #cc0000; margin-bottom: 15px; }
    .forbidden-title { font-weight: bold; font-size: 16px; margin-bottom: 10px; display: flex; align-items: center; }
    .question-box { background-color: #ffffff; color: #000000; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .question-header { font-weight: bold; color: #007bff; margin-bottom: 5px; text-transform: uppercase; font-size: 12px; }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 2. SISTEMA DE MEMÓRIA
# ==============================================================================
ARQUIVO_PERFIL = "meu_perfil.json"

def carregar_perfil():
    if os.path.exists(ARQUIVO_PERFIL):
        with open(ARQUIVO_PERFIL, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_perfil(dados):
    if dados.get('data_referencia') and isinstance(dados.get('data_referencia'), (datetime.date, datetime.datetime)):
        dados['data_referencia'] = str(dados['data_referencia'])
    elif dados.get('data_referencia') is None:
        dados['data_referencia'] = ""
    with open(ARQUIVO_PERFIL, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

# --- PDF HELPERS (ANTI-CRASH) ---
def limpar_texto_pdf(texto):
    if not texto: return ""
    if isinstance(texto, list):
        texto = "\n".join([f"- {str(item)}" for item in texto])
    texto = str(texto)
    return texto.encode('latin-1', 'replace').decode('latin-1')

def gerar_relatorio_pdf(dados, user_data):
    if not TEM_PDF: return None
    pdf = FPDF()
    pdf.add_page()
    
    # 1. CABEÇALHO
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, limpar_texto_pdf(f"Relatório de Análise: {user_data['projeto']['nome']}"), ln=True, align='C')
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, f"Data da Análise: {datetime.date.today()}", ln=True, align='C')
    pdf.ln(5)

    # Organizando dados
    raio_x = dados.get("dados_do_edital", {})
    analise = dados.get("analise_compatibilidade", {})
    docs_analise = dados.get("analise_documental_extra", []) 
    checklist = dados.get("plano_acao_cronograma", [])
    riscos = dados.get("radar_de_riscos", [])

    # 2. VEREDITO PRINCIPAL
    pdf.set_font("Arial", "B", 14)
    res = analise.get('resultado', 'ANÁLISE')
    if "APROVADO" in res.upper(): pdf.set_text_color(0, 128, 0)
    else: pdf.set_text_color(200, 0, 0)
    
    pdf.cell(0, 10, limpar_texto_pdf(f"RESULTADO: {res}"), ln=True)
    pdf.set_text_color(0, 0, 0) 
    
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 6, limpar_texto_pdf(f"Motivo Principal: {analise.get('motivo_principal', '')}"))
    pdf.ln(5)

    # NOVO: RISCOS NO PDF
    if riscos:
        pdf.set_text_color(139, 0, 0)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, limpar_texto_pdf("⚠️ PONTOS DE ATENÇÃO E RISCOS"), ln=True)
        pdf.set_font("Arial", "", 10)
        for r in riscos:
            pdf.multi_cell(0, 5, limpar_texto_pdf(f"• {r}"))
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)

    # 3. FICHA TÉCNICA
    pdf.set_font("Arial", "B", 12); pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 8, limpar_texto_pdf("1. FICHA TÉCNICA"), ln=True, fill=True); pdf.ln(2)
    
    pdf.set_font("Arial", "B", 10); pdf.cell(0, 5, "Objetivo:", ln=True)
    pdf.set_font("Arial", "", 10); pdf.multi_cell(0, 5, limpar_texto_pdf(raio_x.get('objetivo_resumido', 'N/A')))
    pdf.ln(2)
    
    pdf.set_font("Arial", "B", 10); pdf.cell(0, 5, "Valores:", ln=True)
    pdf.set_font("Arial", "", 10); pdf.multi_cell(0, 5, limpar_texto_pdf(str(raio_x.get('valores_projeto', 'N/A'))))
    pdf.ln(3)

    # 4. ITENS VEDADOS
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, limpar_texto_pdf("2. ITENS VEDADOS"), ln=True, fill=True); pdf.ln(2)
    pdf.set_text_color(180, 0, 0)
    for p in raio_x.get('itens_proibidos', []):
        pdf.multi_cell(0, 5, limpar_texto_pdf(f"X {p}"))
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    # 5. DOCUMENTOS
    if docs_analise:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, limpar_texto_pdf("3. ANÁLISE DOS SEUS DOCUMENTOS"), ln=True, fill=True); pdf.ln(2)
        pdf.set_font("Arial", "", 10)
        for doc in docs_analise:
            pdf.multi_cell(0, 5, limpar_texto_pdf(f"• {doc}"))
        pdf.ln(5)

    # 6. TIMELINE
    if checklist:
        pdf.add_page()
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, limpar_texto_pdf("4. PLANO DE AÇÃO"), ln=True, fill=True); pdf.ln(2)
        pdf.set_font("Arial", "", 10)
        for item in checklist:
             pdf.cell(0, 6, limpar_texto_pdf(f"{item.get('data')}: {item.get('tarefa')}"), ln=True)

    return pdf.output(dest="S").encode("latin-1", "replace")

# ==============================================================================
# 3. MOTOR DE IA (ATUALIZADO PARA GEMINI 2.5 FLASH)
# ==============================================================================
def get_safety_settings():
    return [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

def chamar_ia_blindada(model, prompt):
    try:
        return model.generate_content(prompt, safety_settings=get_safety_settings())
    except Exception as e:
        if "429" in str(e):
            st.error("🚨 Cota excedida (Erro 429).")
            return None
        return None

# --- CORREÇÃO ROBUSTA DE JSON ---
def limpar_json_cirurgico(texto_sujo):
    if not texto_sujo: return {"erro": "Resposta vazia da IA"}
    try:
        texto_limpo = texto_sujo.replace("```json", "").replace("```", "").strip()
        inicio = texto_limpo.find("{")
        fim = texto_limpo.rfind("}")
        if inicio != -1 and fim != -1:
            texto_json = texto_limpo[inicio : fim + 1]
            return json.loads(texto_json)
        else:
            return {"erro": "Estrutura JSON não encontrada na resposta."}
    except json.JSONDecodeError:
        return {"erro": "A IA gerou um JSON inválido. Tente novamente."}
    except Exception as e:
        return {"erro": f"Erro inesperado no processamento: {str(e)}"}

@st.cache_data 
def ler_multiplos_pdfs(files):
    text = ""
    pages = 0
    for f in files:
        try:
            pdf = PdfReader(f)
            pages += len(pdf.pages)
            for p in pdf.pages:
                t = p.extract_text()
                if t: text += t + "\n"
        except: pass
    return text, pages

# --- FUNÇÃO 1: ANÁLISE CRUZADA INTELIGENTE (SMART DOC + RISK RADAR) ---
def analisar_doc(texto_edital, texto_empresa, perfil, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("models/gemini-2.5-flash")
    
    prompt = f"""
    ATUE COMO: Auditor Sênior de Riscos em Editais Públicos (Modo: "Advogado do Diabo").
    
    CONTEXTO:
    1. PERFIL: {json.dumps(perfil, indent=2, ensure_ascii=False)}
    2. DOCS EMPRESA: {texto_empresa[:200000]} 
    3. EDITAL: {texto_edital[:700000]}
    
    MISSÃO (BUSCA PESADA):
    Além do básico, procure por "PEGADINHAS" e "SHOWSTOPPERS".
    - Cláusulas de subjetividade excessiva na avaliação?
    - Exigências de certificações caras ou demoradas?
    - Prazos impossíveis entre etapas?
    - Exigência de Capital Social mínimo?
    
    SAÍDA JSON OBRIGATÓRIA (APENAS JSON):
    {{
        "dados_do_edital": {{
            "objetivo_resumido": "Texto curto.",
            "cronograma_chaves": ["Data 1", "Data 2"],
            "fases_selecao": ["Fase 1", "Fase 2"],
            "lista_documentacao": ["Doc 1", "Doc 2"],
            "itens_financiaveis": ["Pode A", "Pode B"],
            "itens_proibidos": ["Proibido A", "Proibido B", "Proibido C"],
            "valores_projeto": "R$ Min e Max"
        }},
        "plano_acao_cronograma": [
            {{"data": "DD/MM", "tarefa": "Ação prática...", "status": "Pendente"}}
        ],
        "perguntas_cruciais": [
            "1. (Jurídico) ...", "2. (Financeiro) ...", "3. ...", "4. ...", "5. ...", "6. ...", "7. ...", "8. ...", "9. ...", "10. ..."
        ],
        "analise_compatibilidade": {{
            "resultado": "APROVADO" ou "REPROVADO" ou "ATENÇÃO",
            "motivo_principal": "Resumo executivo.",
            "dicas_estrategicas": ["Dica 1", "Dica 2"],
            "alerta_cnae": "Análise CNAE ou N/A",
            "alerta_tempo": "Análise Tempo ou N/A"
        }},
        "radar_de_riscos": [
            "⚠️ RISCO DE INABILITAÇÃO: O item 5.4 exige...",
            "⚠️ CUSTO OCULTO: O edital exige...",
            "⚠️ SUBJETIVIDADE: O critério..."
        ],
        "analise_documental_extra": [
            "Análise sobre o Pitch...",
            "Análise sobre o CNPJ..."
        ]
    }}
    """
    res = chamar_ia_blindada(model, prompt)
    if not res: return {"erro": "Falha IA"}
    return limpar_json_cirurgico(res.text)

# ==============================================================================
# 4. FRONT-END
# ==============================================================================
perfil = carregar_perfil()
st.sidebar.title("🚀 Edital.IA")

try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.sidebar.text_input("🔑 API Key", value=perfil.get('api_key', ''), type="password")
except:
    api_key = st.sidebar.text_input("🔑 API Key", value=perfil.get('api_key', ''), type="password")


st.sidebar.header("1. Documentos da Empresa")
st.sidebar.caption("Suba Pitch, CNPJ ou Projetos para auditoria cruzada.")
arquivos_empresa = st.sidebar.file_uploader("📂 Seus Documentos (PDF)", accept_multiple_files=True, key="docs_empresa")

st.sidebar.markdown("---")
st.sidebar.header("2. Perfil Declarado")
tipo_perfil = st.sidebar.radio("Entidade:", ["Pessoa Física (CPF)", "Empresa (CNPJ)"], index=0 if perfil.get('tipo_entidade') == "Pessoa Física (CPF)" else 1)

with st.sidebar.form("form_cadastro"):
    natureza = "N/A"
    data_ref = None
    faixa_fat = "Não faturou"
    
    if tipo_perfil == "Empresa (CNPJ)":
        opcoes_fat = ["Até R$ 81k (MEI)", "Até R$ 360k (ME)", "Até R$ 4.8M (EPP)", "Acima de R$ 4.8M"]
        idx_fat = 0
        if perfil.get('faixa_faturamento') in opcoes_fat: idx_fat = opcoes_fat.index(perfil.get('faixa_faturamento'))
        faixa_fat = st.selectbox("Faturamento", options=opcoes_fat, index=idx_fat)
        
        # --- EXPANSÃO DE NATUREZAS JURÍDICAS ---
        opcoes_natureza = [
            "MEI", 
            "Sociedade Limitada (LTDA)", 
            "Sociedade Anônima (S.A.)", 
            "Sociedade Unipessoal (SLU)",
            "Inova Simples (I.S.)",
            "Cooperativa",
            "Associação/OSC",
            "Consórcio",
            "Outros"
        ]
        # Tenta recuperar o índice salvo, se existir na nova lista
        idx_nat = 0
        nat_salva = perfil.get('natureza_juridica', 'MEI')
        if nat_salva in opcoes_natureza:
            idx_nat = opcoes_natureza.index(nat_salva)
            
        natureza = st.selectbox("Natureza", options=opcoes_natureza, index=idx_nat)
        
        d_padrao = datetime.date.today()
        if perfil.get('data_referencia'):
            try: d_padrao = datetime.datetime.strptime(perfil.get('data_referencia'), '%Y-%m-%d').date()
            except: pass
        data_ref = st.date_input("Abertura CNPJ", value=d_padrao)
    else:
        st.caption("Modo PF Ativado")
    
    st.markdown("---")
    st.header("Projeto")
    nome_projeto = st.text_input("Nome", value=perfil.get('nome_projeto', 'Minha Startup'))
    resumo_projeto = st.text_area("Pitch (Texto)", value=perfil.get('resumo_projeto', ''), height=100)
    
    # Setores Expandidos
    opcoes_setor = ["Agritech", "Saúde/Healthtech", "Educação/Edtech", "Logística", "Varejo", "TI/SaaS", "Bioeconomia", "Fintech", "Indústria 4.0", "Social/Impacto", "Outros"]
    idx_setor = 5
    if perfil.get('setor') in opcoes_setor: idx_setor = opcoes_setor.index(perfil.get('setor'))
    setor = st.selectbox("Setor", opcoes_setor, index=idx_setor)
    
    # --- LISTA EXPANDIDA DE TECNOLOGIAS (TAGS) ---
    lista_tags = [
        "Inteligência Artificial (IA)", 
        "Machine Learning", 
        "SaaS", 
        "Marketplace", 
        "IoT (Internet das Coisas)", 
        "Blockchain", 
        "Big Data & Analytics", 
        "Realidade Virtual/Aumentada (VR/AR)", 
        "Biotech", 
        "Nanotecnologia", 
        "Robótica/Drones", 
        "Cleantech/Energia", 
        "Fintech", 
        "Healthtech", 
        "Agrotech", 
        "Edtech", 
        "Cybersecurity", 
        "Cloud Computing", 
        "API/Integrações", 
        "Mobile App", 
        "Hardware", 
        "Indústria 4.0", 
        "ESG", 
        "Social Tech"
    ]
    # Filtra tags salvas para garantir que ainda existem na lista nova
    tags_salvas = [t for t in perfil.get('tags', []) if t in lista_tags]
    tags_sel = st.multiselect("Tecnologias Envolvidas:", lista_tags, default=tags_salvas)
    
    trl_num = st.slider("TRL (Maturidade):", 1, 9, value=perfil.get('trl', 1))
    equipe = st.number_input("Equipe", min_value=1, value=int(perfil.get('tamanho_equipe', 1)))
    cidade = st.text_input("Cidade", value=perfil.get('localizacao', 'Tucuruí - PA'))
    st.header("Histórico")
    ja_recebeu = st.checkbox("Já recebi fomento?", value=perfil.get('ja_recebeu', False))
    detalhe_fomento = st.text_input("Qual?", value=perfil.get('detalhe_fomento', ''))
    c1, c2 = st.columns(2)
    with c1: mulher = st.checkbox("Lid. Fem.", value=perfil.get('mulher', False))
    with c2: doutor = st.checkbox("Doutores", value=perfil.get('doutor', False))
    btn_salvar = st.form_submit_button("💾 Salvar Perfil")

if btn_salvar:
    dados_salvar = {
        "api_key": api_key, "nome_projeto": nome_projeto, "resumo_projeto": resumo_projeto, "tipo_entidade": tipo_perfil, "natureza_juridica": natureza, "faixa_faturamento": faixa_fat, "localizacao": cidade, "tamanho_equipe": equipe, "setor": setor, "tags": tags_sel, "trl": trl_num, "ja_recebeu": ja_recebeu, "detalhe_fomento": detalhe_fomento, "mulher": mulher, "doutor": doutor
    }
    if data_ref: dados_salvar["data_referencia"] = str(data_ref)
    salvar_perfil(dados_salvar)
    st.success("Salvo!")

# ==============================================================================
# 5. ÁREA PRINCIPAL
# ==============================================================================
st.title(f"Painel: {nome_projeto}")

tab_ia, tab_questions, tab_checklist = st.tabs(["📊 Raio-X & Deep Match", "❓ 10 Perguntas Cruciais", "📍 Timeline de Ação"])

# --- ABA 1: RAIO-X COMPLETO ---
with tab_ia:
    files_edital = st.file_uploader("1. Suba o EDITAL (PDF)", accept_multiple_files=True, key="pdf_edital")
    if 'resultado_analise' not in st.session_state: st.session_state['resultado_analise'] = None

    if st.session_state['resultado_analise']:
        if st.button("🔄 Nova Análise"):
            st.session_state['resultado_analise'] = None
            st.rerun()

    if files_edital and api_key:
        if st.session_state['resultado_analise'] is None:
            if st.button("🔍 Extrair Dados e Analisar (Deep Match)"):
                tem_doc_empresa = arquivos_empresa is not None and len(arquivos_empresa) > 0
                tem_pitch_texto = len(resumo_projeto) > 10
                
                if not tem_pitch_texto and not tem_doc_empresa:
                    st.error("Por favor, preencha o Pitch (texto) OU suba um documento da empresa (PDF) na barra lateral!")
                else:
                    with st.spinner("Lendo Edital e Procurando Pegadinhas..."):
                        texto_edital, pags_edital = ler_multiplos_pdfs(files_edital)
                        texto_empresa = "Nenhum documento da empresa anexado. Usar apenas perfil declarado."
                        if tem_doc_empresa:
                            texto_empresa, pags_empresa = ler_multiplos_pdfs(arquivos_empresa)
                            st.toast(f"Lidos {pags_empresa} páginas de documentos da empresa.")
                        
                        user_data_struct = {
                            "projeto": {"nome": nome_projeto, "resumo": resumo_projeto, "setor": setor},
                            "tecnico": {"equipe": equipe, "trl": trl_num, "tags": tags_sel},
                            "juridico": {"tipo": tipo_perfil, "natureza": natureza, "data_abertura": str(data_ref) if data_ref else "N/A", "local": cidade},
                            "financeiro": {"faixa": faixa_fat},
                            "historico": {"status": "Já recebeu" if ja_recebeu else "Não", "detalhes": detalhe_fomento},
                            "bonus": {"mulheres": mulher, "doutores": doutor}
                        }
                        
                        dados = analisar_doc(texto_edital, texto_empresa, user_data_struct, api_key)
                        
                        if "erro" in dados:
                            st.error(f"Erro na análise: {dados['erro']}")
                        else:
                            st.session_state['dados_analise'] = dados
                            st.session_state['resultado_analise'] = "PRONTO"
                            st.session_state['user_data_cache'] = user_data_struct
                            st.rerun()

        elif st.session_state['resultado_analise'] == "PRONTO":
            dados_brutos = st.session_state['dados_analise']
            
            raio_x = dados_brutos.get("dados_do_edital", {})
            analise = dados_brutos.get("analise_compatibilidade", {})
            docs_extra = dados_brutos.get("analise_documental_extra", [])
            riscos = dados_brutos.get("radar_de_riscos", [])
            
            # --- MATCH ---
            st.subheader("⚖️ Veredito IA (Auditoria)")
            res = analise.get('resultado', 'EM ANÁLISE')
            if "APROVADO" in res.upper(): st.markdown(f'<div class="status-aprovado">✅ {res}</div>', unsafe_allow_html=True)
            elif "ATENÇÃO" in res.upper(): st.markdown(f'<div class="tip-card">⚠️ {res}</div>', unsafe_allow_html=True)
            else: st.markdown(f'<div class="status-reprovado">🚫 {res}</div>', unsafe_allow_html=True)
            
            st.write("")
            st.write(f"**Parecer:** {analise.get('motivo_principal', '')}")
            
            # --- NOVA SEÇÃO: RADAR DE RISCOS ---
            if riscos:
                st.markdown("---")
                st.subheader("⚠️ Radar de Riscos & Pegadinhas")
                with st.expander("Ver Riscos Detectados (Importante)", expanded=True):
                    for r in riscos:
                        st.markdown(f'<div class="risk-card">{r}</div>', unsafe_allow_html=True)

            # --- ANÁLISE DOS DOCUMENTOS ---
            if docs_extra:
                st.markdown("---")
                st.subheader("📂 Análise dos Seus Documentos (Anexos)")
                st.caption("A IA analisou individualmente o conteúdo dos arquivos que você subiu:")
                for doc_analise in docs_extra:
                    st.markdown(f'<div class="smart-doc-card">{doc_analise}</div>', unsafe_allow_html=True)
            
            # ALERTAS DEEP MATCH
            c1, c2 = st.columns(2)
            with c1:
                if analise.get('alerta_cnae') and analise.get('alerta_cnae') != "N/A":
                    st.info(f"🏢 **CNAE/Jurídico:** {analise.get('alerta_cnae')}")
            with c2:
                if analise.get('alerta_tempo') and analise.get('alerta_tempo') != "N/A":
                    st.info(f"⏳ **Tempo/Maturidade:** {analise.get('alerta_tempo')}")

            # --- BOTÃO WHATSAPP ---
            st.markdown("---")
            col_msg, col_btn = st.columns([3, 1])
            with col_msg:
                st.markdown("##### 🆘 Precisa de ajuda com a burocracia?")
                st.caption("Fale diretamente com nosso especialista para tirar dúvidas ou submeter este projeto.")
            with col_btn:
                link_wa = "https://wa.me/556294847289?text=Olá!%20Estou%20no%20Edital.IA%20e%20preciso%20de%20ajuda%20com%20um%20projeto."
                st.link_button("💬 Chamar no Zap", link_wa, use_container_width=True)
            st.markdown("---")

            # --- FATOS ---
            st.subheader("📂 Raio-X do Edital")
            st.info(f"🎯 **Objetivo:** {raio_x.get('objetivo_resumido', 'Não identificado')}")
            
            st.markdown('<div class="forbidden-box">', unsafe_allow_html=True)
            st.markdown('<div class="forbidden-title">🚫 O QUE ESTE EDITAL NÃO PAGA (ITENS VEDADOS)</div>', unsafe_allow_html=True)
            proibidos = raio_x.get('itens_proibidos', [])
            if isinstance(proibidos, list):
                for p in proibidos: st.markdown(f"• {p}")
            else: st.write(proibidos)
            st.markdown('</div>', unsafe_allow_html=True)

            col_fin, col_val = st.columns(2)
            with col_fin:
                st.success("✅ **Financiável (Exemplos):**")
                for p in raio_x.get('itens_financiaveis', []): st.write(f"• {p}")
            
            with col_val:
                st.markdown("##### 💰 Valor do Projeto")
                val_proj = raio_x.get('valores_projeto', 'N/A')
                st.markdown(f'<div class="money-card">{val_proj}</div>', unsafe_allow_html=True)

            st.markdown("---")
            
            col_docs, col_crono = st.columns(2)
            with col_docs:
                st.markdown("##### 📄 Documentos Exigidos")
                for d in raio_x.get('lista_documentacao', []): st.markdown(f'<div class="doc-card">📎 {d}</div>', unsafe_allow_html=True)

            with col_crono:
                st.markdown("##### 📅 Cronograma")
                for d in raio_x.get('cronograma_chaves', []): st.markdown(f'<div class="date-card">🗓️ {d}</div>', unsafe_allow_html=True)

            st.markdown("##### 💡 Dicas Estratégicas")
            for d in analise.get('dicas_estrategicas', []): st.markdown(f'<div class="tip-card">💡 {d}</div>', unsafe_allow_html=True)
            
            if TEM_PDF:
                pdf_bytes = gerar_relatorio_pdf(dados_brutos, st.session_state['user_data_cache'])
                st.download_button("📄 Baixar Relatório Completo", data=pdf_bytes, file_name="relatorio_completo.pdf", mime="application/pdf")

# --- ABA 2: QUESTIONÁRIO ESTRATÉGICO ---
with tab_questions:
    st.markdown("### ❓ 10 Perguntas de Ouro")
    st.caption("A IA formulou estas perguntas com base nas 'pegadinhas' e exigências deste edital. Responda mentalmente ou marque as que você já resolveu.")
    
    if st.session_state.get('resultado_analise') == "PRONTO":
        dados = st.session_state.get('dados_analise', {})
        perguntas = dados.get('perguntas_cruciais', [])
        
        if not perguntas:
            st.warning("⚠️ As perguntas não foram geradas. Tente analisar novamente.")
        else:
            with st.container():
                score_checks = 0
                for i, p in enumerate(perguntas):
                    st.markdown(f"""
                    <div class="question-box">
                        <div class="question-header">QUESTÃO CRUCIAL {i+1}</div>
                        {p}
                    </div>
                    """, unsafe_allow_html=True)
                    if st.checkbox(f"Sim, eu atendo/possuo este item.", key=f"q_{i}"):
                        score_checks += 1
                st.divider()
                st.metric("Sua Prontidão", f"{score_checks}/10")
                if score_checks == 10: st.success("🏆 EXCELENTE! Você cobriu todos os pontos críticos.")
                elif score_checks >= 7: st.info("⚠️ Faltam alguns pontos. Verifique o que não marcou.")
                else: st.error("🛑 CUIDADO! Muitos pontos cruciais estão pendentes.")
    else:
        st.info("ℹ️ Faça a análise na Aba 1 para gerar este questionário personalizado.")

# --- ABA 3: TIMELINE (LINHA DO TEMPO VISUAL) ---
with tab_checklist:
    st.markdown("### 📍 Timeline de Execução")
    st.caption("Roteiro cronológico visual das ações necessárias até a submissão.")

    if st.session_state.get('resultado_analise') == "PRONTO":
        dados = st.session_state.get('dados_analise', {})
        checklist = dados.get('plano_acao_cronograma', [])

        if not checklist:
            st.warning("⚠️ Não foi possível gerar a timeline. Tente analisar novamente.")
        else:
            for item in checklist:
                data_tarefa = item.get('data', 'S/D')
                acao_tarefa = item.get('tarefa', '')
                st.markdown(f"""
                <div class="timeline-box">
                    <div class="timeline-dot"></div>
                    <div class="timeline-date">{data_tarefa}</div>
                    <div class="timeline-content">
                        {acao_tarefa}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.info("💡 Dica: Esta timeline está inclusa no 'Relatório Completo (PDF)' na Aba 1.")
    else:
        st.info("ℹ️ Faça a análise na Aba 1 para gerar sua Linha do Tempo.")
