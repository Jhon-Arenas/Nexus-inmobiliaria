import streamlit as st
import sqlite3
import pandas as pd
import secrets

# 1. MOTOR DE BASE DE DATOS (SQLite)
def conectar():
    return sqlite3.connect('inmobiliaria.db')

def inicializar_db():
    conn = conectar()
    cursor = conn.cursor()
    # Tabla de Prospectos con teléfono incluido
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prospectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            telefono TEXT,
            telegram_user TEXT,
            interes TEXT,
            presupuesto INTEGER,
            codigo_seguridad TEXT,
            id_vendedor INTEGER
        )
    """)
    conn.commit()
    conn.close()

inicializar_db()

# 2. CONFIGURACIÓN VISUAL
st.set_page_config(page_title="Inmobiliaria Nexus", page_icon="🏠")

# 3. NAVEGACIÓN (BARRA LATERAL)
st.sidebar.title("🧭 Menú de Acceso")
rol = st.sidebar.radio("Seleccione su perfil:", ["Cliente (Registro)", "Vendedor (Gestión)", "Administrador"])
st.sidebar.divider()

# 4. CUERPO DE LA APLICACIÓN

# --- VISTA DEL CLIENTE ---
if rol == "Cliente (Registro)":
    st.title("🏠 Encuentra tu próximo hogar")
    st.write("Bienvenido. Completa tus datos y un asesor te contactará de forma segura.")
    
    with st.form("form_cliente"):
        nombre_cli = st.text_input("¿Cuál es tu nombre?")
        telefono_cli = st.text_input("Tu WhatsApp (Ej: +584241234567)")
        user_tg = st.text_input("Tu usuario de Telegram (Ej: @tu_usuario)")
        interes_cli = st.selectbox("¿Qué buscas?", ["Casa", "Apartamento", "Local", "Terreno"])
        presupuesto_cli = st.slider("¿Cuál es tu presupuesto aproximado en USD?", min_value=3000, max_value=500000, step=1000, format="$%d")
        btn_enviar = st.form_submit_button("Solicitar Información")
    
    if btn_enviar:
        if nombre_cli and telefono_cli:
            ref_segura = f"REF-{secrets.token_hex(3).upper()}"
            conn = conectar()
            cursor = conn.cursor()
            # Agregamos 'presupuesto' a la lista de columnas y el '?' correspondiente
            cursor.execute("""
                INSERT INTO prospectos (nombre, telefono, telegram_user, interes, presupuesto, codigo_seguridad, id_vendedor) 
                VALUES (?, ?, ?, ?, ?, ?, ?)""", 
                (nombre_cli, telefono_cli, user_tg, interes_cli, presupuesto_cli, ref_segura, 1))
            conn.commit()
            conn.close()
            st.success(f"¡Registrado! Tu código de seguridad es: **{ref_segura}**")
            st.info("Un asesor usará este código para identificarse contigo.")
        else:
            st.error("Por favor, rellena tu nombre y teléfono para poder contactarte.")

# --- VISTA DEL VENDEDOR (Protegida) ---
elif rol == "Vendedor (Gestión)":
    st.sidebar.subheader("🔒 Autenticación")
    clave_vendedor = st.sidebar.text_input("Clave de Acceso:", type="password")

    if clave_vendedor == "Ventas2026":
        st.title("👨‍💼 Gestión de Prospectos")
        conn = conectar()
        df_leads = pd.read_sql_query("SELECT * FROM prospectos ORDER BY id DESC", conn)
        conn.close()

        if not df_leads.empty:
            cantidad = len(df_leads)
            st.toast(f"🔔 Tienes {cantidad} prospectos esperando atención", icon="🏠")
            
            # Ordenar por los más nuevos (opcional pero recomendado)
            df_leads = df_leads.sort_values(by="id", ascending=False)

            for index, row in df_leads.iterrows():
                # --- LÓGICA VIP ---
                etiqueta_vip = ""
                # Si el presupuesto es mayor o igual a 100,000 USD
                if row['presupuesto'] >= 100000:
                    etiqueta_vip = "⭐ [CLIENTE VIP]"
                elif row['presupuesto'] >= 50000:
                    etiqueta_vip = "💰 [ALTO INTERÉS]"

                # El título del expander ahora cambia según el presupuesto
                with st.expander(f"{etiqueta_vip} Nombre: {row['nombre']} - ${row['presupuesto']:,} USD"):
                    st.write(f"**Interés:** {row['interes']}")
                    st.write(f"**Código de Validación:** :blue[{row['codigo_seguridad']}]")
                    
                    # Lógica de enlaces
                    tg_clean = row['telegram_user'].replace("@", "")
                    link_tg = f"https://t.me/{tg_clean}"
                    
                    # WhatsApp con mensaje automático
                    msj = f"Hola *{row['nombre']}*, soy tu asesor de *Inmobiliaria Nexus*. Mi código de validación es: *{row['codigo_seguridad']}*. ¿En qué puedo ayudarte hoy?"
                    link_ws = f"https://wa.me/{row['telefono']}?text={msj.replace(' ', '%20')}"

                    st.warning(f"Copia el código **{row['codigo_seguridad']}** antes de contactar.")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.link_button("✈️ Telegram", link_tg, use_container_width=True)
                    with col2:
                        st.link_button("🟢 WhatsApp", link_ws, use_container_width=True)
        else:
            st.info("No hay clientes registrados aún.")
    elif clave_vendedor != "":
        st.error("Clave incorrecta.")

# --- VISTA DEL ADMINISTRADOR ---
elif rol == "Administrador":
    st.sidebar.subheader("🔒 Seguridad Admin")
    clave_admin = st.sidebar.text_input("Clave Maestra:", type="password")

    if clave_admin == "RickAdmin99":
        st.title("⚙️ Panel Administrativo")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Generar Excel"):
                conn = conectar()
                df_export = pd.read_sql_query("SELECT * FROM prospectos", conn)
                conn.close()
                if not df_export.empty:
                    df_export.to_excel("reporte_nexus.xlsx", index=False)
                    with open("reporte_nexus.xlsx", "rb") as f:
                        st.download_button("📥 Bajar Excel", f, file_name="reporte_nexus.xlsx")
                else:
                    st.warning("No hay datos.")

        with col2:
            try:
                with open("inmobiliaria.db", "rb") as f:
                    st.download_button("💾 Backup DB", f, file_name="respaldo_nexus.db")
            except:
                st.error("Error al acceder a la base de datos.")
    elif clave_admin != "":
        st.error("Clave de administrador incorrecta.")