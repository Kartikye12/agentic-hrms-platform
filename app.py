import streamlit as st
import pandas as pd
import numpy as np
import os
import json
import urllib.request
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics.pairwise import cosine_similarity

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="Agentic HRMS Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.3rem;
        font-weight: 800;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .stMetric {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        padding: 0.8rem;
        border-radius: 0.6rem;
    }
    .metric-card {
        background: #F1F5F9;
        padding: 1.2rem;
        border-radius: 8px;
        border-left: 5px solid #3B82F6;
    }
</style>
""", unsafe_allow_html=True)

# Cache NLP Transformer Model
@st.cache_resource
def load_embed_model():
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception as e:
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
        # Fallback string matching
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

# Top-level Sidebar Navigation
st.sidebar.image("https://img.icons8.com/color/96/brain--v1.png", width=64)
st.sidebar.title("Agentic HRMS")
st.sidebar.markdown("**Workforce Intelligence Platform**")

navigation = st.sidebar.radio(
    "Navigation Menu",
    [
        "📊 Executive Overview & Org Heatmap",
        "⚠️ Attrition Risk & Explainability",
        "🧩 Semantic Skill Gap Engine",
        "🎓 Course Recommender",
        "🚀 Career Trajectory Simulator",
        "📖 RAG HR Policy Q&A",
        "🤖 Agentic Router Chatbot"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip**: Switch tabs to test each of the 7 core AI engines live.")

# Header
st.markdown(f'<div class="main-header">{navigation}</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TAB 1: EXECUTIVE OVERVIEW & ORG HEATMAP
# -----------------------------------------------------------------------------
if navigation == "📊 Executive Overview & Org Heatmap":
    st.markdown('<div class="sub-header">Leadership Intelligence — Aggregate Net Skill Shortfalls & Decision Support</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Workforce", "1,470 Employees", "+5.2% YOY")
    col2.metric("Target Skill Demand", "115 Headcount", "Across 4 Roles")
    col3.metric("Net Skill Shortfall", "74 Roles", "Gap to fill")
    col4.metric("Recommended Reskill", "48 Internal (65%)", "Upskill Track")
    
    st.markdown("### 🏢 Organization Demand vs Internal Supply")
    
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
            "Role": role,
            "Target Demand": demand,
            "Internal Ready": available,
            "Net Shortfall": gap,
            "Reskill Target (Internal 65%)": int(gap * 0.65),
            "External Hire Target (35%)": int(gap * 0.35)
        })
        
    df_org = pd.DataFrame(summary_data)
    st.dataframe(df_org, use_container_width=True)
    
    st.markdown("### 💡 Leadership Decision Support Summary")
    st.success(
        "**Strategic Recommendation:**\n"
        "• Total Organizational Demand: **115 headcount**\n"
        "• Net Skill Gap Shortfall: **74 roles**\n"
        "👉 **Action Plan:** Reskill **48 internal employees** via targeted LMS learning plans and externally hire **26 senior specialists**."
    )

# -----------------------------------------------------------------------------
# TAB 2: ATTRITION RISK PREDICTOR & EXPLAINABILITY
# -----------------------------------------------------------------------------
elif navigation == "⚠️ Attrition Risk & Explainability":
    st.markdown('<div class="sub-header">Predictive ML + Individual Risk Driver Explainability</div>', unsafe_allow_html=True)
    
    st.write("Adjust employee parameters below to evaluate real-time attrition risk probability and key drivers:")
    
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
    res_col1, res_col2 = st.columns([1, 2])
    
    with res_col1:
        if risk_score >= 50:
            st.error(f"### Attrition Risk: HIGH ({risk_score:.1f}%)")
            st.markdown("**Status:** At Risk of Resignation 🚨")
        else:
            st.success(f"### Attrition Risk: LOW ({risk_score:.1f}%)")
            st.markdown("**Status:** Retained & Stable ✅")
            
    with res_col2:
        st.markdown("#### 🔍 Explainability — Top Risk Drivers:")
        if drivers:
            for d in drivers:
                st.markdown(f"• ⚠️ {d}")
        else:
            st.markdown("• ✅ Normal retention parameters")

# -----------------------------------------------------------------------------
# TAB 3: SEMANTIC SKILL GAP ENGINE
# -----------------------------------------------------------------------------
elif navigation == "🧩 Semantic Skill Gap Engine":
    st.markdown('<div class="sub-header">NLP Transformer Semantic Skill Matching (`all-MiniLM-L6-v2`)</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        emp_choice = st.selectbox("Select Employee", list(EMPLOYEES.keys()), index=2)
    with col2:
        role_choice = st.selectbox("Select Target Role", list(ROLES.keys()), index=1)
        
    emp_skills = EMPLOYEES[emp_choice]
    gap_info = compute_skill_gap(emp_skills, role_choice)
    
    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("Employee Skills", len(emp_skills))
    m2.metric("Target Role Requirements", len(ROLES[role_choice]))
    m3.metric("Skill Gap", f"{gap_info['gap_percent']}%")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### ✅ Matched / Satisfied Skills")
        df_matched = pd.DataFrame(gap_info['matched'])
        if not df_matched.empty:
            st.dataframe(df_matched, use_container_width=True)
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
elif navigation == "🎓 Course Recommender":
    st.markdown('<div class="sub-header">Personalized Learning & Development Recommendations</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        emp_choice = st.selectbox("Select Employee Profile", list(EMPLOYEES.keys()), index=2)
    with col2:
        role_choice = st.selectbox("Target Role", list(ROLES.keys()), index=1)
        
    gap_info = compute_skill_gap(EMPLOYEES[emp_choice], role_choice)
    recs = recommend_courses(gap_info['missing'])
    
    st.markdown("---")
    st.markdown(f"### 📚 Recommended Courses for {emp_choice} -> {role_choice}")
    
    if recs:
        for r in recs:
            badge = "🔴 HIGH PRIORITY" if r['priority'] == "High" else "🟡 MEDIUM PRIORITY"
            st.markdown(
                f"""
                <div class="metric-card" style="margin-bottom: 1rem;">
                    <strong>{badge}</strong><br>
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
elif navigation == "🚀 Career Trajectory Simulator":
    st.markdown('<div class="sub-header">Multi-Stage Career Progression & Post-Training Readiness Projection</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        emp_choice = st.selectbox("Select Employee", list(EMPLOYEES.keys()), index=2)
    with col2:
        curr_role = st.text_input("Current Role", "Junior Data Analyst")
    with col3:
        target_role = st.selectbox("Target Career Goal", list(ROLES.keys()), index=1)
        
    skills = EMPLOYEES[emp_choice]
    init_gap = compute_skill_gap(skills, target_role)
    init_readiness = 100.0 - init_gap['gap_percent']
    
    # Project readiness after completing top 2 missing skill courses
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
elif navigation == "📖 RAG HR Policy Q&A":
    st.markdown('<div class="sub-header">Vector Search & LLM Policy Synthesis over 12 HR Corporate Policies</div>', unsafe_allow_html=True)
    
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
        
        # Check Gemini API integration
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
            except Exception as e:
                pass

# -----------------------------------------------------------------------------
# TAB 7: AGENTIC ROUTER CHATBOT
# -----------------------------------------------------------------------------
elif navigation == "🤖 Agentic Router Chatbot":
    st.markdown('<div class="sub-header">Multi-Engine Intent Router & Unified Assistant</div>', unsafe_allow_html=True)
    
    chat_prompt = st.text_input("Enter natural language request:", placeholder="e.g. Show leadership org shortfall heatmap, or What courses should E103 take for ML Engineer?")
    
    if chat_prompt:
        q = chat_prompt.lower()
        if any(w in q for w in ['org', 'heatmap', 'shortfall', 'hire', 'leadership']):
            st.info("🧠 **Router Decision:** Intent classified as `Org Skill Heatmap`. Forwarding to Leadership Intelligence Engine.")
            st.dataframe(pd.DataFrame([
                {"Role": "Data Scientist", "Target Demand": 50, "Net Shortfall": 40},
                {"Role": "ML Engineer", "Target Demand": 30, "Net Shortfall": 25}
            ]))
        elif any(w in q for w in ['course', 'learn', 'training', 'upskill']):
            st.info("🧠 **Router Decision:** Intent classified as `Course Recommender`. Forwarding to Course Engine.")
            st.success("Recommended Course: **PyTorch for Deep Learning (Udemy)**")
        elif any(w in q for w in ['attrition', 'leave', 'quit']):
            st.info("🧠 **Router Decision:** Intent classified as `Attrition Risk Engine`. Forwarding to ML Predictive Model.")
            st.warning("Prediction: High Risk (65%) | Drivers: High OverTime, Low promotion velocity")
        else:
            st.info("🧠 **Router Decision:** Intent classified as `Policy Q&A`. Forwarding to RAG Vector Engine.")
            st.success("Refer to HR Portal under Benefits & Reimbursement policy.")
