import streamlit as st
import os
import numpy as np
from streamlit_drawable_canvas import st_canvas
from PIL import Image

# Configuração das pastas
PASTA_PENDENTES = "Romaneios_Para_Assinar"

# Inicializa uma lista na memória para guardar os arquivos assinados temporariamente
if "romaneios_assinados_memoria" not in st.session_state:
    st.session_state.romaneios_assinados_memoria = {}

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
                # Garante que só mostra se ainda não tiver sido assinado na sessão
                if f not in st.session_state.romaneios_assinados_memoria:
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
        
        # CORREÇÃO CRÍTICA: Removido o use_container_width que causava o erro!
        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 0)", 
            stroke_width=4,
            stroke_color="black",
            background_color="#ffffff",
            height=150,
            width=400, # Tamanho fixo ideal para telas de celular e PC
            drawing_mode="freedraw",
            key="canvas_assinatura_correto",
        )
        
        if st.button("💾 Enviar Romaneio Assinado"):
            if canvas_result.image_data is not None and np.any(canvas_result.image_data[:, :, 3] > 0):
                with st.spinner("🔄 Juntando assinatura ao documento..."):
                    try:
                        # 1. Abre a imagem original
                        imagem_original = Image.open(caminho_pendente).convert("RGBA")
                        largura_orig, altura_orig = imagem_original.size
                        
                        # 2. Converte o traço do canvas para imagem
                        img_traco = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                        
                        # 3. Redimensiona o traço para ficar estético no rodapé
                        largura_assinatura = int(largura_orig * 0.45)
                        altura_assinatura = int(altura_orig * 0.12)
                        img_traco_redim = img_traco.resize((largura_assinatura, altura_assinatura), Image.Resampling.LANCZOS)
                        
                        # 4. Posiciona a assinatura no rodapé do romaneio
                        camada_transparente = Image.new("RGBA", (largura_orig, altura_orig), (255, 255, 255, 0))
                        pos_x = int((largura_orig - largura_assinatura) / 2)
                        pos_y = int(altura_orig * 0.84)
                        camada_transparente.paste(img_traco_redim, (pos_x, pos_y))
                        
                        # 5. Combina as duas imagens
                        imagem_final = Image.alpha_composite(imagem_original, camada_transparente).convert("RGB")
                        
                        # 6. Salva o resultado final diretamente na memória compartilhada das abas
                        nome_saida = arquivo_selecionado.split(".")[0] + "_ASSINADO.png"
                        
                        # Guarda a imagem pronta na memória
                        st.session_state.romaneios_assinados_memoria[arquivo_selecionado] = {
                            "nome": nome_saida,
                            "imagem": imagem_final
                        }
                        
                        st.balloons()
                        st.success(f"🎉 Sucesso! Enviado para a aba Romaneios Assinados.")
                        st.status("Documento processado com sucesso! Redirecionando...")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao processar o salvamento: {e}")
            else:
                st.warning("⚠️ Por favor, faça a assinatura antes de clicar em enviar.")

# ==========================================
# ABA 2: ROMANEIOS JÁ ASSINADOS
# ==========================================
with aba_assinados:
    st.subheader("Histórico de documentos assinados nesta sessão")
    
    if not st.session_state.romaneios_assinados_memoria:
        st.info("📂 Nenhum documento foi assinado nesta sessão ainda.")
    else:
        st.write(f"✅ **Total de documentos assinados:** {len(st.session_state.romaneios_assinados_memoria)}")
        
        lista_nomes_originais = list(st.session_state.romaneios_assinados_memoria.keys())
        arquivo_ver_orig = st.selectbox("Selecione um romaneio para visualizar o protocolo:", lista_nomes_originais, key="sb_assinados")
        
        dados_romaneio = st.session_state.romaneios_assinados_memoria[arquivo_ver_orig]
        
        # Exibe o documento definitivo direto da memória já com o rabisco fixado nele!
        st.image(dados_romaneio["imagem"], caption=f"Protocolo Concluído: {dados_romaneio['nome']}", use_container_width=True)
