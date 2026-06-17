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
        
        # O QUADRO BRANCO VOLTOU: Configuração limpa e direta
        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 0)", 
            stroke_width=4,
            stroke_color="black",
            background_color="#ffffff",
            height=150,
            width=500, 
            drawing_mode="freedraw",
            key="canvas_quadro_restaurado_v5", 
        )
        
        if st.button("💾 Enviar Romaneio Assinado"):
            if canvas_result.image_data is not None and np.any(canvas_result.image_data[:, :, 3] > 0):
                with st.spinner("🔄 Gravando assinatura permanentemente..."):
                    try:
                        # 1. Abre a imagem original do documento
                        imagem_original = Image.open(caminho_pendente).convert("RGBA")
                        largura_orig, altura_orig = imagem_original.size
                        
                        # 2. Converte o traço do canvas para imagem nativa do PIL
                        img_traco_bruto = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                        
                        # --- NOVA LÓGICA DE DIMENSÃO (Sem travar o servidor) ---
                        # Definimos uma proporção fixa e elegante baseada na folha original
                        largura_assinatura = int(largura_orig * 0.35)
                        altura_assinatura = int(altura_orig * 0.10)
                        img_assinatura_final = img_traco_bruto.resize((largura_assinatura, altura_assinatura), Image.Resampling.LANCZOS)
                        
                        # 3. Criamos a camada transparente do tamanho total do documento
                        camada_colagem = Image.new("RGBA", (largura_orig, altura_orig), (255, 255, 255, 0))
                        
                        # Posicionamento exato acima da linha do retângulo vermelho superior
                        pos_x = int(largura_orig * 0.06)      # Alinhado à esquerda na direção do campo Nome
                        pos_y_linha = int(altura_orig * 0.25) # Altura exata da linha divisória superior
                        
                        # Cola a assinatura para flutuar exatamente em cima da linha
                        pos_y_colagem = pos_y_linha - altura_assinatura - 5
                        
                        camada_colagem.paste(img_assinatura_final, (pos_x, pos_y_colagem), img_assinatura_final)
                        
                        # 4. Combina o documento original com a assinatura
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
