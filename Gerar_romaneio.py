import streamlit as st
import os
import numpy as np
from streamlit_drawable_canvas import st_canvas
from PIL import Image
from datetime import datetime

# Configuração de diretórios
PASTA_PENDENTES = "Romaneios_Para_Assinar"
PASTA_ASSINADOS = "Romaneios_Assinados"

os.makedirs(PASTA_PENDENTES, exist_ok=True)
os.makedirs(PASTA_ASSINADOS, exist_ok=True)

st.set_page_config(page_title="Luft Logistics - Painel de Romaneios", layout="wide")
st.title("🚚 Painel Digital de Romaneios")

# Controla o reset do quadro de assinatura na memória do sistema
if "versão_canvas" not in st.session_state:
    st.session_state["versão_canvas"] = 0

aba_pendentes, aba_assinados = st.tabs(["📝 Romaneios Pendentes", "✅ Romaneios Assinados"])

with aba_pendentes:
    st.subheader("Documentos aguardando assinatura do motorista")
    
    arquivos_pendentes = []
    if os.path.exists(PASTA_PENDENTES):
        for f in os.listdir(PASTA_PENDENTES):
            if f.endswith((".png", ".jpg", ".jpeg")):
                arquivos_pendentes.append(f)
                
    if not arquivos_pendentes:
        st.info("🎉 Nenhum romaneio pendente! Insira modelos na pasta Romaneios_Para_Assinar.")
    else:
        arquivo_selecionado = st.selectbox("Selecione o Romaneio para Assinar:", arquivos_pendentes, key="sb_pendentes")
        caminho_pendente = os.path.join(PASTA_PENDENTES, arquivo_selecionado)
        
        st.markdown("---")
        st.write(f"📋 **Visualizando: {arquivo_selecionado}**")
        st.image(caminho_pendente, use_container_width=True)
        
        st.markdown("---")
        st.write("✍️ **ASSINE ABAIXO (Use o dedo dentro do quadro branco):**")
        
        # A chave muda dinamicamente após o envio para forçar o quadro a limpar na tela
        chave_canvas = f"canvas_smart_v13_{st.session_state['versão_canvas']}"
        
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
                with st.spinner("🔍 Analisando documento e alinhando assinatura..."):
                    try:
                        # 1. Abre o romaneio original (mantendo o arquivo intacto)
                        imagem_original = Image.open(caminho_pendente).convert("RGBA")
                        largura_orig, altura_orig = imagem_original.size
                        
                        # 2. Converte o traço do motorista e remove as rebarbas vazias
                        img_traco_bruto = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                        bbox_assinatura = img_traco_bruto.getbbox()
                        
                        if bbox_assinatura:
                            img_assinatura_cortada = img_traco_bruto.crop(bbox_assinatura)
                            
                            # Escaneamento Automático Inteligente
                            img_cinza = imagem_original.convert("L")
                            matriz_pixels = np.array(img_cinza)
                            
                            y_inicio_busca = int(altura_orig * 0.20)
                            y_fim_busca = int(altura_orig * 0.45)
                            
                            linhas_escuras = np.where(matriz_pixels[y_inicio_busca:y_fim_busca, :].mean(axis=1) < 200)[0]
                            
                            if len(linhas_escuras) > 0:
                                pos_y_detectado = y_inicio_busca + lines_escuras[-1]
                            else:
                                pos_y_detectado = int(altura_orig * 0.31)
                            
                            # Ajuste dimensional estrito para não estourar os textos
                            largura_maxima = int(largura_orig * 0.30)
                            altura_maxima = int(altura_orig * 0.04)
                            img_assinatura_cortada.thumbnail((largura_maxima, altura_maxima), Image.Resampling.LANCZOS)
                            largura_ass_final, altura_ass_final = img_assinatura_cortada.size
                            
                            # Montagem do arquivo final
                            camada_colagem = Image.new("RGBA", (largura_orig, altura_orig), (255, 255, 255, 0))
                            pos_x = int(largura_orig * 0.06)
                            pos_y_colagem = pos_y_detectado - altura_ass_final - 4
                            
                            camada_colagem.paste(img_assinatura_cortada, (pos_x, pos_y_colagem), img_assinatura_cortada)
                            imagem_concluida = Image.alpha_composite(imagem_original, camada_colagem).convert("RGB")
                            
                            # Gera arquivo único com o horário exato
                            timestamp = datetime.now().strftime("%H%M%S")
                            nome_base = arquivo_selecionado.split(".")[0]
                            nome_saida = f"{nome_base}_ASSINADO_{timestamp}.png"
                            
                            caminho_salvamento = os.path.join(PASTA_ASSINADOS, nome_saida)
                            imagem_concluida.save(caminho_salvamento, "PNG")
                            
                            # O SEGREDO DO RESET AQUI: 
                            # Altera o contador para mudar a chave do canvas e forçar o quadro a limpar
                            st.session_state["versão_canvas"] += 1
                            
                            st.balloons()
                            st.success(f"🎉 Salvo com sucesso! Nova versão criada: {nome_saida}")
                            st.rerun()
                        else:
                            st.error("❌ Quadro em branco. Assine antes de clicar em enviar.")
                    except Exception as e:
                        st.error(f"❌ Erro operacional: {e}")
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
        arquivo_ver = st.selectbox("Selecione qual versão do romaneio deseja visualizar:", arquivos_assinados, key="sb_assinados_geral")
        caminho_assinado_ver = os.path.join(PASTA_ASSINADOS, arquivo_ver)
        st.image(caminho_assinado_ver, use_container_width=True)
