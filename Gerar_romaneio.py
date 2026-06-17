import streamlit as st
import os
import numpy as np
from streamlit_drawable_canvas import st_canvas
from PIL import Image

# Configuração das pastas físicas no servidor
PASTA_PENDENTES = "Romaneios_Para_Assinar"
PASTA_ASSINADOS = "Romaneios_Assinados"

# Garante que as duas pastas existem fisicamente no servidor da nuvem
os.makedirs(PASTA_PENDENTES, exist_ok=True)
os.makedirs(PASTA_ASSINADOS, exist_ok=True)

st.set_page_config(page_title="Luft Logistics - Painel de Romaneios", layout="wide")

st.title("🚚 Painel Digital de Romaneios")

# Criando as duas abas solicitadas
aba_pendentes, aba_assinados = st.tabs(["📝 Romaneios Pendentes", "✅ Romaneios Assinados"])

# ==========================================
# ABA 1: ROMANEIOS PENDENTES DE ASSINATURA
# ==========================================
with aba_pendentes:
    st.subheader("Documentos aguardando assinatura do motorista")
    
    arquivos_pendentes = []
    if os.path.exists(PASTA_PENDENTES):
        for f in os.listdir(PASTA_PENDENTES):
            if f.endswith(".png") or f.endswith(".jpg") or f.endswith(".jpeg"):
                arquivos_pendentes.append(f)
                
    if not arquivos_pendentes:
        st.info("🎉 Nenhum romaneio pendente! Todos os documentos foram assinados.")
    else:
        arquivo_selecionado = st.selectbox("Selecione o Romaneio para Assinar:", arquivos_pendentes, key="sb_pendentes")
        caminho_pendente = os.path.join(PASTA_PENDENTES, arquivo_selecionado)
        
        st.markdown("---")
        st.write(f"📋 **Visualizando: {arquivo_selecionado}**")
        
        # Exibe o romaneio de forma limpa
        st.image(caminho_pendente, use_container_width=True)
        
        st.markdown("---")
        st.write("✍️ **ASSINE ABAIXO (Use o dedo dentro do quadro branco):**")
        
        # Quadro branco padrão para o motorista rabiscar
        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 0)", 
            stroke_width=4,
            stroke_color="black",
            background_color="#ffffff",
            height=150,
            width=500, # Aumentado um pouco para dar mais espaço de escrita horizontal
            drawing_mode="freedraw",
            key="canvas_assinatura_v4_final", # Chave alterada para resetar o cache do servidor
        )
        
        if st.button("💾 Enviar Romaneio Assinado"):
            if canvas_result.image_data is not None and np.any(canvas_result.image_data[:, :, 3] > 0):
                with st.spinner("🔄 Gravando assinatura permanentemente..."):
                    try:
                        # 1. Abre a imagem original do documento
                        imagem_original = Image.open(caminho_pendente).convert("RGBA")
                        largura_orig, altura_orig = imagem_original.size
                        
                        # 2. Converte o traço do canvas para uma imagem com fundo transparente
                        img_traco_bruto = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                        
                        # 3. Localiza os limites exatos onde há desenho (remove as bordas vazias do quadro branco)
                        bbox = img_traco_bruto.getbbox()
                        if bbox:
                            # Recorta apenas a assinatura, eliminando o espaço em branco inútil ao redor
                            img_assinatura_cortada = img_traco_bruto.crop(bbox)
                            
                            # Redimensiona de forma proporcional para caber perfeitamente no campo sem deformar
                            largura_maxima = int(largura_orig * 0.45)
                            img_assinatura_cortada.thumbnail((largura_maxima, int(altura_orig * 0.15)), Image.Resampling.LANCZOS)
                            
                            largura_ass, altura_ass = img_assinatura_cortada.size
                            
                            # 4. Criamos a camada transparente do tamanho total do documento
                            camada_colagem = Image.new("RGBA", (largura_orig, altura_orig), (255, 255, 255, 0))
                            
                            # Posicionamento exato baseado no retângulo vermelho do topo
                            pos_x = int(largura_orig * 0.06)  # Alinhado com o início da linha "Nome:"
                            pos_y_linha = int(altura_orig * 0.30) # Posição vertical da linha correspondente
                            
                            # Cola a assinatura ligeiramente acima da linha demarcatória
                            pos_y_colagem = pos_y_linha - altura_ass - 10
                            
                            camada_colagem.paste(img_assinatura_cortada, (pos_x, pos_y_colagem), img_assinatura_cortada)
                            
                            # 5. Combina o documento original com a assinatura tratada
                            imagem_concluida = Image.alpha_composite(imagem_original, camada_colagem).convert("RGB")
                            
                            # 6. Salva o arquivo permanentemente na pasta física do servidor
                            nome_saida = arquivo_selecionado.split(".")[0] + "_ASSINADO.png"
                            caminho_salvamento = os.path.join(PASTA_ASSINADOS, nome_saida)
                            imagem_concluida.save(caminho_salvamento, "PNG")
                            
                            # 7. Remove o arquivo original da pasta de pendentes
                            os.remove(caminho_pendente)
                            
                            st.balloons()
                            st.success(f"🎉 Sucesso! Enviado para a pasta de assinados.")
                            st.rerun()
                        else:
                            st.warning("⚠️ O traço está muito fraco ou em branco. Tente assinar novamente.")
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao processar o salvamento: {e}")
            else:
                st.warning("⚠️ Por favor, faça a assinatura antes de clicar em enviar.")

# ==========================================
# ABA 2: ROMANEIOS JÁ ASSINADOS
# ==========================================
with aba_assinados:
    st.subheader("Histórico geral de documentos assinados no servidor")
    
    arquivos_assinados = []
    if os.path.exists(PASTA_ASSINADOS):
        for f in os.listdir(PASTA_ASSINADOS):
            if f.endswith(".png") or f.endswith(".jpg") or f.endswith(".jpeg"):
                arquivos_assinados.append(f)
                
    if not arquivos_assinados:
        st.info("📂 Nenhum documento assinado armazenado no servidor até o momento.")
    else:
        st.write(f"✅ **Total de documentos assinados disponíveis:** {len(arquivos_assinados)}")
        
        arquivo_ver = st.selectbox("Selecione um romaneio para visualizar o protocolo:", arquivos_assinados, key="sb_assinados_geral")
        caminho_assinado_ver = os.path.join(PASTA_ASSINADOS, arquivo_ver)
        
        st.image(caminho_assinado_ver, caption=f"Protocolo Armazenado: {arquivo_ver}", use_container_width=True)
