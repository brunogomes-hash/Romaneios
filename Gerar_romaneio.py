import streamlit as st
import os
import numpy as np
from streamlit_drawable_canvas import st_canvas
from PIL import Image
from pdf2image import convert_from_path

# Corrigido: Aponta diretamente para a raiz onde os ficheiros estão soltos no seu GitHub
PASTA_ROMANEIOS = "" 

st.set_page_config(page_title="Luft Logistics - Romaneio Digital", layout="centered")

st.title("🚚 Assinatura de Romaneio Digital")

# Lê automaticamente o número da carga colocado no final do link (?carga=XXXXXX)
query_params = st.query_params
id_carga = query_params.get("carga", None)

if not id_carga:
    id_carga = st.text_input("Digite ou confirme o número da carga:")

if id_carga:
    # Nome exato que o robô gera
    nome_arquivo_pdf = f"Romaneio_Carga_{id_carga}_QR.pdf"
    
    # Define o caminho para procurar o ficheiro na raiz principal do repositório
    caminho_pdf = os.path.join(PASTA_ROMANEIOS, nome_arquivo_pdf)

    if not os.path.exists(caminho_pdf):
        st.error(f"❌ Ficheiro não encontrado. Certifique-se de que o ficheiro '{nome_arquivo_pdf}' está na raiz principal do seu GitHub.")
    else:
        try:
            # 1. Transforma o PDF numa imagem de alta qualidade
            paginas = convert_from_path(caminho_pdf, dpi=120)
            imagem_romaneio = paginas[0]
            largura_orig, altura_orig = imagem_romaneio.size
            
            # 2. Redimensiona de forma proporcional para caber no telemóvel do motorista
            largura_display = 600
            proporcao = largura_display / float(largura_orig)
            altura_display = int(float(altura_orig) * float(proporcao))
            imagem_fundo = imagem_romaneio.resize((largura_display, altura_display), Image.Resampling.LANCZOS)
            
            st.write(f"### 📦 Carga Identificada: {id_carga}")
            st.write("📝 **Assine com o dedo diretamente sobre o documento abaixo:**")
            
            # 3. Cria a área interativa para rabiscar por cima da folha
            canvas_result = st_canvas(
                fill_color="rgba(255, 255, 255, 0)", 
                stroke_width=3,
                stroke_color="black",
                background_image=imagem_fundo,
                height=altura_display,
                width=largura_display,
                drawing_mode="freedraw",
                key="canvas_assinatura",
            )
            
            # 4. Botão para gravar e fazer a fusão final
            if st.button("💾 Confirmar e Enviar Assinatura"):
                if canvas_result.image_data is not None and np.any(canvas_result.image_data[:, :, 3] > 0):
                    with st.spinner("🔄 A processar e a colar a assinatura no documento original..."):
                        
                        img_traco = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                        img_traco_alta = img_traco.resize((largura_orig, altura_orig), Image.Resampling.LANCZOS)
                        
                        # Junta a camada do risco do dedo com a folha original do romaneio
                        documento_final = imagem_romaneio.convert("RGBA")
                        documento_final.alpha_composite(img_traco_alta)
                        
                        # Salva o ficheiro final com a assinatura integrada
                        nome_saida = f"Romaneio_Carga_{id_carga}_ASSINADO.png"
                        documento_final.convert("RGB").save(nome_saida, "PNG")
                        
                        st.balloons()
                        st.success(f"🎉 Excelente! O documento foi assinado com sucesso e guardado como: {nome_saida}")
                else:
                    st.warning("⚠️ O campo de assinatura está vazio. Por favor, assine antes de confirmar.")
        except Exception as e:
            st.error(f"❌ Ocorreu um problema ao renderizar a imagem do PDF: {e}")
