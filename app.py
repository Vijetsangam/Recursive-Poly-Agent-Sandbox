import streamlit as st
from agents import super_agent, parse_output
from graphviz import Digraph
import time

# Voice + PDF
import speech_recognition as sr
import pyttsx3
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="AI Agent System", layout="wide")

# 🌈 NEON THEME
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    color: #00ffe1;
}
h1, h2, h3 {color: #00ffe1;}

.agent-box {
    padding: 12px;
    border-radius: 12px;
    margin-bottom: 10px;
    box-shadow: 0px 0px 10px #00ffe1;
}
.planner {background-color: rgba(0, 255, 225, 0.1);}
.worker {background-color: rgba(0, 200, 255, 0.1);}
.evaluator {background-color: rgba(255, 150, 0, 0.1);}
</style>
""", unsafe_allow_html=True)

st.title("🚀 Recursive Multi-Agent AI System")
st.caption("⚡ Optimized Multi-Agent | Decision Intelligence System")

# 🎤 Voice Input
def get_voice_input():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 Speak now...")
        audio = r.listen(source)
    try:
        return r.recognize_google(audio)
    except:
        return "Could not understand"

# 🔊 Speak
def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

# 📄 PDF
def create_pdf(text):
    doc = SimpleDocTemplate("output.pdf")
    styles = getSampleStyleSheet()
    content = [Paragraph(text, styles["Normal"])]
    doc.build(content)

# ✍️ Typing animation
def type_writer(text):
    output = ""
    placeholder = st.empty()
    for char in text:
        output += char
        placeholder.markdown(output)
        time.sleep(0.001)

# 🌳 Graph
def build_graph(tasks):
    dot = Digraph()
    dot.node("Goal", "Goal")
    for i, t in enumerate(tasks):
        dot.node(f"T{i}", t)
        dot.edge("Goal", f"T{i}")
    return dot

# 🎯 Decision Engine
def decision_engine(conf_text):
    import re
    try:
        score = int(re.findall(r'\d+', conf_text)[0])
        if score >= 75:
            return "🟢 GO — Strong Opportunity"
        elif score >= 50:
            return "🟡 CAUTION — Moderate Risk"
        else:
            return "🔴 NO-GO — High Risk"
    except:
        return "⚠️ Unable to determine decision"

# INPUT
goal = st.text_input("💡 Enter your goal:")

if st.button("🎤 Voice Input"):
    goal = get_voice_input()
    st.success(f"You said: {goal}")

# RUN
if st.button("Run Agents"):

    start_time = time.time()

    with st.spinner("🤖 Running AI Decision System..."):
        result = super_agent(goal)

    sections = parse_output(result)

    tasks = [t.strip("- ") for t in sections["tasks"].split("\n") if t.strip()]

    st.success("Execution Complete")

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Tasks", len(tasks))
    col2.metric("LLM Calls", "1 ⚡")
    col3.metric("Mode", "Optimized")

    st.markdown("---")
    st.markdown("### 💬 Agent Conversation")

    # Planner
    st.markdown(f"""
    <div class="agent-box planner">
    🧠 Planner:<br>{sections["tasks"]}
    </div>
    """, unsafe_allow_html=True)

    # Worker
    st.markdown('<div class="agent-box worker">🤖 Worker:</div>', unsafe_allow_html=True)
    type_writer(sections["solutions"])

    # Evaluator
    st.markdown(f"""
    <div class="agent-box evaluator">
    🔍 Evaluator:<br>{sections["evaluation"]}
    </div>
    """, unsafe_allow_html=True)

    # Risk
    st.markdown(f"""
    <div class="agent-box evaluator">
    ⚠️ Risk Analysis:<br>{sections["risk"]}
    </div>
    """, unsafe_allow_html=True)

    # Finance
    st.markdown(f"""
    <div class="agent-box worker">
    📊 Financial Estimation:<br>{sections["finance"]}
    </div>
    """, unsafe_allow_html=True)

    # Confidence
    st.markdown(f"""
    <div class="agent-box planner">
    📈 Confidence Score:<br>{sections["confidence"]}
    </div>
    """, unsafe_allow_html=True)

    # 🎯 Decision
    decision = decision_engine(sections["confidence"])
    st.markdown(f"""
    <div class="agent-box planner">
    🎯 Decision: {decision}
    </div>
    """, unsafe_allow_html=True)

    # Speak (optional)
    try:
        speak(sections["solutions"][:120])
    except:
        pass

    st.markdown("---")

    # Graph
    st.markdown("### 🌳 Task Flow Visualization")
    graph = build_graph(tasks)
    st.graphviz_chart(graph)

    end_time = time.time()
    st.success(f"Completed in {round(end_time - start_time, 2)} sec 🚀")

    # PDF
    if st.button("📄 Export to PDF"):
        create_pdf(result)
        st.success("Saved as output.pdf")