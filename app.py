import streamlit as st
import math

# 1. Configuração da página
st.set_page_config(
    page_title="CrossFit WOD Predictor PRO", 
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

# 3. CSS de limpeza
custom_css = """
    <style>
    #MainMenu {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# 4. Função utilitária para estimativa de RM (Epley & Brzycki)
def calcular_rm(carga, reps):
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

# 5. Interface Principal com Abas
st.title("🏋️ CrossFit WOD Predictor & Performance PRO")

aba_wod, aba_rm = st.tabs(["⏱️ Preditor de Tempo de WOD", "📊 Calculadora Preditora de PR / Rep Max"])

# ==================== ABA 1: PREDIÇÃO DE WOD ====================
with aba_wod:
    with st.expander("👤 **CONFIGURAR SEU PERFIL (1RM & REPS MÁXIMAS)**", expanded=True):
        st.markdown("### 🏋️ Força Máxima (1RM em kg)")
        c1, c2 = st.columns(2)
        with c1:
            rm_thruster = st.number_input("Thruster", min_value=1.0, value=80.0, step=2.5)
            rm_deadlift = st.number_input("Deadlift", min_value=1.0, value=140.0, step=5.0)
            rm_bsquat = st.number_input("Back Squat", min_value=1.0, value=120.0, step=2.5)
            rm_fsquat = st.number_input("Front Squat", min_value=1.0, value=100.0, step=2.5)
            rm_ohs = st.number_input("Overhead Squat", min_value=1.0, value=75.0, step=2.5)
        with c2:
            rm_cj = st.number_input("Clean & Jerk", min_value=1.0, value=90.0, step=2.5)
            rm_snatch = st.number_input("Snatch", min_value=1.0, value=70.0, step=2.5)
            rm_pclean = st.number_input("Power Clean", min_value=1.0, value=85.0, step=2.5)
            rm_ppress = st.number_input("Push Press", min_value=1.0, value=75.0, step=2.5)

        st.markdown("### 🤸 Capacidade Ginástica (Max Unbroken)")
        c3, c4 = st.columns(2)
        with c3:
            max_pullups = st.number_input("Pull-ups", min_value=1, value=25)
            max_c2b = st.number_input("Chest to Bar", min_value=1, value=18)
            max_bmu = st.number_input("Bar Muscle-ups", min_value=1, value=8)
            max_rmu = st.number_input("Ring Muscle-ups", min_value=1, value=6)
            max_ttb = st.number_input("Toes to Bar", min_value=1, value=20)
        with c4:
            max_hspu = st.number_input("HSPU", min_value=1, value=15)
            max_hsw = st.number_input("HS Walk (m)", min_value=1, value=15)
            max_rope = st.number_input("Rope Climb", min_value=1, value=4)
            max_pistols = st.number_input("Pistols (cada perna)", min_value=1, value=15)

        st.markdown("### 🏃 Ergômetros e Pace")
        c5, c6 = st.columns(2)
        with c5:
            pace_burpee = st.number_input("Seg/Burpee", min_value=1.0, value=3.0, step=0.1)
            pace_run = st.number_input("Pace Corrida (seg / 100m)", min_value=10.0, value=25.0, step=1.0)
        with c6:
            pace_row = st.number_input("Pace Remo/Ski (seg / 100m ou 10cal)", min_value=10.0, value=22.0, step=1.0)
            pace_bike = st.number_input("Pace Bike (seg / 10cal)", min_value=5.0, value=18.0, step=1.0)
            pace_du = st.number_input("Seg / 10 Double Unders", min_value=1.0, value=6.0, step=0.5)

    EXERCISES = {
        "Thruster": {"type": "lpo", "rm_key": "thruster", "tpr": 2.2, "pattern": "push_legs"},
        "Deadlift": {"type": "lpo", "rm_key": "deadlift", "tpr": 2.0, "pattern": "pull_posterior"},
        "Back Squat": {"type": "lpo", "rm_key": "bsquat", "tpr": 2.3, "pattern": "legs"},
        "Front Squat": {"type": "lpo", "rm_key": "fsquat", "tpr": 2.2, "pattern": "legs"},
        "Overhead Squat": {"type": "lpo", "rm_key": "ohs", "tpr": 2.4, "pattern": "push_legs"},
        "Clean & Jerk": {"type": "lpo", "rm_key": "cj", "tpr": 3.2, "pattern": "full_body"},
        "Snatch": {"type": "lpo", "rm_key": "snatch", "tpr": 2.8, "pattern": "full_body"},
        "Power Clean": {"type": "lpo", "rm_key": "pclean", "tpr": 2.1, "pattern": "pull_posterior"},
        "Push Press": {"type": "lpo", "rm_key": "ppress", "tpr": 1.9, "pattern": "push"},
        "Pull-up": {"type": "gym", "max_key": "pullups", "tpr": 1.4, "pattern": "pull_upper"},
        "Chest to Bar": {"type": "gym", "max_key": "c2b", "tpr": 1.6, "pattern": "pull_upper"},
        "Bar Muscle-up": {"type": "gym", "max_key": "bmu", "tpr": 3.0, "pattern": "pull_push_upper"},
        "Ring Muscle-up": {"type": "gym", "max_key": "rmu", "tpr": 3.5, "pattern": "pull_push_upper"},
        "Toes to Bar": {"type": "gym", "max_key": "ttb", "tpr": 1.6, "pattern": "pull_core"},
        "HSPU": {"type": "gym", "max_key": "hspu", "tpr": 2.0, "pattern": "push"},
        "Handstand Walk (m)": {"type": "gym", "max_key": "hsw", "tpr": 0.8, "pattern": "push_shoulders"},
        "Rope Climb": {"type": "gym", "max_key": "rope", "tpr": 7.0, "pattern": "pull_upper"},
        "Pistols": {"type": "gym", "max_key": "pistols", "tpr": 2.0, "pattern": "legs"},
        "Burpee": {"type": "cardio", "pace_key": "burpee", "tpr": 3.0, "pattern": "push_engine"},
        "Corrida (m)": {"type": "cardio", "pace_key": "run", "tpr": 0.25, "pattern": "legs_engine"},
        "Remo (m/cal)": {"type": "cardio", "pace_key": "row", "tpr": 0.22, "pattern": "pull_engine"},
        "Echo / BikeErg (cal)": {"type": "cardio", "pace_key": "bike", "tpr": 1.8, "pattern": "legs_engine"},
        "Double Unders": {"type": "cardio", "pace_key": "du", "tpr": 0.6, "pattern": "engine_shoulders"}
    }

    st.divider()
    st.header("📋 Estrutura do WOD")
    c_format, c_config = st.columns(2)
    with c_format:
        wod_format = st.selectbox("Formato", ["For Time", "AMRAP"])
    with c_config:
        if wod_format == "For Time":
            num_rounds = st.number_input("Rodadas", min_value=1, value=3)
            time_cap = st.number_input("Time Cap (min)", min_value=0, value=15)
        else:
            amrap_minutes = st.number_input("Minutos", min_value=1, value=12)

    num_movements = st.slider("Qtd Movimentos", 1, 5, 2)
    mov_inputs = []
    cols = st.columns(num_movements)
    for i in range(num_movements):
        with cols[i]:
            ex_name = st.selectbox(f"Mov {i+1}", sorted(list(EXERCISES.keys())), key=f"ex_{i}")
            reps = st.number_input(f"Reps {i+1}", min_value=1, value=15, key=f"reps_{i}")
            load = st.number_input(f"Carga (kg)", min_value=0.0, value=40.0, key=f"load_{i}") if EXERCISES[ex_name]["type"] == "lpo" else 0.0
            mov_inputs.append({"name": ex_name, "reps": reps, "load": load})

    def calc(name, reps, load, r_d, m_d, p_d):
        info = EXERCISES[name]
        if info["type"] == "lpo":
            pct = load / r_d.get(info["rm_key"], 80.0)
            tpr = info["tpr"] * (1 + (pct**2))
            sets = math.ceil(reps / max(2, int(15 * (1 - pct))))
            rest = 8 + (pct * 14)
        elif info["type"] == "gym":
            tpr = info["tpr"]
            sets = math.ceil(reps / max(2, int(m_d.get(info["max_key"], 15) * 0.45)))
            rest = 7.0
        else:
            tpr = p_d.get(info["pace_key"], 3.0) / (100 if "m" in name else 10)
            sets, rest = 1, 0.0
        return (reps * tpr) + ((sets - 1) * rest), sets, rest, info["pattern"]

    if st.button("🚀 Calcular", use_container_width=True, type="primary"):
        r_d = {'thruster': rm_thruster, 'deadlift': rm_deadlift, 'bsquat': rm_bsquat, 'fsquat': rm_fsquat, 'ohs': rm_ohs, 'cj': rm_cj, 'snatch': rm_snatch, 'pclean': rm_pclean, 'ppress': rm_ppress}
        m_d = {'pullups': max_pullups, 'c2b': max_c2b, 'bmu': max_bmu, 'rmu': max_rmu, 'ttb': max_ttb, 'hspu': max_hspu, 'hsw': max_hsw, 'rope': max_rope, 'pistols': max_pistols}
        p_d = {'burpee': pace_burpee, 'run': pace_run, 'row': pace_row, 'bike': pace_bike, 'du': pace_du}
        
        rt, pats = 0.0, []
        breakdowns = []
        
        for i, m in enumerate(mov_inputs):
            t, s, rest_s, p = calc(m["name"], m["reps"], m["load"], r_d, m_d, p_d)
            penalty = (i > 0 and (p in pats[-1] or pats[-1] in p))
            pen_factor = 1.25 if penalty else 1.0
            
            rt += t * pen_factor
            pats.append(p)
            
            breakdowns.append({
                "name": m["name"],
                "reps": m["reps"],
                "sets": s,
                "rest": rest_s + (5.0 if penalty else 0.0),
                "penalty": penalty
            })
            
        rt += num_movements * 5.0
        
        st.subheader("🎯 Resultado")
        if wod_format == "For Time":
            tot = rt * num_rounds
            st.metric("Tempo Total Estimado", f"{int(tot//60)}:{int(tot%60):02d} min")
        else:
            rnds = (amrap_minutes * 60) / rt
            full_r = int(rnds)
            extra_reps = int((rnds - full_r) * sum(m['reps'] for m in mov_inputs))
            st.metric("Estimativa de Score", f"{full_r} rounds + {extra_reps} reps")
        
        st.markdown("---")
        st.subheader("💡 Análise Tática e Estratégia de Quebra")

        for b in breakdowns:
            name = b["name"]
            sets = b["sets"]
            rest = b["rest"]
            penalty = b["penalty"]
            reps = b["reps"]

            base_reps = reps // sets
            rem_reps = reps % sets

            if sets > 1:
                set_list = [base_reps + (1 if k < rem_reps else 0) for k in range(sets)]
                set_str = " - ".join(map(str, set_list))
                msg = f"**{name}** ({reps} reps): Divida em **{sets} sets** (`{set_str}`). Descanso sugerido: **{int(rest)}s** entre os sets."
            else:
                msg = f"**{name}** ({reps} reps): Faça **unbroken** (set único) mantendo ritmo constante."

            if penalty:
                st.warning(f"⚠️ {msg}\n\n*Atenção: Fadiga muscular por interferência do movimento anterior. Adicione +5s de pausa.*")
            else:
                st.info(f"✅ {msg}")

# ==================== ABA 2: PREDICTOR DE PR / REP MAX ====================
with aba_rm:
    st.header("📊 Calculadora de PR & Estimativa de Rep Max")
    st.markdown("Calcule sua **1RM estimada** e obtenha a tabela de cargas de **1RM a 10RM** a partir de qualquer série recente.")

    c_calc1, c_calc2 = st.columns(2)
    with c_calc1:
        carga_input = st.number_input("Carga levantada (kg)", min_value=1.0, value=80.0, step=2.5, key="rm_carga_input")
        reps_input = st.number_input("Repetições realizadas", min_value=1, max_value=30, value=5, key="rm_reps_input")
    
    rm1_est, tabela_rms = calcular_rm(carga_input, reps_input)

    with c_calc2:
        st.metric("🎯 1RM Estimada", f"{rm1_est} kg")
        st.caption(f"Baseado em {reps_input} reps com {carga_input} kg")

    st.markdown("---")
    st.subheader("📋 Tabela Preditiva de Cargas (1RM - 10RM)")
    
    cols_rm = st.columns(5)
    rm_items = list(tabela_rms.items())
    
    for idx, (rm_label, val) in enumerate(rm_items):
        col_idx = idx % 5
        with cols_rm[col_idx]:
            st.metric(label=rm_label, value=f"{val} kg")

