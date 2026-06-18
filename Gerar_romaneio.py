import streamlit as st
import os
import numpy as np
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import fitz  # PyMuPDF
import io
import shutil

# ==============================================================================
# 📂 CAMINHO DA PASTA SINCRONIZADA COM O SHAREPOINT/ONEDRIVE (LUFT SOLUTIONS)
# ==============================================================================
# Caminho exato da sua máquina configurado com as barras corretas para o Python
PASTA_DESTINO_SHAREPOINT = "C:/Users/bruno.gomes/OneDrive - luftsolutions.com.br/Romaneios/Digitalizados"

# Pasta temporária local do site para receber os PDFs originais vindos do SAP
PASTA_PENDENTES = "Romaneios_Para_Assinar"

# Garante que as pastas existam ao iniciar o sistema
os.makedirs(PASTA_PENDENTES, exist_ok=True)
os.makedirs(PASTA_DESTINO_SHAREPOINT, exist_ok=True)

st.set_page_config(page_title="Luft Logistics - Painel de Romaneios", layout="wide")
st.title("🚚 Painel Digital de Romaneios")

if "versão_canvas" not in st.session_state:
    st.session_state["versão_canvas"] = 0

aba_pendentes, aba_assinados = st.tabs(["📝 Romaneios Pendentes", "✅ Histórico Sincronizado"])

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
    """Carimba a assinatura no PDF e move o arquivo para a pasta de sincronização do OneDrive"""
    doc = fitz.open(caminho_pdf)
    ultima_pagina = doc[-1]
    
    # Busca a coordenada exata do texto "Nome:"
    retangulos_texto = ultima_pagina.search_for("Nome:")
    
    if retangulos_texto:
        retangulo_alvo = retangulos_texto[0]
        x0 = retangulo_alvo.x0
        y0 = retangulo_alvo.y0 - 65
        x1 = x0 + 180
        y1 = retangulo_alvo.y0 - 10
    else:
        largura_pag = ultima_pagina.rect.width
        altura_pag = ultima_pagina.rect.height
        x0, y0, x1, y1 = 40, altura_pag - 120, 220, altura_pag - 70
        
    # Insere a imagem da assinatura
    rect_insercao = fitz.Rect(x0, y0, x1, y1)
    ultima_pagina.insert_image(rect_insercao, stream=img_bytes_assinatura)
    
    # Define o local de salvamento final dentro da pasta sincronizada da transportadora
    pasta_final_trans = os.path.join(PASTA_DESTINO_SHAREPOINT, trans_nome)
    os.makedirs(pasta_final_trans, exist_ok=True)
    
    nome_arquivo = os.path.basename(caminho_pdf)
    nome_base = nome_arquivo.split(".")[0]
    nome_saida_pdf = f"{nome_base}_ASSINADO.pdf"
    caminho_salvamento_final = os.path.join(pasta_final_trans, nome_saida_pdf)
    
    # Salva o arquivo final direto na pasta do OneDrive local do computador
    doc.save(caminho_salvamento_final, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
    doc.close()
    
    # Remove dos pendentes originais do site para liberar a fila
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
            if os.path.isdir(caminho_subpasta) and any(f.endswith(".pdf") for f in os.listdir(camin_subpasta)):
                transportadoras_pendentes.append(item)
                    
    if not transportadoras_pendentes:
        st.info("🎉 Nenhum romaneio pendente!")
    else:
        trans_selecionada = st.selectbox("📌 Selecione a Transportadora:", sorted(transportadoras_pendentes), key="sb_trans_pendentes")
        
        pasta_trans_escolhida = os.path.join(PASTA_PENDENTES, trans_selecionada)
        arquivos_da_trans = sorted([f for f in os.listdir(pasta_trans_escolhida) if f.endswith(".pdf")])
        
        st.markdown(f"### 📋 Romaneios para a transportadora: **{trans_selecionada}** ({len(arquivos_da_trans)} encontrados)")
        
        opcoes_filtro = ["-- MOSTRAR TODOS OS ROMANEIOS (Assinar em Lote) --"] + arquivos_da_trans
        arquivo_selecionado = st.selectbox("📄 Buscar/Filtrar um Romaneio Específico (Opcional):", opcoes_filtro, key="sb_arquivos_pendentes")
        
        st.markdown("---")
        
        if arquivo_selecionado == "-- MOSTRAR TODOS OS ROMANEIOS (Assinar em Lote) --":
            st.info(f"💡 Modo de assinatura em Lote ativado. Os {len(arquivos_da_trans)} romaneios listados abaixo serão assinados juntos.")
            
            with st.spinner("Carregando visualização de todos os romaneios pendentes..."):
                for idx, arquivo_pdf in enumerate(arquivos_da_trans):
                    st.markdown(f"##### 📄 {idx + 1}º Romaneio: `{arquivo_pdf}`")
                    caminho_completo = os.path.join(pasta_trans_escolhida, arquivo_pdf)
                    imagem_original = converter_pdf_para_imagem_continua(caminho_completo)
                    st.image(imagem_original, use_container_width=True)
                    st.markdown("<br>", unsafe_allow_html=True)
            modo_lote = True
        else:
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
        
        col1, col2 = st.columns(2)
        
        with col1:
            if not modo_lote:
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
                                    st.success("🎉 Assinado! O arquivo foi movido para a pasta do OneDrive local e subirá em instantes.")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro operacional: {e}")
                    else:
                        st.warning("⚠️ Por favor, faça a assinatura antes de enviar.")
            else:
                st.write("")

        with col2:
            texto_botao_lote = f"🔥 Assinar TODOS os {len(arquivos_da_trans)} Romaneios de uma vez"
            if st.button(texto_botao_lote, type="primary", use_container_width=True):
                if canvas_result.image_data is not None and np.any(canvas_result.image_data[:, :, 3] > 0):
                    with st.spinner(f"⚡ Carimbando e transferindo {len(arquivos_da_trans)} PDFs para o OneDrive..."):
                        try:
                            img_traco_bruto = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                            bbox_assinatura = img_traco_bruto.getbbox()
                            
                            if bbox_assinatura:
                                img_assinatura_cortada = img_traco_bruto.crop(bbox_assinatura)
                                img_byte_arr = io.BytesIO()
                                img_assinatura_cortada.save(img_byte_arr, format='PNG')
                                img_bytes = img_byte_arr.getvalue()
                                
                                for arquivo_pdf in arquivos_da_trans:
                                    caminho_completo_pdf = os.path.join(pasta_trans_escolhida, arquivo_pdf)
                                    aplicar_assinatura_em_pdf(caminho_completo_pdf, img_bytes, trans_selecionada)
                                
                                st.session_state["versão_canvas"] += 1
                                st.balloons()
                                st.success(f"🚀 Todos os {len(arquivos_da_trans)} arquivos foram enviados para a pasta local sincronizada!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro no processamento em lote: {e}")
                else:
                    st.warning("⚠️ Por favor, faça a assinatura antes de enviar em lote.")

# ==========================================
# ✅ ABA 2: INFORMAÇÃO DO HISTÓRICO
# ==========================================
with aba_assinados:
    st.subheader("📁 Sincronização Local com Nuvem Habilitada")
    st.info(
        "Os arquivos assinados são movidos imediatamente para a sua pasta sincronizada do OneDrive corporativo. "
        "Acompanhe o ícone de nuvem azul da Microsoft perto do relógio do seu Windows para ver o progresso do upload automático."
    )

# ==========================================
# 🛠️ PAINEL DE CONTROLE DA FILA DE ENTRADA
# ==========================================
st.markdown("---")
with st.expander("⚙️ Painel de Controle da Fila de Entrada"):
    if st.button("🧹 LIMPAR FILA DE ENTRADA (PENDENTES)"):
        if os.path.exists(PASTA_PENDENTES):
            for transportadora in os.listdir(PASTA_PENDENTES):
                caminho_sub = os.path.join(PASTA_PENDENTES, transportadora)
                if os.path.isdir(caminho_sub):
                    for arquivo in os.listdir(caminho_sub):
                        try: os.remove(os.path.join(caminho_sub, arquivo))
                        except: pass
                    try: shutil.rmtree(caminho_sub)
                    except: pass
        st.success("Fila limpa!")
        st.rerun()
