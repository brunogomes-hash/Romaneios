import streamlit as st
import os
import numpy as np
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import fitz  # PyMuPDF para abrir o PDF dentro do site
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
# 📝 ABA 1: ROMANEIOS PENDENTES (POR TRANSPORTADORA)
# ==========================================
with aba_pendentes:
    st.subheader("Documentos aguardando assinatura do motorista")
    
    # 🔍 Mapeia subpastas que possuem arquivos PDF dentro
    transportadoras_pendentes = []
    if os.path.exists(PASTA_PENDENTES):
        for item in os.listdir(PASTA_PENDENTES):
            caminho_subpasta = os.path.join(PASTA_PENDENTES, item)
            if os.path.isdir(caminho_subpasta):
                # Verifica se há algum PDF dentro dessa pasta de transportadora
                possui_pdf = any(f.endswith(".pdf") for f in os.listdir(caminho_subpasta))
                if possui_pdf:
                    transportadoras_pendentes.append(item)
                    
    if not transportadoras_pendentes:
        st.info("🎉 Nenhum romaneio pendente! Todos os documentos foram assinados com sucesso.")
    else:
        # Primeiro filtro: Transportadora
        trans_selecionada = st.selectbox("📌 Selecione a Transportadora:", sorted(transportadoras_pendentes), key="sb_trans_pendentes")
        
        pasta_trans_escolhida = os.path.join(PASTA_PENDENTES, trans_selecionada)
        arquivos_da_trans = [f for f in os.listdir(pasta_trans_escolhida) if f.endswith(".pdf")]
        
        # Segundo filtro: O número do romaneio limpo daquela transportadora
        arquivo_selecionado = st.selectbox("📄 Selecione o Romaneio:", arquivos_da_trans, key="sb_arquivos_pendentes")
        
        caminho_pendente = os.path.join(pasta_trans_escolhida, arquivo_selecionado)
        
        st.markdown("---")
        st.write(f"📋 **Visualizando Romaneio:** `{arquivo_selecionado}` da transportadora **{trans_selecionada}**")
        
        with st.spinner("Carregando páginas do Romaneio..."):
            imagem_original = converter_pdf_para_imagem_continua(caminho_pendente)
        
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
                with st.spinner("🔍 Analisando rodapé do documento e alinhando assinatura..."):
                    try:
                        imagem_original_rgba = imagem_original.convert("RGBA")
                        largura_orig, altura_orig = imagem_original_rgba.size
                        
                        img_traco_bruto = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                        bbox_assinatura = img_traco_bruto.getbbox()
                        
                        if bbox_assinatura:
                            img_assinatura_cortada = img_traco_bruto.crop(bbox_assinatura)
                            
                            img_cinza = imagem_original_rgba.convert("L")
                            matriz_pixels = np.array(img_cinza)
                            
                            y_inicio_busca = int(altura_orig * 0.50)
                            y_fim_busca = int(altura_orig * 0.98)
                            
                            regiao_rodape = matriz_pixels[y_inicio_busca:y_fim_busca, :]
                            medias_horizontais = regiao_rodape.mean(axis=1)
                            
                            linhas_escuras = np.where(medias_horizontais < 210)[0]
                            
                            if len(linhas_escuras) > 0:
                                pos_y_detectado = y_inicio_busca + linhas_escuras[-1]
                            else:
                                pos_y_detectado = int(altura_orig * 0.90)
                            
                            largura_maxima = int(largura_orig * 0.32)
                            altura_maxima = int(altura_orig * 0.05)
                            img_assinatura_cortada.thumbnail((largura_maxima, altura_maxima), Image.Resampling.LANCZOS)
                            largura_ass_final, altura_ass_final = img_assinatura_cortada.size
                            
                            camada_colagem = Image.new("RGBA", (largura_orig, altura_orig), (255, 255, 255, 0))
                            
                            pos_x = int(largura_orig * 0.06)
                            pos_y_colagem = pos_y_detectado - altura_ass_final - 12
                            
                            camada_colagem.paste(img_assinatura_cortada, (pos_x, pos_y_colagem), img_assinatura_cortada)
                            imagem_concluida = Image.alpha_composite(imagem_original_rgba, camada_colagem).convert("RGB")
                            
                            # Mantém a organização salvando na pasta histórica também por transportadora
                            pasta_salvamento_assinado = os.path.join(PASTA_ASSINADOS, trans_selecionada)
                            os.makedirs(pasta_salvamento_assinado, exist_ok=True)
                            
                            nome_base = arquivo_selecionado.split(".")[0]
                            nome_saida = f"{nome_base}_ASSINADO.png"
                            caminho_salvamento = os.path.join(pasta_salvamento_assinado, nome_saida)
                            
                            imagem_concluida.save(caminho_salvamento, "PNG")
                            
                            if os.path.exists(caminho_pendente):
                                os.remove(caminho_pendente)
                            
                            st.session_state["versão_canvas"] += 1
                            st.balloons()
                            st.success(f"🎉 Perfeito! Documento assinado e salvo na pasta {trans_selecionada}.")
                            st.rerun()
                        else:
                            st.error("❌ Quadro em branco. Assine antes de clicar em enviar.")
                    except Exception as e:
                        st.error(f"❌ Erro operacional no processamento visual: {e}")
            else:
                st.warning("⚠️ Por favor, faça a assinatura antes de clicar em enviar.")

# ==========================================
# ✅ ABA 2: HISTÓRICO SEGURO (POR TRANSPORTADORA)
# ==========================================
with aba_assinados:
    st.subheader("Histórico geral de documentos assinados no servidor")
    
    transportadoras_assinadas = []
    if os.path.exists(PASTA_ASSINADOS):
        for item in os.listdir(PASTA_ASSINADOS):
            caminho_subpasta = os.path.join(PASTA_ASSINADOS, item)
            if os.path.isdir(caminho_subpasta):
                possui_imagem = any(f.endswith((".png", ".jpg", ".jpeg")) for f in os.listdir(caminho_subpasta))
                if possui_imagem:
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
