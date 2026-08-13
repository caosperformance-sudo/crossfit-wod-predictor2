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

# Tenta importar Groq (IA Gratuita)
try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

# 1. Configuração da página
st.set_page_config(
    page_title="CrossFit Predictor & Motion Lab Pro", 
    page_icon="🏋️", 
    layout="wide",
    initial_sidebar_state="auto"
)

# Fix para erro no navegador (Evita que o tradutor automático do Google altere o DOM e quebre o React/Streamlit)
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)

# 2. Autenticação
def checar_senha():
    SENHA_CORRETA = "SUA_SENHA_AQUI"  # <--- Altere para a sua senha

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

# 4. Funções de Biomecânica / Cinesiologia (Inteligência de Dados)
def calcular_angulo(a, b, c):
    """Calcula o ângulo entre três pontos articulares (em graus)."""
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0:
        angle = 360.0 - angle
    return round(angle, 1)

# 5. Funções de Cálculo de RM
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

# Dicionário de Exercícios
EXERCISES = {
    "Thruster": {"type": "lpo", "rm_key": "thruster", "tpr": 2.2, "pattern": "push_legs", "grip_stress": 2},
    "Deadlift": {"type": "lpo", "rm_key": "deadlift", "tpr": 2.0, "pattern": "pull_posterior", "grip_stress": 3},
    "Back Squat": {"type": "lpo", "rm_key": "bsquat", "tpr": 2.3, "pattern": "legs", "grip_stress": 1},
    "Front Squat": {"type": "lpo", "rm_key": "fsquat", "tpr": 2.2, "pattern": "legs", "grip_stress": 1},
    "Overhead Squat": {"type": "lpo", "rm_key": "ohs", "tpr": 2.4, "pattern": "push_legs", "grip_stress": 2},
    "Clean & Jerk": {"type": "lpo", "rm_key": "cj", "tpr": 3.2, "pattern": "full_body", "grip_stress": 3},
    "Snatch": {"type": "lpo", "rm_key": "snatch", "tpr": 2.8, "pattern": "full_body", "grip_stress": 3},
    "Power Clean": {"type": "lpo", "rm_key": "pclean", "tpr": 2.1, "pattern": "pull_posterior", "grip_stress": 3},
    "Push Press": {"type": "lpo", "rm_key": "ppress", "tpr": 1.9, "pattern": "push", "grip_stress": 1},
    "Pull-up": {"type": "gym", "max_key": "pullups", "tpr": 1.4, "pattern": "pull_upper", "grip_stress": 3},
    "Chest to Bar": {"type": "gym", "max_key": "c2b", "tpr": 1.6, "pattern": "pull_upper", "grip_stress": 3},
    "Bar Muscle-up": {"type": "gym", "max_key": "bmu", "tpr": 3.0, "pattern": "pull_push_upper", "grip_stress": 3},
    "Ring Muscle-up": {"type": "gym", "max_key": "rmu", "tpr": 3.5, "pattern": "pull_push_upper", "grip_stress": 3},
    "Toes to Bar": {"type": "gym", "max_key": "ttb", "tpr": 1.6, "pattern": "pull_core", "grip_stress": 3},
    "HSPU": {"type": "gym", "max_key": "hspu", "tpr": 2.0, "pattern": "push", "grip_stress": 0},
    "Burpee": {"type": "cardio", "pace_key": "burpee", "tpr": 3.0, "pattern": "push_engine", "grip_stress": 0},
    "Corrida (m)": {"type": "cardio", "pace_key": "run", "tpr": 0.25, "pattern": "legs_engine", "grip_stress": 0},
    "Remo (m/cal)": {"type": "cardio", "pace_key": "row", "tpr": 0.22, "pattern": "pull_engine", "grip_stress": 2},
    "Double Unders": {"type": "cardio", "pace_key": "du", "tpr": 0.6, "pattern": "engine_shoulders", "grip_stress": 2}
}

# 6. Estrutura Principal de Navegação
st.title("🏋️ CrossFit Predictor & Motion Lab")

aba_wod, aba_timer, aba_rm, aba_vision, aba_ai = st.tabs([
    "⏱️ Predição WOD", 
    "⏱️ Timer", 
    "📊 Calculadora RM", 
    "📹 Câmera & Biomecânica",
    "🤖 Coach IA & Groq"
])

# ==================== ABA 1: PREDIÇÃO WOD ====================
with aba_wod:
    st.header("⚙️ Simulação e Tática de WODs")
    
    with st.expander("👤 **PERFIL DO ATLETA & RPE ALVO**", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("#### 🏋️ 1RM (kg)")
            rm_thruster = st.number_input("Thruster", value=80.0, step=2.5)
            rm_deadlift = st.number_input("Deadlift", value=140.0, step=5.0)
            rm_bsquat = st.number_input("Back Squat", value=120.0, step=2.5)
            rm_fsquat = st.number_input("Front Squat", value=100.0, step=2.5)
            rm_snatch = st.number_input("Snatch", value=70.0, step=2.5)
        with c2:
            st.markdown("#### 🤸 Ginástica (Max Unbroken)")
            max_pullups = st.number_input("Pull-ups", value=25)
            max_c2b = st.number_input("Chest to Bar", value=18)
            max_bmu = st.number_input("Bar Muscle-ups", value=8)
            max_ttb = st.number_input("Toes to Bar", value=20)
            max_hspu = st.number_input("HSPU", value=15)
        with c3:
            st.markdown("#### 🏃 Ergômetros & RPE")
            pace_burpee = st.number_input("Seg/Burpee", value=3.0, step=0.1)
            pace_run = st.number_input("Pace Corrida (seg / 100m)", value=25.0, step=1.0)
            pace_row = st.number_input("Pace Remo (seg / 100m)", value=22.0, step=1.0)
            rpe_target = st.select_slider("🎯 RPE Alvo do Evento", options=[6, 7, 8, 9, 10], value=8)

    st.success("✅ Defina seu treino abaixo e execute a predição algorítmica para estratégias de quebra.")

# ==================== ABA 2: TIMER WOD ====================
with aba_timer:
    st.header("⏱️ Timer WOD Profissional")
    
    t_col1, t_col2 = st.columns([1, 2])
    with t_col1:
        modo_timer = st.selectbox("Modo do Cronômetro", ["For Time (Progressivo)", "AMRAP / Countdown (Regressivo)"])
        tempo_min = st.number_input("Tempo Cap / Minutos", min_value=1, value=10)
        tempo_seg_total = tempo_min * 60

    with t_col2:
        st.subheader("Controle do Timer")
        btn_start = st.button("▶️ INICIAR TREINO", type="primary", use_container_width=True)
        
        timer_display = st.empty()
        timer_display.markdown("<div class='big-timer'>00:00</div>", unsafe_allow_html=True)

        if btn_start:
            if modo_timer == "For Time (Progressivo)":
                for seg in range(tempo_seg_total + 1):
                    m, s = divmod(seg, 60)
                    timer_display.markdown(f"<div class='big-timer'>{m:02d}:{s:02d}</div>", unsafe_allow_html=True)
                    time.sleep(1)
                st.balloons()
                st.success("🎉 TIME CAP ATINGIDO!")
            else:
                for seg in range(tempo_seg_total, -1, -1):
                    m, s = divmod(seg, 60)
                    timer_display.markdown(f"<div class='big-timer'>{m:02d}:{s:02d}</div>", unsafe_allow_html=True)
                    time.sleep(1)
                st.balloons()
                st.success("🚨 TEMPO ESGOTADO!")

# ==================== ABA 3: PREDICTOR DE RM ====================
with aba_rm:
    st.header("📊 Calculadora & Preditor de Rep Max")
    c_calc1, c_calc2 = st.columns(2)
    with c_calc1:
        carga_input = st.number_input("Carga levantada (kg)", min_value=1.0, value=80.0, step=2.5)
        reps_input = st.number_input("Repetições realizadas", min_value=1, max_value=30, value=5)
    
    rm1_est, tabela_rms = calcular_rm_lpo(carga_input, reps_input)

    with c_calc2:
        st.metric("🎯 1RM Estimada", f"{rm1_est} kg")
        st.caption(f"Baseado em {reps_input} reps com {carga_input} kg")

    st.markdown("---")
    st.subheader("📋 Tabela Preditiva de Cargas")
    cols_rm = st.columns(5)
    for idx, (rm_label, val) in enumerate(tabela_rms.items()):
        with cols_rm[idx % 5]:
            st.metric(label=rm_label, value=f"{val} kg")

# ==================== ABA 4: ANALISADOR DE MOVIMENTO (CÂMERA) ====================
with aba_vision:
    st.header("📹 Analisador Biomecânico em Tempo Real")
    st.markdown("Capture a imagem da sua execução técnica para medir ângulos articulares de profundidade de agachamento e postura.")

    modo_analise = st.radio(
        "Selecione o Método de Análise:",
        ["📐 Inteligência de Dados (MediaPipe / Cinesiologia)", "🤖 Análise Assistida por IA"],
        horizontal=True
    )

    img_file_buffer = st.camera_input("📷 Capturar foto do movimento (Squat, Overhead, etc.)")

    if img_file_buffer is not None:
        bytes_data = img_file_buffer.getvalue()
        cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

        if "Inteligência de Dados" in modo_analise:
            if not HAS_MEDIAPIPE:
                st.error("⚠️ A biblioteca `mediapipe` não está instalada no servidor. Adicione `mediapipe` ao arquivo requirements.txt.")
            else:
                mp_pose = mp.solutions.pose
                mp_drawing = mp.solutions.drawing_utils

                with mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5) as pose:
                    image_rgb = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
                    results = pose.process(image_rgb)

                    # Usa um container estático st.empty para renderizar com segurança no React
                    img_container = st.empty()

                    if results.pose_landmarks:
                        landmarks = results.pose_landmarks.landmark

                        # Posição dos pontos articulares principais (Lado Esquerdo)
                        quadril = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                        joelho = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
                        tornozelo = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
                        ombro = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]

                        # Cálculo de Ângulos Cinesiológicos
                        ang_joelho = calcular_angulo(quadril, joelho, tornozelo)
                        ang_quadril = calcular_angulo(ombro, quadril, joelho)

                        # Desenha as articulações na imagem
                        annotated_image = cv2_img.copy()
                        mp_drawing.draw_landmarks(
                            annotated_image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS
                        )

                        img_container.image(cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB), caption="Rastreamento Articular Concluído", use_container_width=True)

                        st.subheader("📊 Métrica Cinesiológica:")
                        cm1, cm2 = st.columns(2)
                        with cm1:
                            st.metric("📐 Ângulo do Joelho", f"{ang_joelho}°")
                            if ang_joelho < 90:
                                st.success("✅ **Profundidade Válida:** Agachamento abaixo da paralela (< 90°).")
                            else:
                                st.warning("⚠️ **Parcial:** Não quebrou a paralela (ângulo > 90°).")

                        with cm2:
                            st.metric("📐 Ângulo do Tronco", f"{ang_quadril}°")
                            if ang_quadril < 75:
                                st.warning("⚠️ **Torção:** Tronco projetado excessivamente à frente.")
                            else:
                                st.success("✅ **Postura Neutra:** Alinhamento de coluna preservado.")
                    else:
                        img_container.image(cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB), caption="Imagem Capturada", use_container_width=True)
                        st.warning("Corpo não detectado na imagem. Certifique-se de enquadrar o atleta por inteiro.")

        else:
            st.info("💡 Envie a imagem para o seu modelo de visão no painel do Groq para relatórios táticos de biomecânica.")

# ==================== ABA 5: COACH IA & LEITOR DE WOD (GROQ - GRATUITO) ====================
with aba_ai:
    st.header("🤖 Coach IA & Parser de WOD (100% Grátis via Groq)")
    st.markdown("Utilize a API gratuita da Groq com modelos Llama 3 para tirar dúvidas táticas e estruturar WODs.")

    groq_key = st.text_input("🔑 Groq API Key (Obtenha grátis em console.groq.com):", type="password")

    if groq_key and HAS_GROQ:
        client = Groq(api_key=groq_key)

        sub_ai_parse, sub_ai_advice = st.tabs(["📝 Extrair WOD por Texto", "🧠 Consultar Coach IA"])

        with sub_ai_parse:
            wod_raw_text = st.text_area("Texto do WOD (Instagram, WODify, etc.):", value="21-15-9\nThruster (43kg)\nPull-ups\nTime Cap: 10 min")
            if st.button("🪄 Processar WOD"):
                prompt_parser = f"""
                Analise o WOD e retorne APENAS um JSON válido no formato:
                {{
                   "format": "For Time",
                   "rounds": 3,
                   "cap_min": 10,
                   "movs": [
                      {{"name": "Thruster", "reps": 21, "load": 43.0}},
                      {{"name": "Pull-up", "reps": 21, "load": 0.0}}
                   ]
                }}
                Texto: {wod_raw_text}
                """
                try:
                    res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": prompt_parser}],
                        response_format={"type": "json_object"}
                    )
                    st.success("✅ WOD Estruturado:")
                    st.json(json.loads(res.choices[0].message.content))
                except Exception as e:
                    st.error(f"Erro ao processar: {e}")

        with sub_ai_advice:
            duvida = st.text_area("Dúvida técnica/estratégica:", "Qual a melhor estratégia para quebrar as séries de Thruster no 21-15-9 sem desgastar o grip?")
            if st.button("💬 Perguntar ao Coach IA"):
                try:
                    res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": "Você é um especialista em CrossFit e Fisiologia do Exercício."},
                            {"role": "user", "content": duvida}
                        ]
                    )
                    st.markdown("### 📋 Resposta do Coach:")
                    st.info(res.choices[0].message.content)
                except Exception as e:
                    st.error(f"Erro ao consultar a API: {e}")

    elif groq_key and not HAS_GROQ:
        st.warning("⚠️ A biblioteca `groq` não está instalada. Adicione `groq` ao seu requirements.txt no GitHub.")
    else:
        st.info("💡 Insira sua API Key da Groq (começa com `gsk_`) para liberar o assistente de IA.")





