import streamlit as st
import os
import numpy as np
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import fitz  # PyMuPDF
import io
import shutil
import requests  # <--- COLOQUE ESSA LINHA AQUI NO TOPO

# Configuração de diretórios (Estrutura com subpastas por transportadora)
PASTA_PENDENTES = "Romaneios_Para_Assinar"
PASTA_ASSINADOS = "Romaneios_Assinados"

os.makedirs(PASTA_PENDENTES, exist_ok=True)
os.makedirs(PASTA_ASSINADOS, exist_ok=True)

st.set_page_config(page_title="Luft Logistics - Painel de Romaneios", layout="wide")
st.title("🚚 Painel Digital de Romaneios")

if "versão_canvas" not in st.session_state:
    st.session_state["versão_canvas"] = 0

aba_pendentes, aba_assinados = st.tabs(["📝 Romaneios Pendentes", "✅ Romaneios Assinados"])

def converter_pdf_para_imagem_continua(caminho_pdf):
    """Abre o PDF e junta as páginas em uma imagem única vertical para visualização rápida no site"""
    pdf_documento = fitz.open(caminho_pdf)
    imagens_paginas = []
    largura_maxima = 0
    altura_total = 0
    
    for pagina in pdf_documento:
        zoom = 2
        pixmap = pagina.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        img_pil = Image.open(io.BytesIO(pixmap.tobytes("png")))
        imagens_paginas.append(img_pil)
        
        if img_pil.width > largura_maxima:
            largura_maxima = img_pil.width
        altura_total += img_pil.height
        
    pdf_documento.close()
    
    imagem_comprida = Image.new("RGBA", (largura_maxima, altura_total), (255, 255, 255, 255))
    y_offset = 0
    for img in imagens_paginas:
        imagem_comprida.paste(img, (0, y_offset))
        y_offset += img.height
        
    return imagem_comprida

def aplicar_assinatura_em_pdf(caminho_pdf, img_bytes_assinatura, trans_nome):
    """MANTÉM A SUA LÓGICA: Carimba a assinatura no PDF na posição correta acima do campo Nome:"""
    doc = fitz.open(caminho_pdf)
    ultima_pagina = doc[-1]  # Pega estritamente a ÚLTIMA página
    
    # Busca a coordenada exata do texto "Nome:"
    retangulos_texto = ultima_pagina.search_for("Nome:")
    
    if retangulos_texto:
        retangulo_alvo = retangulos_texto[0]
        x0 = retangulo_alvo.x0
        y0 = retangulo_alvo.y0 - 65  # Sobe 65 pixels para ficar acima da linha preta longa
        x1 = x0 + 180                # Largura proporcional da assinatura
        y1 = retangulo_alvo.y0 - 10  # Margem para não colar em cima do texto "Nome:"
    else:
        largura_pag = ultima_pagina.rect.width
        altura_pag = ultima_pagina.rect.height
        x0, y0, x1, y1 = 40, altura_pag - 120, 220, altura_pag - 70
        
    # Insere a imagem no local exato calculado
    rect_insercao = fitz.Rect(x0, y0, x1, y1)
    ultima_pagina.insert_image(rect_insercao, stream=img_bytes_assinatura)
    
    # Prepara caminhos de salvamento na pasta de assinados
    pasta_salvamento_assinado = os.path.join(PASTA_ASSINADOS, trans_nome)
    os.makedirs(pasta_salvamento_assinado, exist_ok=True)
    
    nome_arquivo = os.path.basename(caminho_pdf)
    nome_base = nome_arquivo.split(".")[0]
    nome_saida_png = f"{nome_base}_ASSINADO.png"
    caminho_salvamento_png = os.path.join(pasta_salvamento_assinado, nome_saida_png)
    
    # Salva o PDF alterado de forma incremental e fecha o arquivo
    doc.save(caminho_pdf, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
    doc.close()
    
    # Gera o print do documento final completo com as assinaturas para o histórico do site
    imagem_final_historico = converter_pdf_para_imagem_continua(caminho_pdf)
    imagem_final_historico.convert("RGB").save(caminho_salvamento_png, "PNG")
    
    # Remove dos pendentes originais
    if os.path.exists(caminho_pdf):
        os.remove(caminho_pdf)

# ==========================================
# 📝 ABA 1: ROMANEIOS PENDENTES
# ==========================================
with aba_pendentes:
    st.subheader("Documentos aguardando assinatura do motorista")
    
    transportadoras_pendentes = []
    if os.path.exists(PASTA_PENDENTES):
        for item in os.listdir(PASTA_PENDENTES):
            caminho_subpasta = os.path.join(PASTA_PENDENTES, item)
            if os.path.isdir(caminho_subpasta) and any(f.endswith(".pdf") for f in os.listdir(caminho_subpasta)):
                transportadoras_pendentes.append(item)
                    
    if not transportadoras_pendentes:
        st.info("🎉 Nenhum romaneio pendente!")
    else:
        # 1. Filtro Principal: Seleciona a Transportadora
        trans_selecionada = st.selectbox("📌 Selecione a Transportadora:", sorted(transportadoras_pendentes), key="sb_trans_pendentes")
        
        pasta_trans_escolhida = os.path.join(PASTA_PENDENTES, trans_selecionada)
        arquivos_da_trans = sorted([f for f in os.listdir(pasta_trans_escolhida) if f.endswith(".pdf")])
        
        # Mostra todos os romaneios pendentes encontrados para ela
        st.markdown(f"### 📋 Romaneios para a transportadora: **{trans_selecionada}** ({len(arquivos_da_trans)} encontrados)")
        
        # 2. Filtro Secundário: Escolher um específico ou deixar em Lote (Todos)
        opcoes_filtro = ["-- MOSTRAR TODOS OS ROMANEIOS (Assinar em Lote) --"] + arquivos_da_trans
        arquivo_selecionado = st.selectbox("📄 Buscar/Filtrar um Romaneio Específico (Opcional):", opcoes_filtro, key="sb_arquivos_pendentes")
        
        st.markdown("---")
        
        # Gerencia o modo de visualização na tela
        if arquivo_selecionado == "-- MOSTRAR TODOS OS ROMANEIOS (Assinar em Lote) --":
            st.info(f"💡 Modo de assinatura em Lote ativado. Os {len(arquivos_da_trans)} romaneios listados abaixo serão assinados juntos.")
            
            # MUDANÇA AQUI: Loop para renderizar TODOS os PDFs na tela um embaixo do outro
            with st.spinner("Carregando visualização de todos os romaneios pendentes..."):
                for idx, arquivo_pdf in enumerate(arquivos_da_trans):
                    st.markdown(f"##### 📄 {idx + 1}º Romaneio: `{arquivo_pdf}`")
                    caminho_completo = os.path.join(pasta_trans_escolhida, arquivo_pdf)
                    imagem_original = converter_pdf_para_imagem_continua(caminho_completo)
                    st.image(imagem_original, use_container_width=True)
                    st.markdown("<br>", unsafe_allow_html=True)  # Dá um espaço entre as imagens
            modo_lote = True
        else:
            # Mostra apenas o PDF selecionado no filtro
            with st.spinner("Carregando visualização do Romaneio..."):
                caminho_pendente = os.path.join(pasta_trans_escolhida, arquivo_selecionado)
                imagem_original = converter_pdf_para_imagem_continua(caminho_pendente)
            st.image(imagem_original, caption=f"Visualizando Romaneio: {arquivo_selecionado}", use_container_width=True)
            modo_lote = False
        
        st.markdown("---")
        st.write("✍️ **ASSINE ABAIXO (Use o dedo ou mouse dentro do quadro branco):**")
        
        chave_canvas = f"canvas_smart_final_{st.session_state['versão_canvas']}"
        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 0)", 
            stroke_width=4,
            stroke_color="black",
            background_color="#ffffff",
            height=150,
            width=500,
            drawing_mode="freedraw",
            key=chave_canvas,
        )
        
        # Botões de ação baseados no filtro selecionado
        col1, col2 = st.columns(2)
        
        with col1:
            if not modo_lote:
                # Botão para assinar apenas 1 único romaneio focado
                if st.button("💾 Enviar Romaneio Assinado (Apenas Este)", use_container_width=True):
                    if canvas_result.image_data is not None and np.any(canvas_result.image_data[:, :, 3] > 0):
                        with st.spinner("🎯 Processando assinatura..."):
                            try:
                                img_traco_bruto = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                                bbox_assinatura = img_traco_bruto.getbbox()
                                
                                if bbox_assinatura:
                                    img_assinatura_cortada = img_traco_bruto.crop(bbox_assinatura)
                                    img_byte_arr = io.BytesIO()
                                    img_assinatura_cortada.save(img_byte_arr, format='PNG')
                                    img_bytes = img_byte_arr.getvalue()
                                    
                                    aplicar_assinatura_em_pdf(caminho_pendente, img_bytes, trans_selecionada)
                                    
                                    st.session_state["versão_canvas"] += 1
                                    st.balloons()
                                    st.success("🎉 Romaneio individual assinado e movido com sucesso!")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro operacional: {e}")
                    else:
                        st.warning("⚠️ Por favor, faça a assinatura antes de enviar.")
            else:
                st.write("") # Deixa o espaço em branco se estiver no modo Lote

        with col2:
            # Botão para assinar TODOS os arquivos da pasta da transportadora de uma vez
            texto_botao_lote = f"🔥 Assinar TODOS os {len(arquivos_da_trans)} Romaneios de uma vez"
            if st.button(texto_botao_lote, type="primary", use_container_width=True):
                if canvas_result.image_data is not None and np.any(canvas_result.image_data[:, :, 3] > 0):
                    with st.spinner(f"⚡ Carimbando assinatura em {len(arquivos_da_trans)} PDFs..."):
                        try:
                            img_traco_bruto = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                            bbox_assinatura = img_traco_bruto.getbbox()
                            
                            if bbox_assinatura:
                                img_assinatura_cortada = img_traco_bruto.crop(bbox_assinatura)
                                img_byte_arr = io.BytesIO()
                                img_assinatura_cortada.save(img_byte_arr, format='PNG')
                                img_bytes = img_byte_arr.getvalue()
                                
                                # Loop inteligente aplicando sua lógica de busca por "Nome:" em cada arquivo
                                for arquivo_pdf in arquivos_da_trans:
                                    caminho_completo_pdf = os.path.join(pasta_trans_escolhida, arquivo_pdf)
                                    aplicar_assinatura_em_pdf(caminho_completo_pdf, img_bytes, trans_selecionada)
                                
                                st.session_state["versão_canvas"] += 1
                                st.balloons()
                                st.success(f"🚀 Todos os {len(arquivos_da_trans)} romaneios foram processados e assinados de uma só vez!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro no processamento em lote: {e}")
                else:
                    st.warning("⚠️ Por favor, faça a assinatura antes de enviar em lote.")

# ==========================================
# ✅ ABA 2: HISTÓRICO SEGURO
# ==========================================
with aba_assinados:
    st.subheader("Histórico geral de documentos assinados no servidor")
    
    transportadoras_assinadas = []
    if os.path.exists(PASTA_ASSINADOS):
        for item in os.listdir(PASTA_ASSINADOS):
            caminho_subpasta = os.path.join(PASTA_ASSINADOS, item)
            if os.path.isdir(caminho_subpasta) and any(f.endswith((".png", ".jpg", ".jpeg")) for f in os.listdir(caminho_subpasta)):
                transportadoras_assinadas.append(item)
                    
    if not transportadoras_assinadas:
        st.info("📂 Nenhum documento assinado armazenado no servidor no momento.")
    else:
        trans_assinada_sel = st.selectbox("📌 Filtrar Histórico por Transportadora:", sorted(transportadoras_assinadas), key="sb_trans_assinados")
        
        pasta_ass_escolhida = os.path.join(PASTA_ASSINADOS, trans_assinada_sel)
        arquivos_assinados = sorted([f for f in os.listdir(pasta_ass_escolhida) if f.endswith((".png", ".jpg", ".jpeg"))])
        
        arquivo_ver = st.selectbox("📄 Selecione o romaneio assinado para visualizar:", arquivos_assinados, key="sb_arquivos_assinados")
        caminho_assinado_ver = os.path.join(pasta_ass_escolhida, arquivo_ver)
                            
        st.markdown("---")
        st.image(caminho_assinado_ver, use_container_width=True)

# ==========================================
# 🛠️ PAINEL DE LIMPEZA SEGURO (CORRIGIDO)
# ==========================================
st.markdown("---")
with st.expander("⚙️ Painel Avançado de Limpeza do Sistema (Zerar Tudo)"):
    st.warning("⚠️ Esta ação apagará permanentemente todos os arquivos das pastas temporárias do servidor do site!")
    
    if st.button("🔥 EXCLUIR TODOS OS ARQUIVOS E ZERAR SITE"):
        with st.spinner("Apagando arquivos e limpando o histórico do zero..."):
            if os.path.exists(PASTA_PENDENTES):
                for transportadora in os.listdir(PASTA_PENDENTES):
                    caminho_sub = os.path.join(PASTA_PENDENTES, transportadora)
                    if os.path.isdir(caminho_sub):
                        for arquivo in os.listdir(caminho_sub):
                            try: os.remove(os.path.join(caminho_sub, arquivo))
                            except: pass
                        try: shutil.rmtree(caminho_sub)
                        except: pass
                try: shutil.rmtree(PASTA_PENDENTES)
                except: pass
            os.makedirs(PASTA_PENDENTES, exist_ok=True)
            
            if os.path.exists(PASTA_ASSINADOS):
                for transportadora in os.listdir(PASTA_ASSINADOS):
                    caminho_sub = os.path.join(PASTA_ASSINADOS, transportadora)
                    if os.path.isdir(caminho_sub):
                        for arquivo in os.listdir(caminho_sub):
                            try: os.remove(os.path.join(caminho_sub, arquivo))
                            except: pass
                        try: shutil.rmtree(caminho_sub)
                        except: pass
                try: shutil.rmtree(PASTA_ASSINADOS)
                except: pass
            os.makedirs(PASTA_ASSINADOS, exist_ok=True)
                
            st.cache_data.clear()
            st.cache_resource.clear()
            
            if "versão_canvas" in st.session_state:
                st.session_state["versão_canvas"] += 1
                
            st.success("🧹 Sucesso total! Tudo foi deletado e o servidor do site está zerado.")
            st.rerun()
