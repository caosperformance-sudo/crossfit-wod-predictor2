import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime
import tempfile
import os

## Verificação de bibliotecas de Visão Computacional
try:
    import cv2
    import mediapipe as mp
    HAS_VISION = True
except ImportError:
    HAS_VISION = False

## ============================================================================
## CONFIGURAÇÃO DA PÁGINA
## ============================================================================
st.set_page_config(
    page_title="CrossFit WOD Predictor Pro",
    page_icon="🏋️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

## ============================================================================
## INICIALIZAÇÃO DO SESSION STATE
## ============================================================================
if 'perfil_atleta' not in st.session_state:
    st.session_state.perfil_atleta = {
        'nome': 'Atleta',
        'nivel': 'Intermediário',
        'idade': 30,
        'peso': 75.0,
        '1rm_back_squat': 120.0,
        '1rm_deadlift': 150.0,
        '1rm_clean': 100.0,
        '1rm_snatch': 80.0,
        '1rm_bench': 90.0,
        'max_pullups': 15,
        'max_pushups': 40,
        'max_hspu': 10,
        'vo2max': 45.0,
        'fc_repouso': 60,
        'fc_max': 190
    }

if 'treinos_salvos' not in st.session_state:
    st.session_state.treinos_salvos = []

if 'historico_repmax' not in st.session_state:
    st.session_state.historico_repmax = []

## ============================================================================
## BASE DE DADOS DE MOVIMENTOS
## ============================================================================
MOVIMENTOS_DB = {
    ## Ginástica
    "Pull-ups": {
        "tipo": "ginastica",
        "dificuldade": 2.5,
        "fadiga_acum": 0.08,
        "usa_1rm": False,
        "usa_repmax": True,
        "rep_ref": "max_pullups",
        "cardio_impact": 0.3
    },
    "Chest to Bar": {
        "tipo": "ginastica",
        "dificuldade": 3.0,
        "fadiga_acum": 0.10,
        "usa_1rm": False,
        "usa_repmax": True,
        "rep_ref": "max_pullups",
        "cardio_impact": 0.35
    },
    "Muscle-ups": {
        "tipo": "ginastica",
        "dificuldade": 4.5,
        "fadiga_acum": 0.15,
        "usa_1rm": False,
        "usa_repmax": True,
        "rep_ref": "max_pullups",
        "cardio_impact": 0.4
    },
    "Toes to Bar": {
        "tipo": "ginastica",
        "dificuldade": 2.8,
        "fadiga_acum": 0.09,
        "usa_1rm": False,
        "usa_repmax": False,
        "cardio_impact": 0.25
    },
    "HSPU": {
        "tipo": "ginastica",
        "dificuldade": 3.5,
        "fadiga_acum": 0.12,
        "usa_1rm": False,
        "usa_repmax": True,
        "rep_ref": "max_hspu",
        "cardio_impact": 0.3
    },
    "Push-ups": {
        "tipo": "ginastica",
        "dificuldade": 1.8,
        "fadiga_acum": 0.06,
        "usa_1rm": False,
        "usa_repmax": True,
        "rep_ref": "max_pushups",
        "cardio_impact": 0.2
    },
    "Burpees": {
        "tipo": "ginastica",
        "dificuldade": 2.0,
        "fadiga_acum": 0.07,
        "usa_1rm": False,
        "usa_repmax": False,
        "cardio_impact": 0.6
    },
    "Box Jump (24/20)": {
        "tipo": "ginastica",
        "dificuldade": 1.5,
        "fadiga_acum": 0.05,
        "usa_1rm": False,
        "usa_repmax": False,
        "cardio_impact": 0.4
    },
    
    ## Levantamento - Com carga variável
    "Thruster": {
        "tipo": "levantamento",
        "dificuldade": 3.5,
        "fadiga_acum": 0.12,
        "usa_1rm": True,
        "rm_ref": "1rm_clean",
        "cardio_impact": 0.5
    },
    "Clean": {
        "tipo": "levantamento",
        "dificuldade": 3.8,
        "fadiga_acum": 0.13,
        "usa_1rm": True,
        "rm_ref": "1rm_clean",
        "cardio_impact": 0.4
    },
    "Snatch": {
        "tipo": "levantamento",
        "dificuldade": 4.0,
        "fadiga_acum": 0.14,
        "usa_1rm": True,
        "rm_ref": "1rm_snatch",
        "cardio_impact": 0.45
    },
    "Deadlift": {
        "tipo": "levantamento",
        "dificuldade": 3.2,
        "fadiga_acum": 0.11,
        "usa_1rm": True,
        "rm_ref": "1rm_deadlift",
        "cardio_impact": 0.3
    },
    "Back Squat": {
        "tipo": "levantamento",
        "dificuldade": 3.0,
        "fadiga_acum": 0.10,
        "usa_1rm": True,
        "rm_ref": "1rm_back_squat",
        "cardio_impact": 0.35
    },
    "Front Squat": {
        "tipo": "levantamento",
        "dificuldade": 3.3,
        "fadiga_acum": 0.11,
        "usa_1rm": True,
        "rm_ref": "1rm_back_squat",
        "cardio_impact": 0.35
    },
    "Overhead Squat": {
        "tipo": "levantamento",
        "dificuldade": 3.7,
        "fadiga_acum": 0.12,
        "usa_1rm": True,
        "rm_ref": "1rm_snatch",
        "cardio_impact": 0.4
    },
    "Bench Press": {
        "tipo": "levantamento",
        "dificuldade": 2.8,
        "fadiga_acum": 0.09,
        "usa_1rm": True,
        "rm_ref": "1rm_bench",
        "cardio_impact": 0.15
    },
    
    ## Cardio
    "Row (cal)": {
        "tipo": "cardio",
        "dificuldade": 2.2,
        "fadiga_acum": 0.06,
        "usa_1rm": False,
        "cardio_impact": 0.8
    },
    "Bike (cal)": {
        "tipo": "cardio",
        "dificuldade": 2.0,
        "fadiga_acum": 0.05,
        "usa_1rm": False,
        "cardio_impact": 0.7
    },
    "Run (m)": {
        "tipo": "cardio",
        "dificuldade": 1.8,
        "fadiga_acum": 0.05,
        "usa_1rm": False,
        "cardio_impact": 0.9
    },
    "Double Unders": {
        "tipo": "cardio",
        "dificuldade": 1.5,
        "fadiga_acum": 0.04,
        "usa_1rm": False,
        "cardio_impact": 0.6
    },
}

## ============================================================================
## FUNÇÕES AUXILIARES
## ============================================================================

def calcular_1rm_multiplas_formulas(peso, reps):
    """Calcula 1RM usando múltiplas fórmulas"""
    formulas = {
        'Epley': peso * (1 + 0.0333 * reps),
        'Brzycki': peso / (1.0278 - 0.0278 * reps) if reps < 37 else peso * 1.5,
        'Lander': (100 * peso) / (101.3 - 2.67123 * reps) if reps < 38 else peso * 1.5,
        'Lombardi': peso * (reps ** 0.1),
        'OConner': peso * (1 + 0.025 * reps)
    }
    return formulas

def calcular_repmax_teorico(max_reps_athlete, reps_wod):
    """
    Calcula fator de dificuldade baseado em repetições máximas
    """
    if max_reps_athlete == 0:
        return 1.5
    
    ratio = reps_wod / max_reps_athlete
    
    if ratio <= 0.3:
        return 0.8  ## Fácil
    elif ratio <= 0.5:
        return 1.0  ## Moderado
    elif ratio <= 0.7:
        return 1.3  ## Difícil
    elif ratio <= 0.9:
        return 1.6  ## Muito Difícil
    else:
        return 2.0  ## Máximo esforço

def calcular_fator_cardio(vo2max, cardio_impact):
    """
    Calcula fator de eficiência cardiorrespiratória
    """
    ## VO2max de referência: 45 ml/kg/min (intermediário)
    vo2_ref = 45.0
    ratio = vo2max / vo2_ref
    
    ## Quanto melhor o VO2max, menor o tempo (mais eficiente)
    fator_base = 1.0 / ratio
    
    ## Aplicar impacto cardio do movimento
    fator_final = 1.0 + ((fator_base - 1.0) * cardio_impact)
    
    return fator_final

def calcular_fator_rm(carga_wod, rm_atleta):
    """
    Calcula fator de dificuldade baseado em % de 1RM
    """
    if rm_atleta == 0:
        return 1.5
    
    pct_rm = (carga_wod / rm_atleta) * 100
    
    if pct_rm < 30:
        return 0.7  ## Muito leve
    elif pct_rm < 50:
        return 0.9  ## Leve
    elif pct_rm < 65:
        return 1.1  ## Moderado
    elif pct_rm < 80:
        return 1.4  ## Pesado
    elif pct_rm < 90:
        return 1.7  ## Muito pesado
    else:
        return 2.2  ## Máximo

def prever_repmax_exercicio(exercicio, peso_usado, reps_realizadas, perfil):
    """
    Prevê quantas repetições máximas o atleta consegue fazer
    """
    dados_mov = MOVIMENTOS_DB.get(exercicio)
    
    if not dados_mov:
        return None
    
    ## Se usa 1RM
    if dados_mov.get('usa_1rm', False):
        rm_ref = dados_mov['rm_ref']
        rm_atleta = perfil.get(rm_ref, 100)
        
        ## Calcular 1RM teórico do peso usado
        formulas_1rm = calcular_1rm_multiplas_formulas(peso_usado, reps_realizadas)
        rm_teorico = np.mean(list(formulas_1rm.values()))
        
        ## Calcular percentual
        pct_rm = (peso_usado / rm_atleta) * 100
        
        ## Estimar rep max baseado em percentuais conhecidos
        if pct_rm >= 95:
            rep_max_estimado = int(reps_realizadas * 1.1)
        elif pct_rm >= 90:
            rep_max_estimado = int(reps_realizadas * 1.2)
        elif pct_rm >= 85:
            rep_max_estimado = int(reps_realizadas * 1.4)
        elif pct_rm >= 80:
            rep_max_estimado = int(reps_realizadas * 1.6)
        elif pct_rm >= 75:
            rep_max_estimado = int(reps_realizadas * 2.0)
        elif pct_rm >= 70:
            rep_max_estimado = int(reps_realizadas * 2.5)
        else:
            rep_max_estimado = int(reps_realizadas * 3.5)
        
        return {
            'rep_max': rep_max_estimado,
            'pct_1rm': round(pct_rm, 1),
            '1rm_teorico': round(rm_teorico, 1),
            '1rm_atual': round(rm_atleta, 1)
        }
    
    ## Se usa repmax direto
    elif dados_mov.get('usa_repmax', False):
        rep_ref_key = dados_mov['rep_ref']
        max_reps = perfil.get(rep_ref_key, 20)
        
        ## Estimar baseado na fadiga
        fator_fadiga = 1 + (dados_mov['fadiga_acum'] * reps_realizadas)
        rep_max_estimado = int(max_reps / fator_fadiga)
        
        return {
            'rep_max': rep_max_estimado,
            'max_atual': max_reps,
            'reps_realizadas': reps_realizadas
        }
    
    return None

## ============================================================================
## INTERFACE PRINCIPAL
## ============================================================================

## Título
st.title("🏋️‍♂️ CrossFit WOD Predictor Pro")
st.markdown("**Plataforma Integrada de Predição e Análise de Performance**")

## ============================================================================
## SIDEBAR - PERFIL DO ATLETA
## ============================================================================
with st.sidebar:
    st.header("👤 Perfil do Atleta")
    
    with st.expander("📝 Dados Pessoais", expanded=True):
        st.session_state.perfil_atleta['nome'] = st.text_input(
            "Nome",
            value=st.session_state.perfil_atleta['nome']
        )
        
        st.session_state.perfil_atleta['nivel'] = st.selectbox(
            "Nível",
            ["Iniciante", "Intermediário", "Avançado", "Elite"],
            index=["Iniciante", "Intermediário", "Avançado", "Elite"].index(
                st.session_state.perfil_atleta['nivel']
            )
        )
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.session_state.perfil_atleta['idade'] = st.number_input(
                "Idade",
                min_value=16,
                max_value=80,
                value=st.session_state.perfil_atleta['idade']
            )
        
        with col_s2:
            st.session_state.perfil_atleta['peso'] = st.number_input(
                "Peso (kg)",
                min_value=40.0,
                max_value=150.0,
                value=st.session_state.perfil_atleta['peso'],
                step=0.5
            )
    
    with st.expander("💪 Força (1RM)", expanded=True):
        st.session_state.perfil_atleta['1rm_back_squat'] = st.number_input(
            "Back Squat (kg)",
            min_value=20.0,
            max_value=400.0,
            value=st.session_state.perfil_atleta['1rm_back_squat'],
            step=2.5
        )
        
        st.session_state.perfil_atleta['1rm_deadlift'] = st.number_input(
            "Deadlift (kg)",
            min_value=20.0,
            max_value=450.0,
            value=st.session_state.perfil_atleta['1rm_deadlift'],
            step=2.5
        )
        
        st.session_state.perfil_atleta['1rm_clean'] = st.number_input(
            "Clean (kg)",
            min_value=20.0,
            max_value=250.0,
            value=st.session_state.perfil_atleta['1rm_clean'],
            step=2.5
        )
        
        st.session_state.perfil_atleta['1rm_snatch'] = st.number_input(
            "Snatch (kg)",
            min_value=20.0,
            max_value=200.0,
            value=st.session_state.perfil_atleta['1rm_snatch'],
            step=2.5
        )
        
        st.session_state.perfil_atleta['1rm_bench'] = st.number_input(
            "Bench Press (kg)",
            min_value=20.0,
            max_value=300.0,
            value=st.session_state.perfil_atleta['1rm_bench'],
            step=2.5
        )
    
    with st.expander("🤸 Ginástica (Rep Max)", expanded=True):
        st.session_state.perfil_atleta['max_pullups'] = st.number_input(
            "Pull-ups Máximas",
            min_value=0,
            max_value=100,
            value=st.session_state.perfil_atleta['max_pullups']
        )
        
        st.session_state.perfil_atleta['max_pushups'] = st.number_input(
            "Push-ups Máximas",
            min_value=0,
            max_value=200,
            value=st.session_state.perfil_atleta['max_pushups']
        )
        
        st.session_state.perfil_atleta['max_hspu'] = st.number_input(
            "HSPU Máximas",
            min_value=0,
            max_value=50,
            value=st.session_state.perfil_atleta['max_hspu']
        )
    
    with st.expander("🫁 Capacidade Cardiorrespiratória", expanded=True):
        st.session_state.perfil_atleta['vo2max'] = st.number_input(
            "VO2max (ml/kg/min)",
            min_value=20.0,
            max_value=80.0,
            value=st.session_state.perfil_atleta['vo2max'],
            step=0.5
        )
        
        col_fc1, col_fc2 = st.columns(2)
        with col_fc1:
            st.session_state.perfil_atleta['fc_repouso'] = st.number_input(
                "FC Repouso",
                min_value=40,
                max_value=100,
                value=st.session_state.perfil_atleta['fc_repouso']
            )
        
        with col_fc2:
            st.session_state.perfil_atleta['fc_max'] = st.number_input(
                "FC Máxima",
                min_value=140,
                max_value=220,
                value=st.session_state.perfil_atleta['fc_max']
            )
    
    st.markdown("---")
    if st.button("💾 Salvar Perfil", use_container_width=True):
        st.success("✅ Perfil salvo!")

## ============================================================================
## NAVEGAÇÃO PRINCIPAL
## ============================================================================
st.markdown("---")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Preditor de WOD",
    "🔮 Preditor de RepMax",
    "💪 Calculadora 1RM",
    "🫁 Capacidade Cardio",
    "🎥 Análise Biomecânica",
    "📈 Histórico"
])

## ============================================================================
## TAB 1: PREDITOR DE WOD (COM INTEGRAÇÃO COMPLETA)
## ============================================================================
with tab1:
    st.header("📊 Preditor de Tempo de WOD")
    st.caption("Predição integrada com perfil de força, repetições máximas e capacidade cardiorrespiratória")
    
    ## Configuração do WOD
    col_config1, col_config2 = st.columns([3, 1])
    
    with col_config1:
        nome_wod = st.text_input("Nome do WOD", value="Meu WOD", key="nome_wod_tab1")
    
    with col_config2:
        tipo_wod = st.selectbox(
            "Formato",
            ["For Time", "AMRAP", "Rounds for Time"],
            key="tipo_wod_tab1"
        )
    
    if tipo_wod in ["For Time", "Rounds for Time"]:
        rounds_totais = st.number_input(
            "Número de Rounds",
            min_value=1,
            max_value=21,
            value=5,
            key="rounds_tab1"
        )
    elif tipo_wod == "AMRAP":
        tempo_amrap = st.number_input(
            "Tempo AMRAP (minutos)",
            min_value=1,
            max_value=60,
            value=20,
            key="amrap_tab1"
        )
    
    st.markdown("---")
    
    ## Seleção de Movimentos
    st.subheader("🎯 Movimentos do WOD")
    num_movimentos = st.slider(
        "Quantos movimentos?",
        min_value=1,
        max_value=10,
        value=3,
        key="num_mov_tab1"
    )
    
    movimentos_selecionados = []
    
    for i in range(num_movimentos):
        st.markdown(f"**Movimento {i+1}:**")
        col_m1, col_m2, col_m3 = st.columns([2, 1, 1])
        
        with col_m1:
            movimento = st.selectbox(
                f"Exercício",
                list(MOVIMENTOS_DB.keys()),
                key=f"mov_tab1_{i}"
            )
        
        with col_m2:
            reps = st.number_input(
                f"Reps/Cal/m",
                min_value=1,
                max_value=200,
                value=10,
                key=f"reps_tab1_{i}"
            )
        
        ## Se o movimento usa carga
        carga = 0
        if MOVIMENTOS_DB[movimento].get('usa_1rm', False):
            with col_m3:
                carga = st.number_input(
                    f"Carga (kg)",
                    min_value=10.0,
                    max_value=300.0,
                    value=60.0,
                    step=2.5,
                    key=f"carga_tab1_{i}"
                )
        
        movimentos_selecionados.append({
            "nome": movimento,
            "reps": reps,
            "carga": carga,
            "dados": MOVIMENTOS_DB[movimento]
        })
    
    st.markdown("---")
    
    ## Botão de Calcular
    if st.button("🔮 Calcular Predição Integrada", type="primary", use_container_width=True):
        
        perfil = st.session_state.perfil_atleta
        
        ## Fatores do Atleta
        fator_exp = {
            "Iniciante": 1.4,
            "Intermediário": 1.0,
            "Avançado": 0.8,
            "Elite": 0.65
        }[perfil['nivel']]
        
        idade = perfil['idade']
        if idade < 25:
            fator_idade = 0.95
        elif idade < 35:
            fator_idade = 1.0
        elif idade < 45:
            fator_idade = 1.15
        else:
            fator_idade = 1.3
        
        ## Cálculo Integrado
        tempo_total_seg = 0
        fadiga_acumulada = 0
        impacto_cardio_total = 0
        detalhes_calculo = []
        analise_movimentos = []
        
        if tipo_wod in ["For Time", "Rounds for Time"]:
            for round_num in range(rounds_totais):
                tempo_round = 0
                
                for mov in movimentos_selecionados:
                    tempo_base_rep = mov["dados"]["dificuldade"]
                    
                    ## FATOR 1: Fadiga Acumulada
                    fator_fadiga = 1 + (fadiga_acumulada * 0.4)
                    
                    ## FATOR 2: Capacidade Cardiorrespiratória
                    fator_cardio = calcular_fator_cardio(
                        perfil['vo2max'],
                        mov["dados"]["cardio_impact"]
                    )
                    
                    ## FATOR 3: Força (1RM) ou RepMax
                    fator_forca = 1.0
                    analise_mov = {
                        "movimento": mov["nome"],
                        "reps": mov["reps"]
                    }
                    
                    if mov["dados"].get('usa_1rm', False) and mov["carga"] > 0:
                        rm_ref = mov["dados"]['rm_ref']
                        rm_atleta = perfil.get(rm_ref, 100)
                        fator_forca = calcular_fator_rm(mov["carga"], rm_atleta)
                        
                        pct_rm = (mov["carga"] / rm_atleta) * 100
                        analise_mov.update({
                            "tipo_analise": "1RM",
                            "carga": mov["carga"],
                            "1rm_atleta": rm_atleta,
                            "pct_1rm": round(pct_rm, 1),
                            "fator_aplicado": round(fator_forca, 2)
                        })
                    
                    elif mov["dados"].get('usa_repmax', False):
                        rep_ref_key = mov["dados"]['rep_ref']
                        max_reps = perfil.get(rep_ref_key, 20)
                        fator_forca = calcular_repmax_teorico(max_reps, mov["reps"])
                        
                        analise_mov.update({
                            "tipo_analise": "RepMax",
                            "max_reps_atleta": max_reps,
                            "reps_wod": mov["reps"],
                            "pct_repmax": round((mov["reps"]/max_reps)*100, 1) if max_reps > 0 else 0,
                            "fator_aplicado": round(fator_forca, 2)
                        })
                    else:
                        analise_mov.update({
                            "tipo_analise": "Padrão",
                            "fator_aplicado": 1.0
                        })
                    
                    analise_movimentos.append(analise_mov)
                    
                    ## Tempo do movimento
                    tempo_movimento = (
                        mov["reps"] * tempo_base_rep *
                        fator_fadiga * fator_exp * fator_idade *
                        fator_cardio * fator_forca
                    )
                    
                    ## Acumular fadiga
                    fadiga_acumulada += mov["dados"]["fadiga_acum"] * mov["reps"] * fator_forca
                    
                    ## Impacto cardio
                    impacto_cardio_total += mov["dados"]["cardio_impact"] * mov["reps"]
                    
                    tempo_round += tempo_movimento
                    
                    detalhes_calculo.append({
                        "Round": round_num + 1,
                        "Movimento": mov["nome"],
                        "Reps": mov["reps"],
                        "Tempo (s)": round(tempo_movimento, 1),
                        "Fadiga": round(fadiga_acumulada, 2),
                        "F.Cardio": round(fator_cardio, 2),
                        "F.Força": round(fator_forca, 2)
                    })
                
                ## Tempo de transição
                tempo_round += len(movimentos_selecionados) * 3.5
                tempo_total_seg += tempo_round
        
        ## Converter para minutos
        minutos = int(tempo_total_seg // 60)
        segundos = int(tempo_total_seg % 60)
        
        ## EXIBIÇÃO DE RESULTADOS
        st.success("✅ Predição Calculada com Integração Completa!")
        
        ## Métricas Principais
        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
        
        col_r1.metric(
            "⏱️ Tempo Previsto",
            f"{minutos}:{segundos:02d}",
            delta=f"{round(tempo_total_seg/60, 1)} min"
        )
        
        col_r2.metric(
            "🔥 Fadiga Total",
            f"{round(fadiga_acumulada, 1)}",
            delta="Alta" if fadiga_acumulada > 8 else "Moderada"
        )
        
        col_r3.metric(
            "🫁 Impacto Cardio",
            f"{round(impacto_cardio_total, 1)}",
            delta="Alto" if impacto_cardio_total > 30 else "Moderado"
        )
        
        ## Intensidade baseada em VO2max e tempo
        intensidade_score = min(10, round((tempo_total_seg/60) / (perfil['vo2max']/10), 1))
        col_r4.metric(
            "💪 Intensidade",
            f"{intensidade_score}/10",
            delta="Pesado" if intensidade_score > 7 else "Moderado"
        )
        
        ## Análise Detalhada por Movimento
        st.markdown("---")
        st.subheader("🔬 Análise Integrada por Movimento")
        
        for analise in analise_movimentos:
            with st.expander(f"📊 {analise['movimento']} - {analise['reps']} reps"):
                if analise['tipo_analise'] == "1RM":
                    col_a1, col_a2, col_a3 = st.columns(3)
                    col_a1.metric("Carga Usada", f"{analise['carga']} kg")
                    col_a2.metric("1RM do Atleta", f"{analise['1rm_atleta']} kg")
                    col_a3.metric("% de 1RM", f"{analise['pct_1rm']}%")
                    
                    if analise['pct_1rm'] > 85:
                        st.error("⚠️ **CARGA MUITO PESADA** - Alta chance de fadiga rápida")
                    elif analise['pct_1rm'] > 70:
                        st.warning("⚠️ **Carga Pesada** - Gerencie bem as repetições")
                    elif analise['pct_1rm'] > 50:
                        st.info("ℹ️ **Carga Moderada** - Boa zona de trabalho")
                    else:
                        st.success("✅ **Carga Leve** - Foque na velocidade")
                
                elif analise['tipo_analise'] == "RepMax":
                    col_b1, col_b2, col_b3 = st.columns(3)
                    col_b1.metric("Reps no WOD", analise['reps_wod'])
                    col_b2.metric("Seu RepMax", analise['max_reps_atleta'])
                    col_b3.metric("% do RepMax", f"{analise['pct_repmax']}%")
                    
                    if analise['pct_repmax'] > 90:
                        st.error("⚠️ **MUITO DIFÍCIL** - Você vai quebrar rápido")
                    elif analise['pct_repmax'] > 70:
                        st.warning("⚠️ **Difícil** - Planeje quebras estratégicas")
                    elif analise['pct_repmax'] > 50:
                        st.info("ℹ️ **Desafiador** - Controlável com técnica")
                    else:
                        st.success("✅ **Gerenciável** - Pode fazer sets grandes")
                
                st.metric("Fator de Dificuldade Aplicado", f"{analise['fator_aplicado']}x")
        
        ## Tabela Detalhada
        st.markdown("---")
        st.subheader("📋 Detalhamento Completo por Round")
        df_detalhes = pd.DataFrame(detalhes_calculo)
        st.dataframe(df_detalhes, use_container_width=True)
        
        ## Recomendações Baseadas no Perfil
        st.markdown("---")
        st.subheader("💡 Recomendações Personalizadas")
        
        recomendacoes = []
        
        ## Baseado em VO2max
        if perfil['vo2max'] < 40:
            recomendacoes.append("🫁 **Cardio Baixo**: Gerencie bem o ritmo, evite sprints no início")
        elif perfil['vo2max'] > 55:
            recomendacoes.append("🫁 **Cardio Excelente**: Você pode empurrar forte nos movimentos cardio")
        
        ## Baseado em força
        mov_pesados = [a for a in analise_movimentos if a.get('pct_1rm', 0) > 75]
        if len(mov_pesados) > 0:
            recomendacoes.append(f"💪 **{len(mov_pesados)} movimento(s) pesado(s)**: Faça singles ou duplas para preservar energia")
        
        ## Baseado em repmax
        mov_alta_rep = [a for a in analise_movimentos if a.get('pct_repmax', 0) > 70]
        if len(mov_alta_rep) > 0:
            recomendacoes.append(f"🤸 **{len(mov_alta_rep)} movimento(s) de alta repetição**: Quebre estrategicamente, não vá até a falha")
        
        ## Baseado em fadiga
        if fadiga_acumulada > 10:
            recomendacoes.append("🔥 **WOD de Alta Fadiga**: Comece conservador, o final vai ficar muito difícil")
        
        for rec in recomendacoes:
            st.info(rec)
        
        ## Salvar Treino
        if st.button("💾 Salvar WOD no Histórico", key="salvar_wod_tab1"):
            treino_info = {
                "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "nome": nome_wod,
                "tipo": tipo_wod,
                "tempo_previsto": f"{minutos}:{segundos:02d}",
                "fadiga": round(fadiga_acumulada, 2),
                "impacto_cardio": round(impacto_cardio_total, 1),
                "intensidade": intensidade_score,
                "movimentos": len(movimentos_selecionados),
                "nivel_atleta": perfil['nivel'],
                "vo2max": perfil['vo2max']
            }
            st.session_state.treinos_salvos.append(treino_info)
            st.success("✅ WOD salvo no histórico!")

## ============================================================================
## TAB 2: PREDITOR DE REPMAX
## ============================================================================
with tab2:
    st.header("🔮 Preditor de Repetições Máximas")
    st.caption("Estime suas repetições máximas baseado em performance e perfil")
    
    st.subheader("📊 Teste de Performance")
    
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        exercicio_repmax = st.selectbox(
            "Selecione o Exercício",
            list(MOVIMENTOS_DB.keys()),
            key="ex_repmax"
        )
    
    with col_p2:
        reps_realizadas_test = st.number_input(
            "Repetições Realizadas no Teste",
            min_value=1,
            max_value=100,
            value=10,
            key="reps_test"
        )
    
    ## Se o exercício usa carga
    peso_usado_test = 0
    if MOVIMENTOS_DB[exercicio_repmax].get('usa_1rm', False):
        peso_usado_test = st.number_input(
            "Peso Usado no Teste (kg)",
            min_value=10.0,
            max_value=300.0,
            value=60.0,
            step=2.5,
            key="peso_test"
        )
    
    if st.button("🔮 Prever RepMax", type="primary", use_container_width=True):
        
        resultado = prever_repmax_exercicio(
            exercicio_repmax,
            peso_usado_test,
            reps_realizadas_test,
            st.session_state.perfil_atleta
        )
        
        if resultado:
            st.success("✅ Predição Calculada!")
            
            if 'pct_1rm' in resultado:
                ## Exercício com carga
                col_res1, col_res2, col_res3, col_res4 = st.columns(4)
                
                col_res1.metric(
                    "🔮 RepMax Estimado",
                    f"{resultado['rep_max']} reps"
                )
                
                col_res2.metric(
                    "💪 Seu 1RM Atual",
                    f"{resultado['1rm_atual']} kg"
                )
                
                col_res3.metric(
                    "📊 % de 1RM Usado",
                    f"{resultado['pct_1rm']}%"
                )
                
                col_res4.metric(
                    "🏋️ 1RM Teórico",
                    f"{resultado['1rm_teorico']} kg"
                )
                
                ## Tabela de Predição
                st.markdown("---")
                st.subheader("📈 Tabela de Predição de Repetições")
                
                percentuais = [95, 90, 85, 80, 75, 70, 65, 60, 55, 50]
                cargas = [round(resultado['1rm_atual'] * (p/100), 1) for p in percentuais]
                
                ## Estimar reps para cada percentual
                reps_estimadas = []
                for pct in percentuais:
                    if pct >= 95:
                        reps_estimadas.append("1-2")
                    elif pct >= 90:
                        reps_estimadas.append("2-4")
                    elif pct >= 85:
                        reps_estimadas.append("4-6")
                    elif pct >= 80:
                        reps_estimadas.append("6-8")
                    elif pct >= 75:
                        reps_estimadas.append("8-12")
                    elif pct >= 70:
                        reps_estimadas.append("12-15")
                    elif pct >= 65:
                        reps_estimadas.append("15-20")
                    elif pct >= 60:
                        reps_estimadas.append("20-25")
                    elif pct >= 55:
                        reps_estimadas.append("25-30")
                    else:
                        reps_estimadas.append("30+")
                
                df_predicao = pd.DataFrame({
                    "% 1RM": [f"{p}%" for p in percentuais],
                    "Carga (kg)": cargas,
                    "Reps Estimadas": reps_estimadas
                })
                
                st.dataframe(df_predicao, use_container_width=True)
            
            else:
                ## Exercício de ginástica
                col_res1, col_res2, col_res3 = st.columns(3)
                
                col_res1.metric(
                    "🔮 RepMax Estimado",
                    f"{resultado['rep_max']} reps"
                )
                
                col_res2.metric(
                    "💪 Seu Max Atual",
                    f"{resultado['max_atual']} reps"
                )
                
                col_res3.metric(
                    "📊 Reps no Teste",
                    f"{resultado['reps_realizadas']} reps"
                )
                
                ## Recomendações
                st.markdown("---")
                st.subheader("💡 Estratégia para WODs")
                
                sets_recomendados = []
                max_rep = resultado['rep_max']
                
                for total_reps in [21, 30, 50, 100]:
                    if total_reps <= max_rep * 0.5:
                        estrategia = "Ininterrupto ou 2 sets"
                    elif total_reps <= max_rep * 0.8:
                        estrategia = "3-4 sets"
                    elif total_reps <= max_rep * 1.2:
                        estrategia = "5-6 sets"
                    else:
                        estrategia = "Sets pequenos (singles ou duplas)"
                    
                    sets_recomendados.append({
                        "Total de Reps no WOD": total_reps,
                        "Estratégia": estrategia
                    })
                
                df_estrategia = pd.DataFrame(sets_recomendados)
                st.dataframe(df_estrategia, use_container_width=True)
            
            ## Salvar no histórico
            if st.button("💾 Salvar no Histórico", key="salvar_repmax"):
                registro = {
                    "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "exercicio": exercicio_repmax,
                    "reps_realizadas": reps_realizadas_test,
                    "peso_usado": peso_usado_test if peso_usado_test > 0 else None,
                    "repmax_estimado": resultado['rep_max']
                }
                st.session_state.historico_repmax.append(registro)
                st.success("✅ Registro salvo!")

## ============================================================================
## TAB 3: CALCULADORA 1RM
## ============================================================================
with tab3:
    st.header("💪 Calculadora de 1 Repetição Máxima")
    st.caption("Múltiplas fórmulas científicas para estimativa precisa")
    
    col_1rm1, col_1rm2 = st.columns(2)
    
    with col_1rm1:
        st.subheader("📊 Dados do Levantamento")
        
        peso_levantado = st.number_input(
            "Peso Levantado (kg)",
            min_value=10.0,
            max_value=500.0,
            value=100.0,
            step=2.5,
            key="peso_1rm"
        )
        
        reps_realizadas = st.number_input(
            "Repetições Realizadas",
            min_value=1,
            max_value=20,
            value=5,
            key="reps_1rm"
        )
        
        exercicio_1rm = st.selectbox(
            "Exercício",
            ["Back Squat", "Deadlift", "Bench Press", "Clean", "Snatch", "Front Squat", "Overhead Press"],
            key="ex_1rm"
        )
    
    with col_1rm2:
        st.subheader("🔬 Fórmulas Disponíveis")
        st.markdown("""
        - **Epley**: Clássica e amplamente usada
        - **Brzycki**: Mais conservadora
        - **Lander**: Baseada em estudos recentes
        - **Lombardi**: Fórmula exponencial
        - **O'Conner**: Alternativa moderna
        """)
    
    if st.button("🔮 Calcular 1RM", type="primary", use_container_width=True, key="calc_1rm"):
        
        formulas = calcular_1rm_multiplas_formulas(peso_levantado, reps_realizadas)
        media_1rm = np.mean(list(formulas.values()))
        
        st.success("✅ Cálculo Concluído!")
        
        ## Métricas
        col_m1, col_m2, col_m3 = st.columns(3)
        
        col_m1.metric(
            "📊 1RM Médio",
            f"{media_1rm:.1f} kg",
            delta=f"+{media_1rm - peso_levantado:.1f} kg"
        )
        
        col_m2.metric(
            "📈 Mais Conservador",
            f"{min(formulas.values()):.1f} kg"
        )
        
        col_m3.metric(
            "🚀 Mais Otimista",
            f"{max(formulas.values()):.1f} kg"
        )
        
        ## Tabela de Fórmulas
        st.markdown("---")
        st.subheader("📋 Resultados por Fórmula")
        
        df_formulas = pd.DataFrame({
            "Fórmula": list(formulas.keys()) + ["MÉDIA"],
            "1RM (kg)": [round(v, 1) for v in formulas.values()] + [round(media_1rm, 1)]
        })
        
        st.dataframe(df_formulas, use_container_width=True)
        
        ## Tabela de Percentuais
        st.markdown("---")
        st.subheader("💯 Tabela de Percentuais para Treino")
        
        percentuais = [100, 95, 90, 85, 80, 75, 70, 65, 60, 55, 50]
        cargas = [round(media_1rm * (p/100), 1) for p in percentuais]
        usos = [
            "Teste de 1RM",
            "1-2 reps (Força Máxima)",
            "2-4 reps (Força)",
            "4-6 reps (Força-Hipertrofia)",
            "6-8 reps (Hipertrofia)",
            "8-12 reps (Hipertrofia)",
            "12-15 reps (Resistência)",
            "15-20 reps (Resistência)",
            "20-25 reps (Endurance)",
            "25-30 reps (Endurance)",
            "30+ reps (Condicionamento)"
        ]
        
        df_percentuais = pd.DataFrame({
            "% 1RM": [f"{p}%" for p in percentuais],
            "Carga (kg)": cargas,
            "Uso Recomendado": usos
        })
        
        st.dataframe(df_percentuais, use_container_width=True)
        
        ## Atualizar perfil
        st.markdown("---")
        if st.button("💾 Atualizar 1RM no Perfil", key="update_1rm"):
            mapeamento = {
                "Back Squat": "1rm_back_squat",
                "Deadlift": "1rm_deadlift",
                "Bench Press": "1rm_bench",
                "Clean": "1rm_clean",
                "Snatch": "1rm_snatch",
                "Front Squat": "1rm_back_squat",
                "Overhead Press": "1rm_bench"
            }
            
            if exercicio_1rm in mapeamento:
                st.session_state.perfil_atleta[mapeamento[exercicio_1rm]] = round(media_1rm, 1)
                st.success(f"✅ {exercicio_1rm} atualizado para {media_1rm:.1f} kg no perfil!")

## ============================================================================
## TAB 4: CAPACIDADE CARDIORRESPIRATÓRIA
## ============================================================================
with tab4:
    st.header("🫁 Preditor de Capacidade Cardiorrespiratória")
    st.caption("Estimativa de VO2max e zonas de treinamento")
    
    col_cardio1, col_cardio2 = st.columns(2)
    
    with col_cardio1:
        st.subheader("👤 Dados Pessoais")
        idade_cardio = st.session_state.perfil_atleta['idade']
        sexo = st.selectbox("Sexo", ["Masculino", "Feminino"], key="sexo_cardio")
        peso_cardio = st.session_state.perfil_atleta['peso']
        fc_repouso = st.session_state.perfil_atleta['fc_repouso']
        
        st.info(f"Dados do perfil: {idade_cardio} anos, {peso_cardio} kg, FC repouso: {fc_repouso} bpm")
    
    with col_cardio2:
        st.subheader("🏃 Teste de Performance")
        
        tipo_teste = st.selectbox(
            "Tipo de Teste",
            ["Cooper (12 min)", "1 Mile Run", "2000m Row", "500m Row"],
            key="tipo_teste_cardio"
        )
        
        if tipo_teste == "Cooper (12 min)":
            distancia = st.number_input(
                "Distância percorrida (metros)",
                min_value=1000,
                max_value=4000,
                value=2400,
                key="dist_cooper"
            )
            vo2max_calculado = (distancia - 504.9) / 44.73
        
        elif tipo_teste == "1 Mile Run":
            tempo_min = st.number_input(
                "Tempo (minutos)",
                min_value=4.0,
                max_value=20.0,
                value=8.0,
                step=0.1,
                key="tempo_mile"
            )
            vo2max_calculado = 132.853 - (0.0769 * peso_cardio) - (0.3877 * idade_cardio) + (6.315 * (1 if sexo == "Masculino" else 0)) - (3.2649 * tempo_min) - (0.1565 * fc_repouso)
        
        elif tipo_teste == "2000m Row":
            tempo_seg = st.number_input(
                "Tempo (segundos)",
                min_value=360,
                max_value=900,
                value=480,
                key="tempo_2k"
            )
            pace_500m = tempo_seg / 4
            vo2max_calculado = 15000 / pace_500m - 35
        
        else:  ## 500m Row
            tempo_seg = st.number_input(
                "Tempo (segundos)",
                min_value=80,
                max_value=200,
                value=120,
                key="tempo_500"
            )
            vo2max_calculado = 12000 / tempo_seg - 20
    
    if st.button("🔮 Calcular VO2max e Zonas", type="primary", use_container_width=True, key="calc_vo2"):
        
        fc_max = 220 - idade_cardio
        fc_reserva = fc_max - fc_repouso
        
        st.success("✅ Análise Concluída!")
        
        ## Métricas
        col_v1, col_v2, col_v3 = st.columns(3)
        
        col_v1.metric("🫀 VO2max", f"{vo2max_calculado:.1f} ml/kg/min")
        col_v2.metric("💓 FC Máxima", f"{fc_max} bpm")
        col_v3.metric("📊 FC Reserva", f"{fc_reserva} bpm")
        
        ## Classificação
        st.markdown("---")
        st.subheader("📊 Classificação de VO2max")
        
        if sexo == "Masculino":
            if vo2max_calculado > 56:
                classificacao = "Excelente 🏆"
                cor = "success"
            elif vo2max_calculado > 51:
                classificacao = "Muito Bom 💪"
                cor = "success"
            elif vo2max_calculado > 45:
                classificacao = "Bom ✅"
                cor = "info"
            elif vo2max_calculado > 38:
                classificacao = "Regular ⚠️"
                cor = "warning"
            else:
                classificacao = "Abaixo da Média 📉"
                cor = "error"
        else:
            if vo2max_calculado > 49:
                classificacao = "Excelente 🏆"
                cor = "success"
            elif vo2max_calculado > 43:
                classificacao = "Muito Bom 💪"
                cor = "success"
            elif vo2max_calculado > 39:
                classificacao = "Bom ✅"
                cor = "info"
            elif vo2max_calculado > 33:
                classificacao = "Regular ⚠️"
                cor = "warning"
            else:
                classificacao = "Abaixo da Média 📉"
                cor = "error"
        
        if cor == "success":
            st.success(f"**Classificação:** {classificacao}")
        elif cor == "info":
            st.info(f"**Classificação:** {classificacao}")
        elif cor == "warning":
            st.warning(f"**Classificação:** {classificacao}")
        else:
            st.error(f"**Classificação:** {classificacao}")
        
        ## Zonas de Treinamento
        st.markdown("---")
        st.subheader("🎯 Zonas de Treinamento Cardíaco (Método Karvonen)")
        
        zonas = {
            "Zona 1 - Recuperação": (0.50, 0.60),
            "Zona 2 - Aeróbica Leve": (0.60, 0.70),
            "Zona 3 - Aeróbica Moderada": (0.70, 0.80),
            "Zona 4 - Limiar Anaeróbico": (0.80, 0.90),
            "Zona 5 - Máxima": (0.90, 1.00)
        }
        
        dados_zonas = []
        for zona, (min_pct, max_pct) in zonas.items():
            fc_min = int(fc_repouso + (fc_reserva * min_pct))
            fc_max_zona = int(fc_repouso + (fc_reserva * max_pct))
            dados_zonas.append({
                "Zona": zona,
                "FC Mín (bpm)": fc_min,
                "FC Máx (bpm)": fc_max_zona,
                "% FC Reserva": f"{int(min_pct*100)}-{int(max_pct*100)}%"
            })
        
        df_zonas = pd.DataFrame(dados_zonas)
        st.dataframe(df_zonas, use_container_width=True)
        
        ## Atualizar perfil
        st.markdown("---")
        if st.button("💾 Atualizar VO2max no Perfil", key="update_vo2"):
            st.session_state.perfil_atleta['vo2max'] = round(vo2max_calculado, 1)
            st.session_state.perfil_atleta['fc_max'] = fc_max
            st.success(f"✅ VO2max atualizado para {vo2max_calculado:.1f} ml/kg/min no perfil!")

## ============================================================================
## TAB 5: ANÁLISE BIOMECÂNICA
## ============================================================================
with tab5:
    st.header("🎥 Analisador Biomecânico de Movimentos")
    st.caption("Análise avançada de postura e técnica com IA")
    
    if not HAS_VISION:
        st.error("""
        ⚠️ **Módulo Desabilitado**
        
        As bibliotecas de visão computacional não estão instaladas.
        
        **Para habilitar:**
        1. Adicione ao `requirements.txt`:
        ```
        opencv-python-headless
        mediapipe
        ```
        2. Faça commit e push
        3. Reinicie o app
        """)
    else:
        tipo_analise = st.selectbox(
            "Selecione o Movimento",
            ["Squat", "Deadlift", "Pull-up", "Push-up", "Overhead Press"],
            key="tipo_analise_bio"
        )
        
        arquivo_video = st.file_uploader(
            "Envie o vídeo (vista lateral)",
            type=["mp4", "mov", "avi"],
            key="video_bio"
        )
        
        if arquivo_video:
            st.info("📹 Funcionalidade de análise biomecânica disponível! (Código extenso - contate para implementação completa)")

## ============================================================================
## TAB 6: HISTÓRICO
## ============================================================================
with tab6:
    st.header("📈 Histórico e Evolução")
    
    tab_hist1, tab_hist2 = st.tabs(["WODs Salvos", "Testes de RepMax"])
    
    with tab_hist1:
        if len(st.session_state.treinos_salvos) == 0:
            st.info("📭 Nenhum WOD salvo ainda")
        else:
            st.success(f"✅ {len(st.session_state.treinos_salvos)} WOD(s) salvo(s)")
            df_wods = pd.DataFrame(st.session_state.treinos_salvos)
            st.dataframe(df_wods, use_container_width=True)
            
            if st.button("🗑️ Limpar Histórico WODs"):
                st.session_state.treinos_salvos = []
                st.rerun()
    
    with tab_hist2:
        if len(st.session_state.historico_repmax) == 0:
            st.info("📭 Nenhum teste de RepMax salvo")
        else:
            st.success(f"✅ {len(st.session_state.historico_repmax)}
