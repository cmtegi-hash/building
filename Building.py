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
# HEADER (COMPACT 2 LINES)
# ======================================================
header_html = f"""
<div style="
    background-color:#1e1e1e;
    color:#28a745;
    padding:10px 15px;
    border-radius:8px;
    border:1px solid #28a745;
    text-align:center;
    margin-bottom:15px;
    font-family:sans-serif;
    line-height:1.4;
">
    <div style="color:white; font-size:16px; margin-bottom:4px;">
        {st.session_state.building_name} | {st.session_state.address}
    </div>
    <div style="font-size:15px; font-weight:500;">
        Area: {int(grand_total):,} Sq Ft | 
        Landings: {int(st_total_landings_area):,} Sq Ft | 
        Steps: {int(st_total_steps)}
    </div>
</div>
"""
components.html(header_html, height=90)

# ======================================================
# BUILDING SETUP
# ======================================================
st.markdown("### Building Setup")
c_n, c_a, c_f = st.columns([2, 2, 1])

st.session_state.building_name = c_n.text_input("Building Name", st.session_state.building_name)
st.session_state.address = c_a.text_input("Address", st.session_state.address)

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
                        found = True
                        break
                if not found:
                    st.session_state.floor1.append({"Name": name, "Details": f"{w}x{l}", "Area": area})
                st.rerun()
    if st.session_state.floor1:
        ed1 = st.data_editor(pd.DataFrame(st.session_state.floor1), num_rows="dynamic", use_container_width=True, key="ed_f1")
        if len(ed1) != len(st.session_state.floor1): 
            st.session_state.floor1 = ed1.to_dict("records")
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
            st.session_state.repeat = ed_rep.to_dict("records")
            st.rerun()

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
        if cb1.button("➕ Add New Staircase Column (New Name)"): st.session_state.st_current_f=None; st.rerun()
        if cb2.button("✅ Finish & Close Current Route"): st.session_state.st_current_f=None; st.rerun()
    if st.session_state.stairs:
        ed_s = st.data_editor(pd.DataFrame(st.session_state.stairs), num_rows="dynamic", use_container_width=True, key="ed_st")
        if len(ed_s) != len(st.session_state.stairs): 
            st.session_state.stairs=ed_s.to_dict("records")
            st.rerun()

# ======================================================
# TAB 4: LOGISTICS
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
Personnel: {st.session_state.log_data['techs']} Techs / {st.session_state.log_data['hours']} Hours
Equipment: {", ".join(st.session_state.log_data['equipment'])}
Facilities: Laundry Room: {"Yes" if st.session_state.log_data['laundry'] else "No"} | Washroom: {"Yes" if st.session_state.log_data['washroom'] else "No"}
Soil Level: {st.session_state.log_data['soil']}
Parking: {st.session_state.log_data['parking']}
Notes: {st.session_state.log_data['notes']}
        </div>
        """
        components.html(log_html,height=180)

# ======================================================
# TAB 5: REPORT
# ======================================================
with tabs[4]:
    rep = [
        f"{st.session_state.building_name}",
        f"{st.session_state.address}","",
        f"Total Area: {int(grand_total):,} Sq Ft",
        f"Total Landings Area: {int(st_total_landings_area):,} Sq Ft",
        f"Total Steps: {int(st_total_steps)}","",
        "---","Logistics",
        f"Personnel: {st.session_state.log_data['techs']} Techs / {st.session_state.log_data['hours']} Hours",
        f"Equipment: {', '.join(st.session_state.log_data['equipment'])}",
        f"Facilities: Laundry: {'Yes' if st.session_state.log_data['laundry'] else 'No'} | Washroom: {'Yes' if st.session_state.log_data['washroom'] else 'No'}",
        f"Soil Level: {st.session_state.log_data['soil']}",
        f"Parking: {st.session_state.log_data['parking']}",
        f"Notes: {st.session_state.log_data['notes']}","---","Floor 1 Detail"
    ]

    for r in st.session_state.floor1:
        rep.append(f"- {r['Name']}: {r['Details']} (1) = {r['Area']} Sq Ft")

    if st.session_state.repeat:
        rep.append(f"\nRepeated Floors Detail (2 To {st.session_state.total_floors})")
        for r in st.session_state.repeat:
            rep.append(f"- Typical Layout: {r['W']} x {r['L']} x {repeat_count} = {int(rep_total_area)} Sq Ft")

    if st.session_state.stairs:
        rep.append("\nStairs Detail")
        df_s = pd.DataFrame(st.session_state.stairs)
        for name, group in df_s.groupby("Staircase"):
            rep.append(f"\n[{name}]")
            for _, row in group.iterrows():
                rep.append(f"- Section {row['Section']}: {row['Steps']} Steps | {row['Landings']} Landings ({row['Area']} Sq Ft)")

    final_text = "\n".join(rep)
    st.text_area("Final Output", final_text, height=400)
    components.html(
        f'<button style="width:100%;padding:12px;background:#28a745;color:white;border:none;border-radius:6px;font-weight:bold;cursor:pointer;" onclick="navigator.clipboard.writeText(`{final_text}`); this.innerText=\'COPIED TO CLIPBOARD!\';">COPY REPORT</button>',
        height=70
    )import streamlit as st
import streamlit.components.v1 as components
import re
import json
import uuid

st.set_page_config(page_title="Tech Service Report", layout="wide")
st.title("🛠️ Tech Service Report & Audit")

# --- INITIAL SESSION STATE ---
if "template_text" not in st.session_state:
    st.session_state["template_text"] = ""
if "final_report" not in st.session_state:
    st.session_state["final_report"] = ""
if "audit_lines_h" not in st.session_state:
    st.session_state["audit_lines_h"] = []
if "audit_lines_s" not in st.session_state:
    st.session_state["audit_lines_s"] = []

# --- MAIN INTERFACE ---
col_gen, col_paste = st.columns([1, 2])

with col_gen:
    st.subheader("Step 1: Setup")
    f_count = st.number_input("Total Floors", min_value=1, value=3)
    s_count = st.number_input("Stairwells", min_value=0, value=2)
    
    if st.button("Generate Master Template"):
        temp = [
            "--- CONFIGURATION (DO NOT DELETE) ---",
            "Rate SQFT: 0.30",
            "Rate Step: 3.50",
            "---------------------------------------",
            f"\nBuilding: [Name]", 
            "Type: Commercial", 
            f"Total Floors: {f_count}\n"
        ]
        for i in range(1, f_count + 1):
            temp.append(f"Floor {i}:")
            temp.append("0x0\n")
        for s in range(1, s_count + 1):
            temp.append(f"Stairwell {s}:")
            temp.append("Basement → 1")
            temp.append("0 steps")
            temp.append("0x0\n")
            for f in range(1, f_count):
                temp.append(f"{f} → {f+1}")
                temp.append("0 steps")
                temp.append("0x0\n")
            temp.append(f"{f_count} → Roof")
            temp.append("0 steps")
            temp.append("0x0\n")
        
        temp.extend([
            "Logistics & Site Resources:",
            "Technicians: 0",
            "Estimated Hours: 0",
            "xParking", "xWater Access", "xElectricity", "xBathroom", "xElevator", "xLaundry Room",
            "\nEquipment Checklist:",
            "#Truck Mount", "#Portable", "#Cimex",
            "\nSoil Level Assessment:",
            "Light", "xMedium", "xHeavy",
            "\nAdditional Notes:"
        ])
        st.session_state["template_text"] = "\n".join(temp)
    
    if st.session_state["template_text"]:
        st.text_area("Master Template:", st.session_state["template_text"], height=400)

with col_paste:
    st.subheader("Step 2: Process Data")
    user_input = st.text_area("Input Area (Paste here)", height=415)
    
    if st.button("Generate Final Tech Report"):
        if user_input.strip():
            lines = user_input.splitlines()
            c_rate_sqft = 0.30
            c_rate_step = 3.50
            h_sqft_total = 0
            l_sqft_total = 0
            t_steps_total = 0
            est_h = 1.0
            tech_n = "0"
            
            breakdown = {}
            available = []
            not_available = []
            equip_used = []
            soil_info = []

            curr_m = ""
            curr_sub = ""
            
            log_keys = ["Parking", "Water", "Electricity", "Bathroom", "Elevator", "Laundry"]
            equip_keys = ["Mount", "Portable", "Cimex"]
            soil_keys = ["Light", "Medium", "Heavy"]

            for line in lines:
                clean = line.strip()
                if not clean:
                    continue

                # OMIT completely lines starting with #
                if clean.startswith("#"):
                    continue
                
                if "Rate SQFT" in clean:
                    m = re.search(r"(\d+\.?\d*)", clean)
                    if m: c_rate_sqft = float(m.group(1))
                    continue

                if "Rate Step" in clean:
                    m = re.search(r"(\d+\.?\d*)", clean)
                    if m: c_rate_step = float(m.group(1))
                    continue
                
                if any(x in clean for x in ["Floor", "Stairwell", "Logistics", "Equipment", "Soil", "Notes"]):
                    curr_m = clean.replace(":", "")
                    curr_sub = ""
                    if curr_m not in breakdown:
                        breakdown[curr_m] = {"h_sqft": 0, "sub": {}}
                    continue
                
                # --- LOGISTICS CORE ---
                if "Technicians" in clean:
                    m = re.search(r"(\d+)", clean)
                    tech_n = m.group(1) if m else "0"
                    continue

                if "Estimated Hours" in clean:
                    m = re.search(r"(\d+\.?\d*)", clean)
                    if m: est_h = float(m.group(1))
                    continue

                # --- FLAGS ---
                is_neg = clean.lower().startswith("x")
                name = clean[1:].strip() if is_neg else clean.strip()

                # --- LOGISTICS GROUPING ---
                if any(k in name for k in log_keys):
                    if is_neg:
                        not_available.append(name)
                    else:
                        available.append(name)
                    continue

                # --- EQUIPMENT ---
                if any(k in name for k in equip_keys):
                    equip_used.append(name)
                    continue

                # --- SOIL ---
                if any(k in name for k in soil_keys):
                    if not is_neg:
                        soil_info.append(f"Soil Level: {name}")
                    continue
                
                # --- CALCULATIONS ---
                if "0x0" in clean:
                    continue

                if "→" in clean:
                    curr_sub = clean
                    if curr_sub not in breakdown[curr_m]["sub"]:
                        breakdown[curr_m]["sub"][curr_sub] = {"sqft": 0, "steps": 0, "details": []}
                    continue
                
                if "steps" in clean.lower():
                    m = re.search(r"(\d+)", clean)
                    if m:
                        v = int(m.group(1))
                        t_steps_total += v
                        if curr_sub:
                            breakdown[curr_m]["sub"][curr_sub]["steps"] += v
                    continue
                
                dims = re.findall(r"(\d+\.?\d*)x(\d+\.?\d*)", clean)
                if dims:
                    sub_total = sum(float(w) * float(l) for w, l in dims)
                    if "Stairwell" in curr_m or "→" in curr_sub:
                        l_sqft_total += sub_total
                        if curr_sub:
                            breakdown[curr_m]["sub"][curr_sub]["sqft"] += sub_total
                            breakdown[curr_m]["sub"][curr_sub]["details"].append(clean)
                    else:
                        h_sqft_total += sub_total
                        if curr_m:
                            breakdown[curr_m]["h_sqft"] += sub_total
                            if "details" not in breakdown[curr_m]:
                                breakdown[curr_m]["details"] = []
                            breakdown[curr_m]["details"].append(clean)

            # --- AUDIT DASHBOARD ---
            st.session_state.audit_lines_h = []
            st.session_state.audit_lines_s = []

            for m, data in breakdown.items():
                if "Floor" in m and data["h_sqft"] > 0:
                    ops = " + ".join(data.get("details", []))
                    st.session_state.audit_lines_h.append(
                        f"**{m}:** `{ops}` = **{data['h_sqft']:.2f} ft²** | Subtotal: **${data['h_sqft']*c_rate_sqft:.2f}**"
                    )

                if "Stairwell" in m:
                    for s, v in data["sub"].items():
                        if v["sqft"] > 0 or v["steps"] > 0:
                            ops = " + ".join(v.get("details", [])) if v.get("details") else "0x0"
                            cost = (v["sqft"] * c_rate_sqft) + (v["steps"] * c_rate_step)
                            st.session_state.audit_lines_s.append(
                                f"**{m} ({s}):** `{ops}` (**{v['sqft']:.2f} ft²**) + **{v['steps']} steps** = **${cost:.2f}**"
                            )

            # --- FINAL REPORT ---
            inv = ((h_sqft_total + l_sqft_total) * c_rate_sqft) + (t_steps_total * c_rate_step)
            h_rate = inv / est_h if est_h > 0 else 0
            b_match = re.search(r'Building: \[(.*?)\]', user_input)
            title = b_match.group(1) if b_match else "BUILDING"

            res = [f"--- {title.upper()} - TECH REPORT ---", "\n1. SERVICE SUMMARY"]
            res.append(f"* Hallways Area: {h_sqft_total:.2f} ft²\n* Landings Area: {l_sqft_total:.2f} ft²\n* Total Steps: {t_steps_total} units")
            
            # --- LOGISTICS FORMATTED ---
            res.append("\n2. LOGISTICS & SITE STATUS")
            res.append(f"\nTechnicians: {tech_n}")
            res.append(f"Estimated Hours: {est_h}")

            if available:
                res.append("\nAvailable:")
                res.extend(available)

            if not_available:
                res.append("\nNot Available:")
                res.extend(not_available)

            if equip_used:
                res.append("\nEquipment Used:")
                res.extend(equip_used)

            if soil_info:
                res.append("\n3. SOIL ASSESSMENT")
                res.extend(soil_info)

            res.append(f"\n4. FINAL SUMMARY\nPROJECT TOTAL: ${inv:.2f}\nHOURLY PROFIT: ${h_rate:.2f}/hr")

            st.session_state.final_report = "\n".join(res)

# --- OUTPUT ---
if st.session_state.final_report:
    st.subheader("🔍 1. Audit Dashboard (Friendly View)")
    st.markdown("#### 🏢 Hallways & Floors")
    if st.session_state.audit_lines_h:
        for line in st.session_state.audit_lines_h:
            st.write(line)
    else:
        st.write("*No hallways processed.*")
    
    st.markdown("#### 🪜 Staircases (Landings & Steps)")
    if st.session_state.audit_lines_s:
        for line in st.session_state.audit_lines_s:
            st.write(line)
    else:
        st.write("*No stairwells processed.*")
    
    st.markdown("---")
    st.subheader("📋 2. Final Tech Report")
    st.text_area("Ready to copy:", st.session_state.final_report, height=350)
