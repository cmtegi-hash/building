import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

# ======================================================
# CONFIGURATION
# ======================================================
st.set_page_config(page_title="Pro Quote Master", layout="wide")

# Session State
if "floor1_rooms" not in st.session_state: st.session_state.floor1_rooms = []
if "repeat_rooms" not in st.session_state: st.session_state.repeat_rooms = []
if "total_floors" not in st.session_state: st.session_state.total_floors = 3  # default
if "logistics" not in st.session_state: st.session_state.logistics = {
    "equipment": [],
    "soil": "Heavy (Restoration)",
    "parking": "Yes",
    "water": "Yes",
    "elevator": "No",
    "techs": "",
    "hours": "",
    "notes": ""
}
if "current_view" not in st.session_state: st.session_state.current_view = "floor1"

# ======================================================
# FUNCTIONS
# ======================================================
def safe_sum(data, key):
    if not data: return 0
    return pd.to_numeric(pd.DataFrame(data)[key], errors='coerce').fillna(0).sum()

def aggregate_rooms(rooms):
    """Sum areas by name, avoid duplicates"""
    agg = {}
    for r in rooms:
        name = r["name"]
        area = int(r["area"])
        if name in agg:
            agg[name] += area
        else:
            agg[name] = area
    return [{"name": k, "area": v} for k, v in agg.items()]

def format_rooms(rooms):
    lines = []
    for r in rooms:
        lines.append(f"- {r['name']}: {r['area']} sq ft")
    return lines

# ======================================================
# VIEW BUTTONS
# ======================================================
c1, c2, c3 = st.columns(3)
if c1.button("Floor 1"): st.session_state.current_view = "floor1"
if c2.button("Repeated Floors"): st.session_state.current_view = "repeat"
if c3.button("Logistics / Report"): st.session_state.current_view = "logistics"

st.divider()

# ======================================================
# FLOOR 1 INPUT
# ======================================================
if st.session_state.current_view == "floor1":
    st.subheader("Floor 1 - Manual Input")
    with st.form("floor1_form", clear_on_submit=True):
        r_name = st.text_input("Room Name", placeholder="Lobby, Hallway, Suite A...")
        c1_col, c2_col = st.columns(2)
        rw = c1_col.text_input("Width (ft)")
        rl = c2_col.text_input("Length (ft)")
        if st.form_submit_button("Add Room"):
            try:
                area = float(rw) * float(rl)
                st.session_state.floor1_rooms.append({"name": r_name, "w": rw, "l": rl, "area": int(area)})
            except:
                st.error("Invalid dimensions")
    if st.session_state.floor1_rooms:
        df_f1 = pd.DataFrame(st.session_state.floor1_rooms)
        edited_f1 = st.data_editor(df_f1, num_rows="dynamic", use_container_width=True, key="editor_f1")
        st.session_state.floor1_rooms = edited_f1.to_dict(orient="records")

# ======================================================
# REPEATED FLOORS
# ======================================================
elif st.session_state.current_view == "repeat":
    st.subheader("Repeated Floors (from Floor 2)")
    with st.form("repeat_form", clear_on_submit=True):
        c1_col, c2_col = st.columns(2)
        rw = c1_col.text_input("Width (ft) Base Layout")
        rl = c2_col.text_input("Length (ft) Base Layout")
        total_floors = st.number_input("Total floors in building (including Floor 1)", min_value=2, value=st.session_state.total_floors, step=1)
        if st.form_submit_button("Save Base Layout"):
            try:
                area = float(rw) * float(rl)
                st.session_state.repeat_rooms = [{"w": rw, "l": rl, "area": int(area)}]
                st.session_state.total_floors = total_floors
            except:
                st.error("Invalid dimensions")
    if st.session_state.repeat_rooms:
        df_rp = pd.DataFrame(st.session_state.repeat_rooms)
        edited_rp = st.data_editor(df_rp, num_rows="dynamic", use_container_width=True, key="editor_rp")
        st.session_state.repeat_rooms = edited_rp.to_dict(orient="records")
        # Immediate summary
        repeat_count = max(st.session_state.total_floors - 1, 0)
        r_area = st.session_state.repeat_rooms[0]["area"]
        st.info(f"Total repeated floors: {repeat_count} → Total Area: {r_area * repeat_count} sq ft")

# ======================================================
# LOGISTICS / REPORT
# ======================================================
elif st.session_state.current_view == "logistics":
    st.subheader("Logistics / Planning")
    with st.form("logistics_form", clear_on_submit=False):
        # Technicians / Hours
        techs = st.text_input("Technicians Assigned", value=st.session_state.logistics.get("techs",""))
        hours = st.text_input("Estimated Hours", value=st.session_state.logistics.get("hours",""))
        
        # Equipment multi-select buttons
        st.write("Equipment")
        eq_cols = st.columns(3)
        eq_options = ["Truck mount", "Portable", "Cimex"]
        selected_eq = st.session_state.logistics.get("equipment", [])
        for i, eq in enumerate(eq_options):
            if eq_cols[i].checkbox(eq, value=eq in selected_eq, key=f"cb_{eq}"):
                if eq not in selected_eq: selected_eq.append(eq)
            else:
                if eq in selected_eq: selected_eq.remove(eq)
        
        # Soil Level
        soil = st.radio("Soil Level", ["Light", "Medium", "Heavy (Restoration)"], index=2, horizontal=True)
        # Parking / Water / Elevator as buttons
        parking = st.radio("Parking Available?", ["Yes", "No"], index=0, horizontal=True)
        water = st.radio("Water Source Provided?", ["Yes", "No"], index=0, horizontal=True)
        elevator = st.radio("Elevator Access?", ["Yes", "No"], index=1, horizontal=True)
        notes = st.text_area("Field Notes", value=st.session_state.logistics.get("notes",""))
        
        if st.form_submit_button("Save Logistics"):
            st.session_state.logistics.update({
                "techs": techs,
                "hours": hours,
                "equipment": selected_eq,
                "soil": soil,
                "parking": parking,
                "water": water,
                "elevator": elevator,
                "notes": notes
            })
    
    # ------------------- FINAL REPORT -------------------
    st.divider()
    st.subheader("Final Report")
    
    # Total Areas
    total_floor1 = sum(r["area"] for r in aggregate_rooms(st.session_state.floor1_rooms))
    repeat_count = max(st.session_state.total_floors - 1, 0)
    total_repeat = sum(r["area"] for r in st.session_state.repeat_rooms) * repeat_count
    total_area = total_floor1 + total_repeat
    
    report_lines = []
    report_lines.append(f"[Building Name / Address]\n")
    report_lines.append(f"TOTAL AREA: {int(total_area)} sq ft\n")
    
    # Logistics
    logistics = st.session_state.logistics
    report_lines.append("1. LOGISTICS / PLANNING\n")
    report_lines.append("TECHNICIANS & TIME")
    report_lines.append(f"- Assigned: {logistics.get('techs','')}")
    report_lines.append(f"- Estimated Hours: {logistics.get('hours','')}\n")
    
    report_lines.append("EQUIPMENT")
    eq_list = logistics.get('equipment', [])
    if eq_list:
        for eq in eq_list:
            report_lines.append(f"- {eq}")
    else:
        report_lines.append("- None")
    
    report_lines.append("\nSOIL CONDITION")
    report_lines.append(f"- {logistics.get('soil','')}\n")
    
    report_lines.append("ACCESS & FACILITIES")
    report_lines.append(f"- Parking Available: {logistics.get('parking','')}")
    report_lines.append(f"- Water Source Provided: {logistics.get('water','')}")
    report_lines.append(f"- Elevator Access: {logistics.get('elevator','')}\n")
    
    report_lines.append("NOTES")
    notes_text = logistics.get('notes','')
    report_lines.append(f"- {notes_text if notes_text else 'No observations.'}\n")
    
    # Floor Details
    report_lines.append("2. FLOOR DETAILS\n")
    report_lines.append("Floor 1:")
    report_lines += format_rooms(aggregate_rooms(st.session_state.floor1_rooms))
    
    if st.session_state.repeat_rooms and repeat_count > 0:
        report_lines.append(f"\nFloors 2 → {st.session_state.total_floors} (Repeated):")
        for r in st.session_state.repeat_rooms:
            report_lines.append(f"- Base Layout: {r['w']} ft x {r['l']} ft = {int(r['area'])} sq ft each")
        report_lines.append(f"- Number of Repeated Floors: {repeat_count}")
        report_lines.append(f"- Total Repeated Floors Area: {total_repeat} sq ft")
    
    # Totals
    report_lines.append("\n3. TOTALS")
    report_lines.append(f"- Floor 1 Total .......... {total_floor1} sq ft")
    report_lines.append(f"- Floors 2-{st.session_state.total_floors} Total ...... {total_repeat} sq ft")
    report_lines.append(f"- GRAND TOTAL ............ {total_area} sq ft\n")
    report_lines.append("Notes: Areas ready for professional cleaning. Confirm access and floor conditions before starting.\n")
    
    summary_text = "\n".join(report_lines)
    
    st.text_area("Final Report:", summary_text, height=450)
    
    components.html(f"""
        <button style="padding:12px;background-color:#007bff;color:white;border:none;border-radius:6px;width:100%;font-weight:bold;cursor:pointer;font-family:sans-serif;"
        onclick="navigator.clipboard.writeText(`{summary_text}`); this.innerText='✓ Report Copied'; this.style.backgroundColor='#28a745';">
        Copy Report</button>
    """, height=70)

# ===================== RESET =====================
st.divider()
if st.button("Reset All Data"):
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.rerun()
