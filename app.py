import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# Configuração da Página para Celular
st.set_page_config(page_title="Controle 99 - Cronos", layout="centered")

# Banco de Dados Local
conn = sqlite3.connect("historico_corridas.db", check_same_thread=False)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS jornadas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        km_rodados REAL,
        faturamento REAL,
        horas REAL,
        combustivel REAL,
        reservas REAL,
        lucro_liquido REAL,
        ganho_hora REAL
    )
''')
conn.commit()

st.title("🚖 Controle Diário 99")

# Menu de Navegação
aba = st.radio("Escolha uma opção:", ["➕ Novo Cálculo", "📋 Ver Histórico"], horizontal=True)

if aba == "➕ Novo Cálculo":
    st.subheader("Lançamento do Dia")
    
    data_jornada = st.date_input("Data", value=date.today())
    km = st.number_input("Km Rodados", min_value=0.0, step=5.0, value=100.0)
    fat = st.number_input("Faturamento Bruto Total (R$)", min_value=0.0, step=10.0, value=200.0)
    horas = st.number_input("Horas Trabalhadas", min_value=0.1, step=0.5, value=6.5)
    
    with st.expander("⚙️ Ajustar Preço do Combustível / Consumo"):
        kml = st.number_input("Consumo Cronos (km/L)", value=12.8)
        preco_gasolina = st.number_input("Preço Gasolina (R$/L)", value=6.00)
    
    if st.button("Calcular e Salvar no Histórico", type="primary"):
        # Cálculos
        custo_comb = (km / kml) * preco_gasolina
        lucro_op = fat - custo_comb
        reservas = lucro_op * 0.20 if lucro_op > 0 else 0.0  # 10% Manut + 5% Emerg + 5% MEI
        lucro_liq = lucro_op - reservas
        ganho_hora = lucro_liq / horas if horas > 0 else 0.0

        # Salvar no Banco
        c.execute('''
            INSERT INTO jornadas (data, km_rodados, faturamento, horas, combustivel, reservas, lucro_liquido, ganho_hora)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (str(data_jornada), km, fat, horas, custo_comb, reservas, lucro_liq, ganho_hora))
        conn.commit()
        
        st.success("✅ Jornada calculada e salva com sucesso!")
        
        # Exibição dos Cards de Resultado
        st.metric(label="💰 Dinheiro Real no Bolso", value=f"R$ {lucro_liq:.2f}")
        col1, col2 = st.columns(2)
        col1.metric("⛽ Custo Gasolina", f"R$ {custo_comb:.2f}")
        col2.metric("🛡️ Reservas (20%)", f"R$ {reservas:.2f}")
        st.info(f"⏱️ **Ganho Líquido:** R$ {ganho_hora:.2f} por hora | **Consumo:** {(km/kml):.1f} Litros")

elif aba == "📋 Ver Histórico":
    st.subheader("Histórico de Jornadas Salvas")
    df = pd.read_sql_query("SELECT data, km_rodados, faturamento, combustivel, reservas, lucro_liquido, ganho_hora FROM jornadas ORDER BY id DESC", conn)
    
    if not df.empty:
        df.columns = ["Data", "Km", "Faturamento (R$)", "Gasolina (R$)", "Reservas (R$)", "Lucro Líquido (R$)", "R$/Hora"]
        st.dataframe(df, use_container_width=True)
        st.metric("Total Líquido Acumulado", f"R$ {df['Lucro Líquido (R$)'].sum():.2f}")
    else:
        st.info("Nenhum cálculo registrado ainda.")
