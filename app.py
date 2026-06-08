import streamlit as st
import pandas as pd
import json
import csv
import random

# --- CONFIGURATION ---
USE_TEAMS = False  # Set to True to enable team groupings, abbreviations, and colors

# --- Page Configuration ---
st.set_page_config(page_title="NBA 2K Roster Database", layout="wide")

# Lock and resize sidebar via CSS
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        min-width: 350px !important;
        max-width: 350px !important;
        width: 350px !important;
    }
    [data-testid="stSidebarResizer"] {
        display: none;
    }
    @media (min-width: 768px) {
        [data-testid="stDataFrameContainer"], [data-testid="stDataFrame"] {
            width: auto !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)

NBA_TEAMS = [
    {"abbr": "ATL", "color": "#E03A3E"}, {"abbr": "BOS", "color": "#007A33"},
    {"abbr": "BKN", "color": "#000000"}, {"abbr": "CHA", "color": "#00788C"},
    {"abbr": "CHI", "color": "#CE1141"}, {"abbr": "CLE", "color": "#860038"},
    {"abbr": "DAL", "color": "#00538C"}, {"abbr": "DEN", "color": "#0E2240"},
    {"abbr": "DET", "color": "#1D42BA"}, {"abbr": "GSW", "color": "#1D428A"},
    {"abbr": "HOU", "color": "#D31145"}, {"abbr": "IND", "color": "#FDBB30"},
    {"abbr": "LAC", "color": "#C8102E"}, {"abbr": "LAL", "color": "#552583"},
    {"abbr": "MEM", "color": "#5D76A9"}, {"abbr": "MIA", "color": "#98002E"},
    {"abbr": "MIL", "color": "#00471B"}, {"abbr": "MIN", "color": "#0C2340"},
    {"abbr": "NOH", "color": "#85714D"}, {"abbr": "NYK", "color": "#F58426"},
    {"abbr": "OKC", "color": "#007AC1"}, {"abbr": "ORL", "color": "#0077C0"},
    {"abbr": "PHI", "color": "#006BB6"}, {"abbr": "PHO", "color": "#E56020"},
    {"abbr": "POR", "color": "#E03A3F"}, {"abbr": "SAC", "color": "#5A2D81"},
    {"abbr": "SAS", "color": "#C4CED4"}, {"abbr": "TOR", "color": "#CE1142"},
    {"abbr": "UTA", "color": "#002B5C"}, {"abbr": "WAS", "color": "#E31837"}
]

team_color_map = {team["abbr"]: team["color"] for team in NBA_TEAMS}
pos_order = ['PG', 'SG', 'SF', 'PF', 'C', 'N/A']
grade_order = ['F', 'D-', 'D', 'D+', 'C-', 'C', 'C+', 'B-', 'B', 'B+', 'A-', 'A', 'A+']
grade_cols = ["IN", "MID", "3PT", "POST D", "PER D", "PLAY", "REB", "ATHL", "IQ", "POT"]

def get_text_color(hex_color):
    h = hex_color.lstrip('#')
    r, g, b = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    luminance = (0.299 * r + 0.587 * g + 0.114 * b)
    return 'black' if luminance > 128 else 'white'

@st.cache_data
def load_data():
    csv_data = []
    try:
        with open('player_names.csv', mode='r', encoding='utf-8-sig') as f:
            csv_data = list(csv.DictReader(f))
    except FileNotFoundError:
        pass

    def get_match_data(j_name, j_age, j_rating, j_pos):
        if not csv_data: return j_name, j_pos
        
        parts = j_name.split('.', 1) if '.' in j_name else j_name.split()
        first_init = (parts[0].strip()[0].lower() if parts[0] else "") if '.' in j_name else (parts[0][0].lower() if parts else "")
        last_name = parts[1].strip() if '.' in j_name else (parts[-1] if parts else j_name)
        clean_last_name = last_name.replace('.', '').lower()
        
        matches = []
        for c in csv_data:
            c_name = c.get('Name', '')
            if not c_name: continue
            
            if c_name[0].lower() == first_init and c_name.replace('.', '').lower().endswith(clean_last_name):
                try:
                    if abs(int(c.get('Age', 0)) - int(j_age)) <= 1 and abs(int(c.get('Ovr', 0)) - int(j_rating)) <= 1:
                        matches.append(c)
                except ValueError: pass
                    
        if not matches: return j_name, j_pos
        if len(matches) == 1: return matches[0]['Name'], matches[0].get('Pos', j_pos)
            
        pos_matches = [m for m in matches if j_pos in m.get('Pos', '').split('/')]
        chosen = random.choice(pos_matches) if pos_matches else random.choice(matches)
        return chosen['Name'], chosen.get('Pos', j_pos)

    players = []
    try:
        with open('grades.json', mode='r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        return pd.DataFrame()

    team_idx, prev_rating = 0, 999
    
    for row in data:
        j_name, j_age, j_rating, j_pos = row.get("name", ""), str(row.get("age", "")), str(row.get("rating", "")), row.get("pos", "")
        
        full_name, csv_pos = get_match_data(j_name, j_age, j_rating, j_pos)
        pri_pos, sec_pos = csv_pos.split('/', 1) if '/' in csv_pos else (csv_pos, "N/A")
        
        player_data = {
            "NAME": full_name,
        }
        
        # Insert TEAM conditionally right after NAME
        if USE_TEAMS:
            current_rating = int(j_rating) if j_rating.isdigit() else 0
            if current_rating > prev_rating:
                team_idx = min(team_idx + 1, len(NBA_TEAMS) - 1)
            prev_rating, curr_team = current_rating, NBA_TEAMS[team_idx]
            player_data["TEAM"] = curr_team["abbr"]

        player_data.update({
            "PRI": pri_pos.strip(), "SEC": sec_pos.strip(),
            "AGE": int(j_age) if j_age.isdigit() else 0,
            "RATING": int(j_rating) if j_rating.isdigit() else 0,
            "IN": row.get("inside", ""), "MID": row.get("mid", ""), "3PT": row.get("three_pt", ""),
            "POST D": row.get("post_d", ""), "PER D": row.get("per_d", ""), "PLAY": row.get("play", ""),
            "REB": row.get("reb", ""), "ATHL": row.get("athl", ""), "IQ": row.get("iq", ""), "POT": row.get("pot", "")
        })
        
        players.append(player_data)
    
    df = pd.DataFrame(players)
    
    # Sort by overall rating if not grouping by team
    if not USE_TEAMS and not df.empty:
        df = df.sort_values(by="RATING", ascending=False).reset_index(drop=True)
    
    # Apply Categorical sorting for positions and grades
    if not df.empty:
        df['PRI'] = pd.Categorical(df['PRI'], categories=[p for p in pos_order if p != 'N/A'], ordered=True)
        df['SEC'] = pd.Categorical(df['SEC'], categories=pos_order, ordered=True)
        
        for col in grade_cols:
            df[col] = pd.Categorical(df[col], categories=grade_order, ordered=True)
            
    return df

# --- UI Setup ---
st.title("NBA 2K MORDVA Roster Database")

df = load_data()
if df.empty:
    st.error("No players loaded. Ensure `grades.json` and `player_names.csv` exist in the root folder.")
    st.stop()

# --- Sidebar ---
st.sidebar.header("Controls & Filters")

if USE_TEAMS:
    use_colors = st.sidebar.checkbox("Use Team Colors", value=True)
else:
    use_colors = False

search_terms = st.sidebar.text_input("Search Name:").lower().split()

st.sidebar.subheader("Positions")
cols = st.sidebar.columns(5)
selected_pos = [p for i, p in enumerate(["PG", "SG", "SF", "PF", "C"]) if cols[i].checkbox(p, value=True)]

st.sidebar.subheader("Advanced Filters")
if "filters" not in st.session_state:
    st.session_state.filters = []

c1, c2, c3 = st.sidebar.columns([3, 2, 3])
f_col = c1.selectbox("Stat", ["AGE", "RATING"] + grade_cols)
f_op = c2.selectbox("Op", [">=", "<=", "=="])
f_val = c3.text_input("Val").strip().upper()

if st.sidebar.button("Add Filter") and f_val:
    st.session_state.filters.append({"col": f_col, "op": f_op, "val": f_val})

if st.sidebar.button("Clear Filters"):
    st.session_state.filters.clear()

for i, f in enumerate(st.session_state.filters):
    st.sidebar.caption(f"✓ {f['col']} {f['op']} {f['val']}")

# --- Filtering Logic ---
filtered_df = df.copy()

if search_terms:
    mask = filtered_df['NAME'].str.lower().apply(lambda x: all(t in x for t in search_terms))
    filtered_df = filtered_df[mask]

if selected_pos:
    mask = filtered_df['PRI'].isin(selected_pos) | filtered_df['SEC'].isin(selected_pos)
    filtered_df = filtered_df[mask]

for f in st.session_state.filters:
    col, op, val = f['col'], f['op'], f['val']
    if col in ["AGE", "RATING"]:
        try:
            val_num = int(val)
            if op == ">=": filtered_df = filtered_df[filtered_df[col] >= val_num]
            elif op == "<=": filtered_df = filtered_df[filtered_df[col] <= val_num]
            elif op == "==": filtered_df = filtered_df[filtered_df[col] == val_num]
        except ValueError: pass
    else:
        if val in grade_order:
            if op == ">=": filtered_df = filtered_df[filtered_df[col] >= val]
            elif op == "<=": filtered_df = filtered_df[filtered_df[col] <= val]
            elif op == "==": filtered_df = filtered_df[filtered_df[col] == val]

# --- Display Dataframe ---
def apply_team_colors(row):
    bg_color = team_color_map.get(row.get('TEAM', ''), '#ffffff')
    text_color = get_text_color(bg_color)
    return [f'background-color: {bg_color}; color: {text_color}'] * len(row)

if use_colors and USE_TEAMS:
    st.dataframe(filtered_df.style.apply(apply_team_colors, axis=1), use_container_width=True, hide_index=True, height=700)
else:
    st.dataframe(filtered_df, use_container_width=True, hide_index=True, height=700)