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
            width=500, # Aumentado um pouco para dar mais espaço horizontal
            drawing_mode="freedraw",
            key="canvas_assinatura_melhorada_v3", # Chave alterada para garantir o reset do componente
        )
        
        if st.button("💾 Enviar Romaneio Assinado"):
            if canvas_result.image_data is not None and np.any(canvas_result.image_data[:, :, 3] > 0):
                with st.spinner("🔄 Juntando assinatura ao documento permanentemente..."):
                    try:
                        # 1. Abre a imagem original do documento
                        imagem_original = Image.open(caminho_pendente).convert("RGBA")
                        largura_orig, altura_orig = imagem_original.size
                        
                        # 2. Converte o traço do canvas para uma imagem nativa do PIL
                        img_traco_bruto = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                        
                        # --- MECANISMO DE POSICIONAMENTO E REDIMENSIONAMENTO DEFENSIVO (NOVO) ---
                        
                        # 1. Recorta apenas o traço desenhado, eliminando todo o espaço branco ao redor.
                        # Isso impede que o traço fique "espremido" dentro de um quadro transparente grande.
                        bbox = img_traco_bruto.getbbox()
                        if bbox:
                            img_assinatura_cortada = img_traco_bruto.crop(bbox)
                            
                            # 2. Define tamanho máximo proporcional e muito menor para caber no campo
                            # (Apenas 30% da largura total e 7% da altura total).
                            largura_maxima = int(largura_orig * 0.30)
                            altura_maxima = int(altura_orig * 0.07)
                            
                            img_assinatura_cortada.thumbnail((largura_maxima, altura_maxima), Image.Resampling.LANCZOS)
                            
                            # Obtém o tamanho final da assinatura redimensionada
                            largura_ass_final, altura_ass_final = img_assinatura_cortada.size
                            
                            # 3. Criamos a camada transparente do tamanho total do documento
                            camada_colagem = Image.new("RGBA", (largura_orig, altura_orig), (255, 255, 255, 0))
                            
                            # --- CÁLCULO DE POSIÇÃO DE BASE (NOVO) ---
                            # Posicionamento horizontal (pos_x): centralizado ou alinhado à esquerda.
                            pos_x = int(largura_orig * 0.08) # Alinhado ligeiramente à esquerda
                            
                            # Posicionamento vertical (pos_y): O segredo está em colar DE BAIXO PARA CIMA.
                            # Definimos o ponto Y exato onde a linha "Nome/RG" está (ex: 85% da altura).
                            # Colamos a assinatura de forma que o *fundo dela* toque na linha, com um pequeno recuo (10px).
                            pos_y_base_linha = int(altura_orig * 0.84) # Alinhado com o campo de assinaturas do rodapé
                            pos_y_colagem = pos_y_base_linha - altura_ass_final - 10 # Recuo de 10 pixels acima da linha
                            
                            # Garante que a colagem não seja negativa (segurança extra)
                            pos_y_colagem = max(0, pos_y_colagem)
                            
                            # Realiza a colagem na camada transparente
                            camada_colagem.paste(img_assinatura_cortada, (pos_x, pos_y_colagem), img_assinatura_cortada)
                            
                            # 4. Combina o documento original com a camada de colagem limpa
                            imagem_concluida = Image.alpha_composite(imagem_original, camada_colagem).convert("RGB")
                            
                            # 5. Salva o arquivo permanentemente na pasta física do servidor
                            nome_saida = arquivo_selecionado.split(".")[0] + "_ASSINADO.png"
                            caminho_salvamento = os.path.join(PASTA_ASSINADOS, nome_saida)
                            imagem_concluida.save(caminho_salvamento, "PNG")
                            
                            # 6. Remove o arquivo original da pasta de pendentes
                            os.remove(caminho_pendente)
                            
                            st.balloons()
                            st.success(f"🎉 Sucesso! Enviado para a pasta de assinados.")
                            st.rerun()
                        else:
                            st.error("❌ Erro ao detectar traço na assinatura. Tente novamente.")
                        
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
        
        # Exibe o documento que foi puxado direto da pasta do servidor
        st.image(caminho_assinado_ver, caption=f"Protocolo Armazenado: {arquivo_ver}", use_container_width=True)
