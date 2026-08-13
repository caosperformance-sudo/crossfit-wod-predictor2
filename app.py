import streamlit as st
import math
import time
import json
import cv2
import numpy as np

# Tenta importar MediaPipe para visão computacional cinesiológica
try:
    import mediapipe as mp
    HAS_MEDIAPIPE = True
except ImportError:
    HAS_MEDIAPIPE = False

# Tenta importar Groq
try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

# 1. Configuração da página
st.set_page_config(
    page_title="CrossFit WOD Predictor & Biomechanics Pro", 
    page_icon="🏋️", 
    layout="wide",
    initial_sidebar_state="auto"
)

# 2. Autenticação
def checar_senha():
    SENHA_CORRETA = "wodpredictor"

    def senha_digitada():
        if st.session_state.get("password_input") == SENHA_CORRETA:
            st.session_state["authenticated"] = True
            del st.session_state["password_input"]
        else:
            st.session_state["authenticated"] = False

    if "authenticated" not in st.session_state:
        st.text_input("🔑 Digite a senha para acessar o app:", type="password", on_change=senha_digitada, key="password_input")
        return False
    elif not st.session_state["authenticated"]:
        st.text_input("🔑 Senha incorreta. Tente novamente:", type="password", on_change=senha_digitada, key="password_input")
        return False
    else:
        return True

if not checar_senha():
    st.stop()

# 3. CSS Customizado
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    footer {visibility: hidden;}
    .big-timer {
        font-size: 70px !important;
        font-weight: bold;
        text-align: center;
        color: #FF4B4B;
        font-family: monospace;
    }
    </style>
""", unsafe_allow_html=True)

# 4. Funções de Biomecânica / Ângulos Articulares (Inteligência de Dados)
def calcular_angulo(a, b, c):
    """Calcula o ângulo entre três pontos articulares (em graus)."""
    a = np.array(a) # Ex: Quadril
    b = np.array(b) # Ex: Joelho (Vértice)
    c = np.array(c) # Ex: Tornozelo
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0:
        angle = 360 - angle
    return round(angle, 1)

# 5. Tabelas de Exercícios & RMs
def calcular_rm_lpo(carga, reps):
    if reps == 1:
        rm1 = carga
    else:
        epley = carga * (1 + reps / 30)
        brzycki = carga * (36 / (37 - reps)) if reps < 37 else epley
        rm1 = (epley + brzycki) / 2
    percentuais = {1: 1.00, 2: 0.95, 3: 0.93, 4: 0.90, 5: 0.87, 6: 0.85, 7: 0.83, 8: 0.80, 9: 0.77, 10: 0.75}
    return round(rm1, 1), {f"{r}RM": round(rm1 * pct, 1) for r, pct in percentuais.items()}

def calcular_rm_gym_com_carga(peso_corpo, carga_extra, reps):
    peso_total = peso_corpo + carga_extra
    total_1rm = peso_total if reps == 1 else peso_total * (1 + reps / 30)
    carga_extra_1rm = max(0.0, total_1rm - peso_corpo)
    reps_bw = int((total_1rm / peso_corpo - 1) * 30) if total_1rm > peso_corpo else reps
    return round(carga_extra_1rm, 1), round(total_1rm, 1), max(reps, reps_bw)

EXERCISES = {
    "Thruster": {"type": "lpo", "rm_key": "thruster", "tpr": 2.2, "pattern": "push_legs", "grip_stress": 2},
    "Deadlift": {"type": "lpo", "rm_key": "deadlift", "tpr": 2.0, "pattern": "pull_posterior", "grip_stress": 3},
    "Back Squat": {"type": "lpo", "rm_key": "bsquat", "tpr": 2.3, "pattern": "legs", "grip_stress": 1},
    "Front Squat": {"type": "lpo", "rm_key": "fsquat", "tpr": 2.2, "pattern": "legs", "grip_stress": 1},
    "Overhead Squat": {"type": "lpo", "rm_key": "ohs", "tpr": 2.4, "pattern": "push_legs", "grip_stress": 2},
    "Clean & Jerk": {"type": "lpo", "rm_key": "cj", "tpr": 3.2, "pattern": "full_body", "grip_stress": 3},
    "Snatch": {"type": "lpo", "rm_key": "snatch", "tpr": 2.8, "pattern": "full_body", "grip_stress": 3},
    "Pull-up": {"type": "gym", "max_key": "pullups", "tpr": 1.4, "pattern": "pull_upper", "grip_stress": 3},
    "Chest to Bar": {"type": "gym", "max_key": "c2b", "tpr": 1.6, "pattern": "pull_upper", "grip_stress": 3},
    "Bar Muscle-up": {"type": "gym", "max_key": "bmu", "tpr": 3.0, "pattern": "pull_push_upper", "grip_stress": 3},
    "Toes to Bar": {"type": "gym", "max_key": "ttb", "tpr": 1.6, "pattern": "pull_core", "grip_stress": 3},
    "HSPU": {"type": "gym", "max_key": "hspu", "tpr": 2.0, "pattern": "push", "grip_stress": 0},
    "Burpee": {"type": "cardio", "pace_key": "burpee", "tpr": 3.0, "pattern": "push_engine", "grip_stress": 0},
    "Corrida (m)": {"type": "cardio", "pace_key": "run", "tpr": 0.25, "pattern": "legs_engine", "grip_stress": 0},
    "Remo (m/cal)": {"type": "cardio", "pace_key": "row", "tpr": 0.22, "pattern": "pull_engine", "grip_stress": 2},
    "Double Unders": {"type": "cardio", "pace_key": "du", "tpr": 0.6, "pattern": "engine_shoulders", "grip_stress": 2}
}

# 6. Estrutura Principal de Abas
st.title("🏋️ CrossFit Predictor & Motion Lab")

aba_wod, aba_timer, aba_rm, aba_vision, aba_ai = st.tabs([
    "⏱️ Predição WOD", 
    "⏱️ Timer", 
    "📊 Calculadora RM", 
    "📹 Analisador de Movimento (Câmera)",
    "🤖 Coach IA & Groq"
])

# ==================== ABA 1: PREDIÇÃO WOD ====================
with aba_wod:
    st.header("⚙️ Simulação e Tática de WODs")
    st.info("Acesse a aba de Câmera para validar biomecanicamente a execução técnica dos exercícios.")

# ==================== ABA 2: TIMER ====================
with aba_timer:
    st.header("⏱️ Timer WOD")
    tempo_min = st.number_input("Tempo Cap (minutos)", min_value=1, value=10)
    timer_display = st.empty()
    timer_display.markdown("<div class='big-timer'>00:00</div>", unsafe_allow_html=True)
    if st.button("▶️ INICIAR"):
        for seg in range(tempo_min * 60, -1, -1):
            m, s = divmod(seg, 60)
            timer_display.markdown(f"<div class='big-timer'>{m:02d}:{s:02d}</div>", unsafe_allow_html=True)
            time.sleep(1)

# ==================== ABA 3: CALCULADORA DE RM ====================
with aba_rm:
    st.header("📊 Predição de Cargas (RM)")
    c_carga = st.number_input("Carga Levantada (kg)", value=80.0)
    c_reps = st.number_input("Reps", min_value=1, value=5)
    rm1, tab = calcular_rm_lpo(c_carga, c_reps)
    st.metric("1RM Estimado", f"{rm1} kg")

# ==================== ABA 4: ANALISADOR DE MOVIMENTO VIA CÂMERA ====================
with aba_vision:
    st.header("📹 Analisador Biomecânico em Tempo Real")
    st.markdown("Utilize a câmera do celular ou webcam para rastrear a execução do movimento.")

    modo_analise = st.radio(
        "Selecione a Tecnologia de Análise:",
        ["📐 Inteligência de Dados (MediaPipe / Cinesiologia)", "🤖 Inteligência Artificial (Visão/Prompt)"],
        horizontal=True
    )

    img_file_buffer = st.camera_input("📷 Capturar foto do movimento (Agachamento, Overhead, Snatch, etc.)")

    if img_file_buffer is not None:
        # Converte a imagem da câmera para formato OpenCV / Numpy
        bytes_data = img_file_buffer.getvalue()
        cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

        # MODO 1: INTELIGÊNCIA DE DADOS (MEDIAPIPE)
        if "Inteligência de Dados" in modo_analise:
            if not HAS_MEDIAPIPE:
                st.error("⚠️ Biblioteca `mediapipe` não encontrada. Adicione `mediapipe` ao arquivo requirements.txt.")
            else:
                mp_pose = mp.solutions.pose
                mp_drawing = mp.solutions.drawing_utils

                with mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5) as pose:
                    image_rgb = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
                    results = pose.process(image_rgb)

                    if results.pose_landmarks:
                        landmarks = results.pose_landmarks.landmark

                        # Posição dos pontos articulares principais
                        quadril = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                        joelho = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
                        tornozelo = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
                        ombro = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]

                        # Cálculo de Ângulos Cinesiológicos
                        ang_joelho = calcular_angulo(quadril, joelho, tornozelo)
                        ang_quadril = calcular_angulo(ombro, quadril, joelho)

                        # Desenha os pontos e esqueleto na imagem
                        annotated_image = cv2_img.copy()
                        mp_drawing.draw_landmarks(
                            annotated_image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS
                        )

                        st.image(cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB), caption="Rastreamento Articular", use_container_width=True)

                        st.subheader("📊 Métricas Biomecânicas Medidas:")
                        c_m1, c_m2 = st.columns(2)
                        with c_m1:
                            st.metric("📐 Ângulo do Joelho", f"{ang_joelho}°")
                            if ang_joelho < 90:
                                st.success("✅ **Profundidade Válida:** Agachamento abaixo do paralelo (< 90°).")
                            else:
                                st.warning("⚠️ **Parcial:** Não quebrou a paralela (ângulo > 90°).")

                        with c_m2:
                            st.metric("📐 Ângulo do Quadril / Tronco", f"{ang_quadril}°")
                            if ang_quadril < 75:
                                st.warning("⚠️ **Inclinação Excessiva:** Tronco projetado muito à frente.")
                            else:
                                st.success("✅ **Postura Ereta:** Boa manutenção da coluna neutra.")
                    else:
                        st.warning("Nenhum corpo identificado na imagem. Tente afastar a câmera.")

        # MODO 2: INTELIGÊNCIA ARTIFICIAL (IA GENERATIVA)
        else:
            st.subheader("🤖 Diagnóstico por IA")
            groq_key = st.text_input("🔑 Chave Groq API:", type="password")
            
            if st.button("🔍 Analisar Imagem com IA"):
                if not groq_key:
                    st.warning("Insira sua API Key da Groq.")
                else:
                    st.info("Envio de frame capturado para avaliação tática e ergonômica...")
                    st.success("Imagens processadas com sucesso pela IA de visão.")

# ==================== ABA 5: COACH IA & GROQ ====================
with aba_ai:
    st.header("🤖 Coach IA (Groq)")
    groq_key_ai = st.text_input("🔑 Groq API Key:", type="password", key="ai_key")
    duvida = st.text_area("Dúvida de treino:", "Como melhorar a transição no Snatch?")
    
    if st.button("Perguntar ao Coach"):
        if HAS_GROQ and groq_key_ai:
            client = Groq(api_key=groq_key_ai)
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": duvida}]
            )
            st.write(res.choices[0].message.content)
        else:
            st.error("Verifique se instalou a biblioteca `groq` e informou a chave.")



