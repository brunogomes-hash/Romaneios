import streamlit as st
import os
import numpy as np
from streamlit_drawable_canvas import st_canvas
from PIL import Image, ImageDraw
from pdf2image import convert_from_path

# ==============================================================================
# CONFIGURAÇÃO DE DIRETÓRIOS CORPORATIVOS
# ==============================================================================
# IMPORTANTE: Em ambiente de nuvem real, substitua o acesso local por autenticação 
# de API da Microsoft Graph ou use caminhos relativos ao repositório para testes.
PASTA_ROMANEIOS = "Romaneios_Para_Assinar" 

st.set_page_config(page_title="Luft Logistics - Romaneio Digital", layout="centered")

st.title("🚚 Painel de Assinatura de Romaneios")
st.write("Insira o número da carga impresso para visualizar o documento e assinar.")

id_carga = st.text_input("Número da Carga:", placeholder="Ex: 822845")

if id_carga:
    nome_arquivo_pdf = f"Romaneio_Carga_{id_carga}_QR.pdf"
    caminho_pdf = os.path.join(PASTA_ROMANEIOS, nome_arquivo_pdf)
    
    # Validação da existência do documento na fila de carregamento
    if not os.path.exists(caminho_pdf):
        st.error(f"❌ Romaneio da Carga {id_carga} não localizado no banco de dados ativo.")
    else:
        st.success(f"📦 Romaneio da Carga {id_carga} carregado com sucesso!")
        
        # Converte o PDF em imagem para servir de fundo no Canvas do celular
        try:
            paginas = convert_from_path(caminho_pdf, dpi=150)
            imagem_romaneio = paginas[0]  # Obtém a folha principal do documento
            largura_orig, altura_orig = imagem_romaneio.size
            
            # Redimensiona proporcionalmente para exibição confortável em telas mobile
            largura_display = 600
            proporcao = largura_display / float(largura_orig)
            altura_display = int(float(altura_orig) * float(proporcao))
            imagem_fundo = imagem_romaneio.resize((largura_display, altura_display), Image.Resampling.LANCZOS)
            
            st.write("### 📝 Rabisque sua assinatura digital diretamente sobre o documento:")
            
            # Inicializa a camada interativa de desenho sobre a imagem de fundo do romaneio
            canvas_result = st_canvas(
                fill_color="rgba(255, 255, 255, 0)",  # Transparência absoluta para capturar apenas o traço
                stroke_width=3,
                stroke_color="black",
                background_image=imagem_fundo,
                height=altura_display,
                width=largura_display,
                drawing_mode="freedraw",
                key="canvas_assinatura",
            )
            
            # Processamento e Fusão das Imagens após a confirmação do motorista
            if st.button("💾 Confirmar e Enviar Documento Assinado"):
                if canvas_result.image_data is not None and np.any(canvas_result.image_data[:, :, 3] > 0):
                    with st.spinner("🔄 Autenticando e fundindo assinaturas nas camadas do documento..."):
                        
                        # Captura a matriz de pixels desenhados (RGBA) e converte em objeto PIL Image
                        img_traço = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                        
                        # Redimensiona a camada de traços de volta ao tamanho de resolução nativa do PDF original
                        img_traço_alta = img_traço.resize((largura_orig, altura_orig), Image.Resampling.LANCZOS)
                        
                        # Realiza o Alpha Blending (Fusão de camadas) mesclando o desenho sobre o PDF original
                        documento_final = imagem_romaneio.convert("RGBA")
                        documento_final.alpha_composite(img_traço_alta)
                        
                        # Salva o arquivo final de imagem assinado de volta ao armazenamento da operação
                        nome_saida = f"Romaneio_Carga_{id_carga}_ASSINADO.png"
                        caminho_salvamento = os.path.join(PASTA_ROMANEIOS, nome_saida)
                        
                        # Converte de volta para RGB para salvar em formato otimizado e estável (PNG ou PDF)
                        documento_final.convert("RGB").save(caminho_salvamento, "PNG")
                        
                        st.balloons()
                        st.success(f"🎉 Documento validado! O arquivo contendo a foto assinada foi gerado com sucesso: {nome_saida}")
                else:
                    st.warning("⚠️ O campo de assinatura está em branco. Forneça o traço com o dedo antes de salvar.")
                    
        except Exception as e:
            st.error(f"❌ Falha crítica no processamento ou renderização de imagem do PDF: {e}")
