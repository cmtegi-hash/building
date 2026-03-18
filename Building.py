import streamlit as st
import streamlit.components.v1 as components

# ======================================================
# 1. CONFIGURACIÓN Y ESTADO
# ======================================================
st.set_page_config(page_title="Building Quote Master Pro", layout="wide")

if "rooms" not in st.session_state: st.session_state.rooms = []
if "stair_names" not in st.session_state: st.session_state.stair_names = []

EQUIPMENT_LIST = ["Truck Mount", "Portable", "Cimex"]
CHEMICALS_LIST = ["Procyon", "Citrus Booster", "Flex Powder", "Bio Break", "Boost All", "Pure O2", "Eco Cide", "Petzap IQ", "Groutmaster"]
FLOOR_TYPES = ["Carpet", "Tile", "Laminate", "Vinyl/LVP"]
LEVELS = ["Lobby / Floor 1", "Basement", "Top Floor", "Typical Floor", "Other"]

# ======================================================
# 2. PHASE 1: MAIN AREAS (UNIQUE VS TYPICAL)
# ======================================================
st.title("🏢 Building Inspection & Quote")

c1, c2 = st.columns([1, 1])

with c1:
    with st.container(border=True):
        st.subheader("📍 Phase 1: Main Areas")
        b_name = st.text_input("Building Name", placeholder="Ej: West Tower")
        total_b_floors = st.number_input("Building Floors (Total Count)", min_value=0, step=1, value=0)
        
        tab_unique, tab_typical = st.tabs(["Unique Areas (Lobby/Base/Gym)", "Typical Floors (Multipliers)"])
        
        with tab_unique:
            with st.form("unique_form", clear_on_submit=True):
                un_lvl = st.selectbox("Level", LEVELS, key="ulvl")
                un_name = st.text_input("Area Description", placeholder="Main Entrance, Gym, Storage...")
                un_type = st.selectbox("Floor Type", FLOOR_TYPES, key="utype")
                uw, ul = st.columns(2)
                w = uw.text_input("Width (ft)")
                l = ul.text_input("Length (ft)")
                if st.form_submit_button("➕ Add Unique Area"):
                    try:
                        sqft = float(w) * float(l)
                        st.session_state.rooms.append({
                            "Level": un_lvl, "Name": un_name, "Type": un_type, 
                            "W": w, "L": l, "SqFt": int(sqft), "Mult": 1
                        })
                    except: st.error("Error en medidas")

        with tab_typical:
            with st.form("typical_form", clear_on_submit=True):
                tw, tl, tm = st.columns(3)
                w = tw.text_input("Width (ft)")
                l = tl.text_input("Length (ft)")
                mult = tm.number_input("Repeat x Floors", min_value=1, value=1)
                if st.form_submit_button("➕ Add Typical Floors"):
                    try:
                        sqft = float(w) * float(l) * mult
                        st.session_state.rooms.append({
                            "Level": "Typical Floor", "Name": "Standard Corridors", "Type": "Carpet", 
                            "W": w, "L": l, "SqFt": int(sqft), "Mult": mult
                        })
                    except: st.error("Error en medidas")
        
        if st.session_state.rooms:
            st.table(st.session_state.rooms)

# ======================================================
# 3. PHASE 2: STAIRWELLS
# ======================================================
with c2:
    with st.container(border=True):
        st.subheader("🪜 Phase 2: Stairwell Systems")
        new_sw = st.text_input("New Stairwell ID", placeholder="Ej: North Stairs")
        if st.button("➕ Create Stairwell"):
            if new_sw and new_sw not in st.session_state.stair_names:
                st.session_state.stair_names.append(new_sw)
                st.rerun()

        stair_data = {}

        for sw in st.session_state.stair_names:
            with st.expander(f"System: {sw.upper()}", expanded=True):
                h_col1, h_col2 = st.columns(2)
                has_roof = h_col1.checkbox("Reach Roof?", key=f"roof_{sw}")
                has_base = h_col2.checkbox("Reach Basement?", key=f"base_{sw}")
                
                total_sw_steps = 0
                if has_roof:
                    val = st.text_input(f"Roof to Floor {total_b_floors} ({sw})", value="0", key=f"rs_{sw}")
                    total_sw_steps += int(val) if val.isdigit() else 0
                for i in range(total_b_floors, 0, -1):
                    label = f"Floor {i} to {i-1 if i-1 > 0 else 'Lobby'}"
                    val = st.text_input(f"{label} ({sw})", value="0", key=f"st_{sw}_{i}")
                    total_sw_steps += int(val) if val.isdigit() else 0
                if has_base:
                    val = st.text_input(f"Lobby to Basement ({sw})", value="0", key=f"bs_{sw}")
                    total_sw_steps += int(val) if val.isdigit() else 0
                
                st.write("**Landings for this stairwell:**")
                lw, ll, lq = st.columns(3)
                w_l = lw.text_input("W", key=f"lw_{sw}", value="0")
                l_l = ll.text_input("L", key=f"ll_{sw}", value="0")
                q_l = lq.text_input("Floors", key=f"lq_{sw}", value="0")
                
                l_area = 0
                try: l_area = float(w_l) * float(l_l) * int(q_l)
                except: pass
                
                start = "Basement" if has_base else "Lobby"
                end = "Roof" if has_roof else f"Floor {total_b_floors}"
                
                stair_data[sw] = {
                    "steps": total_sw_steps, "range": f"{start} to {end}",
                    "l_w": w_l, "l_l": l_l, "l_q": q_l, "l_total": int(l_area)
                }

st.divider()

# ======================================================
# 4. PHASE 3: LABOR, LOGISTICS & STRATEGY
# ======================================================
st.subheader("⚙️ Phase 3: Technical Setup")
s1, s2, s3 = st.columns(3)

with s1:
    with st.container(border=True):
        st.write("**Labor Assignment**")
        num_techs = st.text_input("Technicians Assigned", value="0")
        est_hours = st.text_input("Estimated Hours", value="0")
        shift = st.selectbox("Shift Schedule", ["Regular Hours", "After Hours", "Weekends"])

with s2:
    with st.container(border=True):
        st.write("**Logistics & Access**")
        soil = st.radio("Soil Level", ["Light", "Medium", "Heavy Restoration"], horizontal=True)
        elev = st.checkbox("Elevator Access", value=True)
        water = st.checkbox("Water Source Provided", value=True)
        parking = st.radio("Parking", ["Easy", "Medium", "Difficult"], horizontal=True)

with s3:
    with st.container(border=True):
        st.write("**Technical Strategy**")
        selected_eq = [eq for eq in EQUIPMENT_LIST if st.checkbox(eq, key=f"eq_{eq}")]
        selected_chem = st.multiselect("Chemistry Suggested", CHEMICALS_LIST)
        notes = st.text_area("Field Notes (Technical Observations)", height=68)

# ======================================================
# 5. REPORTE FINAL EJECUTIVO
# ======================================================
totals_by_type = {t: sum([x['SqFt'] for x in st.session_state.rooms if x['Type'] == t]) for t in FLOOR_TYPES}
total_steps = sum([v['steps'] for v in stair_data.values()])

report = [
    f"*** BUILDING SERVICE INSPECTION & QUOTE ***",
    f"Name: {b_name.upper() if b_name else 'N/A'}",
    f"Date: 03/18/2026",
    "--------------------------------------------------------------",
    f"I. SCOPE OF WORK SUMMARY"
]

for f_type, f_sqft in totals_by_type.items():
    if f_sqft > 0: report.append(f" - Total {f_type} Surface: {int(f_sqft)} sq ft")
report.append(f" - Total Steps: {int(total_steps)}")
report.append(f" - Soil Level: {soil}")

report.extend([
    "--------------------------------------------------------------",
    f"II. LABOR & ESTIMATED TIME",
    f" - Technicians Assigned: {num_techs} Specialists",
    f" - Estimated Production Time: {est_hours} Hours",
    f" - Shift Schedule: {shift}",
    "--------------------------------------------------------------",
    f"III. LOGISTICS & SITE ACCESS",
    f" - Elevator Access: {'Yes' if elev else 'No'}",
    f" - Water Source: {'Provided on-site' if water else 'To be determined'}",
    f" - Parking: {parking}",
    "--------------------------------------------------------------",
    f"IV. TECHNICAL STRATEGY",
    f" - Equipment: {', '.join(selected_eq) if selected_eq else 'None'}",
    f" - Chemistry Suggested: {', '.join(selected_chem) if selected_chem else 'None'}",
    f" - Field Notes: {notes if notes else 'No specific observations.'}",
    "--------------------------------------------------------------",
    f"V. DETAILED AREA BREAKDOWN"
])

for r in st.session_state.rooms:
    mult_txt = f" (x{r['Mult']} Floors)" if r['Mult'] > 1 else ""
    report.append(f" - [{r['Level']}] {r['Name']} ({r['Type']}): {r['W']}ft x {r['L']}ft = {r['SqFt']} sq ft{mult_txt}")

if stair_data:
    report.append("--------------------------------------------------------------")
    report.append("VI. STAIRWELL SYSTEMS DETAIL")
    for sw, d in stair_data.items():
        if d['steps'] > 0 or d['l_total'] > 0:
            report.append(f"\n[{sw.upper()}] (Range: {d['range']})")
            report.append(f" - Steps: {d['steps']} total.")
            if d['l_total'] > 0:
                report.append(f" - Landings: {d['l_w']}ft x {d['l_l']}ft = {int(float(d['l_w'])*float(d['l_l']))} sq ft (x{d['l_q']} Floors) | Subtotal: {d['l_total']} sq ft")

report.append("--------------------------------------------------------------")

final_text = "\n".join(report)

st.divider()
st.subheader("📋 Final Executive Report")
st.text_area("Ready for Client:", final_text, height=450)

components.html(f"""
    <button style="padding:12px;background-color:#007bff;color:white;border:none;border-radius:6px;width:100%;font-weight:bold;cursor:pointer;font-family:sans-serif;"
    onclick="navigator.clipboard.writeText(`{final_text}`); this.innerText='✓ Report Copied to Clipboard'; this.style.backgroundColor='#28a745';">
    📎 Copy Executive Report</button>""", height=70)

if st.button("🗑️ Reset All Data"):
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.rerun()
