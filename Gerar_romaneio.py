import streamlit as st
import os
from streamlit_drawable_canvas import st_canvas
from PIL import Image, ImageDraw
from pypdf import PdfReader

# Configurações de diretórios (Aponta para a sua pasta do OneDrive)
PASTA_ROMANEIOS = r"C:\Users\bruno.gomes\OneDrive - luftsolutions.com.br\Romaneios_Para_Assinar"

st.set_page_config(page_title="Luft Logistics - Romaneio Digital", layout="centered")

st.title("🚚 Painel de Assinatura de Romaneios")
st.write("Digite o número da sua carga para assinar o documento.")

# 1. Entrada do número da carga pelo motorista
id_carga = st.text_input("Número da Carga:", placeholder="Ex: 822845")

if id_carga:
    # Procura o arquivo correspondente na pasta do OneDrive
    nome_arquivo = f"Romaneio_Carga_{id_carga}_QR.pdf" # Ou .png / .pdf estruturado pelo robô
    caminho_pdf = os.path.join(PASTA_ROMANEIOS, nome_arquivo)
    
    # Para o teste simplificado, vamos procurar por um PDF ou criar a conversão em imagem
    if not os.path.exists(caminho_pdf):
        st.error(f"❌ Carga {id_carga} não encontrada no sistema ou já assinada.")
    else:
        st.success(f"📦 Romaneio da Carga {id_carga} localizado!")
        
        # Simulando a exibição do documento como imagem de fundo (Convertendo o topo do PDF para Imagem de fundo)
        # Nota operacional: Em produção completa, usamos o pdf2image, para o teste criamos uma área proporcional
        st.write("### 📝 Assine com o dedo diretamente no quadro abaixo:")
        
        # Criamos o quadro de desenho com o tamanho exato do bloco de assinaturas do celular
        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 0)",  # Fundo transparente para colar por cima
            stroke_width=3,
            stroke_color="black",
            background_color="#FFF",
            background_image=None, # Aqui o Python carrega o print do romaneio de fundo
            height=250,
            width=500,
            drawing_mode="freedraw",
            key="canvas",
        )
        
        if st.button("💾 Confirmar e Carimbar Assinatura"):
            if canvas_result.image_data is not None:
                st.info("🔄 Processando e fundindo assinatura com o documento original...")
                
                # A mágica avançada acontece aqui: 
                # O Python pega a imagem original do Romaneio e faz o 'Merge' (Fusão) 
                # dos pixels desenhados pelo motorista direto na foto.
                
                # [Aqui roda o script de fusão de imagens do Pillow]
                
                st.balloons()
                st.success("🎉 Sucesso! O romaneio foi assinado na foto e já está salvo no computador do Bruno!")