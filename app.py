import streamlit as st
import math

st.set_page_config(page_title="CrossFit WOD Predictor PRO", page_icon="🏋️", layout="wide")
# ---------------------------------------------------------
# CORREÇÃO DEFINITIVA DO BOTÃO DA SIDEBAR PARA CELULAR
# ---------------------------------------------------------
custom_css = """
    <style>
    /* Esconde o menu de opções do canto direito e rodapé */
    #MainMenu {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Garante que o botão de EXPANDIR a barra (quando fechada) fique visível e fixo no topo esquerdo */
    [data-testid="stSidebarExpandButton"] {
        visibility: visible !important;
        display: flex !important;
        position: fixed !important;
        top: 10px !important;
        left: 10px !important;
        z-index: 999999 !important;
        background-color: rgba(255, 255, 255, 0.8) !important;
        border-radius: 5px !important;
    }

    /* Mantém o botão de RECOLHER a barra visível */
    [data-testid="stSidebarCollapseButton"] {
        visibility: visible !important;
        display: flex !important;
    }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

import streamlit as st

# Configuração da página
st.set_page_config(page_title="CrossFit WOD Predictor PRO", page_icon="🏋️", layout="wide")

# ---------------------------------------------------------
# AUTENTICAÇÃO / CONTROLE DE ACESSO
# ---------------------------------------------------------
def checar_senha():
    def senha_digitada():
        if st.session_state["password_input"] == "wodpredictor":  # <--- Defina sua senha aqui
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

# Interrompe a execução do código se a senha não estiver correta
if not checar_senha():
    st.stop()

# ---------------------------------------------------------
# O RESTANTE DO SEU CÓDIGO DO APP VEM AQUI ABAIXO...
# ---------------------------------------------------------


st.title("🏋️ CrossFit WOD Time Predictor PRO")
st.caption("Estimador avançado de tempo, ritmo e rounds considerando degradacao muscular e interferencia neuromuscular.")

# ---------------------------------------------------------
# SIDEBAR: PERFIL DO ATLETA (1RM & DADOS GINÁSTICOS/CARDIOS)
# ---------------------------------------------------------
st.sidebar.header("👤 Perfil de Força (1RM em kg)")
col_s1, col_s2 = st.sidebar.columns(2)
with col_s1:
    rm_thruster = st.number_input("Thruster", min_value=1.0, value=80.0, step=2.5)
    rm_deadlift = st.number_input("Deadlift", min_value=1.0, value=140.0, step=5.0)
    rm_bsquat = st.number_input("Back Squat", min_value=1.0, value=120.0, step=2.5)
    rm_fsquat = st.number_input("Front Squat", min_value=1.0, value=100.0, step=2.5)
    rm_ohs = st.number_input("Overhead Squat", min_value=1.0, value=75.0, step=2.5)
with col_s2:
    rm_cj = st.number_input("Clean & Jerk", min_value=1.0, value=90.0, step=2.5)
    rm_snatch = st.number_input("Snatch", min_value=1.0, value=70.0, step=2.5)
    rm_pclean = st.number_input("Power Clean", min_value=1.0, value=85.0, step=2.5)
    rm_ppress = st.number_input("Push Press", min_value=1.0, value=75.0, step=2.5)

st.sidebar.header("🤸 Capacidade Ginástica (Max Unbroken)")
col_g1, col_g2 = st.sidebar.columns(2)
with col_g1:
    max_pullups = st.number_input("Pull-ups", min_value=1, value=25)
    max_c2b = st.number_input("Chest to Bar", min_value=1, value=18)
    max_bmu = st.number_input("Bar Muscle-ups", min_value=1, value=8)
    max_rmu = st.number_input("Ring Muscle-ups", min_value=1, value=6)
    max_ttb = st.number_input("Toes to Bar", min_value=1, value=20)
with col_g2:
    max_hspu = st.number_input("HSPU", min_value=1, value=15)
    max_hsw = st.number_input("HS Walk (metros)", min_value=1, value=15)
    max_rope = st.number_input("Rope Climb (reps)", min_value=1, value=4)
    max_pistols = st.number_input("Pistols (por perna)", min_value=1, value=15)

st.sidebar.header("🏃 Paces de Ergômetros e Cardios")
pace_burpee = st.sidebar.number_input("Segundos por Burpee", min_value=1.0, value=3.0, step=0.1)
pace_run = st.sidebar.number_input("Pace Corrida (seg / 100m)", min_value=10.0, value=25.0, step=1.0)
pace_row = st.sidebar.number_input("Pace Remo/Ski (seg / 100m ou 10cal)", min_value=10.0, value=22.0, step=1.0)
pace_bike = st.sidebar.number_input("Pace Echo/BikeErg (seg / 10cal)", min_value=5.0, value=18.0, step=1.0)
pace_du = st.sidebar.number_input("Segundos por 10 Double Unders", min_value=1.0, value=6.0, step=0.5)

# ---------------------------------------------------------
# DATABASE DE EXERCÍCIOS E METADADOS
# ---------------------------------------------------------
EXERCISES = {
    # LPO / Barbell
    "Thruster": {"type": "lpo", "rm_key": "thruster", "tpr": 2.2, "pattern": "push_legs"},
    "Deadlift": {"type": "lpo", "rm_key": "deadlift", "tpr": 2.0, "pattern": "pull_posterior"},
    "Back Squat": {"type": "lpo", "rm_key": "bsquat", "tpr": 2.3, "pattern": "legs"},
    "Front Squat": {"type": "lpo", "rm_key": "fsquat", "tpr": 2.2, "pattern": "legs"},
    "Overhead Squat": {"type": "lpo", "rm_key": "ohs", "tpr": 2.4, "pattern": "push_legs"},
    "Clean & Jerk": {"type": "lpo", "rm_key": "cj", "tpr": 3.2, "pattern": "full_body"},
    "Snatch": {"type": "lpo", "rm_key": "snatch", "tpr": 2.8, "pattern": "full_body"},
    "Power Clean": {"type": "lpo", "rm_key": "pclean", "tpr": 2.1, "pattern": "pull_posterior"},
    "Push Press": {"type": "lpo", "rm_key": "ppress", "tpr": 1.9, "pattern": "push"},

    # Ginásticos
    "Pull-up": {"type": "gym", "max_key": "pullups", "tpr": 1.4, "pattern": "pull_upper"},
    "Chest to Bar": {"type": "gym", "max_key": "c2b", "tpr": 1.6, "pattern": "pull_upper"},
    "Bar Muscle-up": {"type": "gym", "max_key": "bmu", "tpr": 3.0, "pattern": "pull_push_upper"},
    "Ring Muscle-up": {"type": "gym", "max_key": "rmu", "tpr": 3.5, "pattern": "pull_push_upper"},
    "Toes to Bar": {"type": "gym", "max_key": "ttb", "tpr": 1.6, "pattern": "pull_core"},
    "HSPU": {"type": "gym", "max_key": "hspu", "tpr": 2.0, "pattern": "push"},
    "Handstand Walk (m)": {"type": "gym", "max_key": "hsw", "tpr": 0.8, "pattern": "push_shoulders"},
    "Rope Climb": {"type": "gym", "max_key": "rope", "tpr": 7.0, "pattern": "pull_upper"},
    "Pistols": {"type": "gym", "max_key": "pistols", "tpr": 2.0, "pattern": "legs"},

    # Ergômetros / Engine
    "Burpee": {"type": "cardio", "pace_key": "burpee", "tpr": 3.0, "pattern": "push_engine"},
    "Corrida (m)": {"type": "cardio", "pace_key": "run", "tpr": 0.25, "pattern": "legs_engine"},
    "Remo (m/cal)": {"type": "cardio", "pace_key": "row", "tpr": 0.22, "pattern": "pull_engine"},
    "SkiErg (m/cal)": {"type": "cardio", "pace_key": "row", "tpr": 0.22, "pattern": "pull_engine"},
    "Echo / BikeErg (cal)": {"type": "cardio", "pace_key": "bike", "tpr": 1.8, "pattern": "legs_engine"},
    "Double Unders": {"type": "cardio", "pace_key": "du", "tpr": 0.6, "pattern": "engine_shoulders"}
}

st.divider()

# ---------------------------------------------------------
# CONFIGURAÇÃO DO WOD (FOR TIME OU AMRAP + ATÉ 5 MOVIMENTOS)
# ---------------------------------------------------------
st.header("📋 Estrutura do WOD")

c_format, c_config = st.columns(2)
with c_format:
    wod_format = st.selectbox("Formato do Treino", ["For Time", "AMRAP"])
with c_config:
    if wod_format == "For Time":
        num_rounds = st.number_input("Número de Rodadas", min_value=1, value=3)
        time_cap = st.number_input("Time Cap (minutos, 0 se sem cap)", min_value=0, value=15)
    else:
        amrap_minutes = st.number_input("Tempo do AMRAP (minutos)", min_value=1, value=12)

num_movements = st.slider("Quantidade de Movimentos no WOD", min_value=1, max_value=5, value=2)

st.subheader("Configuração dos Movimentos")

mov_inputs = []
exercise_names = sorted(list(EXERCISES.keys()))

cols = st.columns(num_movements)
for i in range(num_movements):
    with cols[i]:
        st.markdown(f"**Movimento {i+1}**")
        ex_name = st.selectbox(f"Exercício {i+1}", exercise_names, key=f"ex_{i}")
        reps = st.number_input(f"Volume/Reps (Mov {i+1})", min_value=1, value=15, key=f"reps_{i}")
        
        ex_info = EXERCISES[ex_name]
        load = 0.0
        if ex_info["type"] == "lpo":
            load = st.number_input(f"Carga (kg)", min_value=0.0, value=40.0, step=2.5, key=f"load_{i}")
            
        mov_inputs.append({"name": ex_name, "reps": reps, "load": load})

# ---------------------------------------------------------
# FUNÇÃO DE CÁLCULO INDIVIDUAL E INTERFERÊNCIA
# ---------------------------------------------------------
def calcular_tempo_movimento(name, reps, load, rm_dict, max_dict, pace_dict):
    info = EXERCISES[name]
    ex_type = info["type"]
    
    if ex_type == "lpo":
        rm_val = rm_dict.get(info["rm_key"], 80.0)
        pct = load / rm_val if rm_val > 0 else 0.5
        tpr = info["tpr"] * (1 + (pct ** 2))
        max_safe_set = max(2, int(15 * (1 - pct)))
        sets = math.ceil(reps / max_safe_set)
        rest_per_set = 8 + (pct * 14)
        
    elif ex_type == "gym":
        max_unbroken = max_dict.get(info["max_key"], 15)
        tpr = info["tpr"]
        safe_set = max(2, int(max_unbroken * 0.45))
        sets = math.ceil(reps / safe_set)
        rest_per_set = 7.0 + (sets * 0.8)
        
    else: # cardio
        p_val = pace_dict.get(info["pace_key"], 3.0)
        if name == "Corrida (m)":
            tpr = p_val / 100.0
        elif name in ["Remo (m/cal)", "SkiErg (m/cal)"]:
            tpr = p_val / 100.0
        elif name == "Echo / BikeErg (cal)":
            tpr = p_val / 10.0
        elif name == "Double Unders":
            tpr = p_val / 10.0
        else:
            tpr = p_val
            
        sets = 1
        rest_per_set = 0.0
        
    exec_time = reps * tpr
    total_rest = (sets - 1) * rest_per_set
    return exec_time + total_rest, sets, rest_per_set, info["pattern"]

st.markdown("---")

# ---------------------------------------------------------
# BOTÃO DE EXECUÇÃO E LÓGICA PRINCIPAL
# ---------------------------------------------------------
if st.button("🚀 Calcular Estimativa de Desempenho", use_container_width=True, type="primary"):
    
    rm_dict = {
        'thruster': rm_thruster, 'deadlift': rm_deadlift, 'bsquat': rm_bsquat,
        'fsquat': rm_fsquat, 'ohs': rm_ohs, 'cj': rm_cj, 'snatch': rm_snatch,
        'pclean': rm_pclean, 'ppress': rm_ppress
    }
    max_dict = {
        'pullups': max_pullups, 'c2b': max_c2b, 'bmu': max_bmu, 'rmu': max_rmu,
        'ttb': max_ttb, 'hspu': max_hspu, 'hsw': max_hsw, 'rope': max_rope, 'pistols': max_pistols
    }
    pace_dict = {
        'burpee': pace_burpee, 'run': pace_run, 'row': pace_row,
        'bike': pace_bike, 'du': pace_du
    }
    
    round_time_raw = 0.0
    patterns = []
    breakdowns = []
    
    # Processa cada movimento da rodada
    for idx, mov in enumerate(mov_inputs):
        t_mov, sets, rest, pattern = calcular_tempo_movimento(
            mov["name"], mov["reps"], mov["load"], rm_dict, max_dict, pace_dict
        )
        
        # Penalidade por interferência neuromuscular (se o padrão do movimento for igual ao anterior)
        interference_penalty = 1.0
        if idx > 0 and (pattern in patterns[-1] or patterns[-1] in pattern):
            interference_penalty = 1.25 # 25% a mais de tempo por fadiga muscular local
            
        t_mov_final = t_mov * interference_penalty
        round_time_raw += t_mov_final
        patterns.append(pattern)
        
        breakdowns.append({
            "name": mov["name"],
            "time": t_mov_final,
            "sets": sets,
            "rest": rest,
            "penalty": interference_penalty > 1.0
        })
        
    # Transição entre estações (5 segundos por transição)
    transitions_time = num_movements * 5.0
    round_time_total = round_time_raw + transitions_time
    
    st.subheader("🎯 Resultado da Previsão")
    
    if wod_format == "For Time":
        total_wod_time = round_time_total * num_rounds
        mins = int(total_wod_time // 60)
        secs = int(total_wod_time % 60)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Tempo Total Estimado", f"{mins:02d}:{secs:02d} min")
        c2.metric("Pace Médio por Rodada", f"{int(round_time_total // 60):02d}:{int(round_time_total % 60):02d} min")
        
        cap_seconds = time_cap * 60 if time_cap > 0 else 999999
        if time_cap > 0 and total_wod_time > cap_seconds:
            c3.metric("Status do Cap", "⚠️ Risco de Capped", delta="-Estouro do tempo", delta_color="inverse")
        else:
            c3.metric("Status do Cap", "✅ Dentro do Cap")
            
    else: # AMRAP
        amrap_seconds = amrap_minutes * 60
        rounds_completed = amrap_seconds / round_time_total
        full_rounds = int(rounds_completed)
        fraction_round = rounds_completed - full_rounds
        extra_reps = int(fraction_round * sum([m["reps"] for m in mov_inputs]))
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Estimativa de Score", f"{full_rounds} rounds + {extra_reps} reps")
        c2.metric("Tempo Médio por Rodada", f"{int(round_time_total // 60):02d}:{int(round_time_total % 60):02d} min")
        c3.metric("Ritmo Sugerido", f"{round_time_total / 60:.1f} min / round")

    # Estratégia Recomendada
    st.markdown("---")
    st.success("💡 **Análise Tática e Estratégia de Quebra:**")
    for b in breakdowns:
        penalty_str = " *(⚠️ +25% de fadiga por interferência com movimento anterior)*" if b["penalty"] else ""
        if b["sets"] > 1:
            st.write(f"- **{b['name']}:** Faça em **{b['sets']} sets** com descanso de ~{int(b['rest'])}s entre eles.{penalty_str}")
        else:
            st.write(f"- **{b['name']}:** Mantenha ritmo constante (unbroken/pace contínuo).{penalty_str}")
