import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, time

# Configuração da página para celular
st.set_page_config(page_title="Controle 99 - Cronos", layout="centered", page_icon="🚖")

# Conexão com banco de dados SQLite
conn = sqlite3.connect("historico_corridas.db", check_same_thread=False)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS jornadas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        km_rodados REAL,
        faturamento REAL,
        horas_texto TEXT,
        horas_decimal REAL,
        combustivel REAL,
        reservas REAL,
        lucro_liquido REAL,
        ganho_hora REAL
    )
''')
conn.commit()

st.title("🚖 Controle Financeiro 99")

# Menu de navegação
aba = st.radio("Selecione:", ["➕ Novo Lançamento", "📋 Histórico & Totais"], horizontal=True)

# ---------------------------------------------------------
# 1. ABA: NOVO LANÇAMENTO
# ---------------------------------------------------------
if aba == "➕ Novo Lançamento":
    st.subheader("Registrar Jornada")
    
    data_jornada = st.date_input("Data da jornada", value=date.today())
    
    col_km, col_fat = st.columns(2)
    with col_km:
        km = st.number_input("Km Rodados no Dia", min_value=0.0, step=5.0, value=100.0)
    with col_fat:
        fat = st.number_input("Faturamento Bruto (R$)", min_value=0.0, step=10.0, value=200.0)
    
    # Campo de Horas Trabalhadas em Horas e Minutos
    st.markdown("**Tempo Trabalhado (Horas e Minutos):**")
    col_h, col_m = st.columns(2)
    with col_h:
        horas_input = st.number_input("Horas", min_value=0, max_value=24, value=6, step=1)
    with col_m:
        minutos_input = st.number_input("Minutos (ex: 20, 30, 45)", min_value=0, max_value=59, value=30, step=5)
    
    # Conversão automática para decimal para os cálculos
    total_horas_decimal = horas_input + (minutos_input / 60.0)
    texto_tempo = f"{horas_input:02d}:{minutos_input:02d}h"
    
    with st.expander("⚙️ Configurações do Carro / Combustível"):
        kml = st.number_input("Consumo do Cronos (km/L)", value=12.8, step=0.1)
        preco_gasolina = st.number_input("Preço da Gasolina (R$/L)", value=6.00, step=0.05)
    
    if st.button("Calcular e Salvar", type="primary", use_container_width=True):
        if total_horas_decimal <= 0:
            st.error("Informe um tempo trabalhado maior que zero.")
        else:
            # Cálculos automáticos
            litros = km / kml if kml > 0 else 0
            custo_comb = litros * preco_gasolina
            lucro_op = fat - custo_comb
            reservas = lucro_op * 0.20 if lucro_op > 0 else 0.0  # 10% Manutenção + 5% Emergência + 5% MEI
            lucro_liq = lucro_op - reservas
            ganho_hora = lucro_liq / total_horas_decimal if total_horas_decimal > 0 else 0.0

            # Salvar no banco
            c.execute('''
                INSERT INTO jornadas (data, km_rodados, faturamento, horas_texto, horas_decimal, combustivel, reservas, lucro_liquido, ganho_hora)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (str(data_jornada), km, fat, texto_tempo, total_horas_decimal, custo_comb, reservas, lucro_liq, ganho_hora))
            conn.commit()
            
            st.success("✅ Jornada salva com sucesso!")
            
            # Exibição do Resultado
            st.metric(label="💰 DINHEIRO REAL NO BOLSO", value=f"R$ {lucro_liq:.2f}")
            
            c1, c2 = st.columns(2)
            c1.metric("⛽ Custo Gasolina", f"R$ {custo_comb:.2f}")
            c2.metric("🛡️ Reservas Guardadas", f"R$ {reservas:.2f}")
            
            st.info(f"⏱️ **Tempo:** {texto_tempo} | **Ganho Líquido:** R$ {ganho_hora:.2f}/hora | **Consumo:** {litros:.1f} Litros")

# ---------------------------------------------------------
# 2. ABA: HISTÓRICO, TOTAIS E GERENCIAMENTO
# ---------------------------------------------------------
elif aba == "📋 Histórico & Totais":
    st.subheader("Histórico e Somas Gerais")
    
    df = pd.read_sql_query("SELECT id, data, km_rodados, faturamento, horas_texto, combustivel, reservas, lucro_liquido, ganho_hora FROM jornadas ORDER BY id DESC", conn)
    
    if not df.empty:
        # Somas e Totais Gerais
        total_fat = df['faturamento'].sum()
        total_comb = df['combustivel'].sum()
        total_res = df['reservas'].sum()
        total_liq = df['lucro_liquido'].sum()
        total_km = df['km_rodados'].sum()
        
        st.markdown("### 📊 Totais Acumulados")
        m1, m2 = st.columns(2)
        m1.metric("💰 Total Dinheiro no Bolso", f"R$ {total_liq:.2f}")
        m2.metric("💵 Total Faturado Bruto", f"R$ {total_fat:.2f}")
        
        m3, m4 = st.columns(2)
        m3.metric("⛽ Total Gasto Gasolina", f"R$ {total_comb:.2f}")
        m4.metric("🛡️ Total em Reservas", f"R$ {total_res:.2f}")
        
        st.caption(f"🛣️ **Total Rodado:** {total_km:.1f} km | **Jornadas Registradas:** {len(df)}")
        st.markdown("---")
        
        # Tabela Detalhada
        st.markdown("### 📝 Lançamentos Anteriores")
        df_display = df.copy()
        df_display.columns = ["ID", "Data", "Km", "Faturamento (R$)", "Tempo", "Gasolina (R$)", "Reservas (R$)", "Lucro Líq. (R$)", "R$/Hora"]
        st.dataframe(df_display, use_container_width=True)
        
        st.markdown("---")
        # Seção para Apagar
        with st.expander("🗑️ Opções para Apagar Histórico"):
            # Apagar um lançamento específico pelo ID
            ids_disponiveis = df['id'].tolist()
            id_para_apagar = st.selectbox("Escolha o ID do registro que deseja apagar:", ids_disponiveis)
            if st.button("❌ Apagar Registro Selecionado"):
                c.execute("DELETE FROM jornadas WHERE id = ?", (id_para_apagar,))
                conn.commit()
                st.warning(f"Registro ID {id_para_apagar} apagado com sucesso!")
                st.rerun()
            
            st.markdown("---")
            # Apagar tudo
            if st.checkbox("Tenho certeza de que quero apagar TODO o histórico"):
                if st.button("🚨 Limpar Todo o Histórico", type="primary"):
                    c.execute("DELETE FROM jornadas")
                    conn.commit()
                    st.error("Todo o histórico foi apagado!")
                    st.rerun()
    else:
        st.info("Nenhum cálculo registrado ainda.")
