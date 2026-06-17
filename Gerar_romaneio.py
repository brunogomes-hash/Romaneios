import streamlit as st
import os
import numpy as np
from streamlit_drawable_canvas import st_canvas
from PIL import Image
from pypdf import PdfReader

# Caminho para rastrear os arquivos
PASTA_ROMANEIOS = "Romaneios_Para_Assinar"

st.set_page_config(page_title="Luft Logistics - Galeria de Romaneios", layout="wide")

st.title("🚚 Painel Digital - Escolha o Romaneio")
st.write("Clique no romaneio desejado abaixo para abrir a tela de assinatura.")

# 1. Escaneia o projeto procurando arquivos PDF disponíveis
arquivos_encontrados = []

# Procura na pasta principal e na subpasta para garantir que acha tudo
pastas_busca = ["", PASTA_ROMANEIOS]
for pasta in pastas_busca:
    if os.path.exists(pasta):
        for f in os.listdir(pasta):
            if f.endswith(".pdf") and f not in arquivos_encontrados:
                arquivos_encontrados.append(os.path.join(pasta, f))

if not arquivos_encontrados:
    st.info("📂 Nenhum romaneio em PDF foi encontrado no repositório ainda. Coloque os arquivos no GitHub!")
else:
    # 2. Cria uma lista visual/botões para selecionar o romaneio direto
    st.write("### 📂 Selecione o documento na lista:")
    
    # Cria uma lista limpa com os nomes amigáveis para exibição
    opcoes = {os.path.basename(caminho): caminho for caminho in arquivos_encontrados}
    arquivo_selecionado_nome = st.selectbox("Selecione o Romaneio disponível:", list(opcoes.keys()))
    caminho_final_pdf = opcoes[arquivo_selecionado_nome]

    if caminho_final_pdf:
        st.markdown("---")
        try:
            # 3. Converte o PDF em Imagem usando a biblioteca pypdf (Sem quebras de sistema)
            leitor = PdfReader(caminho_final_pdf)
            pagina = leitor.pages[0]
            
            # Extrai e renderiza os dados da imagem de fundo
            if "/XObject" in pagina["/Resources"]:
                xObject = pagina["/Resources"]["/XObject"].get_object()
                for obj in xObject:
                    if xObject[obj]["/Subtype"] == "/Image":
                        data = xObject[obj].get_data()
                        imagem_romaneio = Image.frombytes("RGB", (xObject[obj]["/Width"], xObject[obj]["/Height"]), data)
                        break
            else:
                # Fallback caso não seja imagem pura: cria tela branca padrão com tamanho de nota
                imagem_romaneio = Image.new("RGB", (800, 1100), "white")

            largura_orig, altura_orig = imagem_romaneio.size
            
            # Ajusta proporção para caber em qualquer celular
            largura_display = 600
            proporcao = largura_display / float(largura_orig)
            altura_display = int(float(altura_orig) * float(proporcao))
            imagem_fundo = imagem_romaneio.resize((largura_display, altura_display), Image.Resampling.LANCZOS)
            
            st.write(f"📝 **Documento Aberto: {arquivo_selecionado_nome}**")
            st.caption("Rabisque sua assinatura com o dedo diretamente sobre a folha abaixo:")

            # 4. Tela de desenho livre sobre o documento selecionado
            canvas_result = st_canvas(
                fill_color="rgba(255, 255, 255, 0)", 
                stroke_width=3,
                stroke_color="black",
                background_image=imagem_fundo,
                height=altura_display,
                width=largura_display,
                drawing_mode="freedraw",
                key="canvas_assinatura_direta",
            )
            
            # 5. Botão para salvar
            if st.button("💾 Enviar Romaneio Assinado"):
                if canvas_result.image_data is not None and np.any(canvas_result.image_data[:, :, 3] > 0):
                    with st.spinner("🔄 Gravando assinatura permanente no arquivo..."):
                        img_traco = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                        img_traco_alta = img_traco.resize((largura_orig, altura_orig), Image.Resampling.LANCZOS)
                        
                        documento_final = imagem_romaneio.convert("RGBA")
                        documento_final.alpha_composite(img_traco_alta)
                        
                        nome_saida = arquivo_selecionado_nome.replace(".pdf", "_ASSINADO.png")
                        documento_final.convert("RGB").save(nome_saida, "PNG")
                        
                        st.balloons()
                        st.success(f"🎉 Pronto! O arquivo assinado foi gerado: {nome_saida}")
                else:
                    st.warning("⚠️ Forneça o traço da assinatura antes de confirmar.")
                    
        except Exception as e:
            st.error(f"⚠️ Erro ao abrir a pré-visualização deste PDF: {e}. Certifique-se de que é um PDF válido.")
