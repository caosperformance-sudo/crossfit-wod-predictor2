import streamlit as st
import math
import time
import json

# Tenta importar a biblioteca da OpenAI (opcional)
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# 1. Configuração da página
st.set_page_config(
    page_title="CrossFit WOD Predictor PRO & AI Coach", 
    page_icon="🏋️", 
    layout="wide",
    initial_sidebar_state="auto"
)

# 2. Lógica de Autenticação
def checar_senha():
    SENHA_CORRETA = "wodpredict"  # <--- Altere para a sua senha

    def senha_digitada():
        if st.session_state["password_input"] == SENHA_CORRETA:
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
custom_css = """
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
"""
st.markdown(custom_css, unsafe_allow_html=True)

# 4. Funções Utilitárias de RM
def calcular_rm_lpo(carga, reps):
    if reps == 1:
        rm1 = carga
    else:
        epley = carga * (1 + reps / 30)
        brzycki = carga * (36 / (37 - reps)) if reps < 37 else epley
        rm1 = (epley + brzycki) / 2

    percentuais = {
        1: 1.00, 2: 0.95, 3: 0.93, 4: 0.90, 5: 0.87,
        6: 0.85, 7: 0.83, 8: 0.80, 9: 0.77, 10: 0.75
    }
    tabela = {f"{r}RM": round(rm1 * pct, 1) for r, pct in percentuais.items()}
    return round(rm1, 1), tabela

def calcular_rm_gym_com_carga(peso_corpo, carga_extra, reps):
    peso_total = peso_corpo + carga_extra
    total_1rm = peso_total if reps == 1 else peso_total * (1 + reps / 30)
    carga_extra_1rm = max(0.0, total_1rm - peso_corpo)
    reps_bw = int((total_1rm / peso_corpo - 1) * 30) if total_1rm > peso_corpo else reps
    return round(carga_extra_1rm, 1), round(total_1rm, 1), max(reps, reps_bw)

# 5. Dicionário de Exercícios
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
    "Dumbbell Snatch": {"type": "lpo", "rm_key": "snatch", "tpr": 2.2, "pattern": "full_body", "grip_stress": 2},
    "Pull-up": {"type": "gym", "max_key": "pullups", "tpr": 1.4, "pattern": "pull_upper", "grip_stress": 3},
    "Chest to Bar": {"type": "gym", "max_key": "c2b", "tpr": 1.6, "pattern": "pull_upper", "grip_stress": 3},
    "Bar Muscle-up": {"type": "gym", "max_key": "bmu", "tpr": 3.0, "pattern": "pull_push_upper", "grip_stress": 3},
    "Ring Muscle-up": {"type": "gym", "max_key": "rmu", "tpr": 3.5, "pattern": "pull_push_upper", "grip_stress": 3},
    "Toes to Bar": {"type": "gym", "max_key": "ttb", "tpr": 1.6, "pattern": "pull_core", "grip_stress": 3},
    "HSPU": {"type": "gym", "max_key": "hspu", "tpr": 2.0, "pattern": "push", "grip_stress": 0},
    "Handstand Walk (m)": {"type": "gym", "max_key": "hsw", "tpr": 0.8, "pattern": "push_shoulders", "grip_stress": 1},
    "Rope Climb": {"type": "gym", "max_key": "rope", "tpr": 7.0, "pattern": "pull_upper", "grip_stress": 4},
    "Pistols": {"type": "gym", "max_key": "pistols", "tpr": 2.0, "pattern": "legs", "grip_stress": 0},
    "Burpee": {"type": "cardio", "pace_key": "burpee", "tpr": 3.0, "pattern": "push_engine", "grip_stress": 0},
    "Corrida (m)": {"type": "cardio", "pace_key": "run", "tpr": 0.25, "pattern": "legs_engine", "grip_stress": 0},
    "Remo (m/cal)": {"type": "cardio", "pace_key": "row", "tpr": 0.22, "pattern": "pull_engine", "grip_stress": 2},
    "Echo / BikeErg (cal)": {"type": "cardio", "pace_key": "bike", "tpr": 1.8, "pattern": "legs_engine", "grip_stress": 0},
    "Double Unders": {"type": "cardio", "pace_key": "du", "tpr": 0.6, "pattern": "engine_shoulders", "grip_stress": 2}
}

# 6. Estrutura Principal
st.title("🏋️ CrossFit WOD Predictor PRO & Arena Engine")

aba_wod, aba_timer, aba_rm, aba_ai = st.tabs([
    "⏱️ Predição (Algoritmo Tradicional)", 
    "⏱️ Timer WOD Interativo", 
    "📊 Preditor de RM", 
    "🤖 Coach IA & Leitor de WOD (Opcional)"
])

# ==================== ABA 1: SIMULAÇÃO MULTI-WOD ====================
with aba_wod:
    with st.expander("👤 **PERFIL DO ATLETA & RPE ALVO**", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("#### 🏋️ 1RM (kg)")
            rm_thruster = st.number_input("Thruster", value=80.0, step=2.5)
            rm_deadlift = st.number_input("Deadlift", value=140.0, step=5.0)
            rm_bsquat = st.number_input("Back Squat", value=120.0, step=2.5)
            rm_fsquat = st.number_input("Front Squat", value=100.0, step=2.5)
            rm_ohs = st.number_input("Overhead Squat", value=75.0, step=2.5)
            rm_cj = st.number_input("Clean & Jerk", value=90.0, step=2.5)
            rm_snatch = st.number_input("Snatch", value=70.0, step=2.5)
            rm_pclean = st.number_input("Power Clean", value=85.0, step=2.5)
            rm_ppress = st.number_input("Push Press", value=75.0, step=2.5)
        with c2:
            st.markdown("#### 🤸 Ginástica (Max Unbroken)")
            max_pullups = st.number_input("Pull-ups", value=25)
            max_c2b = st.number_input("Chest to Bar", value=18)
            max_bmu = st.number_input("Bar Muscle-ups", value=8)
            max_rmu = st.number_input("Ring Muscle-ups", value=6)
            max_ttb = st.number_input("Toes to Bar", value=20)
            max_hspu = st.number_input("HSPU", value=15)
            max_hsw = st.number_input("HS Walk (m)", value=15)
            max_rope = st.number_input("Rope Climb", value=4)
            max_pistols = st.number_input("Pistols", value=15)
        with c3:
            st.markdown("#### 🏃 Ergômetros & RPE")
            pace_burpee = st.number_input("Seg/Burpee", value=3.0, step=0.1)
            pace_run = st.number_input("Pace Corrida (seg / 100m)", value=25.0, step=1.0)
            pace_row = st.number_input("Pace Remo (seg / 100m)", value=22.0, step=1.0)
            pace_bike = st.number_input("Pace Bike (seg / 10cal)", value=18.0, step=1.0)
            pace_du = st.number_input("Seg / 10 DU", value=6.0, step=0.5)
            rpe_target = st.select_slider("🎯 RPE Alvo do Evento", options=[6, 7, 8, 9, 10], value=8)

    r_d = {'thruster': rm_thruster, 'deadlift': rm_deadlift, 'bsquat': rm_bsquat, 'fsquat': rm_fsquat, 'ohs': rm_ohs, 'cj': rm_cj, 'snatch': rm_snatch, 'pclean': rm_pclean, 'ppress': rm_ppress}
    m_d = {'pullups': max_pullups, 'c2b': max_c2b, 'bmu': max_bmu, 'rmu': max_rmu, 'ttb': max_ttb, 'hspu': max_hspu, 'hsw': max_hsw, 'rope': max_rope, 'pistols': max_pistols}
    p_d = {'burpee': pace_burpee, 'run': pace_run, 'row': pace_row, 'bike': pace_bike, 'du': pace_du}

    rpe_mult = {6: 1.20, 7: 1.12, 8: 1.05, 9: 1.00, 10: 0.95}[rpe_target]

    num_wods = st.radio("Selecione a Quantidade de WODs na Sessão:", [1, 2, 3], horizontal=True)

    def gerar_estrategia_quebra(reps, sets):
        if sets <= 1:
            return f"**Unbroken** ({reps} reps diretas)"
        base = reps // sets
        rem = reps % sets
        set_list = [base + (1 if k < rem else 0) for k in range(sets)]
        if len(set_list) >= 3 and set_list[0] == set_list[-1]:
            set_list[0] += 1
            set_list[-1] -= 1
        set_str = " - ".join(map(str, set_list))
        return f"Divida em **{sets} sets** (`{set_str}`) *[Front-Loading]*"

    def calc_movimento(name, reps, load, r_d, m_d, p_d, acumulado_fadiga_wod, acumulado_fadiga_sessao):
        info = EXERCISES[name]
        grip_score = info["grip_stress"]
        fator_fadiga = (1 + (acumulado_fadiga_wod * 0.04) + (acumulado_fadiga_sessao * 0.08)) * rpe_mult

        if info["type"] == "lpo":
            pct = load / r_d.get(info["rm_key"], 80.0)
            tpr = info["tpr"] * (1 + (pct**2)) * fator_fadiga
            sets = math.ceil(reps / max(2, int(15 * (1 - pct) / fator_fadiga)))
            rest = (8 + (pct * 14)) * fator_fadiga
        elif info["type"] == "gym":
            tpr = info["tpr"] * fator_fadiga
            sets = math.ceil(reps / max(2, int(m_d.get(info["max_key"], 15) * 0.40 / fator_fadiga)))
            rest = 7.0 * fator_fadiga
        else:
            tpr = (p_d.get(info["pace_key"], 3.0) / (100 if "m" in name else 10)) * fator_fadiga
            sets, rest = 1, 0.0

        tempo_total = (reps * tpr) + ((sets - 1) * rest)
        return tempo_total, sets, rest, info["pattern"], grip_score

    wods_data = []
    fadiga_sessao_cumulativa = 0.0

    for w_idx in range(num_wods):
        st.divider()
        st.header(f"🏋️ WOD {w_idx+1}")
        
        c_fmt, c_cfg, c_rest = st.columns([1, 1, 1])
        with c_fmt:
            w_format = st.selectbox(f"Formato WOD {w_idx+1}", ["For Time", "AMRAP"], key=f"fmt_{w_idx}")
        with c_cfg:
            if w_format == "For Time":
                rounds = st.number_input(f"Rodadas WOD {w_idx+1}", min_value=1, value=3, key=f"rnd_{w_idx}")
                cap_min = st.number_input(f"Time Cap (min) WOD {w_idx+1}", min_value=1, value=12, key=f"cap_{w_idx}")
                amrap_min = 0
            else:
                amrap_min = st.number_input(f"Duração AMRAP (min) WOD {w_idx+1}", min_value=1, value=12, key=f"amrap_{w_idx}")
                cap_min = amrap_min
                rounds = 1

        with c_rest:
            if w_idx < num_wods - 1:
                rest_between_wods = st.number_input(f"Intervalo pós WOD {w_idx+1} (min)", min_value=1, value=15, key=f"rest_between_{w_idx}")
            else:
                rest_between_wods = 0

        n_movs = st.slider(f"Qtd de Movimentos WOD {w_idx+1}", 1, 10, 3, key=f"n_mov_{w_idx}")
        movs = []
        cols = st.columns(min(n_movs, 5))
        for m_i in range(n_movs):
            col_target = cols[m_i % 5]
            with col_target:
                ex_name = st.selectbox(f"Mov {m_i+1}", sorted(list(EXERCISES.keys())), key=f"w{w_idx}_ex_{m_i}")
                reps = st.number_input(f"Reps Mov {m_i+1}", min_value=1, value=15, key=f"w{w_idx}_rep_{m_i}")
                load = st.number_input(f"Carga (kg)", min_value=0.0, value=40.0, key=f"w{w_idx}_load_{m_i}") if EXERCISES[ex_name]["type"] == "lpo" else 0.0
                movs.append({"name": ex_name, "reps": reps, "load": load})
        
        wods_data.append({
            "format": w_format, 
            "rounds": rounds, 
            "cap_min": cap_min,
            "amrap_min": amrap_min, 
            "movs": movs, 
            "rest_next": rest_between_wods
        })

    if st.button("🚀 CALCULAR ESTRATÉGIA COMPLETA DE SESSÃO", type="primary", use_container_width=True):
        st.divider()
        st.subheader("📊 ANÁLISE INTEGRADA DE DESEMPENHO E TIME CAP")

        for w_i, w_data in enumerate(wods_data):
            st.markdown(f"### 🏋️ Resultados e Tática: WOD {w_i+1}")
            
            rt_round = 0.0
            grip_total_wod = 0
            patterns = []
            breakdowns = []
            fadiga_wod_cumulativa = 0.0

            for m_i, m in enumerate(w_data["movs"]):
                tempo, sets, rest, pattern, grip = calc_movimento(
                    m["name"], m["reps"], m["load"], r_d, m_d, p_d, 
                    fadiga_wod_cumulativa, fadiga_sessao_cumulativa
                )
                
                penalty = (m_i > 0 and (pattern in patterns[-1] or patterns[-1] in pattern))
                if penalty:
                    tempo *= 1.20
                    rest += 5.0

                rt_round += tempo
                grip_total_wod += grip * m["reps"]
                patterns.append(pattern)
                fadiga_wod_cumulativa += 0.5
                
                breakdowns.append({
                    "name": m["name"],
                    "reps": m["reps"],
                    "sets": sets,
                    "rest": rest,
                    "penalty": penalty
                })

            tempo_transicao = len(w_data["movs"]) * 4.0
            rt_round += tempo_transicao
            tempo_total_bruto = rt_round * w_data["rounds"]
            cap_segundos = w_data["cap_min"] * 60.0
            total_reps_alvo = sum(m['reps'] for m in w_data['movs']) * w_data['rounds']

            col_res1, col_res2, col_res3 = st.columns(3)
            
            if w_data["format"] == "For Time":
                if tempo_total_bruto <= cap_segundos:
                    m_tot, s_tot = int(tempo_total_bruto // 60), int(tempo_total_bruto % 60)
                    with col_res1:
                        st.metric("⏱️ Tempo Estimado", f"{m_tot}:{s_tot:02d} min")
                    with col_res2:
                        st.metric("✅ Reps Completadas", f"{total_reps_alvo} / {total_reps_alvo}")
                    with col_res3:
                        st.metric("🎯 Reps Restantes (Faltou)", "0 reps", delta="WOD Concluído!", delta_color="normal")
                else:
                    pct_concluido = cap_segundos / tempo_total_bruto
                    reps_completadas = int(total_reps_alvo * pct_concluido)
                    reps_faltantes = total_reps_alvo - reps_completadas
                    
                    with col_res1:
                        st.metric("🚨 Status do Cap", f"CAP + {reps_completadas} reps")
                    with col_res2:
                        st.metric("✅ Total Completado", f"{reps_completadas} reps", delta=f"{int(pct_concluido*100)}% do treino")
                    with col_res3:
                        st.metric("❌ Faltou para Terminar", f"{reps_faltantes} reps", delta=f"-{reps_faltantes} reps", delta_color="inverse")
            
            else: # AMRAP
                reps_por_round = sum(m['reps'] for m in w_data['movs'])
                rnds_completos = int(cap_segundos // rt_round)
                tempo_resto = cap_segundos - (rnds_completos * rt_round)
                reps_extra = int((tempo_resto / rt_round) * reps_por_round)
                
                total_reps_amrap = (rnds_completos * reps_por_round) + reps_extra
                reps_para_proximo_rnd = reps_por_round - reps_extra

                with col_res1:
                    st.metric("🎯 Score Estimado AMRAP", f"{rnds_completos} rnds + {reps_extra} reps")
                with col_res2:
                    st.metric("✅ Total de Reps Feitas", f"{total_reps_amrap} reps")
                with col_res3:
                    st.metric("🏁 Faltou para o Próximo Round", f"{reps_para_proximo_rnd} reps", delta=f"-{reps_para_proximo_rnd} reps", delta_color="inverse")

            # Alertas de Fadiga de Pegada
            st.markdown("---")
            if grip_total_wod > 80:
                st.error("🚨 **ALERTA CRÍTICO DE GRIP FATIGUE:** Alto acúmulo de pegada! Risco alto de travar e deixar mais reps pendentes.")
            elif grip_total_wod > 45:
                st.warning("⚠️ **Grip Moderado:** Desgaste acentuado nos flexores do antebraço.")
            else:
                st.success("✅ **Grip Preservado:** Baixa sobrecarga na pegada.")

            # Detalhamento de Quebra
            with st.expander(f"💡 Ver Plano de Quebra e Pacing do WOD {w_i+1}", expanded=True):
                for b in breakdowns:
                    est_str = gerar_estrategia_quebra(b["reps"], b["sets"])
                    msg = f"**{b['name']}** ({b['reps']} reps): {est_str}. Descanso sugerido: **{int(b['rest'])}s** entre sets."
                    if b["penalty"]:
                        st.warning(f"⚠️ {msg}\n\n*Aviso de Interferência Muscular Adjacente.*")
                    else:
                        st.info(f"✅ {msg}")

            # Efeito do Intervalo pós-WOD
            if w_data["rest_next"] > 0:
                recuperacao = min(1.0, w_data["rest_next"] / 20.0)
                desgaste_retido = 1.5 * (1.0 - (recuperacao * 0.70))
                fadiga_sessao_cumulativa += desgaste_retido
                st.caption(f"☕ **Intervalo de {w_data['rest_next']} min:** Recuperação muscular estimada em **{int(recuperacao*100)}%** antes do próximo WOD.")

# ==================== ABA 2: TIMER WOD INTERATIVO ====================
with aba_timer:
    st.header("⏱️ Timer WOD Profissional")
    
    t_col1, t_col2 = st.columns([1, 2])
    with t_col1:
        modo_timer = st.selectbox("Modo do Cronômetro", ["For Time (Progressivo)", "AMRAP / Countdown (Regressivo)"])
        tempo_min = st.number_input("Tempo Cap / Minutos", min_value=1, value=10)
        tempo_seg_total = tempo_min * 60

    with t_col2:
        st.subheader("Controle do Timer")
        c_b1, c_b2 = st.columns(2)
        btn_start = c_b1.button("▶️ INICIAR TREINO", use_container_width=True, type="primary")
        
        timer_display = st.empty()
        timer_display.markdown(f"<div class='big-timer'>00:00</div>", unsafe_allow_html=True)

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
    sub_lpo, sub_gym = st.tabs(["🏋️ LPO & Barra Olímpica", "🤸 Ginástica & Peso Corporal"])
    
    with sub_lpo:
        st.subheader("Estimativa de 1RM a 10RM (Cargas de LPO)")
        c_calc1, c_calc2 = st.columns(2)
        with c_calc1:
            carga_input = st.number_input("Carga levantada (kg)", min_value=1.0, value=80.0, step=2.5, key="rm_carga_input")
            reps_input = st.number_input("Repetições realizadas", min_value=1, max_value=30, value=5, key="rm_reps_input")
        
        rm1_est, tabela_rms = calcular_rm_lpo(carga_input, reps_input)

        with c_calc2:
            st.metric("🎯 1RM Estimada", f"{rm1_est} kg")
            st.caption(f"Baseado em {reps_input} reps com {carga_input} kg")

        st.markdown("---")
        st.subheader("📋 Tabela Preditiva de Cargas")
        cols_rm = st.columns(5)
        rm_items = list(tabela_rms.items())
        for idx, (rm_label, val) in enumerate(rm_items):
            col_idx = idx % 5
            with cols_rm[col_idx]:
                st.metric(label=rm_label, value=f"{val} kg")

    with sub_gym:
        st.subheader("🤸 Preditor Ginástico (Weighted & Fadiga)")
        modo_gym = st.radio("Escolha o tipo de teste:", ["Com Carga Extra (Weighted)", "Fadiga em Sets Sucessivos (Bodyweight)"], horizontal=True)
        
        if modo_gym == "Com Carga Extra (Weighted)":
            st.caption("Calcule sua 1RM de carga extra em movimentos como Pull-ups, Dips e HSPU com colete/anilha.")
            g1, g2 = st.columns(2)
            with g1:
                peso_atleta = st.number_input("Seu Peso Corporal (kg)", min_value=40.0, value=75.0, step=1.0)
                carga_adicional = st.number_input("Carga Adicional Utilizada (kg)", min_value=0.0, value=15.0, step=2.5)
                reps_gym = st.number_input("Repetições Concluídas", min_value=1, max_value=25, value=3, key="reps_gym_w")
            
            carga_extra_1rm, peso_total_1rm, reps_bw_est = calcular_rm_gym_com_carga(peso_atleta, carga_adicional, reps_gym)
            
            with g2:
                st.metric("🎯 Carga Máxima Adicional (1RM)", f"+{carga_extra_1rm} kg")
                st.metric("🏋️ Peso Total Movido em 1RM", f"{peso_total_1rm} kg")
                st.metric("🔥 Reps Máximas Est. sem Carga (Bodyweight)", f"~{reps_bw_est} reps")
        
        else:
            st.caption("Preveja a queda de repetições acumulada em múltiplas séries unbroken.")
            f1, f2 = st.columns(2)
            with f1:
                max_unbroken = st.number_input("Seu Máximo Unbroken (1 Set)", min_value=1, value=20)
                num_sets_gym = st.number_input("Número de Sets Planejados", min_value=2, max_value=10, value=4)
                descanso_seg = st.number_input("Tempo de Descanso entre Sets (seg)", min_value=10, value=60, step=5)
            
            with f2:
                recuperacao = min(1.0, descanso_seg / 90.0)
                queda_por_set = (1.0 - (recuperacao * 0.25))
                
                reps_projetadas = []
                reps_atual = max_unbroken
                for s in range(num_sets_gym):
                    reps_projetadas.append(int(reps_atual))
                    reps_atual = max(1, reps_atual * queda_por_set)
                
                st.markdown("### 📉 Projeção de Reps por Set:")
                cols_sets = st.columns(min(5, num_sets_gym))
                for idx_s, r_proj in enumerate(reps_projetadas):
                    c_idx = idx_s % 5
                    with cols_sets[c_idx]:
                        st.metric(f"Set {idx_s+1}", f"{r_proj} reps")
                
                st.info(f"**Total acumulado estimado:** {sum(reps_projetadas)} reps.")

# ==================== ABA 4: COACH IA & LEITOR DE WOD (OPCIONAL) ====================
with aba_ai:
    st.header("🤖 Inteligência Artificial Generativa (Coach Virtual & Parser)")
    st.markdown("Esta funcionalidade é **opcional**. Permite ler WODs em texto corrido e receber conselhos táticos personalizados.")
    
    openai_key = st.text_input("🔑 OpenAI API Key (deixe em branco se não quiser usar a IA):", type="password")
    
    if openai_key and HAS_OPENAI:
        client = OpenAI(api_key=openai_key)
        
        sub_ai_parse, sub_ai_advice = st.tabs(["📝 Extrair WOD por Texto", "🧠 Coach Tático Pro"])
        
        # SUB-ABA: EXTRAIR WOD
        with sub_ai_parse:
            st.subheader("Cole o texto bruto do WOD (Instagram, WODify, etc.):")
            wod_raw_text = st.text_area("Texto do Treino", value="21-15-9\nThruster (43kg)\nPull-ups\nTime Cap: 10 min")
            
            if st.button("🪄 Extrair e Estruturar WOD com IA"):
                prompt_parser = f"""
                Você é um parser de treinos de CrossFit. Analise o texto e retorne APENAS um JSON válido.
                Formato esperado do JSON:
                {{
                   "format": "For Time" ou "AMRAP",
                   "rounds": 3,
                   "cap_min": 10,
                   "movs": [
                      {{"name": "Thruster", "reps": 21, "load": 43.0}},
                      {{"name": "Pull-up", "reps": 21, "load": 0.0}}
                   ]
                }}
                Texto para analisar:
                {wod_raw_text}
                """
                try:
                    res = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt_parser}],
                        response_format={"type": "json_object"}
                    )
                    data_json = json.loads(res.choices[0].message.content)
                    st.success("✅ WOD Estruturado com Sucesso!")
                    st.json(data_json)
                except Exception as e:
                    st.error(f"Erro ao processar com a IA: {e}")

        # SUB-ABA: ADVICE
        with sub_ai_advice:
            st.subheader("Solicitar Dica Estratégica da IA")
            duvida_atleta = st.text_area("O que deseja saber sobre sua tática?", "Qual a melhor divisão de séries no Thruster para não travar nos Pull-ups?")
            
            if st.button("💬 Consultar Coach IA"):
                prompt_coach = f"""
                Você é um Coach de CrossFit nível Games e especialista em fisiologia do exercício.
                Responda objetivamente à dúvida do atleta:
                "{duvida_atleta}"
                Apresente conselhos práticos divididos em:
                1. Ritmo de Execução (Pacing)
                2. Estratégia de Quebra (Sets & Pausas)
                3. Alerta Fisiológico (Gestão de Lactato / Grip)
                """
                try:
                    res = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt_coach}]
                    )
                    st.markdown("### 📋 Resposta do Coach IA:")
                    st.info(res.choices[0].message.content)
                except Exception as e:
                    st.error(f"Erro ao consultar o Coach IA: {e}")

    elif openai_key and not HAS_OPENAI:
        st.warning("⚠️ Instale a biblioteca da OpenAI usando `pip install openai` no seu ambiente Python.")
    else:
        st.info("💡 Insira sua API Key da OpenAI para ativar as funções adaptativas de IA nesta aba.")


