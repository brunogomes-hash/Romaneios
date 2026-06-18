import streamlit as st
import os
import numpy as np
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import fitz  # PyMuPDF para abrir o PDF dentro do site!
import io

# Configuração de diretórios
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
    """Abre o PDF (com 1 ou mais páginas) e junta tudo em uma imagem única vertical"""
    pdf_documento = fitz.open(caminho_pdf)
    total_paginas = len(pdf_documento)
    
    imagens_paginas = []
    largura_maxima = 0
    altura_total = 0
    
    for num_pag in range(total_paginas):
        pagina = pdf_documento.load_page(num_pag)
        zoom = 2  # Mantém a alta qualidade do robô
        matriz = fitz.Matrix(zoom, zoom)
        pixmap = pagina.get_pixmap(matrix=matriz)
        
        img_pil = Image.open(io.BytesIO(pixmap.tobytes("png")))
        imagens_paginas.append(img_pil)
        
        if img_pil.width > largura_maxima:
            largura_maxima = img_pil.width
        altura_total += img_pil.height
        
    pdf_documento.close()
    
    # Cria o fundo branco longo para colar todas as páginas do PDF
    imagem_comprida = Image.new("RGBA", (largura_maxima, altura_total), (255, 255, 255, 255))
    y_offset = 0
    for img in imagens_paginas:
        imagem_comprida.paste(img, (0, y_offset))
        y_offset += img.height
        
    return imagem_comprida

# ==========================================
# ABA 1: ROMANEIOS PENDENTES (LENDO PDF)
# ==========================================
with aba_pendentes:
    st.subheader("Documentos aguardando assinatura do motorista")
    
    arquivos_pendentes = []
    if os.path.exists(PASTA_PENDENTES):
        for f in os.listdir(PASTA_PENDENTES):
            # AGORA ELE BUSCA ARQUIVOS .pdf GERADOS PELO ROBÔ 2
            if f.endswith(".pdf"):
                arquivos_pendentes.append(f)
                
    if not arquivos_pendentes:
        st.info("🎉 Nenhum romaneio pendente! Todos os documentos foram assinados com sucesso.")
    else:
        arquivo_selecionado = st.selectbox("Selecione o Romaneio para Assinar:", arquivos_pendentes, key="sb_pendentes")
        caminho_pendente = os.path.join(PASTA_PENDENTES, arquivo_selecionado)
        
        st.markdown("---")
        st.write(f"📋 **Visualizando: {arquivo_selecionado}**")
        
        # Converte o PDF em uma imagem única na memória para o Streamlit desenhar na tela
        with st.spinner("Carregando páginas do Romaneio..."):
            imagem_original = converter_pdf_para_imagem_continua(caminho_pendente)
        
        # Mostra o documento unificado na tela
        st.image(imagem_original, use_container_width=True)
        
        st.markdown("---")
        st.write("✍️ **ASSINE ABAIXO (Use o dedo dentro do quadro branco):**")
        
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
        
        if st.button("💾 Enviar Romaneio Assinado"):
            if canvas_result.image_data is not None and np.any(canvas_result.image_data[:, :, 3] > 0):
                with st.spinner("🔍 Analisando documento e alinhando assinatura..."):
                    try:
                        # Processa a imagem que extraímos do PDF
                        imagem_original_rgba = imagem_original.convert("RGBA")
                        largura_orig, altura_orig = imagem_original_rgba.size
                        
                        img_traco_bruto = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                        bbox_assinatura = img_traco_bruto.getbbox()
                        
                        if bbox_assinatura:
                            img_assinatura_cortada = img_traco_bruto.crop(bbox_assinatura)
                            
                            img_cinza = imagem_original_rgba.convert("L")
                            matriz_pixels = np.array(img_cinza)
                            
                            # Mantém sua regra de busca de linhas escuras
                            y_inicio_busca = int(altura_orig * 0.20)
                            y_fim_busca = int(altura_orig * 0.45)
                            
                            linhas_escuras = np.where(matriz_pixels[y_inicio_busca:y_fim_busca, :].mean(axis=1) < 200)[0]
                            
                            if len(linhas_escuras) > 0:
                                pos_y_detectado = y_inicio_busca + lines_escuras[-1] if 'lines_escuras' in locals() else y_inicio_busca + linhas_escuras[-1]
                            else:
                                pos_y_detectado = int(altura_orig * 0.31)
                            
                            largura_maxima = int(largura_orig * 0.30)
                            altura_maxima = int(altura_orig * 0.04)
                            img_assinatura_cortada.thumbnail((largura_maxima, altura_maxima), Image.Resampling.LANCZOS)
                            largura_ass_final, altura_ass_final = img_assinatura_cortada.size
                            
                            camada_colagem = Image.new("RGBA", (largura_orig, altura_orig), (255, 255, 255, 0))
                            pos_x = int(largura_orig * 0.06)
                            pos_y_colagem = pos_y_detectado - altura_ass_final - 4
                            
                            camada_colagem.paste(img_assinatura_cortada, (pos_x, pos_y_colagem), img_assinatura_cortada)
                            imagem_concluida = Image.alpha_composite(imagem_original_rgba, camada_colagem).convert("RGB")
                            
                            nome_base = arquivo_selecionado.split(".")[0]
                            nome_saida = f"{nome_base}_ASSINADO.png"
                            caminho_salvamento = os.path.join(PASTA_ASSINADOS, nome_saida)
                            
                            # 1. Salva a versão final assinada como imagem no Histórico
                            imagem_concluida.save(caminho_salvamento, "PNG")
                            
                            # 2. Deleta o arquivo PDF original pendente
                            if os.path.exists(caminho_pendente):
                                os.remove(caminho_pendente)
                            
                            st.session_state["versão_canvas"] += 1
                            st.balloons()
                            st.success(f"🎉 Perfeito! Documento assinado e movido para o histórico.")
                            st.rerun()
                        else:
                            st.error("❌ Quadro em branco. Assine antes de clicar em enviar.")
                    except Exception as e:
                        st.error(f"❌ Erro operacional: {e}")
            else:
                st.warning("⚠️ Por favor, faça a assinatura antes de clicar em enviar.")

# ==========================================
# ABA 2: HISTÓRICO SEGURO
# ==========================================
with aba_assinados:
    st.subheader("Histórico geral de documentos assinados no servidor")
    
    arquivos_assinados = []
    if os.path.exists(PASTA_ASSINADOS):
        for f in os.listdir(PASTA_ASSINADOS):
            if f.endswith((".png", ".jpg", ".jpeg")):
                arquivos_assinados.append(f)
                
    if not arquivos_assinados:
        st.info("📂 Nenhum documento assinado armazenado no servidor no momento.")
    else:
        arquivo_ver = st.selectbox("Selecione qual romaneio deseja visualizar:", arquivos_assinados, key="sb_assinados_geral")
        caminho_assinado_ver = os.path.join(PASTA_ASSINADOS, arquivo_ver)
                    
        st.markdown("---")
        st.image(caminho_assinado_ver, use_container_width=True)
