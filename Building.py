import streamlit as st
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
