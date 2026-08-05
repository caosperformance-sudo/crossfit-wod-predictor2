import streamlit as st
import math

st.set_page_config(page_title="CrossFit WOD Predictor", page_icon="🏋️", layout="wide")

# Estilização
st.title("🏋️ CrossFit WOD Time Predictor")
st.caption("Estimador inteligente de tempo e ritmo de prova baseado no seu perfil de força e capacidade ginástica.")

# Sidebar - Perfil do Atleta
st.sidebar.header("👤 Perfil do Atleta (1RM & Max Reps)")
rm_thruster = st.sidebar.number_input("1RM Thruster (kg)", min_value=1.0, value=80.0, step=2.5)
rm_deadlift = st.sidebar.number_input("1RM Deadlift (kg)", min_value=1.0, value=140.0, step=5.0)
max_pullups = st.sidebar.number_input("Max Pull-ups Unbroken", min_value=1, value=25, step=1)
max_ttb = st.sidebar.number_input("Max Toes to Bar Unbroken", min_value=1, value=20, step=1)
max_hspu = st.sidebar.number_input("Max HSPU Unbroken", min_value=1, value=15, step=1)
burpee_pace = st.sidebar.number_input("Segundos por Burpee (Pace)", min_value=1.5, value=3.0, step=0.2)

st.divider()

# Formulário do WOD
st.header("📋 Configuração do WOD")

col_type, col_rounds = st.columns(2)
with col_type:
    wod_format = st.selectbox("Formato do WOD", ["For Time", "AMRAP (Em breve)"])
with col_rounds:
    num_rounds = st.number_input("Número de Rodadas", min_value=1, value=3, step=1)

st.subheader("Movimentos da Rodada")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Movimento 1")
    mov1_name = st.selectbox("Exercício 1", ["Thruster", "Pull-up", "Burpee", "Deadlift", "Toes to Bar", "HSPU"])
    mov1_reps = st.number_input("Repetições por rodada (Mov. 1)", min_value=1, value=15, step=1)
    mov1_load = st.number_input("Carga do Movimento 1 (kg, 0 se peso do corpo)", min_value=0.0, value=43.0, step=2.5)

with col2:
    st.markdown("### Movimento 2")
    mov2_name = st.selectbox("Exercício 2", ["Pull-up", "Thruster", "Burpee", "Deadlift", "Toes to Bar", "HSPU"])
    mov2_reps = st.number_input("Repetições por rodada (Mov. 2)", min_value=1, value=15, step=1)
    mov2_load = st.number_input("Carga do Movimento 2 (kg, 0 se peso do corpo)", min_value=0.0, value=0.0, step=2.5)

def calcular_movimento(nome, reps, carga, rm_dict, max_dict, pace_burpee):
    if nome == "Thruster":
        pct = carga / rm_dict['thruster'] if rm_dict['thruster'] > 0 else 0.5
        tpr = 2.2 * (1 + (pct ** 2))
        max_reps_set = max(2, int(max_dict['pullup'] * 0.8 * (1 - pct)))
        sets = math.ceil(reps / max_reps_set)
        rest_per_set = 10 + (pct * 12)
        
    elif nome == "Deadlift":
        pct = carga / rm_dict['deadlift'] if rm_dict['deadlift'] > 0 else 0.5
        tpr = 2.0 * (1 + (pct ** 1.8))
        max_reps_set = max(3, int(20 * (1 - pct)))
        sets = math.ceil(reps / max_reps_set)
        rest_per_set = 8 + (pct * 10)
        
    elif nome == "Pull-up":
        tpr = 1.4
        max_unbroken = max_dict['pullup']
        safe_set = max(3, int(max_unbroken * 0.5))
        sets = math.ceil(reps / safe_set)
        rest_per_set = 8.0
        
    elif nome == "Toes to Bar":
        tpr = 1.6
        max_unbroken = max_dict['ttb']
        safe_set = max(3, int(max_unbroken * 0.45))
        sets = math.ceil(reps / safe_set)
        rest_per_set = 9.0
        
    elif nome == "HSPU":
        tpr = 2.0
        max_unbroken = max_dict['hspu']
        safe_set = max(2, int(max_unbroken * 0.4))
        sets = math.ceil(reps / safe_set)
        rest_per_set = 12.0
        
    elif nome == "Burpee":
        tpr = pace_burpee
        sets = 1
        rest_per_set = 0.0
        
    else:
        tpr = 2.0
        sets = 1
        rest_per_set = 5.0
        
    time_exec = reps * tpr
    total_rest = (sets - 1) * rest_per_set
    return time_exec + total_rest, sets, rest_per_set

st.markdown("---")

if st.button("🚀 Calcular Estimativa de Tempo", use_container_width=True, type="primary"):
    rms = {'thruster': rm_thruster, 'deadlift': rm_deadlift}
    maxs = {'pullup': max_pullups, 'ttb': max_ttb, 'hspu': max_hspu}
    
    t1, sets1, rest1 = calcular_movimento(mov1_name, mov1_reps, mov1_load, rms, maxs, burpee_pace)
    t2, sets2, rest2 = calcular_movimento(mov2_name, mov2_reps, mov2_load, rms, maxs, burpee_pace)
    
    transition_per_round = 6.0
    time_per_round = t1 + t2 + transition_per_round
    
    total_time = time_per_round * num_rounds
    
    mins = int(total_time // 60)
    secs = int(total_time % 60)
    
    st.subheader("🎯 Resultado da Previsão")
    
    res_col1, res_col2, res_col3 = st.columns(3)
    res_col1.metric("Tempo Total Estimado", f"{mins:02d}:{secs:02d} min")
    res_col2.metric("Tempo Médio por Rodada", f"{int(time_per_round // 60):02d}:{int(time_per_round % 60):02d} min")
    res_col3.metric("Fator de Carga/Fadiga", f"{'Alto' if total_time > 600 else 'Moderado'}")
    
    st.success("💡 **Estratégia Recomendada de Ritmo (Pace):**")
    st.write(f"- **{mov1_name}:** Divida as {mov1_reps} reps em cerca de **{sets1} sets** (descansando ~{int(rest1)}s entre eles).")
    st.write(f"- **{mov2_name}:** Divida as {mov2_reps} reps em cerca de **{sets2} sets** (descansando ~{int(rest2)}s entre eles).")
    st.write(f"- Mantendo transições rápidas de até 3s entre as estações, você evita perder o ritmo ideal.")
