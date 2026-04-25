from __future__ import annotations

import html
import re
import time
from pathlib import Path
from typing import Any

import streamlit as st
try:
    import pandas as pd
except Exception:
    pd = None

try:
    from agents import get_complexity_label, parse_output, super_agent
except Exception as exc:  # pragma: no cover - import safety
    get_complexity_label = None
    parse_output = None
    super_agent = None
    AGENTS_IMPORT_ERROR = exc
else:
    AGENTS_IMPORT_ERROR = None

try:
    from graphviz import Digraph
except Exception:
    Digraph = None

try:
    import speech_recognition as sr
except Exception:
    sr = None

try:
    import pyttsx3
except Exception:
    pyttsx3 = None

try:
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate
except Exception:
    getSampleStyleSheet = None
    Paragraph = None
    SimpleDocTemplate = None


st.set_page_config(page_title="AI Agent System", layout="wide")

st.markdown(
    """
<style>
:root {
    --bg-1: #f4ecf8;
    --bg-2: #eadcf4;
    --bg-3: #efdfc7;
    --ink: #2f1846;
    --muted: #72588e;
    --cyan: #7b58c8;
    --mint: #b68a37;
    --gold: #d4a349;
    --coral: #a96ee4;
    --panel: rgba(255, 255, 255, 0.62);
    --border: rgba(123, 88, 200, 0.18);
}
.stApp {
    background:
        radial-gradient(circle at top left, rgba(169, 110, 228, 0.16), transparent 28%),
        radial-gradient(circle at top right, rgba(212, 163, 73, 0.16), transparent 24%),
        linear-gradient(135deg, var(--bg-1), var(--bg-2) 45%, var(--bg-3));
    color: var(--ink);
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(243, 234, 249, 0.96), rgba(234, 221, 246, 0.96));
    border-right: 1px solid rgba(123, 88, 200, 0.14);
}
[data-testid="stSidebar"] .sidebar-role {
    display: block;
    margin-top: 4px;
    margin-bottom: 12px;
    padding: 10px 12px;
    border-radius: 14px;
    background: rgba(255, 255, 255, 0.62);
    border: 1px solid rgba(123, 88, 200, 0.14);
    color: #3a2458;
    font-size: 0.95rem;
    line-height: 1.45;
    box-shadow: 0 8px 18px rgba(97, 67, 145, 0.08);
}
[data-testid="stSidebar"] .sidebar-role-title {
    display: block;
    color: #5c379a;
    font-weight: 700;
    margin-bottom: 4px;
}
h1, h2, h3, h4 { color: var(--ink); }
@keyframes fadeRise {
    from {
        opacity: 0;
        transform: translateY(16px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
@keyframes glowDrift {
    0% { box-shadow: 0 18px 40px rgba(169, 110, 228, 0.10); }
    50% { box-shadow: 0 20px 48px rgba(212, 163, 73, 0.16); }
    100% { box-shadow: 0 18px 40px rgba(169, 110, 228, 0.10); }
}
.hero {
    padding: 20px 24px;
    border: 1px solid var(--border);
    border-radius: 22px;
    margin-bottom: 18px;
    background:
        linear-gradient(135deg, rgba(169, 110, 228, 0.12), rgba(255, 255, 255, 0.86) 35%, rgba(212, 163, 73, 0.15));
    box-shadow: 0 20px 50px rgba(97, 67, 145, 0.12);
    animation: fadeRise 0.7s ease-out, glowDrift 7s ease-in-out infinite;
    backdrop-filter: blur(10px);
}
.hero-kicker {
    color: var(--gold);
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.18rem;
}
.hero-title {
    font-size: 2.3rem;
    font-weight: 700;
    margin-top: 8px;
    margin-bottom: 8px;
}
.hero-subtitle {
    color: var(--muted);
    max-width: 800px;
}
.agent-box, .task-card, .judge-card {
    padding: 14px 16px;
    border-radius: 18px;
    margin-bottom: 12px;
    border: 1px solid var(--border);
    background: var(--panel);
    box-shadow: 0 12px 28px rgba(97, 67, 145, 0.12);
    backdrop-filter: blur(10px);
    animation: fadeRise 0.55s ease-out;
}
.planner { background: linear-gradient(135deg, rgba(169, 110, 228, 0.12), rgba(255, 255, 255, 0.85)); }
.worker { background: linear-gradient(135deg, rgba(123, 88, 200, 0.10), rgba(255, 255, 255, 0.86)); }
.evaluator { background: linear-gradient(135deg, rgba(212, 163, 73, 0.14), rgba(255, 255, 255, 0.86)); }
.task-card-title {
    color: var(--cyan);
    font-weight: 700;
    margin-bottom: 8px;
}
.role-card {
    padding: 16px 16px 14px;
    border-radius: 18px;
    margin-bottom: 12px;
    border: 1px solid var(--border);
    background:
        linear-gradient(160deg, rgba(169, 110, 228, 0.10), rgba(255, 255, 255, 0.88));
    min-height: 140px;
    box-shadow: 0 12px 28px rgba(97, 67, 145, 0.12);
}
.role-card-title {
    color: var(--cyan);
    font-weight: 800;
    font-size: 1rem;
    margin-bottom: 8px;
}
.role-card-body {
    color: var(--ink);
    line-height: 1.5;
    font-size: 0.95rem;
}
.role-card-tag {
    display: inline-block;
    margin-top: 10px;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.78rem;
    color: white;
    background: linear-gradient(135deg, var(--cyan), var(--gold));
    font-weight: 700;
}
.task-card-body {
    color: var(--ink);
    line-height: 1.5;
}
.section-title {
    margin-top: 18px;
    margin-bottom: 10px;
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--cyan);
}
[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.68);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 8px 12px;
    box-shadow: 0 10px 24px rgba(97, 67, 145, 0.10);
    animation: fadeRise 0.65s ease-out;
}
.stButton > button {
    border-radius: 999px;
    border: 1px solid rgba(123, 88, 200, 0.18);
    background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(242,232,252,0.92));
    color: var(--ink);
    box-shadow: 0 8px 18px rgba(123, 88, 200, 0.14);
    transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 12px 24px rgba(123, 88, 200, 0.18);
}
</style>
""",
    unsafe_allow_html=True,
)


APP_DIR = Path(__file__).resolve().parent
PDF_PATH = APP_DIR / "output.pdf"

DEFAULT_SECTIONS = {
    "tasks": "No task breakdown was returned.",
    "solutions": "No solution text was returned.",
    "evaluation": "No evaluation was returned.",
    "risk": "No risk analysis was returned.",
    "finance": "No financial estimate was returned.",
    "confidence": "0",
    "aggregate": "No aggregate summary was returned.",
    "recursive": "No recursive breakdown was returned.",
    "roadmap": "No roadmap was returned.",
    "judge": "No judge summary was returned.",
}

GOAL_TEMPLATES = {
    "Choose a demo template...": "",
    "AI SaaS Launch": "Build an AI SaaS platform for customer support automation with pricing, launch strategy, and risk analysis.",
    "Hospital Assistant": "Create a hospital operations assistant to reduce patient wait times, improve staff coordination, and manage compliance risk.",
    "Legal Copilot": "Launch a legal workflow copilot for contract review, document drafting, and law firm productivity improvement.",
    "EdTech Platform": "Design an AI-powered education platform for adaptive learning, measurable outcomes, and scalable growth.",
    "Marketplace Expansion": "Build a multi-vendor marketplace growth strategy with product roadmap, finance model, and operational scaling plan.",
}

MODEL_OPTIONS = ["llama3", "llama3:8b", "mistral", "phi3"]

AGENT_WORK = {
    "Planner Agent": "Breaks the main goal into top-level strategic tasks.",
    "Worker Agent": "Creates execution guidance, steps, tools, and examples for each task.",
    "Evaluator Agent": "Reviews the plan with strengths, weaknesses, and improvements.",
    "Risk Analyst Agent": "Finds business, operational, and market risks with mitigations.",
    "Financial Analyst Agent": "Estimates costs, revenue potential, and ROI outlook.",
    "Confidence Scorer Agent": "Assigns a confidence score and explains the reasoning.",
    "Aggregate Agent": "Combines all agent outputs into one final recommendation.",
    "Recursive Agent": "Breaks broader tasks into smaller subtasks when needed.",
    "Roadmap Agent": "Builds 7-day, 30-day, and 90-day execution milestones.",
    "Judge Summary Agent": "Packages the project into a short hackathon-ready story.",
}


def init_state() -> None:
    defaults = {
        "goal": "",
        "recursion_mode": "Smart",
        "selected_agents": [],
        "selected_model": "llama3",
        "selected_template": "Choose a demo template...",
        "last_result": "",
        "last_sections": DEFAULT_SECTIONS.copy(),
        "last_tasks": [],
        "last_runtime": None,
        "run_error": "",
        "animate_worker": False,
        "spoken_result": "",
        "run_history": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def normalize_text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        text = value.strip()
        return text if text else fallback
    text = str(value).strip()
    return text if text else fallback


def safe_sections(raw_result: Any) -> dict[str, str]:
    raw_text = normalize_text(raw_result, "")
    parsed: dict[str, Any] = {}

    if parse_output is not None and raw_text:
        try:
            candidate = parse_output(raw_text)
            if isinstance(candidate, dict):
                parsed = candidate
        except Exception:
            parsed = {}

    sections: dict[str, str] = {}
    for key, fallback in DEFAULT_SECTIONS.items():
        sections[key] = normalize_text(parsed.get(key), fallback)

    if sections["tasks"] == DEFAULT_SECTIONS["tasks"] and raw_text:
        sections["tasks"] = raw_text
    if sections["solutions"] == DEFAULT_SECTIONS["solutions"] and raw_text:
        sections["solutions"] = raw_text

    return sections


def extract_tasks(task_text: str) -> list[str]:
    tasks: list[str] = []
    for line in task_text.splitlines():
        cleaned = re.sub(r"^\s*[-*0-9.)]+\s*", "", line).strip()
        if cleaned:
            tasks.append(cleaned)
    if not tasks and task_text.strip():
        tasks = [task_text.strip()]
    return tasks


def count_recursive_tasks(recursive_text: str) -> int:
    count = 0
    for line in recursive_text.splitlines():
        if line.strip().startswith("- "):
            count += 1
    return count


def get_goal_complexity(goal: str) -> str:
    if get_complexity_label is None:
        return "Unknown"
    normalized_goal = normalize_text(goal, "")
    if not normalized_goal:
        return "Unknown"
    try:
        return get_complexity_label(normalized_goal)
    except Exception:
        return "Unknown"


def extract_score(text: str) -> int:
    match = re.search(r"(\d{1,3})", normalize_text(text, "0"))
    if not match:
        return 0
    return max(0, min(100, int(match.group(1))))


def extract_money_values(finance_text: str) -> dict[str, int]:
    values = {"initial": 0, "monthly": 0, "revenue": 0}
    patterns = {
        "initial": r"initial\s+cost\s*:\s*[^0-9]*(\d[\d,]*)",
        "monthly": r"monthly\s+cost\s*:\s*[^0-9]*(\d[\d,]*)",
        "revenue": r"revenue\s*:\s*[^0-9]*(\d[\d,]*)",
    }
    lowered = finance_text.lower()
    for key, pattern in patterns.items():
        match = re.search(pattern, lowered)
        if match:
            values[key] = int(match.group(1).replace(",", ""))
    return values


def extract_risk_count(risk_text: str) -> int:
    return len([line for line in risk_text.splitlines() if line.strip().startswith("-")])


def split_solution_cards(solution_text: str) -> list[tuple[str, str]]:
    text = normalize_text(solution_text, "")
    if not text:
        return []
    chunks = re.split(r"(?=Task\s+\d+\s*:)", text, flags=re.IGNORECASE)
    cards: list[tuple[str, str]] = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        first_line, _, remainder = chunk.partition("\n")
        title = first_line.strip(": ").strip()
        body = remainder.strip() if remainder.strip() else chunk
        cards.append((title or "Task", body))
    return cards


def get_voice_input() -> str:
    if sr is None:
        raise RuntimeError("SpeechRecognition is not installed.")

    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            st.info("Listening for voice input...")
            recognizer.adjust_for_ambient_noise(source, duration=0.6)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=20)
    except Exception as exc:
        raise RuntimeError(f"Microphone is unavailable: {exc}") from exc

    try:
        return normalize_text(recognizer.recognize_google(audio), "")
    except sr.UnknownValueError as exc:
        raise RuntimeError("Speech was detected, but it could not be understood.") from exc
    except sr.RequestError as exc:
        raise RuntimeError(f"Speech service is unavailable: {exc}") from exc


def speak(text: str) -> None:
    if pyttsx3 is None:
        raise RuntimeError("pyttsx3 is not installed.")

    engine = pyttsx3.init()
    try:
        engine.say(text[:300])
        engine.runAndWait()
    finally:
        stop = getattr(engine, "stop", None)
        if callable(stop):
            stop()


def create_pdf(text: str) -> Path:
    if not all([SimpleDocTemplate, Paragraph, getSampleStyleSheet]):
        raise RuntimeError("ReportLab is not installed.")

    safe_text = html.escape(normalize_text(text, "No content available for export."))
    doc = SimpleDocTemplate(str(PDF_PATH))
    styles = getSampleStyleSheet()
    content = [Paragraph(safe_text.replace("\n", "<br/>"), styles["Normal"])]
    doc.build(content)
    return PDF_PATH


def type_writer(text: str) -> None:
    render_task_cards(text)


def build_graph(tasks: list[str]):
    if Digraph is None:
        return None
    dot = Digraph()
    dot.node("Goal", "Goal")
    for index, task in enumerate(tasks):
        dot.node(f"T{index}", task)
        dot.edge("Goal", f"T{index}")
    return dot


def decision_engine(conf_text: str) -> str:
    numbers = re.findall(r"\d+", normalize_text(conf_text, "0"))
    if not numbers:
        return "Unable to determine decision"

    score = max(0, min(100, int(numbers[0])))
    if score >= 75:
        return "GO - Strong Opportunity"
    if score >= 50:
        return "CAUTION - Moderate Risk"
    return "NO-GO - High Risk"


def render_box(title: str, body: str, css_class: str) -> None:
    safe_body = html.escape(normalize_text(body, "No data available.")).replace("\n", "<br>")
    st.markdown(
        f"""
        <div class="agent-box {css_class}">
        <strong>{html.escape(title)}</strong><br>{safe_body}
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_agent_work_summary(selected_agents: list[str]) -> str:
    lines = [f"- {name}: {description}" for name, description in AGENT_WORK.items()]
    if selected_agents:
        lines.extend(
            f"- {agent}: Active domain specialist perspective applied during analysis."
            for agent in selected_agents
        )
    else:
        lines.append("- Specialist Agents: General mode only, with no extra domain specialists selected.")
    return "\n".join(lines)


def render_task_cards(solution_text: str) -> None:
    cards = split_solution_cards(solution_text)
    if not cards:
        render_box("Worker Output", solution_text, "worker")
        return
    columns = st.columns(2)
    for index, (title, body) in enumerate(cards):
        safe_body = html.escape(normalize_text(body, "No details available.")).replace("\n", "<br>")
        columns[index % 2].markdown(
            f"""
            <div class="task-card">
            <div class="task-card-title">{html.escape(title)}</div>
            <div class="task-card-body">{safe_body}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_charts(confidence_text: str, risk_text: str, finance_text: str) -> None:
    confidence_score = extract_score(confidence_text)
    risk_count = extract_risk_count(risk_text)
    finance = extract_money_values(finance_text)
    if pd is None:
        st.info("Install pandas to render charts.")
        return

    overview_df = pd.DataFrame(
        {
            "Metric": ["Confidence", "Risk Items"],
            "Value": [confidence_score, min(risk_count * 20, 100)],
        }
    ).set_index("Metric")
    finance_df = pd.DataFrame(
        {
            "Metric": ["Initial Cost", "Monthly Cost", "Revenue"],
            "Amount": [finance["initial"], finance["monthly"], finance["revenue"]],
        }
    ).set_index("Metric")

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.caption("Confidence and Risk")
        st.bar_chart(overview_df)
    with chart_col2:
        st.caption("Financial Snapshot")
        st.bar_chart(finance_df)


def render_complexity_badge(label: str) -> None:
    badge_colors = {
        "Simple": "#7fbf7f",
        "Medium": "#d4a349",
        "Complex": "#9b6ce0",
        "Very Complex": "#7a45d1",
        "Unknown": "#8d90a5",
    }
    color = badge_colors.get(label, "#8d90a5")
    st.markdown(
        f"""
        <div style="display:inline-block;padding:8px 14px;border-radius:999px;
        background:{color};color:white;font-weight:700;margin-top:26px;">
        Complexity: {html.escape(label)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_executive_summary(sections: dict[str, str], decision: str, runtime: float | None) -> None:
    runtime_text = f"{runtime} sec" if runtime is not None else "N/A"
    st.markdown("### Executive Summary")
    st.markdown(
        f"""
        <div class="judge-card">
        <strong>Decision:</strong> {html.escape(decision)}<br><br>
        <strong>Aggregate Recommendation:</strong><br>{html.escape(normalize_text(sections["aggregate"], "No recommendation available.")).replace(chr(10), "<br>")}<br><br>
        <strong>Judge Summary:</strong><br>{html.escape(normalize_text(sections["judge"], "No judge summary was returned.")).replace(chr(10), "<br>")}<br><br>
        <strong>Runtime:</strong> {html.escape(runtime_text)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_agent_timeline(tasks_count: int, recursive_count: int, selected_agents: list[str]) -> None:
    specialist_text = ", ".join(selected_agents) if selected_agents else "General mode"
    steps = [
        f"Planner created {tasks_count} top-level tasks from the goal.",
        "Worker converted each task into execution-ready steps and examples.",
        "Evaluator, Risk, and Finance agents reviewed feasibility, exposure, and cost.",
        f"Recursive agent expanded the plan into {recursive_count} task nodes where complexity required it.",
        f"Aggregate and Judge agents merged everything into one final story using specialists: {specialist_text}.",
    ]
    st.markdown("### Agent Timeline")
    for index, item in enumerate(steps, start=1):
        st.markdown(
            f"""
            <div class="agent-box planner">
            <strong>Step {index}</strong><br>{html.escape(item)}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_run_history() -> None:
    history = st.session_state.run_history
    if not history:
        return
    st.markdown("### Recent Runs")
    for item in history[:5]:
        st.markdown(
            f"""
            <div class="agent-box worker">
            <strong>{html.escape(item["goal"])}</strong><br>
            Model: {html.escape(item["model"])} | Mode: {html.escape(item["mode"])} | Complexity: {html.escape(item["complexity"])}<br>
            Tasks: {item["tasks"]} | Recursive Tasks: {item["recursive_tasks"]} | Decision: {html.escape(item["decision"])}
            </div>
            """,
            unsafe_allow_html=True,
        )


def can_run_agents() -> bool:
    return super_agent is not None and parse_output is not None


def run_agents(goal: str, recursion_mode: str, selected_agents: list[str], selected_model: str) -> None:
    st.session_state.run_error = ""
    start_time = time.time()

    try:
        if not can_run_agents():
            raise RuntimeError(f"Agent imports failed: {AGENTS_IMPORT_ERROR}")

        with st.spinner("Running AI decision system..."):
            result = super_agent(
                goal,
                recursion_mode=recursion_mode.lower(),
                selected_agents=selected_agents,
                model_name=selected_model,
            )
    except Exception as exc:
        st.session_state.last_result = ""
        st.session_state.last_sections = DEFAULT_SECTIONS.copy()
        st.session_state.last_tasks = []
        st.session_state.last_runtime = None
        st.session_state.run_error = str(exc)
        return

    sections = safe_sections(result)
    tasks = extract_tasks(sections["tasks"])

    st.session_state.last_result = normalize_text(result, "")
    st.session_state.last_sections = sections
    st.session_state.last_tasks = tasks
    st.session_state.last_runtime = round(time.time() - start_time, 2)
    st.session_state.animate_worker = True
    st.session_state.spoken_result = ""
    recursive_task_count = count_recursive_tasks(sections["recursive"])
    decision = decision_engine(sections["confidence"])
    complexity = get_goal_complexity(goal)
    st.session_state.run_history = [
        {
            "goal": goal[:80],
            "model": selected_model,
            "mode": recursion_mode,
            "complexity": complexity,
            "tasks": len(tasks),
            "recursive_tasks": recursive_task_count,
            "decision": decision,
        }
    ] + st.session_state.run_history[:4]


init_state()

with st.sidebar:
    st.markdown("### Agent Roles")
    for name, description in AGENT_WORK.items():
        st.markdown(
            f"""
            <div class="sidebar-role">
                <span class="sidebar-role-title">{html.escape(name)}</span>
                {html.escape(description)}
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("---")
    st.markdown("### Demo Strategy")
    st.caption("Use Fast mode for live demos, Smart for balanced quality, and Deep when you want to show the recursive planner in action.")

st.markdown(
    """
    <div class="hero">
        <div class="hero-kicker">Executive Strategy Intelligence</div>
        <div class="hero-title">Recursive Multi-Agent Strategy Studio</div>
        <div class="hero-subtitle">
            Turn one idea into strategic tasks, execution plans, risk analysis, finance estimates,
            recursive breakdowns, a roadmap, and a judge-ready project summary.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if not can_run_agents():
    st.error(
        "The app could not import `super_agent` and `parse_output` from `agents`. "
        "Add or fix that module before running the workflow."
    )
    if AGENTS_IMPORT_ERROR:
        st.code(str(AGENTS_IMPORT_ERROR))

top_col1, top_col2, top_col3 = st.columns([1.5, 1, 1])
with top_col1:
    st.selectbox("Demo Template", options=list(GOAL_TEMPLATES.keys()), key="selected_template")
with top_col2:
    render_complexity_badge(get_goal_complexity(st.session_state.goal))
with top_col3:
    st.selectbox("Model", options=MODEL_OPTIONS, key="selected_model")

if (
    st.session_state.selected_template != "Choose a demo template..."
    and GOAL_TEMPLATES[st.session_state.selected_template] != st.session_state.goal
):
    st.session_state.goal = GOAL_TEMPLATES[st.session_state.selected_template]

st.text_input("Enter your goal:", key="goal")
st.segmented_control(
    "Recursion Mode",
    options=["Fast", "Smart", "Deep"],
    key="recursion_mode",
    help="Fast skips recursive breakdown, Smart uses limited recursion, and Deep explores more aggressively.",
)
st.multiselect(
    "Specialist Agents",
    options=[
        "Medical Agent",
        "Legal Agent",
        "Tech Agent",
        "Finance Agent",
        "Marketing Agent",
        "Education Agent",
    ],
    key="selected_agents",
    help="Choose one or more specialist agents to tailor the analysis to a domain.",
)

voice_col, run_col, export_col = st.columns([1, 1, 1])

with voice_col:
    if st.button("Voice Input", use_container_width=True):
        try:
            spoken_text = get_voice_input()
            if spoken_text:
                st.session_state.goal = spoken_text
                st.success(f"Voice captured: {spoken_text}")
            else:
                st.warning("No voice input was captured.")
        except Exception as exc:
            st.warning(str(exc))

with run_col:
    if st.button("Run Agents", type="primary", use_container_width=True):
        goal = normalize_text(st.session_state.goal, "")
        if not goal:
            st.warning("Enter a goal before running the agents.")
        else:
            run_agents(
                goal,
                st.session_state.recursion_mode,
                st.session_state.selected_agents,
                st.session_state.selected_model,
            )

with export_col:
    if st.button("Export to PDF", use_container_width=True):
        result_text = normalize_text(st.session_state.last_result, "")
        if not result_text:
            st.warning("Run the agents before exporting a PDF.")
        else:
            try:
                output_path = create_pdf(result_text)
                st.success(f"PDF saved to {output_path}")
            except Exception as exc:
                st.warning(str(exc))


if st.session_state.run_error:
    st.error(f"Execution failed: {st.session_state.run_error}")


sections = st.session_state.last_sections
tasks = st.session_state.last_tasks
recursive_task_count = count_recursive_tasks(sections["recursive"])

if st.session_state.last_result:
    st.success("Execution complete")
    decision_text = decision_engine(sections["confidence"])
    render_executive_summary(sections, decision_text, st.session_state.last_runtime)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tasks", len(tasks))
    col2.metric("Recursive Tasks", recursive_task_count)
    col3.metric("Model", st.session_state.selected_model)
    col4.metric("Mode", st.session_state.recursion_mode)

    st.markdown("---")
    st.markdown("### Agent Conversation")
    selected_agents = st.session_state.selected_agents
    if selected_agents:
        st.caption(f"Specialist agents active: {', '.join(selected_agents)}")
    else:
        st.caption("Specialist agents active: General mode")

    render_box("Agent Work Summary", build_agent_work_summary(selected_agents), "planner")

    render_box("Planner", sections["tasks"], "planner")

    st.markdown('<div class="section-title">Task Cards</div>', unsafe_allow_html=True)
    if st.session_state.animate_worker:
        type_writer(sections["solutions"])
        st.session_state.animate_worker = False
    else:
        render_task_cards(sections["solutions"])

    render_box("Evaluator", sections["evaluation"], "evaluator")
    render_box("Risk Analysis", sections["risk"], "evaluator")
    render_box("Financial Estimation", sections["finance"], "worker")
    render_box("Confidence Score", sections["confidence"], "planner")
    render_box("Aggregate Agent Summary", sections["aggregate"], "planner")
    st.caption(f"Planner created {len(tasks)} top-level tasks. Recursive breakdown shows {recursive_task_count} total tasks and subtasks.")
    render_box("Recursive Agent Breakdown", sections["recursive"], "worker")
    render_box("Roadmap Agent", sections["roadmap"], "planner")
    st.markdown('<div class="section-title">Judge Summary</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="judge-card">{html.escape(normalize_text(sections["judge"], "No judge summary was returned.")).replace(chr(10), "<br>")}</div>',
        unsafe_allow_html=True,
    )
    render_box("Decision", decision_text, "planner")

    if st.session_state.spoken_result != st.session_state.last_result:
        try:
            speak(sections["solutions"])
            st.session_state.spoken_result = st.session_state.last_result
        except Exception:
            pass

    st.markdown("---")
    st.markdown("### Charts Dashboard")
    render_charts(sections["confidence"], sections["risk"], sections["finance"])

    st.markdown("---")
    render_agent_timeline(len(tasks), recursive_task_count, selected_agents)

    st.markdown("---")
    st.markdown("### Task Flow Visualization")
    graph = build_graph(tasks)
    if graph is not None and tasks:
        st.graphviz_chart(graph)
    elif not tasks:
        st.info("No task graph to render.")
    else:
        st.info("Graphviz is not installed, so the task graph is unavailable.")

    runtime = st.session_state.last_runtime
    if runtime is not None:
        st.success(f"Completed in {runtime} sec")
    render_run_history()
else:
    st.info("Provide a goal, then run the agents to see the workflow.")
