import streamlit as st
import os
import numpy as np
from streamlit_drawable_canvas import st_canvas
from PIL import Image
from pdf2image import convert_from_path

# Define a pasta onde os arquivos ficarão armazenados dentro do seu projeto do GitHub
PASTA_ROMANEIOS = "Romaneios_Para_Assinar"

st.set_page_config(page_title="Luft Logistics - Romaneio Digital", layout="centered")

st.title("🚚 Painel de Assinatura de Romaneios")
st.write("Insira o número da carga impresso para visualizar o documento e assinar.")

id_carga = st.text_input("Número da Carga:", placeholder="Ex: 822845")

if id_carga:
    nome_arquivo_pdf = f"Romaneio_Carga_{id_carga}_QR.pdf"
    caminho_pdf = os.path.join(PASTA_ROMANEIOS, nome_arquivo_pdf)
    
    if not os.path.exists(caminho_pdf):
        st.error(f"❌ Romaneio da Carga {id_carga} não localizado. Certifique-se de carregar o arquivo PDF na pasta '{PASTA_ROMANEIOS}' do seu GitHub.")
    else:
        try:
            # 1. Converte o PDF em uma Imagem para o fundo do Canvas
            paginas = convert_from_path(caminho_pdf, dpi=120)
            imagem_romaneio = paginas[0]
            largura_orig, altura_orig = imagem_romaneio.size
            
            # 2. Redimensiona proporcionalmente para visualização em telas de celulares
            largura_display = 600
            proporcao = largura_display / float(largura_orig)
            altura_display = int(float(altura_orig) * float(proporcao))
            imagem_fundo = imagem_romaneio.resize((largura_display, altura_display), Image.Resampling.LANCZOS)
            
            st.write("### 📝 Assine com o dedo sobre o documento abaixo:")
            
            # 3. Cria a área de desenho interativa sobrepondo a folha do romaneio
            canvas_result = st_canvas(
                fill_color="rgba(255, 255, 255, 0)",  # Mantém os traços transparentes
                stroke_width=3,
                stroke_color="black",
                background_image=imagem_fundo,
                height=altura_display,
                width=largura_display,
                drawing_mode="freedraw",
                key="canvas_assinatura",
            )
            
            # 4. Botão de Fusão e Gravação Final
            if st.button("💾 Confirmar e Enviar Documento Assinado"):
                if canvas_result.image_data is not None and np.any(canvas_result.image_data[:, :, 3] > 0):
                    with st.spinner("🔄 Gravando e fundindo assinaturas diretamente na imagem..."):
                        
                        # Converte a matriz de traços do motorista em um objeto de Imagem (RGBA)
                        img_traco = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                        
                        # Redimensiona o desenho do dedo para a escala original (Alta Resolução) do PDF
                        img_traco_alta = img_traco.resize((largura_orig, altura_orig), Image.Resampling.LANCZOS)
                        
                        # Sobreposição perfeita de camadas: Romaneio Base + Desenho do Motorista
                        documento_final = imagem_romaneio.convert("RGBA")
                        documento_final.alpha_composite(img_traco_alta)
                        
                        # Salva o arquivo final de imagem assinado de volta ao armazenamento da operação
                        nome_saida = f"Romaneio_Carga_{id_carga}_ASSINADO.png"
                        caminho_salvamento = os.path.join(PASTA_ROMANEIOS, nome_saida)
                        
                        # Grava o documento final mesclado
                        documento_final.convert("RGB").save(caminho_salvamento, "PNG")
                        
                        st.balloons()
                        st.success(f"🎉 Validado com sucesso! A imagem contendo o documento oficial assinado foi gerada: {nome_saida}")
                        st.info("Você pode baixar ou resgatar este arquivo diretamente pelo painel do repositório.")
                else:
                    st.warning("⚠️ O campo de assinatura está em branco. Forneça o traço com o dedo antes de salvar.")
                    
        except Exception as e:
            st.error(f"❌ Erro de processamento interno ao converter ou renderizar o documento: {e}")
