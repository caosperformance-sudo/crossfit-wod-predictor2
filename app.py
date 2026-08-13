import streamlit as st
import cv2
import mediapipe as mp
import numpy as np

# Configuração da Página
st.set_page_config(
    page_title="CrossFit WOD & Movement Analyzer",
    page_icon="🏋️‍♂️",
    layout="wide"
)

# Título Principal
st.title("🏋️‍♂️ CrossFit Performance & Movement Analytics")
st.markdown("Plataforma de análise de dados de desempenho, simulação de WODs e biometria de movimento.")

# Navegação Lateral
st.sidebar.header("Navegação")
opcao = st.sidebar.radio(
    "Selecione o Módulo:",
    ["Simulador de WODs & Cargas", "Análise Biomecânica de Movimento", "Timer Interativo"]
)

# -----------------------------------------------------------------------------
# MÓDULO 1: SIMULADOR DE WODS & CARGAS (Inteligência de Dados / Modelos Matemáticos)
# -----------------------------------------------------------------------------
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
    
    # Cálculos de Inteligência de Dados / Métricas
    pct_squat = (carga_wod / back_squat_1rm) * 100
    pct_deadlift = (carga_wod / deadlift_1rm) * 100

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Intensidade Relativa (Squat)", f"{pct_squat:.1f}% de 1RM")
    col_m2.metric("Intensidade Relativa (Deadlift)", f"{pct_deadlift:.1f}% de 1RM")
    
    # Classificação de Estratégia de Quebra por Faixa de Intensidade
    if pct_squat < 50:
        estrategia = "Alta RDJ (Rendimento de Velocidade). Sugestão: Sets grandes (Ex: 21-15-9 Ininterrupto)."
    elif 50 <= pct_squat < 75:
        estrategia = "Carga Moderada. Sugestão: Quebras planejadas com descansos curtos (Ex: 3 a 4 sets regulares)."
    else:
        estrategia = "Carga Alta / Limiar de Força. Sugestão: Singlos ou séries curtas de 2 a 3 reps para conter lactato."

    col_m3.info(f"**Estratégia Recomendada:**\n\n{estrategia}")

# -----------------------------------------------------------------------------
# MÓDULO 2: ANÁLISE BIOMECÂNICA DE MOVIMENTO (Visão Computacional Local)
# -----------------------------------------------------------------------------
elif opcao == "Análise Biomecânica de Movimento":
    st.header("📹 Análise Biomecânica via Visão Computacional")
    st.caption("Identificação de pontos articulares e medição de ângulos em tempo real com MediaPipe.")

    # Função Auxiliar para Calcular Ângulo Articular
    def calcular_angulo(a, b, c):
        a = np.array(a) # Quadril
        b = np.array(b) # Joelho
        c = np.array(c) # Tornozelo
        
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angulo = np.abs(radians*180.0/np.pi)
        
        if angulo > 180.0:
            angulo = 360 - angulo
            
        return angulo

    arquivo_video = st.file_uploader("Envie o vídeo do seu movimento (Agachamento, Clean, Snatch):", type=["mp4", "mov", "avi"])

    if arquivo_video is not None:
        # Salva o arquivo temporariamente
        with open("temp_video.mp4", "wb") as f:
            f.write(arquivo_video.read())

        st.success("Vídeo carregado com sucesso! Processando biometria...")

        # Setup MediaPipe Pose
        mp_pose = mp.solutions.pose
        mp_drawing = mp.solutions.drawing_utils
        pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

        cap = cv2.VideoCapture("temp_video.mp4")
        
        # Container estático no Streamlit para evitar erros no React DOM
        frame_window = st.empty()

        angulos_joelho = []

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Converte cores BGR para RGB
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image)

            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark

                # Posições do Quadril, Joelho e Tornozelo Esquerdos
                hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
                ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]

                # Ângulo do Joelho
                angulo_j = calcular_angulo(hip, knee, ankle)
                angulos_joelho.append(angulo_j)

                # Desenha Esqueleto na Imagem
                mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

                # Escreve o Ângulo na Tela do Vídeo
                cv2.putText(image, f"Joelho: {int(angulo_j)} deg", 
                            tuple(np.multiply(knee, [image.shape[1], image.shape[0]]).astype(int)), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

            # Atualiza a janela no Streamlit
            frame_window.image(image, channels="RGB", use_column_width=True)

        cap.release()
        pose.close()

        # Análise Estatística dos Dados de Movimento
        if len(angulos_joelho) > 0:
            st.markdown("---")
            st.subheader("📈 Dados Biomecânicos Extraídos")
            
            min_ang = min(angulos_joelho)
            st.write(f"**Menor ângulo de joelho atingido (Profundidade Máxima):** {min_ang:.1f}°")
            
            if min_ang <= 90.0:
                st.success("✅ **Profundidade Validada:** O agachamento quebrou a paralela (ângulo do joelho ≤ 90°).")
            else:
                st.warning("⚠️ **Atenção:** O agachamento não quebrou a paralela (ângulo do joelho > 90°).")

# -----------------------------------------------------------------------------
# MÓDULO 3: TIMER INTERATIVO
# -----------------------------------------------------------------------------
elif opcao == "Timer Interativo":
    st.header("⏱️ Controlo de Tempo e Rounds")
    st.caption("Timer para acompanhamento dos treinos.")

    tipo_timer = st.selectbox("Escolha o Formato:", ["AMRAP", "EMOM", "For Time"], key="timer_type")
    
    minutos = st.number_input("Duração (Minutos):", min_value=1, max_value=60, value=10, key="timer_mins")
    
    st.subheader(f"Formato Selecionado: {tipo_timer} - {minutos} min")
    st.info("Utilize este módulo no monitor para controle do WOD.")






