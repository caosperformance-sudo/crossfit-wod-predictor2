import streamlit as st
import numpy as np

## Verificação defensiva das bibliotecas de Visao Computacional
try:
    import cv2
    import mediapipe as mp
    HAS_VISION = True
except ImportError:
    HAS_VISION = False

## Configuração da Página
st.set_page_config(
    page_title="CrossFit WOD & Movement Analyzer",
    page_icon="🏋️‍♂️",
    layout="wide"
)

## Título Principal
st.title("🏋️‍♂️ CrossFit Performance & Movement Analytics")
st.markdown("Plataforma de análise de dados de desempenho, simulação de WODs e biometria de movimento.")

## Navegação Lateral
st.sidebar.header("Navegação")
opcao = st.sidebar.radio(
    "Selecione o Módulo:",
    ["Simulador de WODs & Cargas", "Análise Biomecânica de Movimento", "Timer Interativo"]
)

## -----------------------------------------------------------------------------
## MÓDULO 1: SIMULADOR DE WODS & CARGAS (Inteligência de Dados)
## -----------------------------------------------------------------------------
if opcao == "Simulador de WODs & Cargas":
    st.header("📊 Simulador de Desempenho e Cargas de Treino")
    st.caption("Predição baseada em percentuais de 1RM, densidade de trabalho e curvas de fadiga.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Entrada de Dados do Atleta")
        back_squat_1rm = st.number_input("1RM Back Squat (kg)", min_value=30.0, max_value=300.0, value=120.0, step=2.5, key="bs_rm")
        deadlift_1rm = st.number_input("1RM Deadlift (kg)", min_value=30.0, max_value=350.0, value=150.0, step=2.5, key="dl_rm")
        strict_pullups = st.number_input("Máximo de Pull-ups Estritos (reps)", min_value=0, max_value=60, value=15, key="pu_reps")

    with col2:
        st.subheader("Configuração da Carga do WOD")
        carga_wod = st.slider("Carga do Exercício de LIFT no WOD (kg)", min_value=10.0, max_value=200.0, value=60.0, step=2.5, key="wod_load")
        volume_total = st.number_input("Volume Total Planejado (repetições)", min_value=10, max_value=500, value=100, key="wod_vol")

    st.markdown("---")
    
    ## Cálculos de Inteligência de Dados / Métricas
    pct_squat = (carga_wod / back_squat_1rm) * 100
    pct_deadlift = (carga_wod / deadlift_1rm) * 100

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Intensidade Relativa (Squat)", f"{pct_squat:.1f}% de 1RM")
    col_m2.metric("Intensidade Relativa (Deadlift)", f"{pct_deadlift:.1f}% de 1RM")
    
    ## Classificação de Estratégia de Quebra por Faixa de Intensidade
    if pct_squat < 50:
        estrategia = "Alta RDJ (Rendimento de Velocidade). Sugestão: Sets grandes (Ex: 21-15-9 Ininterrupto)."
    elif 50 <= pct_squat < 75:
        estrategia = "Carga Moderada. Sugestão: Quebras planejadas com descansos curtos (Ex: 3 a 4 sets regulares)."
    else:
        estrategia = "Carga Alta / Limiar de Força. Sugestão: Singlos ou séries curtas de 2 a 3 reps para conter lactato."

    col_m3.info(f"**Estratégia Recomendada:**\n\n{estrategia}")

## -----------------------------------------------------------------------------
## MÓDULO 2: ANÁLISE BIOMECÂNICA DE MOVIMENTO (Visão Computacional Local)
## -----------------------------------------------------------------------------
elif opcao == "Análise Biomecânica de Movimento":
    st.header("📹 Análise Biomecânica via Visão Computacional")
    st.caption("Identificação de pontos articulares e medição de ângulos em tempo real com MediaPipe.")

    if not HAS_VISION:
        st.warning("⚠️ **Módulo de Visão Computacional Desativado:** As bibliotecas `opencv-python-headless` e `mediapipe` não foram encontradas no servidor. Adicione-as ao seu `requirements.txt` para habilitar a análise de vídeos.")
    else:
        ## Função Auxiliar para Calcular Ângulo Articular
        def calcular_angulo(a, b, c):
            a = np.array(a)
            b = np.array(b)
            c = np.array(c)
            
            radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
            angulo = np.abs(radians*180.0/np.pi)
            
            if angulo > 180.0:
                angulo = 360 - angulo
                
            return angulo

        arquivo_video = st.file_uploader("Envie o vídeo do seu movimento (Agachamento, Clean, Snatch):", type=["mp4", "mov", "avi"])

        if arquivo_video is not None:
            import tempfile
            import os
            
            ## Cria arquivo temporário seguro
            tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            tfile.write(arquivo_video.read())
            video_path = tfile.name
            tfile.close()

            st.success("Vídeo carregado com sucesso! Processando biometria...")
            
            ## Aviso sobre processamento
            st.info("⏳ Processando vídeo... Isso pode levar alguns segundos.")

            ## Setup MediaPipe Pose
            mp_pose = mp.solutions.pose
            mp_drawing = mp.solutions.drawing_utils
            pose = mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                min_detection_confidence=0.5, 
                min_tracking_confidence=0.5
            )

            cap = cv2.VideoCapture(video_path)
            
            ## Verificar se o vídeo foi aberto corretamente
            if not cap.isOpened():
                st.error("❌ Erro ao abrir o vídeo. Verifique o formato do arquivo.")
            else:
                frame_window = st.empty()
                progress_bar = st.progress(0)
                angulos_joelho = []
                
                ## Obter total de frames
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                frame_count = 0
                
                ## Processar apenas a cada N frames para melhor performance
                frame_skip = 2  ## Processa 1 a cada 2 frames
                
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    frame_count += 1
                    
                    ## Atualizar barra de progresso
                    if total_frames > 0:
                        progress_bar.progress(min(frame_count / total_frames, 1.0))
                    
                    ## Pular frames para melhor performance
                    if frame_count % frame_skip != 0:
                        continue

                    ## Converte cores BGR para RGB
                    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    image.flags.writeable = False
                    results = pose.process(image)
                    image.flags.writeable = True

                    if results.pose_landmarks:
                        landmarks = results.pose_landmarks.landmark

                        ## Posições do Quadril, Joelho e Tornozelo Esquerdos
                        hip = [
                            landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                            landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y
                        ]
                        knee = [
                            landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                            landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y
                        ]
                        ankle = [
                            landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                            landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y
                        ]

                        ## Ângulo do Joelho
                        angulo_j = calcular_angulo(hip, knee, ankle)
                        angulos_joelho.append(angulo_j)

                        ## Desenha Esqueleto na Imagem
                        mp_drawing.draw_landmarks(
                            image, 
                            results.pose_landmarks, 
                            mp_pose.POSE_CONNECTIONS,
                            mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2),
                            mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)
                        )

                        ## Escreve o Ângulo na Tela do Vídeo
                        knee_pixel = tuple(np.multiply(knee, [image.shape[1], image.shape[0]]).astype(int))
                        cv2.putText(
                            image, 
                            f"Joelho: {int(angulo_j)} deg", 
                            knee_pixel,
                            cv2.FONT_HERSHEY_SIMPLEX, 
                            0.8, 
                            (255, 255, 255), 
                            2, 
                            cv2.LINE_AA
                        )

                    ## Atualiza a janela no Streamlit
                    frame_window.image(image, channels="RGB", use_container_width=True)

                cap.release()
                pose.close()
                progress_bar.empty()
                
                ## Limpar arquivo temporário
                try:
                    os.unlink(video_path)
                except:
                    pass

                ## Análise Estatística dos Dados de Movimento
                if len(angulos_joelho) > 0:
                    st.markdown("---")
                    st.subheader("📈 Dados Biomecânicos Extraídos")
                    
                    min_ang = min(angulos_joelho)
                    max_ang = max(angulos_joelho)
                    media_ang = np.mean(angulos_joelho)
                    
                    col_a1, col_a2, col_a3 = st.columns(3)
                    col_a1.metric("Ângulo Mínimo (Profundidade)", f"{min_ang:.1f}°")
                    col_a2.metric("Ângulo Máximo", f"{max_ang:.1f}°")
                    col_a3.metric("Ângulo Médio", f"{media_ang:.1f}°")
                    
                    if min_ang <= 90.0:
                        st.success("✅ **Profundidade Validada:** O agachamento quebrou a paralela (ângulo do joelho ≤ 90°).")
                    else:
                        st.warning("⚠️ **Atenção:** O agachamento não quebrou a paralela (ângulo do joelho > 90°).")
                    
                    ## Gráfico de evolução dos ângulos
                    st.line_chart(angulos_joelho)
                else:
                    st.warning("⚠️ Nenhum dado de movimento foi detectado no vídeo.")

## -----------------------------------------------------------------------------
## MÓDULO 3: TIMER INTERATIVO
## -----------------------------------------------------------------------------
elif opcao == "Timer Interativo":
    st.header("⏱️ Controlo de Tempo e Rounds")
    st.caption("Timer para acompanhamento dos treinos.")

    tipo_timer = st.selectbox("Escolha o Formato:", ["AMRAP", "EMOM", "For Time"], key="timer_type")
    minutos = st.number_input("Duração (Minutos):", min_value=1, max_value=60, value=10, key="timer_mins")
    
    st.subheader(f"Formato Selecionado: {tipo_timer} - {minutos} min")
    st.info("Utilize este módulo no monitor para controle do WOD.")
