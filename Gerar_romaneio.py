import streamlit as st
import os
import numpy as np
from streamlit_drawable_canvas import st_canvas
from PIL import Image

# Configuração da pasta onde estão as fotos
PASTA_ROMANEIOS = "Romaneios_Para_Assinar"

st.set_page_config(page_title="Luft Logistics - Painel de Romaneios", layout="wide")

st.title("🚚 Painel Digital - Escolha o Romaneio")
st.write("Selecione o romaneio abaixo para abrir a tela de assinatura.")

# 1. Procura exclusivamente ficheiros de imagem (PNG ou JPG)
arquivos_encontrados = []
pastas_busca = ["", PASTA_ROMANEIOS]

for pasta in pastas_busca:
    if os.path.exists(pasta):
        for f in os.listdir(pasta):
            # Garante que apanha apenas as imagens originais e ignora as já assinadas
            if (f.endswith(".png") or f.endswith(".jpg") or f.endswith(".jpeg")) and not f.endswith("_ASSINADO.png"):
                caminho_completo = os.path.join(pasta, f)
                if caminho_completo not in arquivos_encontrados:
                    arquivos_encontrados.append(caminho_completo)

if not arquivos_encontrados:
    st.info("📂 Nenhuma imagem de romaneio (.png ou .jpg) foi encontrada na pasta 'Romaneios_Para_Assinar' do GitHub.")
else:
    # 2. Cria a lista visual automática na barra de seleção
    opcoes = {os.path.basename(caminho): caminho for caminho in arquivos_encontrados}
    arquivo_selecionado_nome = st.selectbox("Selecione o Romaneio disponível:", list(opcoes.keys()))
    caminho_final_imagem = opcoes[arquivo_selecionado_nome]

    if camino_final_imagem:
        st.markdown("---")
        try:
            # 3. Carrega a foto diretamente (Elimina de vez o erro do PDF)
            imagem_romaneio = Image.open(caminho_final_imagem)
            largura_orig, altura_orig = imagem_romaneio.size
            
            # Ajusta o tamanho para o ecrã do telemóvel de forma proporcional
            largura_display = 600
            proporcao = largura_display / float(largura_orig)
            altura_display = int(float(altura_orig) * float(proporcao))
            imagem_fundo = imagem_romaneio.resize((largura_display, altura_display), Image.Resampling.LANCZOS)
            
            st.write(f"📝 **Documento Aberto: {arquivo_selecionado_nome}**")
            st.caption("Assine com o dedo diretamente sobre a imagem abaixo:")

            # 4. Quadro de desenho livre sobre a foto do romaneio
            canvas_result = st_canvas(
                fill_color="rgba(255, 255, 255, 0)", 
                stroke_width=3,
                stroke_color="black",
                background_image=imagem_fundo,
                height=altura_display,
                width=largura_display,
                drawing_mode="freedraw",
                key="canvas_assinatura_foto_direta",
            )
            
            # 5. Botão para guardar a assinatura
            if st.button("💾 Enviar Romaneio Assinado"):
                if canvas_result.image_data is not None and np.any(canvas_result.image_data[:, :, 3] > 0):
                    with st.spinner("🔄 A gravar assinatura permanentemente no documento..."):
                        img_traco = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                        img_traco_alta = img_traco.resize((largura_orig, altura_orig), Image.Resampling.LANCZOS)
                        
                        documento_final = imagem_romaneio.convert("RGBA")
                        documento_final.alpha_composite(img_traco_alta)
                        
                        nome_saida = arquivo_selecionado_nome.split(".")[0] + "_ASSINADO.png"
                        documento_final.convert("RGB").save(nome_saida, "PNG")
                        
                        st.balloons()
                        st.success(f"🎉 Sucesso! O romaneio assinado foi gerado: {nome_saida}")
                else:
                    st.warning("⚠️ Desenhe a assinatura antes de confirmar.")
                    
        except Exception as e:
            st.error(f"⚠️ Erro ao abrir a imagem: {e}")
