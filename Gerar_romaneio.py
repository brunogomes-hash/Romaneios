import streamlit as st
import os
import numpy as np
from streamlit_drawable_canvas import st_canvas
from PIL import Image

# Configuração da pasta onde estão as fotos
PASTA_ROMANEIOS = "Romaneios_Para_Assinar"

st.set_page_config(page_title="Luft Logistics - Painel de Romaneios", layout="wide")

st.title("🚚 Painel Digital - Escolha o Romaneio")
st.write("Selecione o romaneio abaixo para assinar.")

# 1. Procura exclusivamente arquivos de imagem (PNG ou JPG)
arquivos_encontrados = []
pastas_busca = ["", PASTA_ROMANEIOS]

for pasta in pastas_busca:
    if os.path.exists(pasta):
        for f in os.listdir(pasta):
            if (f.endswith(".png") or f.endswith(".jpg") or f.endswith(".jpeg")) and not f.endswith("_ASSINADO.png"):
                caminho_completo = os.path.join(pasta, f)
                if caminho_completo not in arquivos_encontrados:
                    arquivos_encontrados.append(caminho_completo)

if not arquivos_encontrados:
    st.info("📂 Nenhuma imagem de romaneio encontrada na pasta 'Romaneios_Para_Assinar' do GitHub.")
else:
    # 2. Caixa de seleção do documento
    opcoes = {os.path.basename(caminho): caminho for caminho in arquivos_encontrados}
    arquivo_selecionado_nome = st.selectbox("Selecione o Romaneio disponível:", list(opcoes.keys()))
    caminho_final_imagem = opcoes[arquivo_selecionado_nome]

    if caminho_final_imagem:
        st.markdown("---")
        
        st.write(f"📝 **Documento Aberto: {arquivo_selecionado_nome}**")
        
        # 3. Exibe o documento usando o st.image padrão do Streamlit (QUE NUNCA DÁ ERRO)
        st.image(caminho_final_imagem, caption="Visualização do Romaneio", use_container_width=True)
        
        st.markdown("---")
        st.write("✍️ **ASSINE ABAIXO (Rabisque com o dedo dentro do quadro branco):**")

        # 4. Cria a área de assinatura limpa (sem imagem de fundo para evitar o bug)
        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 0)", 
            stroke_width=4,
            stroke_color="black",
            background_color="#ffffff",
            height=200,
            width=600,
            drawing_mode="freedraw",
            key="canvas_assinatura_limpo",
        )
        
        # 5. Botão para salvar a assinatura
        if st.button("💾 Enviar Romaneio Assinado"):
            if canvas_result.image_data is not None and np.any(canvas_result.image_data[:, :, 3] > 0):
                with st.spinner("🔄 Gravando assinatura e gerando documento final..."):
                    try:
                        # Abre a imagem original
                        imagem_romaneio = Image.open(caminho_final_imagem).convert("RGBA")
                        largura_orig, altura_orig = imagem_romaneio.size
                        
                        # Converte o traço da assinatura e redimensiona para colar no rodapé do documento
                        img_traco = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                        # Ajusta o tamanho do traço para caber proporcionalmente embaixo
                        img_traco_redimensionada = img_traco.resize((int(largura_orig * 0.5), int(altura_orig * 0.15)), Image.Resampling.LANCZOS)
                        
                        # Cria uma camada transparente do tamanho do documento para colar o traço no final da página
                        camada_assinatura = Image.new("RGBA", (largura_orig, altura_orig), (255, 255, 255, 0))
                        pos_x = int(largura_orig * 0.25)
                        pos_y = int(altura_orig * 0.82) # Cola perto do rodapé
                        camada_assinatura.paste(img_traco_redimensionada, (pos_x, pos_y))
                        
                        # Junta a folha com a assinatura
                        documento_final = Image.alpha_composite(imagem_romaneio, camada_assinatura)
                        
                        nome_saida = arquivo_selecionado_nome.split(".")[0] + "_ASSINADO.png"
                        documento_final.convert("RGB").save(nome_saida, "PNG")
                        
                        st.balloons()
                        st.success(f"🎉 Sucesso! O romaneio assinado foi gerado: {nome_saida}")
                    except Exception as e:
                        st.error(f"❌ Erro ao salvar arquivo combinado: {e}")
            else:
                st.warning("⚠️ Desenhe a assinatura no quadro branco antes de confirmar.")
