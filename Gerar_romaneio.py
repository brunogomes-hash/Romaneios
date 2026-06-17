import streamlit as st
import os
import numpy as np
from streamlit_drawable_canvas import st_canvas
from PIL import Image

# Configuração de diretórios
PASTA_PENDENTES = "Romaneios_Para_Assinar"
PASTA_ASSINADOS = "Romaneios_Assinados"

os.makedirs(PASTA_PENDENTES, exist_ok=True)
os.makedirs(PASTA_ASSINADOS, exist_ok=True)

st.set_page_config(page_title="Luft Logistics - Painel de Romaneios", layout="wide")
st.title("🚚 Painel Digital de Romaneios")

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
        
        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 0)", 
            stroke_width=4,
            stroke_color="black",
            background_color="#ffffff",
            height=150,
            width=500,
            drawing_mode="freedraw",
            key="canvas_reconhecimento_automatico_v11",
        )
        
        if st.button("💾 Enviar Romaneio Assinado"):
            if canvas_result.image_data is not None and np.any(canvas_result.image_data[:, :, 3] > 0):
                with st.spinner("🔍 Analisando documento e alinhando assinatura automaticamente..."):
                    try:
                        # 1. Abre o romaneio original
                        imagem_original = Image.open(caminho_pendente).convert("RGBA")
                        largura_orig, altura_orig = imagem_original.size
                        
                        # 2. Converte o traço do motorista e remove rebarbas vazias
                        img_traco_bruto = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                        bbox_assinatura = img_traco_bruto.getbbox()
                        
                        if bbox_assinatura:
                            img_assinatura_cortada = img_traco_bruto.crop(bbox_assinatura)
                            
                            # ==========================================
                            # ESCANEAMENTO AUTOMÁTICO DO DOCUMENTO
                            # ==========================================
                            # Convertemos o romaneio para escala de cinza para achar as linhas pretas textuais
                            img_cinza = imagem_original.convert("L")
                            matriz_pixels = np.array(img_cinza)
                            
                            # Varre a região provável do topo (entre 20% e 45% da página) procurando 
                            # a maior concentração de linhas escuras horizontais (onde fica o campo Nome/Linha)
                            y_inicio_busca = int(altura_orig * 0.20)
                            y_fim_busca = int(altura_orig * 0.45)
                            
                            # Encontra a linha horizontal preta com base na intensidade dos pixels
                            linhas_escuras = np.where(matriz_pixels[y_inicio_busca:y_fim_busca, :].mean(axis=1) < 200)[0]
                            
                            if len(linhas_escuras) > 0:
                                # Identifica o local exato da linha preta do campo de escrita
                                pos_y_detectado = y_inicio_busca + linhas_escuras[-1]
                            else:
                                # Caso não detecte por segurança (imagem borrada), usa o padrão seguro
                                pos_y_detectado = int(altura_orig * 0.31)
                            
                            # ==========================================
                            # AJUSTE PROPORCIONAL DA ASSINATURA
                            # ==========================================
                            # Redimensiona para um tamanho harmônico que cabe em qualquer lacuna
                            largura_maxima = int(largura_orig * 0.30)
                            altura_maxima = int(altura_orig * 0.04)
                            img_assinatura_cortada.thumbnail((largura_maxima, altura_maxima), Image.Resampling.LANCZOS)
                            largura_ass_final, altura_ass_final = img_assinatura_cortada.size
                            
                            # 3. Faz a colagem no local encontrado
                            camada_colagem = Image.new("RGBA", (largura_orig, altura_orig), (255, 255, 255, 0))
                            
                            # Alinha horizontalmente na margem do canhoto
                            pos_x = int(largura_orig * 0.06)
                            
                            # Cola exatamente ACIMA do ponto Y que o robô escaneou e detectou na folha
                            pos_y_colagem = pos_y_detectado - altura_ass_final - 4
                            
                            camada_colagem.paste(img_assinatura_cortada, (pos_x, pos_y_colagem), img_assinatura_cortada)
                            imagem_concluida = Image.alpha_composite(imagem_original, camada_colagem).convert("RGB")
                            
                            # 4. Salva e atualiza
                            nome_saida = arquivo_selecionado.split(".")[0] + "_ASSINADO.png"
                            caminho_salvamento = os.path.join(PASTA_ASSINADOS, nome_saida)
                            imagem_concluida.save(caminho_salvamento, "PNG")
                            
                            os.remove(caminho_pendente)
                            
                            st.balloons()
                            st.success("🎉 Sensacional! O sistema localizou o campo e colou o documento com perfeição.")
                            st.rerun()
                        else:
                            st.error("❌ Quadro em branco. Assine antes de clicar em enviar.")
                    except Exception as e:
                        st.error(f"❌ Erro na varredura inteligente: {e}")

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
