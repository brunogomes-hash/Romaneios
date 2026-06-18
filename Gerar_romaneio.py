import streamlit as st
import os
import numpy as np
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import fitz  # PyMuPDF
import io

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
        trans_selecionada = st.selectbox("📌 Selecione a Transportadora:", sorted(transportadoras_pendentes), key="sb_trans_pendentes")
        
        pasta_trans_escolhida = os.path.join(PASTA_PENDENTES, trans_selecionada)
        arquivos_da_trans = [f for f in os.listdir(pasta_trans_escolhida) if f.endswith(".pdf")]
        
        arquivo_selecionado = st.selectbox("📄 Selecione o Romaneio:", arquivos_da_trans, key="sb_arquivos_pendentes")
        caminho_pendente = os.path.join(pasta_trans_escolhida, arquivo_selecionado)
        
        st.markdown("---")
        
        with st.spinner("Carregando visualização do Romaneio..."):
            imagem_original = converter_pdf_para_imagem_continua(caminho_pendente)
        
        st.image(imagem_original, use_container_width=True)
        
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
        
        if st.button("💾 Enviar Romaneio Assinado"):
            if canvas_result.image_data is not None and np.any(canvas_result.image_data[:, :, 3] > 0):
                with st.spinner("🎯 Localizando o campo 'Responsável' na última página..."):
                    try:
                        # 1. Recorta a assinatura feita no quadro branco
                        img_traco_bruto = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                        bbox_assinatura = img_traco_bruto.getbbox()
                        
                        if bbox_assinatura:
                            img_assinatura_cortada = img_traco_bruto.crop(bbox_assinatura)
                            
                            # 2. Abre o PDF original via PyMuPDF para manipular as páginas direto nele
                            doc = fitz.open(caminho_pendente)
                            ultima_pagina = doc[-1] # Pega estritamente a ÚLTIMA página
                            
                            # 3. Busca a coordenada exata do texto "Responsável:"
                            retangulos_texto = ultima_pagina.search_for("Responsável:")
                            
                            if retangulos_texto:
                                # Se achou o texto, pega a posição dele
                                retangulo_alvo = retangulos_texto[0]
                                # Define a área da assinatura (Acima do texto, alinhado à esquerda)
                                x0 = retangulo_alvo.x0
                                y0 = retangulo_alvo.y0 - 55  # 55 pixels acima da palavra
                                x1 = x0 + 180                # Largura proporcional da assinatura
                                y1 = retangulo_alvo.y0 - 5   # Margem de segurança da linha
                            else:
                                # Fallback de segurança se o texto sumir: Assina no rodapé padrão
                                largura_pag = ultima_pagina.rect.width
                                altura_pag = ultima_pagina.rect.height
                                x0, y0, x1, y1 = 40, altura_pag - 110, 220, altura_pag - 60
                            
                            # 4. Salva a assinatura cortada em bytes para injetar no PDF
                            img_byte_arr = io.BytesIO()
                            img_assinatura_cortada.save(img_byte_arr, format='PNG')
                            img_bytes = img_byte_arr.getvalue()
                            
                            # 5. Insere a imagem no local exato calculado
                            rect_insercao = fitz.Rect(x0, y0, x1, y1)
                            ultima_pagina.insert_image(rect_insercao, stream=img_bytes)
                            
                            # 6. Converte o PDF final modificado em Imagem PNG para o histórico
                            pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2)) if len(doc) == 1 else doc[-1].get_pixmap(matrix=fitz.Matrix(2, 2))
                            # Se quiser o histórico como imagem unificada de todas as páginas:
                            imagem_concluida = converter_pdf_para_imagem_continua(caminho_pendente) # Carrega atualizado
                            
                            # 7. Organiza o salvamento na pasta de assinados
                            pasta_salvamento_assinado = os.path.join(PASTA_ASSINADOS, trans_selecionada)
                            os.makedirs(pasta_salvamento_assinado, exist_ok=True)
                            
                            nome_base = arquivo_selecionado.split(".")[0]
                            nome_saida = f"{nome_base}_ASSINADO.png"
                            caminho_salvamento = os.path.join(pasta_salvamento_assinado, nome_saida)
                            
                            # Salva visualização final no histórico e fecha o PDF original deletando o pendente
                            doc.save(caminho_pendente, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
                            doc.close()
                            
                            # Gera o print do documento final completo com as assinaturas para o histórico
                            imagem_final_historico = converter_pdf_para_imagem_continua(caminho_pendente)
                            imagem_final_historico.convert("RGB").save(caminho_salvamento, "PNG")
                            
                            # Remove dos pendentes locais
                            if os.path.exists(caminho_pendente):
                                os.remove(caminho_pendente)
                            
                            st.session_state["versão_canvas"] += 1
                            st.balloons()
                            st.success(f"🎉 Perfeito! Documento assinado digitalmente em cima do campo 'Responsável'.")
                            st.rerun()
                        else:
                            st.error("❌ Quadro em branco. Assine antes de clicar em enviar.")
                    except Exception as e:
                        st.error(f"❌ Erro operacional no processamento visual: {e}")
            else:
                st.warning("⚠️ Por favor, faça a assinatura antes de clicar em enviar.")

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
        arquivos_assinados = [f for f in os.listdir(pasta_ass_escolhida) if f.endswith((".png", ".jpg", ".jpeg"))]
        
        arquivo_ver = st.selectbox("📄 Selecione o romaneio assinado para visualizar:", arquivos_assinados, key="sb_arquivos_assinados")
        caminho_assinado_ver = os.path.join(pasta_ass_escolhida, arquivo_ver)
                            
        st.markdown("---")
        st.image(caminho_assinado_ver, use_container_width=True)
