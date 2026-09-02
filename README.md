# Agentic HRMS Platform — Enterprise Workforce Intelligence

An AI-powered Human Resource Management System (HRMS) designed to deliver enterprise-level workforce insights, attrition risk analytics, skill gap identification, course recommendations, career trajectory mapping, and HR policy Q&A.

---

## 🌟 Key Features

1. **📊 Executive Overview & Org Heatmap**: Leadership decision support for Hire vs. Reskill headcount planning.
2. **⚠️ Attrition Risk & Explainability**: Predictive ML model with per-employee risk driver breakdown.
3. **🧩 Semantic Skill Gap Engine**: NLP Transformer similarity (`all-MiniLM-L6-v2`) comparing employee skills vs role demands.
4. **🎓 Course Recommender Engine**: Personalized learning path suggestions mapped to skill gaps.
5. **🚀 Career Trajectory Simulator**: Multi-stage career progression with post-training readiness projections.
6. **📖 RAG HR Policy Q&A**: Vector search over corporate policies with optional Gemini LLM synthesis.
7. **🤖 Agentic Router Chatbot**: Unified natural language intent classifier and engine orchestrator.

---

## 📁 Repository Structure

```
ST_2_Project_AI/
├── app.py                            # Streamlit Web Application (Deploy ready)
├── index.html                        # HTML/JS Web Dashboard
├── styles.css                        # Dashboard styling
├── app.js                            # Interactive JS logic
├── Agentic_HRMS_Mini_Project.ipynb  # Jupyter Notebook prototype
├── Agentic_HRMS_Platform.pptx        # Executive Presentation Deck
├── requirements.txt                  # Python dependencies for Streamlit
├── README.md                         # Documentation
└── .gitignore                        # Git ignore configurations
```

---

## 🚀 Running the Streamlit App Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Launch the Streamlit dashboard:
   ```bash
   streamlit run app.py
   ```
3. Open your browser at `http://localhost:8501`.

---

## 🌐 Deploying to Streamlit Community Cloud (Free)

1. Push this repository to your GitHub account (`git push -u origin main`).
2. Go to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
3. Click **"New App"**.
4. Select your repository `ST_2_Project_AI`, set Main file path to `app.py`.
5. Click **"Deploy!"** — your app will be live on the web in under 2 minutes.

---

## 📄 License
Created for demonstration and project evaluation purposes.
