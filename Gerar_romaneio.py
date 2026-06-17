import streamlit as st
import os
import numpy as np
from streamlit_drawable_canvas import st_canvas
from PIL import Image

# Configuração das pastas físicas no servidor
PASTA_PENDENTES = "Romaneios_Para_Assinar"
PASTA_ASSINADOS = "Romaneios_Assinados"

os.makedirs(PASTA_PENDENTES, exist_ok=True)
os.makedirs(PASTA_ASSINADOS, exist_ok=True)

st.set_page_config(page_title="Luft Logistics - Painel de Romaneios", layout="wide")
st.title("🚚 Painel Digital de Romaneios")

# Abas do painel
aba_pendentes, aba_assinados = st.tabs(["📝 Romaneios Pendentes", "✅ Romaneios Assinados"])

with aba_pendentes:
    st.subheader("Documentos aguardando assinatura do motorista")
    
    arquivos_pendentes = []
    if os.path.exists(PASTA_PENDENTES):
        for f in os.listdir(PASTA_PENDENTES):
            if f.endswith((".png", ".jpg", ".jpeg")):
                arquivos_pendentes.append(f)
                
    if not arquivos_pendentes:
        st.info("🎉 Nenhum romaneio pendente! Todos os documentos foram assinados.")
    else:
        arquivo_selecionado = st.selectbox("Selecione o Romaneio para Assinar:", arquivos_pendentes, key="sb_pendentes")
        caminho_pendente = os.path.join(PASTA_PENDENTES, arquivo_selecionado)
        
        st.markdown("---")
        st.write(f"📋 **Visualizando: {arquivo_selecionado}**")
        st.image(caminho_pendente, use_container_width=True)
        
        st.markdown("---")
        st.write("✍️ **ASSINE ABAIXO (Use o dedo dentro do quadro branco):**")
        
        # Quadro branco estável
        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 0)", 
            stroke_width=4,
            stroke_color="black",
            background_color="#ffffff",
            height=150,
            width=500,
            drawing_mode="freedraw",
            key="canvas_posicao_cravada_v9",
        )
        
        if st.button("💾 Enviar Romaneio Assinado"):
            if canvas_result.image_data is not None and np.any(canvas_result.image_data[:, :, 3] > 0):
                with st.spinner("🔄 Gravando assinatura no local correto..."):
                    try:
                        # 1. Abre o romaneio original
                        imagem_original = Image.open(caminho_pendente).convert("RGBA")
                        largura_orig, altura_orig = imagem_original.size
                        
                        # 2. Converte o desenho do motorista
                        img_traco_bruto = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                        
                        # 3. Corta o excesso invisível ao redor do desenho
                        bbox = img_traco_bruto.getbbox()
                        if bbox:
                            img_assinatura_cortada = img_traco_bruto.crop(bbox)
                            
                            # --- DIMENSÃO REDUZIDA E CONTROLADA ---
                            # Força a assinatura a ser pequena para caber estritamente no meio do espaço
                            largura_maxima = int(largura_orig * 0.35)
                            altura_maxima = int(altura_orig * 0.05)   # Altura reduzida para não tocar em nada
                            img_assinatura_cortada.thumbnail((largura_maxima, altura_maxima), Image.Resampling.LANCZOS)
                            largura_ass_final, altura_ass_final = img_assinatura_cortada.size
                            
                            # 4. Camada de colagem transparente
                            camada_colagem = Image.new("RGBA", (largura_orig, altura_orig), (255, 255, 255, 0))
                            
                            # --- COORDENADAS CORRIGIDAS PARA CIMA DA LINHA DO NOME ---
                            # Alinha horizontalmente no começo da linha esquerda
                            pos_x = int(largura_orig * 0.05)
                            
                            # Altura calculada para colar exatamente no meio do campo de assinatura superior (31.5% do documento)
                            # Fica abaixo de "Eu Sem Info..." e encostado logo acima da linha preta horizontal
                            pos_y_linha_nome = int(altura_orig * 0.315)
                            pos_y_colagem = pos_y_linha_nome - altura_ass_final - 3
                            
                            # Cola o traço
                            camada_colagem.paste(img_assinatura_cortada, (pos_x, pos_y_colagem), img_assinatura_cortada)
                            
                            # 5. Junta tudo
                            imagem_concluida = Image.alpha_composite(imagem_original, camada_colagem).convert("RGB")
                            
                            # 6. Salva
                            nome_saida = arquivo_selecionado.split(".")[0] + "_ASSINADO.png"
                            caminho_salvamento = os.path.join(PASTA_ASSINADOS, nome_saida)
                            imagem_concluida.save(caminho_salvamento, "PNG")
                            
                            # Remove pendente
                            os.remove(caminho_pendente)
                            
                            st.balloons()
                            st.success("🎉 Romaneio salvo com sucesso no local exato!")
                            st.rerun()
                        else:
                            st.error("❌ Desenho inválido. Tente assinar novamente.")
                    except Exception as e:
                        st.error(f"❌ Erro ao processar: {e}")
            else:
                st.warning("⚠️ Por favor, faça a assinatura antes de clicar em enviar.")

with aba_assinados:
    st.subheader("Histórico geral de documentos assinados no servidor")
    arquivos_assinados = []
    if os.path.exists(PASTA_ASSINADOS):
        for f in os.listdir(PASTA_ASSINADOS):
            if f.endswith((".png", ".jpg", ".jpeg")):
                arquivos_assinados.append(f)
                
    if not arquivos_assinados:
        st.info("📂 Nenhum documento assinado armazenado no servidor.")
    else:
        arquivo_ver = st.selectbox("Selecione um romaneio para visualizar o protocolo:", arquivos_assinados, key="sb_assinados_geral")
        caminho_assinado_ver = os.path.join(PASTA_ASSINADOS, arquivo_ver)
        st.image(caminho_assinado_ver, use_container_width=True)
