import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime

## Configuração da Página
st.set_page_config(
    page_title="CrossFit WOD Predictor Pro",
    page_icon="🏋️‍♂️",
    layout="wide"
)

## Título Principal
st.title("🏋️‍♂️ CrossFit WOD Predictor Pro")
st.markdown("**Predição de Performance, 1RM e Capacidade Cardiorrespiratória**")

## Inicializar Session State
if 'treinos_salvos' not in st.session_state:
    st.session_state.treinos_salvos = []

## Navegação Lateral
st.sidebar.header("🎯 Navegação")
opcao = st.sidebar.radio(
    "Selecione o Módulo:",
    ["📊 Preditor de Tempo de WOD", "💪 Calculadora de 1RM", "🫁 Preditor Cardiorrespiratório", "📈 Histórico de Treinos"]
)

## Base de Dados de Movimentos
MOVIMENTOS_DB = {
    ## Ginástica
    "Pull-ups": {"tipo": "ginastica", "dificuldade": 2.5, "fadiga_acum": 0.08},
    "Chest to Bar": {"tipo": "ginastica", "dificuldade": 3.0, "fadiga_acum": 0.10},
    "Muscle-ups": {"tipo": "ginastica", "dificuldade": 4.5, "fadiga_acum": 0.15},
    "Toes to Bar": {"tipo": "ginastica", "dificuldade": 2.8, "fadiga_acum": 0.09},
    "HSPU": {"tipo": "ginastica", "dificuldade": 3.5, "fadiga_acum": 0.12},
    "Burpees": {"tipo": "ginastica", "dificuldade": 2.0, "fadiga_acum": 0.07},
    "Box Jump (24/20)": {"tipo": "ginastica", "dificuldade": 1.5, "fadiga_acum": 0.05},
    
    ## Levantamento Peso
    "Thruster (43kg)": {"tipo": "levantamento", "dificuldade": 3.5, "fadiga_acum": 0.12},
    "Clean (60kg)": {"tipo": "levantamento", "dificuldade": 3.8, "fadiga_acum": 0.13},
    "Snatch (43kg)": {"tipo": "levantamento", "dificuldade": 4.0, "fadiga_acum": 0.14},
    "Deadlift (100kg)": {"tipo": "levantamento", "dificuldade": 3.2, "fadiga_acum": 0.11},
    "Back Squat (80kg)": {"tipo": "levantamento", "dificuldade": 3.0, "fadiga_acum": 0.10},
    "Front Squat (70kg)": {"tipo": "levantamento", "dificuldade": 3.3, "fadiga_acum": 0.11},
    "Overhead Squat (50kg)": {"tipo": "levantamento", "dificuldade": 3.7, "fadiga_acum": 0.12},
    
    ## Cardio
    "Row (cal)": {"tipo": "cardio", "dificuldade": 2.2, "fadiga_acum": 0.06},
    "Bike (cal)": {"tipo": "cardio", "dificuldade": 2.0, "fadiga_acum": 0.05},
    "Run (m)": {"tipo": "cardio", "dificuldade": 1.8, "fadiga_acum": 0.05},
    "Double Unders": {"tipo": "cardio", "dificuldade": 1.5, "fadiga_acum": 0.04},
}

## ============================================================================
## MÓDULO 1: PREDITOR DE TEMPO DE WOD
## ============================================================================
if opcao == "📊 Preditor de Tempo de WOD":
    st.header("📊 Predição de Tempo de WOD")
    st.caption("Sistema avançado com análise de fadiga acumulada e densidade metabólica")
    
    ## Perfil do Atleta
    st.subheader("👤 Perfil do Atleta")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        nivel_atleta = st.selectbox(
            "Nível do Atleta",
            ["Iniciante", "Intermediário", "Avançado", "Elite"],
            index=1
        )
        
    with col2:
        idade = st.number_input("Idade", min_value=16, max_value=80, value=30)
        
    with col3:
        peso = st.number_input("Peso Corporal (kg)", min_value=40.0, max_value=150.0, value=75.0)
    
    ## Fator de Experiência
    fator_exp = {
        "Iniciante": 1.3,
        "Intermediário": 1.0,
        "Avançado": 0.85,
        "Elite": 0.7
    }[nivel_atleta]
    
    ## Fator de Idade
    if idade < 25:
        fator_idade = 0.95
    elif idade < 35:
        fator_idade = 1.0
    elif idade < 45:
        fator_idade = 1.1
    else:
        fator_idade = 1.2
    
    st.markdown("---")
    
    ## Configuração do WOD
    st.subheader("⚙️ Configuração do WOD")
    
    col_wod1, col_wod2 = st.columns([2, 1])
    
    with col_wod1:
        nome_wod = st.text_input("Nome do WOD", value="Meu WOD", key="nome_wod")
        
    with col_wod2:
        tipo_wod = st.selectbox(
            "Formato",
            ["For Time", "AMRAP", "EMOM", "Rounds for Time"],
            key="tipo_wod"
        )
    
    if tipo_wod == "For Time" or tipo_wod == "Rounds for Time":
        rounds_totais = st.number_input("Número de Rounds", min_value=1, max_value=21, value=5, key="rounds")
    elif tipo_wod == "AMRAP":
        tempo_amrap = st.number_input("Tempo do AMRAP (min)", min_value=1, max_value=60, value=20, key="amrap_time")
    
    st.markdown("---")
    
    ## Seleção de Movimentos
    st.subheader("🎯 Movimentos do WOD")
    st.caption("Adicione até 10 movimentos")
    
    num_movimentos = st.slider("Quantos movimentos?", min_value=1, max_value=10, value=3, key="num_mov")
    
    movimentos_selecionados = []
    
    for i in range(num_movimentos):
        st.markdown(f"**Movimento {i+1}:**")
        col_m1, col_m2 = st.columns([2, 1])
        
        with col_m1:
            movimento = st.selectbox(
                f"Exercício",
                list(MOVIMENTOS_DB.keys()),
                key=f"mov_{i}"
            )
            
        with col_m2:
            reps = st.number_input(
                f"Repetições/Calorias/Metros",
                min_value=1,
                max_value=100,
                value=10,
                key=f"reps_{i}"
            )
        
        movimentos_selecionados.append({
            "nome": movimento,
            "reps": reps,
            "dados": MOVIMENTOS_DB[movimento]
        })
    
    st.markdown("---")
    
    ## Botão de Calcular
    if st.button("🔮 Calcular Predição de Tempo", type="primary", use_container_width=True):
        
        ## Cálculo de Fadiga e Tempo
        tempo_total_seg = 0
        fadiga_acumulada = 0
        detalhes_calculo = []
        
        if tipo_wod == "For Time" or tipo_wod == "Rounds for Time":
            for round_num in range(rounds_totais):
                tempo_round = 0
                
                for mov in movimentos_selecionados:
                    ## Tempo base por rep
                    tempo_base_rep = mov["dados"]["dificuldade"]
                    
                    ## Aplicar fadiga acumulada
                    fator_fadiga = 1 + (fadiga_acumulada * 0.5)
                    
                    ## Tempo do movimento
                    tempo_movimento = mov["reps"] * tempo_base_rep * fator_fadiga * fator_exp * fator_idade
                    
                    ## Acumular fadiga
                    fadiga_acumulada += mov["dados"]["fadiga_acum"] * mov["reps"]
                    
                    tempo_round += tempo_movimento
                    
                    detalhes_calculo.append({
                        "Round": round_num + 1,
                        "Movimento": mov["nome"],
                        "Reps": mov["reps"],
                        "Tempo (seg)": round(tempo_movimento, 1),
                        "Fadiga Acum": round(fadiga_acumulada, 2)
                    })
                
                ## Tempo de transição entre movimentos (3-5 seg)
                tempo_round += len(movimentos_selecionados) * 4
                
                tempo_total_seg += tempo_round
        
        ## Converter para minutos
        minutos = int(tempo_total_seg // 60)
        segundos = int(tempo_total_seg % 60)
        
        ## Exibir Resultado
        st.success("✅ Predição Calculada!")
        
        col_r1, col_r2, col_r3 = st.columns(3)
        
        col_r1.metric(
            "⏱️ Tempo Previsto",
            f"{minutos}:{segundos:02d}",
            delta=f"{round(tempo_total_seg/60, 1)} min"
        )
        
        col_r2.metric(
            "🔥 Fadiga Final",
            f"{round(fadiga_acumulada, 2)}",
            delta="Alta" if fadiga_acumulada > 5 else "Moderada"
        )
        
        col_r3.metric(
            "💪 Intensidade",
            f"{round(tempo_total_seg/60/10, 1)}/10",
            delta="Pesado" if tempo_total_seg > 900 else "Moderado"
        )
        
        ## Tabela Detalhada
        st.markdown("---")
        st.subheader("📋 Detalhamento por Movimento")
        df_detalhes = pd.DataFrame(detalhes_calculo)
        st.dataframe(df_detalhes, use_container_width=True)
        
        ## Salvar Treino
        if st.button("💾 Salvar Treino no Histórico"):
            treino_info = {
                "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "nome": nome_wod,
                "tipo": tipo_wod,
                "tempo_previsto": f"{minutos}:{segundos:02d}",
                "fadiga": round(fadiga_acumulada, 2),
                "movimentos": len(movimentos_selecionados)
            }
            st.session_state.treinos_salvos.append(treino_info)
            st.success("✅ Treino salvo no histórico!")

## ============================================================================
## MÓDULO 2: CALCULADORA DE 1RM
## ============================================================================
elif opcao == "💪 Calculadora de 1RM":
    st.header("💪 Calculadora de 1 Repetição Máxima (1RM)")
    st.caption("Múltiplas fórmulas para estimativa precisa de força máxima")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Dados do Levantamento")
        peso_levantado = st.number_input(
            "Peso Levantado (kg)",
            min_value=10.0,
            max_value=500.0,
            value=100.0,
            step=2.5
        )
        
        reps_realizadas = st.number_input(
            "Repetições Realizadas",
            min_value=1,
            max_value=20,
            value=5
        )
        
        exercicio = st.selectbox(
            "Exercício",
            ["Back Squat", "Deadlift", "Bench Press", "Clean", "Snatch", "Front Squat", "Overhead Press"]
        )
    
    with col2:
        st.subheader("🔬 Fórmulas Disponíveis")
        st.markdown("""
        - **Epley**: 1RM = peso × (1 + 0.0333 × reps)
        - **Brzycki**: 1RM = peso / (1.0278 - 0.0278 × reps)
        - **Lander**: 1RM = 100 × peso / (101.3 - 2.67123 × reps)
        - **Lombardi**: 1RM = peso × reps^0.1
        - **O'Conner**: 1RM = peso × (1 + 0.025 × reps)
        """)
    
    if st.button("🔮 Calcular 1RM", type="primary", use_container_width=True):
        
        ## Fórmula de Epley
        epley = peso_levantado * (1 + 0.0333 * reps_realizadas)
        
        ## Fórmula de Brzycki
        brzycki = peso_levantado / (1.0278 - 0.0278 * reps_realizadas)
        
        ## Fórmula de Lander
        lander = (100 * peso_levantado) / (101.3 - 2.67123 * reps_realizadas)
        
        ## Fórmula de Lombardi
        lombardi = peso_levantado * (reps_realizadas ** 0.1)
        
        ## Fórmula de O'Conner
        oconner = peso_levantado * (1 + 0.025 * reps_realizadas)
        
        ## Média
        media_1rm = np.mean([epley, brzycki, lander, lombardi, oconner])
        
        st.success("✅ Cálculo Concluído!")
        
        ## Métricas
        col_m1, col_m2, col_m3 = st.columns(3)
        
        col_m1.metric(
            "📊 1RM Médio",
            f"{media_1rm:.1f} kg",
            delta=f"+{media_1rm - peso_levantado:.1f} kg"
        )
        
        col_m2.metric(
            "📈 1RM Mais Conservador",
            f"{min(epley, brzycki, lander, lombardi, oconner):.1f} kg"
        )
        
        col_m3.metric(
            "🚀 1RM Mais Otimista",
            f"{max(epley, brzycki, lander, lombardi, oconner):.1f} kg"
        )
        
        ## Tabela de Resultados
        st.markdown("---")
        st.subheader("📋 Resultados por Fórmula")
        
        df_1rm = pd.DataFrame({
            "Fórmula": ["Epley", "Brzycki", "Lander", "Lombardi", "O'Conner", "MÉDIA"],
            "1RM Estimado (kg)": [
                round(epley, 1),
                round(brzycki, 1),
                round(lander, 1),
                round(lombardi, 1),
                round(oconner, 1),
                round(media_1rm, 1)
            ]
        })
        
        st.dataframe(df_1rm, use_container_width=True)
        
        ## Tabela de Percentuais
        st.markdown("---")
        st.subheader("💯 Tabela de Percentuais de Treino")
        
        percentuais = [100, 95, 90, 85, 80, 75, 70, 65, 60]
        cargas = [round(media_1rm * (p/100), 1) for p in percentuais]
        
        df_percentuais = pd.DataFrame({
            "% de 1RM": [f"{p}%" for p in percentuais],
            "Carga (kg)": cargas,
            "Uso Recomendado": [
                "Teste de 1RM",
                "1-2 reps (Força Máxima)",
                "2-4 reps (Força)",
                "4-6 reps (Força-Hipertrofia)",
                "6-8 reps (Hipertrofia)",
                "8-12 reps (Hipertrofia-Resistência)",
                "12-15 reps (Resistência)",
                "15-20 reps (Resistência Muscular)",
                "20+ reps (Endurance)"
            ]
        })
        
        st.dataframe(df_percentuais, use_container_width=True)

## ============================================================================
## MÓDULO 3: PREDITOR CARDIORRESPIRATÓRIO
## ============================================================================
elif opcao == "🫁 Preditor Cardiorrespiratório":
    st.header("🫁 Preditor de Capacidade Cardiorrespiratória")
    st.caption("Estimativa de VO2max e zonas de treinamento")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👤 Dados Pessoais")
        idade_cardio = st.number_input("Idade", min_value=16, max_value=80, value=30, key="idade_cardio")
        sexo = st.selectbox("Sexo", ["Masculino", "Feminino"])
        peso_cardio = st.number_input("Peso (kg)", min_value=40.0, max_value=150.0, value=75.0, key="peso_cardio")
        fc_repouso = st.number_input("FC Repouso (bpm)", min_value=40, max_value=100, value=60)
    
    with col2:
        st.subheader("🏃 Teste de Performance")
        tipo_teste = st.selectbox(
            "Tipo de Teste",
            ["Cooper (12 min)", "1 Mile Run", "2000m Row", "500m Row", "Bike 5km"]
        )
        
        if tipo_teste == "Cooper (12 min)":
            distancia = st.number_input("Distância percorrida (metros)", min_value=1000, max_value=4000, value=2400)
            ## Fórmula de Cooper
            vo2max = (distancia - 504.9) / 44.73
            
        elif tipo_teste == "1 Mile Run":
            tempo_min = st.number_input("Tempo (minutos)", min_value=4.0, max_value=20.0, value=8.0, step=0.1)
            ## Fórmula de Rockport
            vo2max = 132.853 - (0.0769 * peso_cardio) - (0.3877 * idade_cardio) + (6.315 * (1 if sexo == "Masculino" else 0)) - (3.2649 * tempo_min) - (0.1565 * fc_repouso)
            
        elif tipo_teste == "2000m Row":
            tempo_seg = st.number_input("Tempo (segundos)", min_value=360, max_value=900, value=480)
            ## Estimativa baseada em pace
            pace_500m = tempo_seg / 4
            vo2max = 15000 / pace_500m - 35
            
        else:
            tempo_min = st.number_input("Tempo (minutos)", min_value=5.0, max_value=30.0, value=15.0, step=0.1)
            vo2max = 50 - (tempo_min * 0.5)
    
    if st.button("🔮 Calcular VO2max e Zonas", type="primary", use_container_width=True):
        
        ## FC Máxima
        fc_max = 220 - idade_cardio
        
        ## FC de Reserva (Karvonen)
        fc_reserva = fc_max - fc_repouso
        
        st.success("✅ Análise Concluída!")
        
        ## Métricas Principais
        col_m1, col_m2, col_m3 = st.columns(3)
        
        col_m1.metric("🫀 VO2max", f"{vo2max:.1f} ml/kg/min")
        col_m2.metric("💓 FC Máxima", f"{fc_max} bpm")
        col_m3.metric("📊 FC Reserva", f"{fc_reserva} bpm")
        
        ## Classificação VO2max
        st.markdown("---")
        st.subheader("📊 Classificação de VO2max")
        
        if sexo == "Masculino":
            if vo2max > 56:
                classificacao = "Excelente 🏆"
                cor = "success"
            elif vo2max > 51:
                classificacao = "Muito Bom 💪"
                cor = "success"
            elif vo2max > 45:
                classificacao = "Bom ✅"
                cor = "info"
            elif vo2max > 38:
                classificacao = "Regular ⚠️"
                cor = "warning"
            else:
                classificacao = "Abaixo da Média 📉"
                cor = "error"
        else:
            if vo2max > 49:
                classificacao = "Excelente 🏆"
                cor = "success"
            elif vo2max > 43:
                classificacao = "Muito Bom 💪"
                cor = "success"
            elif vo2max > 39:
                classificacao = "Bom ✅"
                cor = "info"
            elif vo2max > 33:
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
        
        ## Zonas de Treinamento (Karvonen)
        st.markdown("---")
        st.subheader("🎯 Zonas de Treinamento Cardíaco")
        
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
                "FC Mínima": fc_min,
                "FC Máxima": fc_max_zona,
                "% FC Reserva": f"{int(min_pct*100)}-{int(max_pct*100)}%"
            })
        
        df_zonas = pd.DataFrame(dados_zonas)
        st.dataframe(df_zonas, use_container_width=True)

## ============================================================================
## MÓDULO 4: HISTÓRICO DE TREINOS
## ============================================================================
elif opcao == "📈 Histórico de Treinos":
    st.header("📈 Histórico de Treinos Salvos")
    
    if len(st.session_state.treinos_salvos) == 0:
        st.info("📭 Nenhum treino salvo ainda. Use o módulo de Predição de WOD para salvar treinos!")
    else:
        st.success(f"✅ {len(st.session_state.treinos_salvos)} treino(s) salvo(s)")
        
        df_historico = pd.DataFrame(st.session_state.treinos_salvos)
        st.dataframe(df_historico, use_container_width=True)
        
        if st.button("🗑️ Limpar Histórico"):
            st.session_state.treinos_salvos = []
            st.rerun()

## Footer
st.markdown("---")
st.caption("🏋️‍♂️ CrossFit WOD Predictor Pro v2.0 | Desenvolvido para atletas de alto desempenho")

