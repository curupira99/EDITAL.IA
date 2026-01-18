"""
NOME DO PROJETO: Edital.IA (Versão 19.1 - Engine 2.5 Flash)
VERSÃO: MVP 19.1 (Atualização de Modelo para Gemini 2.5 + Relatório Completo)
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

st.markdown("""
    <style>
    /* Cards Gerais */
    .tip-card { background-color: #fff3cd; border-left: 5px solid #ffc107; padding: 10px; margin-bottom: 5px; font-size: 14px; }
    .doc-card { background-color: #e2e3e5; border-radius: 5px; padding: 8px; margin-bottom: 5px; border-left: 5px solid #6c757d; font-size: 14px; }
    .date-card { background-color: #cfe2ff; color: #084298; padding: 8px; border-radius: 5px; margin-bottom: 5px; border: 1px solid #b6d4fe; font-weight: bold; }
    
    /* Status */
    .status-aprovado { background-color: #d1e7dd; color: #0f5132; padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 18px; border: 1px solid #c3e6cb; }
    .status-reprovado { background-color: #f8d7da; color: #842029; padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 18px; border: 1px solid #f5c6cb; }
    
    /* Ênfase em Proibidos */
    .forbidden-box { 
        background-color: #ffe6e6; 
        border: 2px solid #ff0000; 
        border-radius: 8px; 
        padding: 15px; 
        color: #cc0000;
        margin-bottom: 15px;
    }
    .forbidden-title { font-weight: bold; font-size: 16px; margin-bottom: 10px; display: flex; align-items: center; }
    
    /* Perguntas */
    .question-box { background-color: #ffffff; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
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

# --- PDF HELPERS ---
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

    # 2. VEREDITO PRINCIPAL
    pdf.set_font("Arial", "B", 14)
    res = analise.get('resultado', 'ANÁLISE')
    if "APROVADO" in res.upper(): pdf.set_text_color(0, 128, 0)
    else: pdf.set_text_color(200, 0, 0)
    pdf.cell(0, 10, f"RESULTADO: {res}", ln=True)
    pdf.set_text_color(0, 0, 0) # Reset cor
    
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 6, limpar_texto_pdf(f"Motivo Principal: {analise.get('motivo_principal', '')}"))
    pdf.ln(5)

    # 3. FICHA TÉCNICA (RAIO-X)
    pdf.set_font("Arial", "B", 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 8, "1. FICHA TÉCNICA DO EDITAL", ln=True, fill=True)
    pdf.ln(2)

    # Objetivo e Valores
    pdf.set_font("Arial", "B", 10); pdf.cell(0, 5, "Objetivo:", ln=True)
    pdf.set_font("Arial", "", 10); pdf.multi_cell(0, 5, limpar_texto_pdf(raio_x.get('objetivo_resumido', 'N/A')))
    pdf.ln(2)
    pdf.set_font("Arial", "B", 10); pdf.cell(0, 5, "Valores:", ln=True)
    pdf.set_font("Arial", "", 10); pdf.multi_cell(0, 5, limpar_texto_pdf(str(raio_x.get('valores_projeto', 'N/A'))))
    pdf.ln(3)

    # Cronograma
    pdf.set_font("Arial", "B", 10); pdf.cell(0, 5, "Cronograma:", ln=True)
    pdf.set_font("Arial", "", 10)
    datas = raio_x.get('cronograma_chaves', [])
    if isinstance(datas, list):
        for d in datas: pdf.cell(0, 5, limpar_texto_pdf(f"- {d}"), ln=True)
    pdf.ln(3)

    # Documentos
    pdf.set_font("Arial", "B", 10); pdf.cell(0, 5, "Documentação Exigida:", ln=True)
    pdf.set_font("Arial", "", 10)
    docs = raio_x.get('lista_documentacao', [])
    if isinstance(docs, list):
        for d in docs: pdf.multi_cell(0, 5, limpar_texto_pdf(f"- {d}"))
    pdf.ln(5)

    # 4. ANÁLISE FINANCEIRA (PODE vs NÃO PODE)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "2. ITENS FINANCIÁVEIS E VEDADOS", ln=True, fill=True)
    pdf.ln(2)

    # Proibidos (Vermelho)
    pdf.set_text_color(180, 0, 0)
    pdf.set_font("Arial", "B", 10); pdf.cell(0, 5, "NÃO PODE (VEDAÇÕES):", ln=True)
    pdf.set_font("Arial", "", 10)
    for p in raio_x.get('itens_proibidos', []):
        pdf.multi_cell(0, 5, limpar_texto_pdf(f"X {p}"))
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    # Permitidos (Verde escuro)
    pdf.set_text_color(0, 100, 0)
    pdf.set_font("Arial", "B", 10); pdf.cell(0, 5, "PODE (FINANCIÁVEL):", ln=True)
    pdf.set_font("Arial", "", 10)
    for p in raio_x.get('itens_financiaveis', []):
        pdf.multi_cell(0, 5, limpar_texto_pdf(f"+ {p}"))
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)

    # 5. DICAS ESTRATÉGICAS
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "3. DICAS ESTRATÉGICAS", ln=True, fill=True)
    pdf.ln(2)
    pdf.set_font("Arial", "", 10)
    for d in analise.get('dicas_estrategicas', []):
        pdf.multi_cell(0, 5, limpar_texto_pdf(f"-> {d}"))
        pdf.ln(1)
    pdf.ln(5)

    # 6. PERGUNTAS CRUCIAIS
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "4. QUESTIONÁRIO DE OURO", ln=True, fill=True)
    pdf.ln(2)
    pdf.set_font("Arial", "", 10)
    for q in dados.get('perguntas_cruciais', []):
        pdf.multi_cell(0, 6, limpar_texto_pdf(f"[ ] {q}"))
        pdf.ln(1)

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

def limpar_json_cirurgico(texto_sujo):
    try:
        if not texto_sujo: return None
        padrao = r"\{.*\}"
        match = re.search(padrao, texto_sujo.replace("\n", " "), re.DOTALL)
        if match: return json.loads(match.group())
        clean = texto_sujo.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except:
        return {"erro": "Erro JSON"}

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

# --- FUNÇÃO 1: ANÁLISE COMPLETA + PERGUNTAS ---
def analisar_doc(texto_full, perfil, api_key):
    genai.configure(api_key=api_key)
    # ATUALIZAÇÃO DO MODELO AQUI
    model = genai.GenerativeModel("models/gemini-2.5-flash")
    
    prompt = f"""
    ATUE COMO: Auditor Sênior de Editais.
    PERFIL: {json.dumps(perfil, indent=2, ensure_ascii=False)}
    EDITAL: {texto_full[:700000]}
    
    MISSÃO:
    1. RAIO-X: Extraia dados puros. Dê atenção extrema ao que é PROIBIDO (Itens vedados).
    2. 10 PERGUNTAS CRUCIAIS: Crie 10 perguntas muito específicas que o proponente deve responder "Sim" para ter chance. Use valores e regras do edital.
    3. ANÁLISE: Compatibilidade com o perfil.
    
    SAÍDA JSON OBRIGATÓRIA:
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
        "perguntas_cruciais": [
            "1. (Jurídico) ...", "2. (Financeiro) ...", "3. ...", "4. ...", "5. ...", "6. ...", "7. ...", "8. ...", "9. ...", "10. ..."
        ],
        "analise_compatibilidade": {{
            "resultado": "APROVADO" ou "REPROVADO",
            "motivo_principal": "Explicação.",
            "dicas_estrategicas": ["Dica 1", "Dica 2"]
        }}
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
api_key = st.sidebar.text_input("🔑 API Key", value=perfil.get('api_key', ''), type="password")

st.sidebar.header("1. Solicitante")
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
        natureza = st.selectbox("Natureza", ["MEI", "LTDA", "S.A.", "Outros"], index=0)
        d_padrao = datetime.date.today()
        if perfil.get('data_referencia'):
            try: d_padrao = datetime.datetime.strptime(perfil.get('data_referencia'), '%Y-%m-%d').date()
            except: pass
        data_ref = st.date_input("Abertura CNPJ", value=d_padrao)
    else:
        st.caption("Modo PF Ativado")
    
    st.markdown("---")
    st.header("2. Projeto")
    nome_projeto = st.text_input("Nome", value=perfil.get('nome_projeto', 'Minha Startup'))
    resumo_projeto = st.text_area("Pitch", value=perfil.get('resumo_projeto', ''), height=100)
    setor = st.selectbox("Setor", ["Agritech", "Saúde", "Educação", "Logística", "Varejo", "TI/SaaS", "Bioeconomia", "Outros"], index=6)
    tags_sel = st.multiselect("Tags:", ["IA", "IoT", "Biotech", "SaaS", "Energia", "Hardware"], default=[t for t in perfil.get('tags', []) if t in ["IA", "IoT", "Biotech", "SaaS", "Energia", "Hardware"]])
    
    trl_num = st.slider("TRL:", 1, 9, value=perfil.get('trl', 1))
    equipe = st.number_input("Equipe", min_value=1, value=int(perfil.get('tamanho_equipe', 1)))
    cidade = st.text_input("Cidade", value=perfil.get('localizacao', 'Tucuruí - PA'))

    st.header("3. Histórico")
    ja_recebeu = st.checkbox("Já recebi fomento?", value=perfil.get('ja_recebeu', False))
    detalhe_fomento = st.text_input("Qual?", value=perfil.get('detalhe_fomento', ''))
    c1, c2 = st.columns(2)
    with c1: mulher = st.checkbox("Lid. Fem.", value=perfil.get('mulher', False))
    with c2: doutor = st.checkbox("Doutores", value=perfil.get('doutor', False))

    btn_salvar = st.form_submit_button("💾 Salvar")

if btn_salvar:
    dados_salvar = {
        "api_key": api_key, "nome_projeto": nome_projeto, "resumo_projeto": resumo_projeto,
        "tipo_entidade": tipo_perfil, "natureza_juridica": natureza, "faixa_faturamento": faixa_fat,
        "localizacao": cidade, "tamanho_equipe": equipe, "setor": setor, "tags": tags_sel, "trl": trl_num,
        "ja_recebeu": ja_recebeu, "detalhe_fomento": detalhe_fomento, "mulher": mulher, "doutor": doutor
    }
    if data_ref: dados_salvar["data_referencia"] = str(data_ref)
    salvar_perfil(dados_salvar)
    st.success("Salvo!")

# ==============================================================================
# 5. ÁREA PRINCIPAL
# ==============================================================================
st.title(f"Painel: {nome_projeto}")

tab_ia, tab_questions = st.tabs(["📊 Raio-X & Análise", "❓ 10 Perguntas Cruciais"])

# --- ABA 1: RAIO-X COMPLETO ---
with tab_ia:
    files = st.file_uploader("Editais (PDF)", accept_multiple_files=True)
    if 'resultado_analise' not in st.session_state: st.session_state['resultado_analise'] = None

    if st.session_state['resultado_analise']:
        if st.button("🔄 Nova Análise"):
            st.session_state['resultado_analise'] = None
            st.rerun()

    if files and api_key:
        if st.session_state['resultado_analise'] is None:
            if st.button("🔍 Extrair Dados e Analisar"):
                if not resumo_projeto:
                    st.error("Preencha o Pitch!")
                else:
                    with st.spinner("Processando Edital..."):
                        texto, pags = ler_multiplos_pdfs(files)
                        
                        user_data_struct = {
                            "projeto": {"nome": nome_projeto, "resumo": resumo_projeto, "setor": setor},
                            "tecnico": {"equipe": equipe, "trl": trl_num, "tags": tags_sel},
                            "juridico": {"tipo": tipo_perfil, "natureza": natureza, "data_abertura": str(data_ref) if data_ref else "N/A", "local": cidade},
                            "financeiro": {"faixa": faixa_fat},
                            "historico": {"status": "Já recebeu" if ja_recebeu else "Não", "detalhes": detalhe_fomento},
                            "bonus": {"mulheres": mulher, "doutores": doutor}
                        }
                        
                        dados = analisar_doc(texto, user_data_struct, api_key)
                        st.session_state['dados_analise'] = dados
                        st.session_state['resultado_analise'] = "PRONTO"
                        st.session_state['user_data_cache'] = user_data_struct
                        st.rerun()

        elif st.session_state['resultado_analise'] == "PRONTO":
            dados_brutos = st.session_state['dados_analise']
            
            if "erro" in dados_brutos: st.error(dados_brutos['erro'])
            else:
                raio_x = dados_brutos.get("dados_do_edital", {})
                analise = dados_brutos.get("analise_compatibilidade", {})
                
                # --- MATCH ---
                st.subheader("⚖️ Veredito IA")
                res = analise.get('resultado', 'EM ANÁLISE')
                
                if "APROVADO" in res.upper():
                    st.markdown(f'<div class="status-aprovado">✅ {res}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="status-reprovado">🚫 {res}</div>', unsafe_allow_html=True)
                st.write("")
                st.write(f"**Motivo:** {analise.get('motivo_principal', '')}")

                st.markdown("---")

                # --- FATOS ---
                st.subheader("📂 Raio-X do Edital")
                st.info(f"🎯 **Objetivo:** {raio_x.get('objetivo_resumido', 'Não identificado')}")
                
                # ÁREA DE ÊNFASE NOS PROIBIDOS
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
                    st.metric("💰 Valor do Projeto", raio_x.get('valores_projeto', 'N/A'))

                st.markdown("---")
                
                col_docs, col_crono = st.columns(2)
                with col_docs:
                    st.markdown("##### 📄 Documentos Exigidos")
                    for d in raio_x.get('lista_documentacao', []): st.markdown(f'<div class="doc-card">📎 {d}</div>', unsafe_allow_html=True)

                with col_crono:
                    st.markdown("##### 📅 Cronograma")
                    for d in raio_x.get('cronograma_chaves', []): st.markdown(f'<div class="date-card">🗓️ {d}</div>', unsafe_allow_html=True)

                # Dicas
                st.markdown("##### 💡 Dicas Estratégicas")
                for d in analise.get('dicas_estrategicas', []): st.markdown(f'<div class="tip-card">💡 {d}</div>', unsafe_allow_html=True)
                
                if TEM_PDF:
                    # Passando o dicionário COMPLETO para o gerador de PDF
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
                
                if score_checks == 10:
                    st.success("🏆 EXCELENTE! Você cobriu todos os pontos críticos.")
                elif score_checks >= 7:
                    st.info("⚠️ Faltam alguns pontos. Verifique o que não marcou.")
                else:
                    st.error("🛑 CUIDADO! Muitos pontos cruciais estão pendentes.")
    else:
        st.info("ℹ️ Faça a análise na Aba 1 para gerar este questionário personalizado.")