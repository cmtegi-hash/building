import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title="Pro Inspection Master", layout="wide")

# ======================================================
# GLOBAL STATE
# ======================================================
if "building_name" not in st.session_state: st.session_state.building_name = ""
if "address" not in st.session_state: st.session_state.address = ""
if "total_floors" not in st.session_state: st.session_state.total_floors = None
if "floor1" not in st.session_state: st.session_state.floor1 = []
if "repeat" not in st.session_state: st.session_state.repeat = []
if "stairs" not in st.session_state: st.session_state.stairs = []
if "st_current_f" not in st.session_state: st.session_state.st_current_f = None
if "st_name" not in st.session_state: st.session_state.st_name = ""
if "st_dir" not in st.session_state: st.session_state.st_dir = "Up"
if "log_data" not in st.session_state:
    st.session_state.log_data = {
        "techs": "", "hours": "", "equipment": [], "soil": "Medium", 
        "parking": "Yes", "notes": "", "saved": False,
        "laundry": False, "washroom": False
    }

def to_float(x):
    try: return float(x)
    except: return 0.0

# ======================================================
# CALCULATIONS
# ======================================================
f1_total = sum(r["Area"] for r in st.session_state.floor1)
repeat_count = max((st.session_state.total_floors or 1) - 1, 0)
rep_total_area = sum(r["Area"] for r in st.session_state.repeat) * repeat_count
st_total_area = sum(s["Area"] for s in st.session_state.stairs)
st_total_steps = sum(s["Steps"] for s in st.session_state.stairs)
st_total_landings_area = sum(s["Area"] for s in st.session_state.stairs)
grand_total = f1_total + rep_total_area + st_total_area

# ======================================================
# HEADER (HTML + CSS vía components.html compatible iOS)
# ======================================================
header_html = f"""
<div style="
    background-color:#1e1e1e; color:#28a745;
    padding:20px; border-radius:10px; border:1px solid #28a745;
    text-align:center; margin-bottom:25px;
    font-family:sans-serif;
">
    <div style="color:white; font-size:18px; margin-bottom:5px;">
        {st.session_state.building_name} | {st.session_state.address}
    </div>
    <div style="display:flex; justify-content:center; gap:20px; flex-wrap:wrap;">
        <div style="font-size:22px; font-weight:bold;">Total Area: {int(grand_total):,} Sq Ft</div>
        <div style="font-size:22px; font-weight:bold;">Total Landings Area: {int(st_total_landings_area):,} Sq Ft</div>
        <div style="font-size:22px; font-weight:bold;">Total Steps: {int(st_total_steps)}</div>
    </div>
</div>
"""
components.html(header_html, height=140)

# ======================================================
# SETUP
# ======================================================
st.markdown("### Building Setup")
c_n, c_a, c_f = st.columns([2, 2, 1])

st.session_state.building_name = c_n.text_input("Building Name", st.session_state.building_name)
st.session_state.address = c_a.text_input("Address", st.session_state.address)

# Total Floors vacío
tf_input = c_f.text_input("Total Floors", "" if st.session_state.total_floors is None else str(st.session_state.total_floors))
if tf_input.isdigit():
    st.session_state.total_floors = int(tf_input)
else:
    st.session_state.total_floors = None

tabs = st.tabs(["Floor 1", "Repeated Floors", "Stairs", "Logistics", "Report"])

# ======================================================
# TAB 1: FLOOR 1
# ======================================================
with tabs[0]:
    st.subheader("Floor 1")
    with st.form("f1_form", clear_on_submit=True):
        f1_n = st.text_input("Area Name")
        c1, c2 = st.columns(2)
        w, l = c1.text_input("Width"), c2.text_input("Length")
        if st.form_submit_button("Save Entry"):
            if w and l:
                name = f1_n.strip().capitalize() if f1_n else "Area"
                area = int(to_float(w) * to_float(l))
                found = False
                for item in st.session_state.floor1:
                    if item["Name"] == name:
                        item["Area"] += area
                        item["Details"] += f" + {w}x{l}"
                        found = True; break
                if not found:
                    st.session_state.floor1.append({"Name": name, "Details": f"{w}x{l}", "Area": area})
                st.rerun()
    if st.session_state.floor1:
        ed1 = st.data_editor(pd.DataFrame(st.session_state.floor1), num_rows="dynamic", use_container_width=True, key="ed_f1")
        if len(ed1) != len(st.session_state.floor1): st.session_state.floor1 = ed1.to_dict("records"); st.rerun()

# ======================================================
# TAB 2: REPEATED FLOORS
# ======================================================
with tabs[1]:
    st.subheader(f"Repeated Floors (2 To {st.session_state.total_floors or '?'})")
    with st.form("rep_form"):
        c1, c2 = st.columns(2)
        rw, rl = c1.text_input("Width"), c2.text_input("Length")
        if st.form_submit_button("Save Entry"):
            if rw and rl:
                st.session_state.repeat = [{"W": rw, "L": rl, "Area": int(to_float(rw)*to_float(rl))}]
                st.rerun()
    if st.session_state.repeat:
        df_rep = pd.DataFrame(st.session_state.repeat)
        df_rep["Report Formula"] = df_rep.apply(lambda x: f"{x['W']} x {x['L']} x {repeat_count} = {int(x['Area']*repeat_count)} Sq Ft", axis=1)
        ed_rep = st.data_editor(df_rep, num_rows="dynamic", use_container_width=True, key="ed_rep")
        if len(ed_rep) != len(st.session_state.repeat): st.session_state.repeat = ed_rep.to_dict("records"); st.rerun()

# ======================================================
# TAB 3: STAIRS
# ======================================================
with tabs[2]:
    st.subheader("Stairs Case")
    if st.session_state.st_current_f is None:
        st.session_state.st_name = st.text_input("Staircase Name", "Main Stairs")
        st.write("Select Start Point To Begin:")
        cs1, cs2, cs3, cs4 = st.columns(4)
        if cs1.button("🏢 Floor 1"): st.session_state.st_current_f = "1"; st.session_state.st_dir = "Up"; st.rerun()
        if cs2.button("🔝 Floor " + str(st.session_state.total_floors or "?")): st.session_state.st_current_f = str(st.session_state.total_floors or "?"); st.session_state.st_dir = "Down"; st.rerun()
        if cs3.button("📦 Basement"): st.session_state.st_current_f = "Basement"; st.session_state.st_dir = "Up"; st.rerun()
        if cs4.button("🏠 Roof"): st.session_state.st_current_f = "Roof"; st.session_state.st_dir = "Down"; st.rerun()
    else:
        curr = st.session_state.st_current_f
        try:
            val = int(curr)
            target = str(val + 1) if st.session_state.st_dir == "Up" else str(val - 1)
            if st.session_state.st_dir == "Up" and st.session_state.total_floors and val >= st.session_state.total_floors: target="Roof"
            if st.session_state.st_dir == "Down" and val <= 1: target="Basement"
        except:
            if curr=="Basement": target="1"
            elif curr=="Roof": target=str(st.session_state.total_floors or "?")
            else: target=""
        with st.form("st_form_v3"):
            st.info(f"Adding to {st.session_state.st_name}: From {st.session_state.st_current_f} Going {st.session_state.st_dir}")
            c1, c2, c3 = st.columns(3)
            f_from = c1.text_input("From Floor", st.session_state.st_current_f)
            f_to = c2.text_input("To Floor", target)
            stps = c3.text_input("Steps Quantity")
            st.write("Landings (W1 L1 | W2 L2)")
            ca, cb, cc, cd = st.columns(4)
            w1, l1, w2, l2 = ca.text_input("W1"), cb.text_input("L1"), cc.text_input("W2"), cd.text_input("L2")
            if st.form_submit_button("Save Section"):
                if f_to and stps:
                    area_st = (to_float(w1)*to_float(l1)) + (to_float(w2)*to_float(l2))
                    st.session_state.stairs.append({"Staircase": st.session_state.st_name,"Section": f"{f_from}-{f_to}","Steps": int(to_float(stps)),"Area": int(area_st),"Landings": 2 if w2 else 1})
                    st.session_state.st_current_f = f_to; st.rerun()
        st.write("---")
        cb1, cb2 = st.columns(2)
        if cb1.button("➕ Add New Staircase Column (New Name)"): st.session_state.st_current_f=None; st.rerun()
        if cb2.button("✅ Finish & Close Current Route"): st.session_state.st_current_f=None; st.rerun()
    if st.session_state.stairs:
        ed_s = st.data_editor(pd.DataFrame(st.session_state.stairs), num_rows="dynamic", use_container_width=True, key="ed_st")
        if len(ed_s) != len(st.session_state.stairs): st.session_state.stairs=ed_s.to_dict("records"); st.rerun()

# ======================================================
# TAB 4: LOGISTICS (intacto)
# ======================================================
with tabs[3]:
    st.subheader("Logistics")
    with st.form("log_form"):
        cl1, cl2 = st.columns(2)
        techs = cl1.text_input("Personnel (Techs)", st.session_state.log_data["techs"])
        hours = cl2.text_input("Estimated Hours", st.session_state.log_data["hours"])
        st.write("Equipment & Facilities")
        ec1, ec2, ec3, ec4, ec5 = st.columns(5)
        tm = ec1.checkbox("Truck Mount", "Truck Mount" in st.session_state.log_data["equipment"])
        pt = ec2.checkbox("Portable", "Portable" in st.session_state.log_data["equipment"])
        cx = ec3.checkbox("Cimex", "Cimex" in st.session_state.log_data["equipment"])
        lnd = ec4.checkbox("Laundry Room", st.session_state.log_data["laundry"])
        wsh = ec5.checkbox("Washroom", st.session_state.log_data["washroom"])
        soil_options = ["Light","Medium","Heavy (Restoration)"]
        soil = st.radio("Soil Level", soil_options, index=soil_options.index(st.session_state.log_data["soil"]))
        parking = st.radio("Parking Available?", ["Yes","No"], index=0 if st.session_state.log_data["parking"]=="Yes" else 1)
        notes = st.text_area("Additional Notes", st.session_state.log_data["notes"])
        if st.form_submit_button("Save Logistics"):
            st.session_state.log_data.update({
                "techs": techs, "hours": hours, "soil": soil, 
                "parking": parking, "notes": notes, "saved": True,
                "laundry": lnd, "washroom": wsh,
                "equipment": [e for e,v in zip(["Truck Mount","Portable","Cimex"],[tm,pt,cx]) if v]
            })
            st.rerun()
    if st.session_state.log_data["saved"]:
        log_html=f"""
        <div style='background:#fff;border:1px solid #000;padding:15px;white-space:pre-wrap;font-family:Courier New, monospace;color:#000'>
PERSONNEL: {st.session_state.log_data['techs']} Techs / {st.session_state.log_data['hours']} Hours
EQUIPMENT: {", ".join(st.session_state.log_data['equipment'])}
FACILITIES: Laundry Room: {"YES" if st.session_state.log_data['laundry'] else "NO"} | Washroom: {"YES" if st.session_state.log_data['washroom'] else "NO"}
SOIL LEVEL: {st.session_state.log_data['soil'].upper()}
PARKING: {st.session_state.log_data['parking'].upper()}
NOTES: {st.session_state.log_data['notes']}
        </div>
        """
        components.html(log_html,height=180)

# ======================================================
# TAB 5: REPORT
# ======================================================
with tabs[4]:
    rep = [
        f"{st.session_state.building_name.upper()}",
        f"{st.session_state.address}","",
        f"Total Area: {int(grand_total):,} Sq Ft",
        f"Total Landings Area: {int(st_total_landings_area):,} Sq Ft",
        f"Total Steps: {int(st_total_steps)}","",
        "---","LOGISTICS",
        f"PERSONNEL: {st.session_state.log_data['techs']} Techs / {st.session_state.log_data['hours']} Hours",
        f"EQUIPMENT: {', '.join(st.session_state.log_data['equipment'])}",
        f"FACILITIES: Laundry: {'Yes' if st.session_state.log_data['laundry'] else 'No'} | Washroom: {'Yes' if st.session_state.log_data['washroom'] else 'No'}",
        f"SOIL LEVEL: {st.session_state.log_data['soil'].upper()}",
        f"PARKING: {st.session_state.log_data['parking'].upper()}",
        f"NOTES: {st.session_state.log_data['notes']}","---","FLOOR 1 DETAIL"
    ]
    for r in st.session_state.floor1: rep.append(f"- {r['Name']}: {r['Details']} (1) = {r['Area']} Sq Ft")
    if st.session_state.repeat:
        rep.append(f"\nREPEATED FLOORS DETAIL (2 To {st.session_state.total_floors})")
        for r in st.session_state.repeat: rep.append(f"- Typical Layout: {r['W']} x {r['L']} x {repeat_count} = {int(rep_total_area)} Sq Ft")
    if st.session_state.stairs:
        rep.append("\nSTAIRS DETAIL")
        df_s=pd.DataFrame(st.session_state.stairs)
        for name,group in df_s.groupby("Staircase"):
            rep.append(f"\n[{name.upper()}]")
            for _,row in group.iterrows(): rep.append(f"- Section {row['Section']}: {row['Steps']} Steps | {row['Landings']} Landings ({row['Area']} Sq Ft)")
    final_text="\n".join(rep)
    st.text_area("Final Output",final_text,height=400)
    components.html(f'<button style="width:100%;padding:12px;background:#28a745;color:white;border:none;border-radius:6px;font-weight:bold;cursor:pointer;" onclick="navigator.clipboard.writeText(`{final_text}`); this.innerText=\'COPIED TO CLIPBOARD!\';">COPY REPORT</button>',height=70)import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title="Pro Inspection Master", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .resumen-box {
        background-color: #1e1e1e; color: #28a745;
        padding: 20px; border-radius: 10px;
        border: 1px solid #28a745; text-align: center; margin-bottom: 25px;
    }
    .log-confirm {
        background-color: #ffffff; border: 1px solid #000;
        padding: 15px; border-radius: 0px; margin-top: 10px; color: #000;
        font-family: 'Courier New', Courier, monospace;
        white-space: pre-wrap;
    }
    .total-val { font-size: 22px; font-weight: bold; margin: 0 25px; }
    div.stButton > button { 
        width: 100%; border-radius: 8px; font-weight: bold; 
        background-color: #007bff; color: white; height: 3em;
    }
</style>
""", unsafe_allow_html=True)

# ======================================================
# GLOBAL STATE
# ======================================================
if "building_name" not in st.session_state: st.session_state.building_name = ""
if "address" not in st.session_state: st.session_state.address = ""
if "total_floors" not in st.session_state: st.session_state.total_floors = None
if "floor1" not in st.session_state: st.session_state.floor1 = []
if "repeat" not in st.session_state: st.session_state.repeat = []
if "stairs" not in st.session_state: st.session_state.stairs = []
if "st_current_f" not in st.session_state: st.session_state.st_current_f = None
if "st_name" not in st.session_state: st.session_state.st_name = ""
if "st_dir" not in st.session_state: st.session_state.st_dir = "Up"
if "log_data" not in st.session_state:
    st.session_state.log_data = {
        "techs": "", "hours": "", "equipment": [], "soil": "Medium", 
        "parking": "Yes", "notes": "", "saved": False,
        "laundry": False, "washroom": False
    }

def to_float(x):
    try: return float(x)
    except: return 0.0

# ======================================================
# CALCULATIONS
# ======================================================
f1_total = sum(r["Area"] for r in st.session_state.floor1)
repeat_count = max((st.session_state.total_floors or 1) - 1, 0)
rep_total_area = sum(r["Area"] for r in st.session_state.repeat) * repeat_count

st_total_area = sum(s["Area"] for s in st.session_state.stairs)
st_total_steps = sum(s["Steps"] for s in st.session_state.stairs)

# 👉 Landings en Sq Ft
st_total_landings_area = sum(s["Area"] for s in st.session_state.stairs)

grand_total = f1_total + rep_total_area + st_total_area

# ======================================================
# HEADER
# ======================================================
st.markdown(f'''
<div class="resumen-box">
    <div style="color:white; font-size:18px; margin-bottom:5px;">{st.session_state.building_name} | {st.session_state.address}</div>
    <span class="total-val">Total Area: {int(grand_total):,} Sq Ft</span>
    <span class="total-val">Total Landings Area: {int(st_total_landings_area):,} Sq Ft</span>
    <span class="total-val">Total Steps: {int(st_total_steps)}</span>
</div>
''', unsafe_allow_html=True)

# ======================================================
# SETUP
# ======================================================
st.markdown("### Building Setup")
c_n, c_a, c_f = st.columns([2, 2, 1])

st.session_state.building_name = c_n.text_input("Building Name", st.session_state.building_name)
st.session_state.address = c_a.text_input("Address", st.session_state.address)

# 👇 VACÍO (sin default)
tf_input = c_f.text_input("Total Floors", "" if st.session_state.total_floors is None else str(st.session_state.total_floors))
if tf_input.isdigit():
    st.session_state.total_floors = int(tf_input)
else:
    st.session_state.total_floors = None

tabs = st.tabs(["Floor 1", "Repeated Floors", "Stairs", "Logistics", "Report"])

# ======================================================
# TAB 1: FLOOR 1
# ======================================================
with tabs[0]:
    st.subheader("Floor 1")
    with st.form("f1_form", clear_on_submit=True):
        f1_n = st.text_input("Area Name")
        c1, c2 = st.columns(2)
        w, l = c1.text_input("Width"), c2.text_input("Length")
        if st.form_submit_button("Save Entry"):
            if w and l:
                name = f1_n.strip().capitalize() if f1_n else "Area"
                area = int(to_float(w) * to_float(l))
                found = False
                for item in st.session_state.floor1:
                    if item["Name"] == name:
                        item["Area"] += area
                        item["Details"] += f" + {w}x{l}"
                        found = True; break
                if not found:
                    st.session_state.floor1.append({"Name": name, "Details": f"{w}x{l}", "Area": area})
                st.rerun()
    if st.session_state.floor1:
        ed1 = st.data_editor(pd.DataFrame(st.session_state.floor1), num_rows="dynamic", use_container_width=True, key="ed_f1")
        if len(ed1) != len(st.session_state.floor1): 
            st.session_state.floor1 = ed1.to_dict("records"); 
            st.rerun()

# ======================================================
# TAB 2: REPEATED FLOORS
# ======================================================
with tabs[1]:
    st.subheader(f"Repeated Floors (2 To {st.session_state.total_floors or '?'})")
    with st.form("rep_form"):
        c1, c2 = st.columns(2)
        rw, rl = c1.text_input("Width"), c2.text_input("Length")
        if st.form_submit_button("Save Entry"):
            if rw and rl:
                st.session_state.repeat = [{"W": rw, "L": rl, "Area": int(to_float(rw)*to_float(rl))}]
                st.rerun()
    if st.session_state.repeat:
        df_rep = pd.DataFrame(st.session_state.repeat)
        df_rep["Report Formula"] = df_rep.apply(lambda x: f"{x['W']} x {x['L']} x {repeat_count} = {int(x['Area']*repeat_count)} Sq Ft", axis=1)
        ed_rep = st.data_editor(df_rep, num_rows="dynamic", use_container_width=True, key="ed_rep")
        if len(ed_rep) != len(st.session_state.repeat): 
            st.session_state.repeat = ed_rep.to_dict("records"); 
            st.rerun()

# ======================================================
# TAB 3: STAIRS
# ======================================================
with tabs[2]:
    st.subheader("Stairs Case")
    
    if st.session_state.st_current_f is None:
        st.session_state.st_name = st.text_input("Staircase Name (e.g. Main Stairs, Service A)", "Main Stairs")
        st.write("Select Start Point To Begin:")
        cs1, cs2, cs3, cs4 = st.columns(4)
        if cs1.button("🏢 Floor 1"): 
            st.session_state.st_current_f = "1"; st.session_state.st_dir = "Up"; st.rerun()
        if cs2.button("🔝 Floor " + str(st.session_state.total_floors or "?")): 
            st.session_state.st_current_f = str(st.session_state.total_floors or "?"); st.session_state.st_dir = "Down"; st.rerun()
        if cs3.button("📦 Basement"): 
            st.session_state.st_current_f = "Basement"; st.session_state.st_dir = "Up"; st.rerun()
        if cs4.button("🏠 Roof"): 
            st.session_state.st_current_f = "Roof"; st.session_state.st_dir = "Down"; st.rerun()
    else:
        curr = st.session_state.st_current_f
        try:
            val = int(curr)
            if st.session_state.st_dir == "Up":
                target = str(val + 1) if st.session_state.total_floors and val < st.session_state.total_floors else "Roof"
            else:
                target = str(val - 1) if val > 1 else "Basement"
        except:
            if curr == "Basement": target = "1"
            elif curr == "Roof": target = str(st.session_state.total_floors or "?")
            else: target = ""

        with st.form("st_form_v3"):
            st.info(f"Adding to {st.session_state.st_name}: From {st.session_state.st_current_f} Going {st.session_state.st_dir}")
            c1, c2, c3 = st.columns(3)
            f_from = c1.text_input("From Floor", st.session_state.st_current_f)
            f_to = c2.text_input("To Floor", target)
            stps = c3.text_input("Steps Quantity")
            st.write("Landings (W1 L1 | W2 L2)")
            ca, cb, cc, cd = st.columns(4)
            w1, l1, w2, l2 = ca.text_input("W1"), cb.text_input("L1"), cc.text_input("W2"), cd.text_input("L2")
            
            if st.form_submit_button("Save Section"):
                if f_to and stps:
                    area_st = (to_float(w1)*to_float(l1)) + (to_float(w2)*to_float(l2))
                    st.session_state.stairs.append({
                        "Staircase": st.session_state.st_name,
                        "Section": f"{f_from}-{f_to}", 
                        "Steps": int(to_float(stps)), 
                        "Area": int(area_st),
                        "Landings": 2 if w2 else 1
                    })
                    st.session_state.st_current_f = f_to
                    st.rerun()

        st.write("---")
        cb1, cb2 = st.columns(2)
        if cb1.button("➕ Add New Staircase Column (New Name)"):
            st.session_state.st_current_f = None; st.rerun()
        if cb2.button("✅ Finish & Close Current Route"):
            st.session_state.st_current_f = None; st.rerun()

    if st.session_state.stairs:
        ed_s = st.data_editor(pd.DataFrame(st.session_state.stairs), num_rows="dynamic", use_container_width=True, key="ed_st")
        if len(ed_s) != len(st.session_state.stairs): 
            st.session_state.stairs = ed_s.to_dict("records"); 
            st.rerun()

# ======================================================
# TAB 4: LOGISTICS (INTACTO)
# ======================================================
with tabs[3]:
    st.subheader("Logistics")
    with st.form("log_form"):
        cl1, cl2 = st.columns(2)
        techs = cl1.text_input("Personnel (Techs)", st.session_state.log_data["techs"])
        hours = cl2.text_input("Estimated Hours", st.session_state.log_data["hours"])
        
        st.write("Equipment & Facilities")
        ec1, ec2, ec3, ec4, ec5 = st.columns(5)
        tm = ec1.checkbox("Truck Mount", "Truck Mount" in st.session_state.log_data["equipment"])
        pt = ec2.checkbox("Portable", "Portable" in st.session_state.log_data["equipment"])
        cx = ec3.checkbox("Cimex", "Cimex" in st.session_state.log_data["equipment"])
        lnd = ec4.checkbox("Laundry Room", st.session_state.log_data["laundry"])
        wsh = ec5.checkbox("Washroom", st.session_state.log_data["washroom"])
        
        soil_options = ["Light", "Medium", "Heavy (Restoration)"]
        soil = st.radio("Soil Level", soil_options, index=soil_options.index(st.session_state.log_data["soil"]))
        parking = st.radio("Parking Available?", ["Yes", "No"], index=0 if st.session_state.log_data["parking"] == "Yes" else 1)
        notes = st.text_area("Additional Notes", st.session_state.log_data["notes"])
        
        if st.form_submit_button("Save Logistics"):
            st.session_state.log_data.update({
                "techs": techs, "hours": hours, "soil": soil, 
                "parking": parking, "notes": notes, "saved": True,
                "laundry": lnd, "washroom": wsh,
                "equipment": [e for e, v in zip(["Truck Mount", "Portable", "Cimex"], [tm, pt, cx]) if v]
            })
            st.rerun()

    if st.session_state.log_data["saved"]:
        st.markdown(f"""<div class="log-confirm">
PERSONNEL: {st.session_state.log_data['techs']} Techs / {st.session_state.log_data['hours']} Hours
EQUIPMENT: {", ".join(st.session_state.log_data['equipment'])}
FACILITIES: Laundry Room: {"YES" if st.session_state.log_data['laundry'] else "NO"} | Washroom: {"YES" if st.session_state.log_data['washroom'] else "NO"}
SOIL LEVEL: {st.session_state.log_data['soil'].upper()}
PARKING: {st.session_state.log_data['parking'].upper()}
NOTES: {st.session_state.log_data['notes']}
        </div>""", unsafe_allow_html=True)

# ======================================================
# TAB 5: REPORT (AJUSTADO)
# ======================================================
with tabs[4]:
    rep = [
        f"{st.session_state.building_name.upper()}",
        f"{st.session_state.address}",
        "",
        f"Total Area: {int(grand_total):,} Sq Ft",
        f"Total Landings Area: {int(st_total_landings_area):,} Sq Ft",
        f"Total Steps: {int(st_total_steps)}",
        "",
        "---",
        "LOGISTICS",
        f"PERSONNEL: {st.session_state.log_data['techs']} Techs / {st.session_state.log_data['hours']} Hours",
        f"EQUIPMENT: {', '.join(st.session_state.log_data['equipment'])}",
        f"FACILITIES: Laundry: {'Yes' if st.session_state.log_data['laundry'] else 'No'} | Washroom: {'Yes' if st.session_state.log_data['washroom'] else 'No'}",
        f"SOIL LEVEL: {st.session_state.log_data['soil'].upper()}",
        f"PARKING: {st.session_state.log_data['parking'].upper()}",
        f"NOTES: {st.session_state.log_data['notes']}",
        "---",
        "FLOOR 1 DETAIL"
    ]

    for r in st.session_state.floor1:
        rep.append(f"- {r['Name']}: {r['Details']} (1) = {r['Area']} Sq Ft")
    
    if st.session_state.repeat:
        rep.append(f"\nREPEATED FLOORS DETAIL (2 To {st.session_state.total_floors})")
        for r in st.session_state.repeat:
            rep.append(f"- Typical Layout: {r['W']} x {r['L']} x {repeat_count} = {int(rep_total_area)} Sq Ft")
            
    if st.session_state.stairs:
        rep.append("\nSTAIRS DETAIL")
        df_s = pd.DataFrame(st.session_state.stairs)
        for name, group in df_s.groupby("Staircase"):
            rep.append(f"\n[{name.upper()}]")
            for _, row in group.iterrows():
                rep.append(f"- Section {row['Section']}: {row['Steps']} Steps | {row['Landings']} Landings ({row['Area']} Sq Ft)")
    
    final_text = "\n".join(rep)
    st.text_area("Final Output", final_text, height=400)
    components.html(f'<button style="width:100%;padding:12px;background:#28a745;color:white;border:none;border-radius:6px;font-weight:bold;cursor:pointer;" onclick="navigator.clipboard.writeText(`{final_text}`); this.innerText=\'COPIED TO CLIPBOARD!\';">COPY REPORT</button>', height=70)
