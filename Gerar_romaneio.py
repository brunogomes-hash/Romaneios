import streamlit as st
import os
import numpy as np
from streamlit_drawable_canvas import st_canvas
from PIL import Image
from pdf2image import convert_from_path

# Deixando vazio, o Python procura o PDF diretamente na pasta que você colocou!
PASTA_ROMANEIOS = "" 

st.set_page_config(page_title="Luft Logistics - Romaneio Digital", layout="centered")

st.title("🚚 Assinatura de Romaneio Digital")

# Pega o número da carga direto do link do navegador (?carga=XXXXXX)
query_params = st.query_params
id_carga = query_params.get("carga", None)

if not id_carga:
    id_carga = st.text_input("Digite ou confirme o número da carga:")

if id_carga:
    # O script vai procurar o arquivo exatamente com esse nome na pasta principal do Git
    nome_arquivo_pdf = f"Romaneio_Carga_{id_carga}_QR.pdf"
    
    # Se você colocou o PDF dentro de uma pasta específica com o nome da carga, mudamos o caminho:
    if os.path.exists(nome_arquivo_pdf):
        caminho_pdf = nome_arquivo_pdf
    else:
        # Tenta procurar dentro da pasta caso você tenha criado uma pasta com o nome da carga
        caminho_pdf = os.path.join(f"Romaneio_Carga_{id_carga}_QR", nome_arquivo_pdf)

    if not os.path.exists(caminho_pdf):
        st.error(f"❌ Arquivo não encontrado. Certifique-se de que o arquivo '{nome_arquivo_pdf}' está no seu GitHub.")
    else:
        try:
            # 1. Converte o PDF em imagem para o fundo
            paginas = convert_from_path(caminho_pdf, dpi=120)
            imagem_romaneio = paginas[0]
            largura_orig, altura_orig = imagem_romaneio.size
            
            # 2. Ajusta tamanho para a tela do celular
            largura_display = 600
            proporcao = largura_display / float(largura_orig)
            altura_display = int(float(altura_orig) * float(proporcao))
            imagem_fundo = imagem_romaneio.resize((largura_display, altura_display), Image.Resampling.LANCZOS)
            
            st.write(f"### 📦 Carga: {id_carga}")
            st.write("📝 **Assine com o dedo diretamente sobre o documento abaixo:**")
            
            # 3. Abre o quadro de desenho corrigido
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
            
            # 4. Salvar imagem final
            if st.button("💾 Confirmar e Enviar Assinatura"):
                if canvas_result.image_data is not None and np.any(canvas_result.image_data[:, :, 3] > 0):
                    with st.spinner("🔄 Gravando e fundindo sua assinatura no documento..."):
                        img_traco = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                        img_traco_alta = img_traco.resize((largura_orig, altura_orig), Image.Resampling.LANCZOS)
                        
                        documento_final = imagem_romaneio.convert("RGBA")
                        documento_final.alpha_composite(img_traco_alta)
                        
                        nome_saida = f"Romaneio_Carga_{id_carga}_ASSINADO.png"
                        documento_final.convert("RGB").save(nome_saida, "PNG")
                        
                        st.balloons()
                        st.success(f"🎉 Perfeito! O documento foi assinado com sucesso como {nome_saida}!")
                else:
                    st.warning("⚠️ Campo de assinatura em branco.")
        except Exception as e:
            st.error(f"❌ Erro de processamento interno: {e}")
