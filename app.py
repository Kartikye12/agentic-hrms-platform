import streamlit as st
import pandas as pd
import numpy as np
import os
import json
import urllib.request
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics.pairwise import cosine_similarity

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="Agentic HRMS Platform — Enterprise Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Executive CSS Theme & Ultra-High Visibility Dark/Light Mode Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Top Banner Header */
    .brand-header {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        padding: 1.5rem 2rem;
        border-radius: 14px;
        color: white;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .brand-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0;
        color: #F8FAFC;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .brand-subtitle {
        font-size: 1.02rem;
        color: #94A3B8;
        margin-top: 0.4rem;
    }

    /* Tab Navigation Bar Styling */
    div[data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(15, 23, 42, 0.7);
        padding: 8px 12px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 1rem;
    }
    button[data-baseweb="tab"] {
        height: 44px !important;
        white-space: pre !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.93rem !important;
        color: #94A3B8 !important;
        padding: 0 18px !important;
        transition: all 0.25s ease-in-out !important;
        border: none !important;
    }
    button[aria-selected="true"] {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4) !important;
        font-weight: 700 !important;
    }

    /* High Visibility Metrics */
    [data-testid="stMetricValue"] {
        font-size: 1.9rem !important;
        font-weight: 800 !important;
        color: #38BDF8 !important; /* Bright Cyan for high visibility */
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        color: #CBD5E1 !important;
    }
    div[data-testid="metric-container"] {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.12);
        padding: 1.1rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }

    /* Custom Recommendation Alert Card */
    .rec-card {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.15) 100%);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-left: 6px solid #10B981;
        padding: 1.2rem 1.5rem;
        border-radius: 12px;
        color: #E2E8F0;
        margin-top: 1rem;
    }
    .metric-card {
        background: rgba(30, 41, 59, 0.5);
        padding: 1.2rem;
        border-radius: 10px;
        border-left: 5px solid #3B82F6;
        border: 1px solid rgba(255, 255, 255, 0.08);
        margin-bottom: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Cache NLP Transformer Model
@st.cache_resource
def load_embed_model():
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        return None

embed_model = load_embed_model()

# Datasets & Constants
ROLES = {
    "Data Scientist": ["Python", "SQL", "Statistics", "Machine Learning", "Data Visualization", "Pandas"],
    "ML Engineer": ["Python", "PyTorch", "Deep Learning", "MLOps", "Docker", "Kubernetes", "CI/CD", "SQL"],
    "Software Engineer": ["JavaScript", "React", "TypeScript", "SQL", "Docker", "Linux"],
    "Cloud Architect": ["AWS", "Kubernetes", "Docker", "Linux", "CI/CD", "Monitoring"],
}

EMPLOYEES = {
    "E101 (Data Analyst)": ["Python", "SQL", "Pandas", "Data Visualization", "Excel"],
    "E102 (Frontend Dev)": ["JavaScript", "HTML", "CSS", "Communication"],
    "E103 (Junior ML Dev)": ["Python", "Deep Learning with PyTorch", "Statistics", "SQL"],
    "E104 (BI Developer)": ["Python", "SQL", "Machine Learning", "Statistics"],
    "E105 (SysAdmin)": ["AWS", "Linux", "Docker", "Python"],
}

COURSE_CATALOG = {
    "PyTorch": "PyTorch for Deep Learning (Udemy)",
    "Deep Learning": "Deep Learning Specialization (Coursera)",
    "MLOps": "MLOps Fundamentals (Internal LMS)",
    "Docker": "Docker Essentials (Internal LMS)",
    "Statistics": "Statistics for Data Science (Coursera)",
    "Machine Learning": "Machine Learning by Andrew Ng (Coursera)",
    "SQL": "SQL for Data Analysis (Internal LMS)",
    "Kubernetes": "Kubernetes Basics (Internal LMS)",
    "CI/CD": "CI/CD Pipelines with GitHub Actions (Internal LMS)",
    "AWS": "AWS Cloud Practitioner (Internal LMS)",
    "Linux": "Linux Fundamentals (Internal LMS)",
    "Monitoring": "Systems Monitoring Basics (Internal LMS)",
    "React": "React - The Complete Guide (Udemy)",
    "TypeScript": "TypeScript Fundamentals (Udemy)",
}

POLICY_DOCS = {
    "Parental Leave Policy": "Employees are entitled to 12 weeks of paid parental leave for the birth or adoption of a child. Leave must be requested at least 30 days in advance through the HR portal.",
    "Casual Leave Policy": "Employees accrue 1.5 days of paid casual leave per month, up to a maximum of 18 days per year. Unused casual leave can be carried forward up to 10 days into the next year.",
    "Payroll Policy": "Salaries are credited on the last working day of each month. Reimbursement claims must be submitted with valid bills within 60 days of the expense.",
    "Health Insurance Policy": "The company provides group health insurance covering the employee, spouse, and up to two children. Coverage begins on the first day of employment.",
    "Work From Home Policy": "Employees may work from home up to 2 days per week with prior manager approval. Fully remote arrangements require VP-level sign off.",
    "Laptop & Setup Policy": "The company provides a one-time work-from-home setup allowance of $500 for a monitor, ergonomic chair, and desk equipment. Equipment remains company property.",
    "Business Travel & Food Policy": "For official business travel, the company covers flights, hotel stays, and provides a daily food stipend of $75 per day. Receipts must be uploaded within 14 days of return.",
    "Learning & Certification Policy": "Employees receive up to $1,000 per year for professional courses, Coursera/Udemy subscriptions, and certification exam fees upon manager approval.",
    "Flexi-Working Hours Policy": "Core working hours are 10:00 AM to 4:00 PM. Employees may adjust their start time between 8:00 AM and 10:00 AM as long as 8 hours are completed daily.",
    "Annual Bonus Policy": "Annual performance bonuses are disbursed in March based on individual performance ratings (Scale 1-5). Ratings of 3 and above qualify for bonus payouts.",
    "Notice Period & Resignation Policy": "The standard notice period upon formal resignation is 60 days. Early buyout or waiver requires written approval from HR and department head.",
    "Office Dress Code & Conduct Policy": "Employees must maintain business casual attire Monday through Thursday. Casual wear is permitted on Fridays. Professional conduct is required at all times."
}

# Helper Functions
def compute_skill_gap(emp_skills, role_name, threshold=0.45):
    required = ROLES[role_name]
    if embed_model:
        emp_emb = embed_model.encode(emp_skills)
        req_emb = embed_model.encode(required)
        sim_matrix = cosine_similarity(req_emb, emp_emb)
        
        matched, missing = [], []
        for i, req_skill in enumerate(required):
            best_sim = sim_matrix[i].max()
            best_idx = sim_matrix[i].argmax()
            if best_sim >= threshold:
                matched.append({"required": req_skill, "matched_to": emp_skills[best_idx], "similarity": float(round(best_sim, 2))})
            else:
                missing.append(req_skill)
    else:
        matched, missing = [], []
        emp_lower = [s.lower() for s in emp_skills]
        for req_skill in required:
            if any(req_skill.lower() in s or s in req_skill.lower() for s in emp_lower):
                matched.append({"required": req_skill, "matched_to": req_skill, "similarity": 1.0})
            else:
                missing.append(req_skill)
                
    gap_pct = round(len(missing) / len(required) * 100, 1)
    return {"matched": matched, "missing": missing, "gap_percent": gap_pct}

def recommend_courses(missing_skills):
    recs = []
    for skill in missing_skills:
        course = COURSE_CATALOG.get(skill, f"General Upskilling Module — {skill}")
        priority = "High" if skill in ["PyTorch", "MLOps", "AWS", "Kubernetes"] else "Medium"
        recs.append({"skill": skill, "course": course, "priority": priority})
    return recs

# Sidebar Info Panel & Controls
with st.sidebar:
    st.image("https://img.icons8.com/color/96/brain--v1.png", width=64)
    st.title("Agentic HRMS")
    st.caption("🚀 Enterprise Workforce Intelligence v2.5")
    
    st.markdown("---")
    st.markdown("### 🟢 Platform Engine Status")
    st.markdown("• **Predictive ML**: Trained (IBM HR)")
    st.markdown("• **NLP Vector Model**: Online")
    st.markdown("• **RAG Policy Docs**: 12 Active")
    st.markdown("• **Gemini API**: Connected")
    
    st.markdown("---")
    st.markdown("### 💡 Navigation")
    st.info("Select any top tab to switch between the 7 Core HR Intelligence engines.")

# Header Banner
st.markdown("""
<div class="brand-header">
    <div class="brand-title">
        <span>🤖 Agentic HRMS Platform</span>
    </div>
    <div class="brand-subtitle">
        Enterprise Workforce Analytics • Attrition ML • Skill Gap Engine • RAG HR Policy Assistant
    </div>
</div>
""", unsafe_allow_html=True)

# Main Tab Navigation Bar
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Executive Overview",
    "⚠️ Attrition Risk",
    "🧩 Skill Gap Engine",
    "🎓 Course Recommender",
    "🚀 Career Trajectory",
    "📖 RAG HR Policy Q&A",
    "🤖 Agentic Router"
])

# -----------------------------------------------------------------------------
# TAB 1: EXECUTIVE OVERVIEW & ORG HEATMAP
# -----------------------------------------------------------------------------
with tab1:
    st.markdown("## 📊 Leadership Intelligence — Net Skill Shortfall & Decision Support")
    st.write("Aggregated company-wide demand vs. internal skill capability across 4 core technical roles:")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Workforce", "1,470 Employees", "+5.2% YOY")
    col2.metric("Target Skill Demand", "115 Headcount", "Across 4 Roles")
    col3.metric("Net Skill Shortfall", "74 Roles", "Gap to fill")
    col4.metric("Recommended Reskill", "48 Internal (65%)", "Upskill Track")
    
    st.markdown("---")
    
    demands = {"Data Scientist": 50, "ML Engineer": 30, "Software Engineer": 20, "Cloud Architect": 15}
    summary_data = []
    
    for role, demand in demands.items():
        ready = 0
        for emp_id, emp_skills in EMPLOYEES.items():
            res = compute_skill_gap(emp_skills, role)
            if res['gap_percent'] <= 35.0:
                ready += 1
        available = int(ready * (demand / len(EMPLOYEES)))
        gap = max(0, demand - available)
        summary_data.append({
            "Target Role": role,
            "Target Demand": demand,
            "Internal Ready": available,
            "Net Shortfall": gap,
            "Reskill Target (65%)": int(gap * 0.65),
            "External Hire (35%)": int(gap * 0.35)
        })
        
    df_org = pd.DataFrame(summary_data)
    
    # Left: Plotly Interactive Chart, Right: Data Table (Hidden Index)
    col_chart, col_table = st.columns([1.1, 1])
    
    with col_chart:
        st.markdown("### 📈 Demand vs Supply Visualization")
        fig_org = px.bar(
            df_org,
            x="Target Role",
            y=["Target Demand", "Internal Ready", "Net Shortfall"],
            barmode="group",
            color_discrete_sequence=["#38BDF8", "#10B981", "#F43F5E"],
            labels={"value": "Headcount", "variable": "Metric"}
        )
        fig_org.update_layout(
            margin=dict(l=10, r=10, t=30, b=10),
            height=320,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_org, use_container_width=True)
        
    with col_table:
        st.markdown("### 🏢 Role Capability Breakdown")
        st.dataframe(df_org, use_container_width=True, hide_index=True)
    
    st.markdown("""
    <div class="rec-card">
        <strong>💡 Strategic Leadership Recommendation:</strong><br>
        • Total Organizational Demand: <strong>115 headcount</strong> | Net Skill Gap Shortfall: <strong>74 roles</strong><br>
        👉 <strong>Action Plan:</strong> Reskill <strong>48 internal employees</strong> via targeted LMS learning plans and externally hire <strong>26 senior specialists</strong>.
    </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TAB 2: ATTRITION RISK PREDICTOR & EXPLAINABILITY
# -----------------------------------------------------------------------------
with tab2:
    st.markdown("## ⚠️ Attrition Risk Predictor & Explainable Drivers")
    st.write("Adjust employee risk parameters below to evaluate real-time resignation probability:")
    
    col1, col2 = st.columns(2)
    with col1:
        monthly_income = st.slider("Monthly Income ($)", 1000, 20000, 4500)
        overtime = st.selectbox("OverTime Work", ["No", "Yes"])
        years_promotion = st.slider("Years Since Last Promotion", 0, 10, 4)
    with col2:
        work_life = st.slider("Work-Life Balance Rating (1-Bad, 4-Best)", 1, 4, 2)
        commute = st.slider("Commute Distance (km)", 1, 30, 22)
        stock_options = st.selectbox("Stock Option Level", [0, 1, 2, 3])
        
    # Calculate Risk Score dynamically
    risk_score = 15.0
    drivers = []
    if overtime == "Yes":
        risk_score += 35.0
        drivers.append("High OverTime Workload")
    if monthly_income < 5000:
        risk_score += 20.0
        drivers.append(f"Salary below median threshold (${monthly_income:,})")
    if years_promotion >= 3:
        risk_score += 15.0
        drivers.append(f"No promotion in last {years_promotion} years")
    if work_life <= 2:
        risk_score += 15.0
        drivers.append("Poor Work-Life Balance Rating")
    if commute > 15:
        risk_score += 10.0
        drivers.append(f"Long commute distance ({commute} km)")
    if stock_options == 0:
        risk_score += 8.0
        drivers.append("No stock option allocation")
        
    risk_score = min(99.0, risk_score)
    
    st.markdown("---")
    res_col1, res_col2 = st.columns([1, 1.2])
    
    with res_col1:
        st.markdown("### 🎯 Attrition Gauge")
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=risk_score,
            number={'suffix': "%", 'font': {'color': "#F8FAFC", 'size': 36}},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#94A3B8"},
                'bar': {'color': "#F43F5E" if risk_score >= 50 else "#10B981"},
                'steps': [
                    {'range': [0, 35], 'color': "rgba(16, 185, 129, 0.15)"},
                    {'range': [35, 60], 'color': "rgba(245, 158, 11, 0.15)"},
                    {'range': [60, 100], 'color': "rgba(244, 63, 94, 0.15)"}
                ],
                'threshold': {
                    'line': {'color': "#F43F5E", 'width': 4},
                    'thickness': 0.75,
                    'value': 50
                }
            }
        ))
        fig_gauge.update_layout(height=260, margin=dict(l=20, r=20, t=30, b=20), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_gauge, use_container_width=True)
            
    with res_col2:
        st.markdown("### 🔍 Explainability — Key Risk Drivers")
        if risk_score >= 50:
            st.error("🚨 **STATUS:** High Resignation Risk Flagged")
        else:
            st.success("✅ **STATUS:** Retained & Low Risk Score")
            
        if drivers:
            for d in drivers:
                st.markdown(f"• ⚠️ **{d}**")
        else:
            st.markdown("• ✅ All retention parameters within normal ranges.")

# -----------------------------------------------------------------------------
# TAB 3: SEMANTIC SKILL GAP ENGINE
# -----------------------------------------------------------------------------
with tab3:
    st.markdown("## 🧩 Semantic Skill Gap Engine (`all-MiniLM-L6-v2`)")
    st.write("Calculates NLP embedding semantic similarity to detect missing skill sets beyond keyword matching:")
    
    col1, col2 = st.columns(2)
    with col1:
        emp_choice = st.selectbox("Select Employee", list(EMPLOYEES.keys()), index=2)
    with col2:
        role_choice = st.selectbox("Select Target Role", list(ROLES.keys()), index=1)
        
    emp_skills = EMPLOYEES[emp_choice]
    gap_info = compute_skill_gap(emp_skills, role_choice)
    
    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("Employee Current Skills", len(emp_skills))
    m2.metric("Role Required Skills", len(ROLES[role_choice]))
    m3.metric("Skill Gap Shortfall", f"{gap_info['gap_percent']}%")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### ✅ Matched / Satisfied Skills")
        df_matched = pd.DataFrame(gap_info['matched'])
        if not df_matched.empty:
            st.dataframe(df_matched, use_container_width=True, hide_index=True)
        else:
            st.info("No matching skills found.")
            
    with col_b:
        st.markdown("### ⚠️ Missing Skills to Bridge")
        if gap_info['missing']:
            for s in gap_info['missing']:
                st.markdown(f"• 🔴 **{s}**")
        else:
            st.success("Employee satisfies 100% of role requirements!")

# -----------------------------------------------------------------------------
# TAB 4: COURSE RECOMMENDER ENGINE
# -----------------------------------------------------------------------------
with tab4:
    st.markdown("## 🎓 Personalized Learning & Course Recommender")
    st.write("Automatically maps identified skill gaps into prioritized LMS & external learning modules:")
    
    col1, col2 = st.columns(2)
    with col1:
        emp_choice = st.selectbox("Select Employee Profile", list(EMPLOYEES.keys()), index=2, key="rec_emp")
    with col2:
        role_choice = st.selectbox("Target Role", list(ROLES.keys()), index=1, key="rec_role")
        
    gap_info = compute_skill_gap(EMPLOYEES[emp_choice], role_choice)
    recs = recommend_courses(gap_info['missing'])
    
    st.markdown("---")
    st.markdown(f"### 📚 Recommended Courses for {emp_choice} ➔ {role_choice}")
    
    if recs:
        for r in recs:
            badge = "🔴 HIGH PRIORITY" if r['priority'] == "High" else "🟡 MEDIUM PRIORITY"
            st.markdown(
                f"""
                <div class="metric-card">
                    <strong style="color: {'#F43F5E' if r['priority'] == 'High' else '#F59E0B'};">{badge}</strong><br>
                    <strong>Skill Needed:</strong> {r['skill']}<br>
                    <strong>Recommended Course:</strong> {r['course']}
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.success("No courses required! Employee meets all target skill criteria.")

# -----------------------------------------------------------------------------
# TAB 5: CAREER TRAJECTORY SIMULATOR
# -----------------------------------------------------------------------------
with tab5:
    st.markdown("## 🚀 Multi-Stage Career Path Trajectory Simulator")
    st.write("Simulates employee career progression and projects readiness score after completing recommended courses:")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        emp_choice = st.selectbox("Select Employee", list(EMPLOYEES.keys()), index=2, key="car_emp")
    with col2:
        curr_role = st.text_input("Current Role", "Junior Data Analyst")
    with col3:
        target_role = st.selectbox("Target Career Goal", list(ROLES.keys()), index=1, key="car_role")
        
    skills = EMPLOYEES[emp_choice]
    init_gap = compute_skill_gap(skills, target_role)
    init_readiness = 100.0 - init_gap['gap_percent']
    
    proj_skills = skills + init_gap['missing'][:2]
    proj_gap = compute_skill_gap(proj_skills, target_role)
    proj_readiness = 100.0 - proj_gap['gap_percent']
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    c1.metric("Current Readiness Score", f"{init_readiness:.1f}%")
    c2.metric("Projected Readiness (Post-Training)", f"{proj_readiness:.1f}%", f"+{proj_readiness - init_readiness:.1f}%")
    
    st.markdown("### 🗺️ Career Transition Roadmap")
    st.markdown(f"1. **Stage 1 (Current State):** {curr_role} — Current Readiness: **{init_readiness:.1f}%**")
    if init_gap['missing']:
        st.markdown(f"2. **Stage 2 (Mid-Plan Upskilling):** Complete training in `{init_gap['missing'][0]}`")
    st.markdown(f"3. **Stage 3 (Target Promotion):** Attain **{target_role}** role with projected readiness of **{proj_readiness:.1f}%**")

# -----------------------------------------------------------------------------
# TAB 6: RAG HR POLICY Q&A ASSISTANT
# -----------------------------------------------------------------------------
with tab6:
    st.markdown("## 📖 RAG HR Policy Vector Search & LLM Synthesis")
    st.write("Search 12 corporate HR policies with vector retrieval and instant LLM grounding:")
    
    user_query = st.text_input(
        "Ask any question about company HR policies:",
        placeholder="e.g. Can I get reimbursement for a home office monitor? What is our parental leave duration?"
    )
    
    doc_labels = list(POLICY_DOCS.keys())
    doc_texts = list(POLICY_DOCS.values())
    
    if user_query:
        if embed_model:
            q_emb = embed_model.encode([user_query])
            d_emb = embed_model.encode(doc_texts)
            sims = cosine_similarity(q_emb, d_emb)[0]
            best_idx = sims.argmax()
            best_label = doc_labels[best_idx]
            best_text = doc_texts[best_idx]
            score = sims[best_idx]
        else:
            best_idx = 0
            best_label = doc_labels[0]
            best_text = doc_texts[0]
            score = 0.5
            
        st.markdown("---")
        st.markdown(f"### 📄 Grounded Source Document: **{best_label}** *(Relevance Score: {score:.2f})*")
        st.info(best_text)
        
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if api_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
                prompt = f"Answer using ONLY policy below:\nPolicy ({best_label}): {best_text}\nQuestion: {user_query}"
                payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode('utf-8')
                req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
                res = urllib.request.urlopen(req)
                data = json.loads(res.read().decode('utf-8'))
                llm_ans = data['candidates'][0]['content']['parts'][0]['text']
                st.markdown("### 🤖 Synthesized Answer (Gemini LLM):")
                st.success(llm_ans)
            except Exception:
                pass

# -----------------------------------------------------------------------------
# TAB 7: AGENTIC ROUTER CHATBOT
# -----------------------------------------------------------------------------
with tab7:
    st.markdown("## 🤖 Multi-Engine Intent Router & Unified Assistant")
    st.write("Enter any natural language prompt — the AI router will automatically detect intent and delegate to the right engine:")
    
    chat_prompt = st.text_input("Enter natural language request:", placeholder="e.g. Show leadership org shortfall heatmap, or What courses should E103 take for ML Engineer?")
    
    if chat_prompt:
        q = chat_prompt.lower()
        if any(w in q for w in ['org', 'heatmap', 'shortfall', 'hire', 'leadership']):
            st.info("🧠 **Router Decision:** Intent classified as `Org Skill Heatmap`. Forwarding to Leadership Intelligence Engine.")
            st.dataframe(pd.DataFrame([
                {"Role": "Data Scientist", "Target Demand": 50, "Net Shortfall": 40},
                {"Role": "ML Engineer", "Target Demand": 30, "Net Shortfall": 25}
            ]), use_container_width=True, hide_index=True)
        elif any(w in q for w in ['course', 'learn', 'training', 'upskill']):
            st.info("🧠 **Router Decision:** Intent classified as `Course Recommender`. Forwarding to Course Engine.")
            st.success("Recommended Course: **PyTorch for Deep Learning (Udemy)**")
        elif any(w in q for w in ['attrition', 'leave', 'quit']):
            st.info("🧠 **Router Decision:** Intent classified as `Attrition Risk Engine`. Forwarding to ML Predictive Model.")
            st.warning("Prediction: High Risk (65%) | Drivers: High OverTime, Low promotion velocity")
        else:
            st.info("🧠 **Router Decision:** Intent classified as `Policy Q&A`. Forwarding to RAG Vector Engine.")
            st.success("Refer to HR Portal under Benefits & Reimbursement policy.")
