import streamlit as st
import streamlit.components.v1 as components
import re

st.set_page_config(page_title="Tech Service Report", layout="wide")
st.title("🛠️ Tech Service Report & Audit")

# --- CONSTANTS ---
ARROW = "→"
SKIP_DIM = "0x0"
FLAG_SKIP = "#"
FLAG_UNAVAIL = "x"

LOG_KEYS = ["Parking", "Water", "Electricity", "Bathroom", "Elevator", "Laundry"]
EQUIP_KEYS = ["Mount", "Portable", "Cimex"]
SOIL_KEYS = ["Light", "Medium", "Heavy"]
SECTION_KEYS = ["Floor", "Stairwell", "Logistics", "Equipment", "Soil", "Notes"]

# --- INITIAL SESSION STATE ---
for key, val in [
    ("template_text", ""),
    ("final_report", ""),
    ("audit_data", None),
    ("audit_ready", False),
]:
    if key not in st.session_state:
        st.session_state[key] = val

# --- COPY BUTTON HELPER ---
def copy_button(text_to_copy, label="📋 Copy to Clipboard"):
    escaped = text_to_copy.replace("`", "\\`").replace("\\", "\\\\").replace("$", "\\$")
    components.html(f"""
        <button onclick="navigator.clipboard.writeText(`{escaped}`).then(()=>{{
            this.innerText='✅ Copied!';
            setTimeout(()=>this.innerText='{label}',2000);
        }})" style="
            background: transparent;
            border: 1px solid #ccc;
            border-radius: 8px;
            padding: 6px 16px;
            font-size: 14px;
            cursor: pointer;
            color: inherit;
            width: 100%;
        ">{label}</button>
    """, height=45)

# --- PARSE FUNCTION ---
def parse_input(lines):
    sqft_rate = 0.30
    step_rate = 3.50
    hallway_sqft = 0.0
    landing_sqft = 0.0
    total_steps = 0
    est_hours = 1.0
    tech_count = "0"

    breakdown = {}
    available = []
    not_available = []
    equip_used = []
    soil_levels = []
    skipped_lines = []
    audit_log = []  # list of dicts: {type, label, detail, value}

    current_section = ""
    current_subsection = ""

    for raw_line in lines:
        clean = raw_line.strip()
        if not clean:
            continue

        # Equipment: #tag = skip entirely
        if clean.startswith(FLAG_SKIP):
            name = clean[1:].strip()
            if any(k in name for k in EQUIP_KEYS):
                skipped_lines.append(clean)
                audit_log.append({"type": "skip", "label": "Skipped", "detail": clean, "value": "not in report"})
            continue

        # Config rates
        if "Rate SQFT" in clean:
            m = re.search(r"(\d+\.?\d*)", clean)
            if m:
                sqft_rate = float(m.group(1))
                audit_log.append({"type": "config", "label": "Config", "detail": "Rate SQFT", "value": f"${sqft_rate:.2f} / ft²"})
            continue

        if "Rate Step" in clean:
            m = re.search(r"(\d+\.?\d*)", clean)
            if m:
                step_rate = float(m.group(1))
                audit_log.append({"type": "config", "label": "Config", "detail": "Rate Step", "value": f"${step_rate:.2f} / step"})
            continue

        # Skip config header lines
        if clean.startswith("---"):
            continue

        # Section detection
        if any(x in clean for x in SECTION_KEYS):
            current_section = clean.replace(":", "").strip()
            current_subsection = ""
            if current_section not in breakdown:
                breakdown[current_section] = {"sqft": 0.0, "details": [], "sub": {}}
            continue

        # Technicians / Hours
        if "Technicians" in clean:
            m = re.search(r"(\d+)", clean)
            tech_count = m.group(1) if m else "0"
            continue

        if "Estimated Hours" in clean:
            m = re.search(r"(\d+\.?\d*)", clean)
            if m:
                est_hours = float(m.group(1))
            continue

        # Flags: x = unavailable prefix
        is_unavail = clean.lower().startswith(FLAG_UNAVAIL) and len(clean) > 1 and clean[1].isupper()
        name = clean[1:].strip() if is_unavail else clean.strip()

        # Logistics
        if any(k in name for k in LOG_KEYS):
            if is_unavail:
                not_available.append(name)
            else:
                available.append(name)
            continue

        # Equipment (no # prefix = include)
        if any(k in name for k in EQUIP_KEYS):
            equip_used.append(name)
            continue

        # Soil
        if any(k in name for k in SOIL_KEYS):
            if not is_unavail:
                soil_levels.append(name)
            continue

        # Skip 0x0
        if SKIP_DIM in clean:
            audit_log.append({"type": "skip", "label": "Skipped", "detail": f'"{clean}" — zero dims', "value": "—"})
            continue

        # Subsection arrow
        if ARROW in clean:
            current_subsection = clean
            if current_section in breakdown:
                if current_subsection not in breakdown[current_section]["sub"]:
                    breakdown[current_section]["sub"][current_subsection] = {"sqft": 0.0, "steps": 0, "details": []}
            continue

        # Steps
        if "steps" in clean.lower():
            m = re.search(r"(\d+)", clean)
            if m:
                v = int(m.group(1))
                total_steps += v
                if current_section and current_subsection and current_section in breakdown:
                    breakdown[current_section]["sub"].setdefault(
                        current_subsection, {"sqft": 0.0, "steps": 0, "details": []}
                    )["steps"] += v
            continue

        # Dimensions
        dims = re.findall(r"(\d+\.?\d*)x(\d+\.?\d*)", clean)
        if dims:
            sub_total = sum(float(w) * float(l) for w, l in dims)
            is_stair = "Stairwell" in current_section or ARROW in current_subsection

            if is_stair:
                landing_sqft += sub_total
                if current_section in breakdown and current_subsection:
                    breakdown[current_section]["sub"].setdefault(
                        current_subsection, {"sqft": 0.0, "steps": 0, "details": []}
                    )
                    breakdown[current_section]["sub"][current_subsection]["sqft"] += sub_total
                    breakdown[current_section]["sub"][current_subsection]["details"].append(clean)
            else:
                hallway_sqft += sub_total
                if current_section in breakdown:
                    breakdown[current_section]["sqft"] += sub_total
                    breakdown[current_section]["details"].append(clean)

            cost = sub_total * sqft_rate
            section_label = current_section or "?"
            subsec = f" ({current_subsection})" if current_subsection else ""
            audit_log.append({
                "type": "ok",
                "label": f"{section_label}{subsec}",
                "detail": clean,
                "value": f"{sub_total:.1f} ft² → ${cost:.2f}"
            })

    return {
        "sqft_rate": sqft_rate,
        "step_rate": step_rate,
        "hallway_sqft": hallway_sqft,
        "landing_sqft": landing_sqft,
        "total_steps": total_steps,
        "est_hours": est_hours,
        "tech_count": tech_count,
        "available": available,
        "not_available": not_available,
        "equip_used": equip_used,
        "soil_levels": soil_levels,
        "breakdown": breakdown,
        "audit_log": audit_log,
    }

def build_report(d, building_name):
    sqft_rate = d["sqft_rate"]
    step_rate = d["step_rate"]
    inv = ((d["hallway_sqft"] + d["landing_sqft"]) * sqft_rate) + (d["total_steps"] * step_rate)
    h_rate = inv / d["est_hours"] if d["est_hours"] > 0 else 0
    sep = "=" * 40

    res = []
    res.append(sep)
    res.append("TECH SERVICE REPORT")
    res.append(f"Building: {building_name.upper()}")
    res.append(sep)
    res.append("")
    res.append("SERVICE SUMMARY")
    res.append("-" * 24)

    # First 3 lines: totals
    res.append(f"Hallways Area:    {d['hallway_sqft']:.2f} ft2")
    res.append(f"Landings Area:    {d['landing_sqft']:.2f} ft2")
    res.append(f"Total Steps:      {d['total_steps']} units")
    res.append("")

    # Floor breakdown - result only
    breakdown = d["breakdown"]
    for section, data in breakdown.items():
        if "Floor" in section and data["sqft"] > 0:
            res.append(f"{section}:  {data['sqft']:.2f} ft2")

    res.append("")

    # Stairwell breakdown - result only, grouped by stairwell
    for section, data in breakdown.items():
        if "Stairwell" in section:
            sub_lines = []
            for subsec, v in data["sub"].items():
                if v["sqft"] > 0 or v["steps"] > 0:
                    parts = []
                    if v["sqft"] > 0:
                        parts.append(f"{v['sqft']:.2f} ft2")
                    if v["steps"] > 0:
                        parts.append(f"{v['steps']} steps")
                    sub_lines.append(f"{subsec}:  {', '.join(parts)}")
            if sub_lines:
                res.append(f"-- {section} --")
                res.extend(sub_lines)
                res.append("")
    res.append("")
    res.append("LOGISTICS & SITE STATUS")
    res.append("-" * 24)
    res.append(f"Technicians:      {d['tech_count']}")
    res.append(f"Estimated Hours:  {d['est_hours']}")

    if d["available"]:
        res.append(f"Available:        {', '.join(d['available'])}")

    if d["not_available"]:
        clean_na = [n.lstrip("xX").strip() for n in d["not_available"]]
        res.append(f"Not Available:    {', '.join(clean_na)}")

    if d["equip_used"]:
        res.append(f"Equipment Used:   {', '.join(d['equip_used'])}")

    if d["soil_levels"]:
        res.append("")
        res.append("SOIL ASSESSMENT")
        res.append("-" * 24)
        res.append(f"Soil Level:       {', '.join(d['soil_levels'])}")

    res.append("")
    res.append("FINAL SUMMARY")
    res.append("-" * 24)
    res.append(f"Project Total:    ${inv:.2f}")
    res.append(f"Hourly Profit:    ${h_rate:.2f}/hr")
    res.append("")
    res.append(sep)

    return "\n".join(res)

# ─── LAYOUT ───────────────────────────────────────────────────────────────────
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
            "\nBuilding: [Name]",
            "Type: Commercial",
            f"Total Floors: {f_count}\n",
        ]
        for i in range(1, f_count + 1):
            temp.append(f"Floor {i}:")
            temp.append("0x0\n")
        for s in range(1, s_count + 1):
            temp.append(f"Stairwell {s}:")
            temp.append(f"Basement {ARROW} 1")
            temp.append("0 steps")
            temp.append("0x0\n")
            for f in range(1, f_count):
                temp.append(f"{f} {ARROW} {f+1}")
                temp.append("0 steps")
                temp.append("0x0\n")
            temp.append(f"{f_count} {ARROW} Roof")
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
            "\nAdditional Notes:",
        ])
        st.session_state["template_text"] = "\n".join(temp)

    if st.session_state["template_text"]:
        st.text_area("Master Template:", st.session_state["template_text"], height=380)
        copy_button(st.session_state["template_text"], "📋 Copy Template")

with col_paste:
    st.subheader("Step 2: Process Data")
    user_input = st.text_area("Input Area (Paste here)", height=380)

    preview_clicked = st.button("🔍 Preview / Audit", use_container_width=True)

    if preview_clicked and user_input.strip():
        lines = user_input.splitlines()
        st.session_state["audit_data"] = parse_input(lines)
        st.session_state["audit_ready"] = True
        st.session_state["final_report"] = ""

    if st.session_state["audit_ready"]:
        if st.button("📄 Generate Final Report", use_container_width=True):
            d = st.session_state["audit_data"]
            b_match = re.search(r'Building:\s*\[?(.*?)\]?\s*$', user_input, re.MULTILINE)
            building_name = b_match.group(1).strip() if b_match else "BUILDING"
            st.session_state["final_report"] = build_report(d, building_name)
    else:
        st.info("▲ Run Preview / Audit first to enable the report")

# ─── AUDIT PANEL ──────────────────────────────────────────────────────────────
if st.session_state["audit_ready"] and st.session_state["audit_data"]:
    d = st.session_state["audit_data"]
    breakdown = d["breakdown"]
    sqft_rate = d["sqft_rate"]
    step_rate = d["step_rate"]

    st.markdown("---")
    st.subheader("🔍 1. Audit Dashboard (Friendly View)")

    # ── Summary metrics ──
    inv = ((d["hallway_sqft"] + d["landing_sqft"]) * sqft_rate) + (d["total_steps"] * step_rate)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Hallway ft²", f"{d['hallway_sqft']:.2f}")
    m2.metric("Landing ft²", f"{d['landing_sqft']:.2f}")
    m3.metric("Steps", d["total_steps"])
    m4.metric("Est. Total", f"${inv:.2f}")

    # ── Hallways & Floors ──
    st.markdown("#### 🏢 Hallways & Floors")
    floor_found = False
    for section, data in breakdown.items():
        if "Floor" in section and data["sqft"] > 0:
            floor_found = True
            dims_str = " + ".join(data["details"])
            subtotal = data["sqft"] * sqft_rate
            st.write(f"**{section}:** {dims_str} = **{data['sqft']:.2f} ft²** | Subtotal: **${subtotal:.2f}**")
    if not floor_found:
        st.write("*No hallways processed.*")

    # ── Staircases ──
    st.markdown("#### 🪜 Staircases (Landings & Steps)")
    stair_found = False
    for section, data in breakdown.items():
        if "Stairwell" in section:
            for subsec, v in data["sub"].items():
                if v["sqft"] > 0 or v["steps"] > 0:
                    stair_found = True
                    dims_str = " + ".join(v["details"]) if v["details"] else "—"
                    cost = (v["sqft"] * sqft_rate) + (v["steps"] * step_rate)
                    st.write(
                        f"**{section} ({subsec}):** {dims_str} "
                        f"(**{v['sqft']:.2f} ft²**) + **{v['steps']} steps** = **${cost:.2f}**"
                    )
    if not stair_found:
        st.write("*No stairwells processed.*")

    # ── Logistics preview ──
    st.markdown("#### 📦 Logistics & Soil")
    if d["available"]:
        st.markdown("**Available:** " + " · ".join(f"✓ {x}" for x in d["available"]))
    if d["not_available"]:
        clean_na_display = [n.lstrip("xX").strip() for n in d["not_available"]]
        st.markdown("**Not Available:** " + " · ".join(f"✗ {x}" for x in clean_na_display))
    if d["equip_used"]:
        st.markdown("**Equipment:** " + " · ".join(d["equip_used"]))
    if d["soil_levels"]:
        st.markdown("**Soil Level:** " + " · ".join(d["soil_levels"]))

# ─── FINAL REPORT ─────────────────────────────────────────────────────────────
if st.session_state["final_report"]:
    st.markdown("---")
    st.subheader("📋 Final Tech Report")
    st.code(st.session_state["final_report"], language=None)
    copy_button(st.session_state["final_report"], "📋 Copy Report")
