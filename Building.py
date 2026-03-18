import streamlit as st
import streamlit.components.v1 as components

# ======================================================
# 1. CONFIGURACIÓN Y ESTADO
# ======================================================
st.set_page_config(page_title="Building Quote Master", layout="wide")

if "b_p1_rooms" not in st.session_state: st.session_state.b_p1_rooms = []
if "b_base_rooms" not in st.session_state: st.session_state.b_base_rooms = []
if "b_landings" not in st.session_state: st.session_state.b_landings = []
if "b_stairwells" not in st.session_state: st.session_state.b_stairwells = []

def add_room(list_key, name_key, w_key, l_key):
    try:
        name = st.session_state[name_key].strip()
        w = float(st.session_state[w_key])
        l = float(st.session_state[l_key])
        if name:
            st.session_state[list_key].append({"Area": name, "ft²": int(w*l)})
            st.session_state[name_key] = ""; st.session_state[w_key] = ""; st.session_state[l_key] = ""
    except: st.error("Error en medidas")

# ======================================================
# 2. UI - PANEL SUPERIOR (CON HORAS Y TÉCNICOS)
# ======================================================
st.title("🏢 Building Quote Calculator")

c1, c2, c3 = st.columns(3)

with c1:
    with st.container(border=True):
        st.subheader("📋 Estructura")
        b_name = st.text_input("Edificio", placeholder="Ej: Tower A")
        num_floors = st.number_input("Cant. Pisos Tipo", min_value=0, step=1)
        col_w, col_l = st.columns(2)
        tw = col_w.text_input("Ancho (P. Tipo)")
        tl = col_l.text_input("Largo (P. Tipo)")
        has_bs = st.checkbox("¿Tiene Basement?")

with c2:
    with st.container(border=True):
        st.subheader("🛠️ Tools & Info")
        p_type = st.radio("Proyecto", ["House", "Office"], horizontal=True)
        st.divider()
        eq_tm = st.checkbox("Truck Mount")
        eq_port = st.checkbox("Portable")
        eq_cimex = st.checkbox("Cimex")
        st.divider()
        dirt = st.radio("Dirt Level", ["Light", "Medium", "Heavy"], horizontal=True)

with c3:
    with st.container(border=True):
        st.subheader("🚶 Labor & Access")
        col_h, col_t = st.columns(2)
        est_hours = col_h.text_input("Horas Est.", placeholder="0")
        num_techs = col_t.text_input("Técnicos", placeholder="0")
        st.divider()
        acc_elev = st.checkbox("Elevator")
        acc_water = st.checkbox("Water Access")
        acc_wash = st.checkbox("Washroom Access")
        st.divider()
        parking = st.radio("Parking", ["Easy", "Medium", "Difficult"], horizontal=True)
        notes = st.text_area("Notas / Observaciones:", height=45)

st.divider()

# ======================================================
# 3. ÁREAS Y ESCALERAS (DISEÑO ORIGINAL SIN BOTONES)
# ======================================================
d1, d2 = st.columns(2)

with d1:
    with st.container(border=True):
        st.subheader("🏙️ Áreas Únicas")
        t1, t2 = st.tabs(["Piso 1", "Basement"])
        with t1:
            with st.form("f_p1", clear_on_submit=True):
                st.text_input("Nombre Área", key="p1n")
                cw, cl = st.columns(2)
                cw.text_input("W", key="p1w"); cl.text_input("L", key="p1l")
                st.form_submit_button("➕ Añadir Área", on_click=add_room, args=("b_p1_rooms", "p1n", "p1w", "p1l"))
            st.table(st.session_state.b_p1_rooms)
        with t2:
            if has_bs:
                with st.form("f_bs", clear_on_submit=True):
                    st.text_input("Nombre Área", key="bsn")
                    cw, cl = st.columns(2)
                    cw.text_input("W", key="bsw"); cl.text_input("L", key="bsl")
                    st.form_submit_button("➕ Añadir Área", on_click=add_room, args=("b_base_rooms", "bsn", "bsw", "bsl"))
                st.table(st.session_state.b_base_rooms)

with d2:
    with st.container(border=True):
        st.subheader("🪜 Stairwells")
        
        # Crear la escalera
        with st.container(border=True):
            new_sw = st.text_input("Nombre de la Escalera (Ej: North)", key="sw_in")
            if st.button("Crear Escalera"):
                if new_sw and new_sw not in st.session_state.b_stairwells:
                    st.session_state.b_stairwells.append(new_sw)
                    st.rerun()

        # Tramos automáticos SIN BOTONES (como al inicio)
        stair_data_capture = {}
        for sw in st.session_state.b_stairwells:
            with st.expander(f"Escalera: {sw.upper()}", expanded=True):
                if num_floors > 0:
                    for i in range(num_floors, 0, -1):
                        label = f"Piso {i}-{i-1 if i-1 > 0 else 'Lobby'}"
                        val = st.text_input(f"{label} ({sw}):", key=f"st_{sw}_{i}", value="0")
                        stair_data_capture[f"{sw}_{label}"] = int(val) if val.isdigit() else 0
                else:
                    st.info("Define la cantidad de pisos.")

        st.divider()
        st.write("**Landings**")
        with st.form("f_land", clear_on_submit=True):
            cl1, cl2, cl3 = st.columns(3)
            cl1.text_input("W", key="lw"); cl2.text_input("L", key="ll"); cl3.text_input("Qty", key="lq")
            if st.form_submit_button("➕ Añadir Landings"):
                try:
                    area = float(st.session_state.lw) * float(st.session_state.ll) * int(st.session_state.lq)
                    st.session_state.b_landings.append({"Dim": f"{st.session_state.lw}x{st.session_state.ll}", "Qty": st.session_state.lq, "Total": area})
                except: st.error("Error")
        st.table(st.session_state.b_landings)

# ======================================================
# 4. REPORTE FINAL
# ======================================================
p1_sum = sum([x['ft²'] for x in st.session_state.b_p1_rooms])
bs_sum = sum([x['ft²'] for x in st.session_state.b_base_rooms])
typ_sum = (float(tw or 0) * float(tl or 0)) * num_floors
land_sum = sum([x['Total'] for x in st.session_state.b_landings])
step_sum = sum(stair_data_capture.values())

report = [
    f"*** {p_type.upper()} REPORT: {b_name.upper() if b_name else 'N/A'} ***",
    "===============================",
    f"TOTAL CARPET AREA: {int(p1_sum + bs_sum + typ_sum)} sq ft",
    f"TOTAL LANDINGS: {int(land_sum)} sq ft",
    f"TOTAL STEPS: {int(step_sum)}",
    "===============================",
    f"LABOR: {num_techs if num_techs else '0'} Tech(s) | EST. TIME: {est_hours if est_hours else '0'} Hours",
    "===============================",
    f"Truck Mount: {'Yes' if eq_tm else 'No'} | Portable: {'Yes' if eq_port else 'No'} | Cimex: {'Yes' if eq_cimex else 'No'}",
    f"Elevator: {'Yes' if acc_elev else 'No'} | Water: {'Yes' if acc_water else 'No'} | Washroom: {'Yes' if acc_wash else 'No'}",
    f"Parking: {parking} | Dirt Level: {dirt}",
    f"Notes: {notes if notes else 'None'}",
    "-------------------------------",
    "STAIRS DETAILED:"
]
for k, v in stair_data_capture.items():
    if v > 0:
        report.append(f" - {k.replace('_', ' ')}: {v} steps")

final_text = "\n".join(report)

st.divider()
st.text_area("Copia el Reporte Final aquí:", final_text, height=350)
components.html(f"""
    <button style="padding:12px;background-color:#007bff;color:white;border:none;border-radius:6px;width:100%;font-weight:bold;cursor:pointer;"
    onclick="navigator.clipboard.writeText(`{final_text}`); this.innerText='✓ Copiado';">📎 Copiar Reporte</button>""", height=70)

if st.button("🗑️ Reset All"):
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.rerun()