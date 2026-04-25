from __future__ import annotations

import json
import re
import time
from typing import Any

import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"
REQUEST_TIMEOUT = (3, 45)
MAX_RETRIES = 1

RECURSION_MODES = {
    "fast": {
        "label": "Fast",
        "max_depth": 0,
        "max_child_tasks": 0,
        "max_root_tasks": 0,
    },
    "smart": {
        "label": "Smart",
        "max_depth": 2,
        "max_child_tasks": 4,
        "max_root_tasks": 4,
    },
    "deep": {
        "label": "Deep",
        "max_depth": 3,
        "max_child_tasks": 5,
        "max_root_tasks": 6,
    },
}

COMPLEXITY_KEYWORDS = {
    "integrate": 2,
    "integration": 2,
    "platform": 2,
    "dashboard": 1,
    "automation": 2,
    "workflow": 2,
    "multi-agent": 2,
    "recursive": 2,
    "compliance": 3,
    "legal": 2,
    "medical": 3,
    "finance": 2,
    "security": 2,
    "analytics": 1,
    "marketplace": 2,
    "scalable": 2,
    "scale": 2,
    "enterprise": 3,
    "real-time": 2,
    "api": 2,
    "mobile": 1,
    "web": 1,
    "backend": 1,
    "frontend": 1,
    "deployment": 2,
    "team": 1,
    "stakeholder": 2,
    "customer": 1,
    "investor": 1,
}

SPECIALIST_AGENT_PROMPTS = {
    "Medical Agent": (
        "Medical Agent:\n"
        "- Focus on patient impact, safety, workflow practicality, compliance sensitivity, and clinical adoption risk.\n"
        "- Do not invent diagnoses or treatment claims.\n"
    ),
    "Legal Agent": (
        "Legal Agent:\n"
        "- Focus on legal exposure, contracts, liability, privacy, regulatory concerns, and compliance risk.\n"
        "- Provide strategic legal considerations, not formal legal advice.\n"
    ),
    "Tech Agent": (
        "Tech Agent:\n"
        "- Focus on system design, implementation complexity, scalability, security, data flow, and technical feasibility.\n"
    ),
    "Finance Agent": (
        "Finance Agent:\n"
        "- Focus on pricing, cost structure, margins, unit economics, budget discipline, and ROI drivers.\n"
    ),
    "Marketing Agent": (
        "Marketing Agent:\n"
        "- Focus on audience, messaging, channels, acquisition strategy, positioning, and conversion risk.\n"
    ),
    "Education Agent": (
        "Education Agent:\n"
        "- Focus on learning outcomes, pedagogy, accessibility, adoption barriers, and measurable user improvement.\n"
    ),
}

SECTION_ORDER = [
    "tasks",
    "solutions",
    "evaluation",
    "risk",
    "finance",
    "confidence",
    "aggregate",
    "recursive",
    "roadmap",
    "judge",
]

DEFAULT_SECTIONS = {
    "tasks": (
        "- Clarify the objective and define the ideal customer profile.\n"
        "- Research the market, competitors, and demand signals.\n"
        "- Design a practical pilot with measurable success criteria."
    ),
    "solutions": (
        "Task 1:\n"
        "Explanation:\n"
        "- Define the business problem, target user, and expected outcome.\n"
        "Steps:\n"
        "- Interview users\n"
        "- Analyze competitors\n"
        "- Write a focused problem statement\n"
        "Tools:\n"
        "- Surveys, spreadsheets, CRM\n"
        "Example:\n"
        "- A founder narrows a broad AI idea into an internal support copilot for small e-commerce teams.\n\n"
        "Task 2:\n"
        "Explanation:\n"
        "- Validate the concept with a controlled pilot before scaling.\n"
        "Steps:\n"
        "- Build a lightweight MVP\n"
        "- Recruit a few early users\n"
        "- Measure conversion, retention, and cost\n"
        "Tools:\n"
        "- Streamlit, analytics, customer interviews\n"
        "Example:\n"
        "- A team pilots a dashboard with three design partners before full rollout."
    ),
    "evaluation": "- Strengths: Fast validation.\n- Weaknesses: Early assumptions may be incomplete.\n- Improvements: Add user feedback loops and milestone reviews.",
    "risk": "- Business risk: Weak demand.\n- Operational risk: Delivery delays.\n- Market risk: Strong competitors.\n- Mitigation: Pilot early, monitor metrics, and keep costs lean.",
    "finance": "- Initial cost: Low-to-medium MVP budget.\n- Monthly cost: Hosting, model usage, and maintenance.\n- Revenue: Depends on traction and pricing.\n- ROI: Positive if early retention and conversion are strong.",
    "confidence": "- Score: 62\n- Reason: Sensible strategy, but execution quality and market demand will decide results.",
    "aggregate": (
        "- Final recommendation: Validate demand first, then run a lean pilot.\n"
        "- Why: This balances speed, cost control, and learning.\n"
        "- Priority actions: Define target users, launch a pilot, measure results, and improve the plan."
    ),
    "recursive": (
        "- Clarify the target user and business problem.\n"
        "  - Identify the primary customer segment.\n"
        "  - Define the success metric for the first release.\n"
        "- Launch a lean pilot and measure outcomes.\n"
        "  - Build the smallest useful prototype.\n"
        "  - Track adoption, retention, and operating cost."
    ),
    "roadmap": (
        "7-DAY PLAN:\n"
        "- Define the user, problem, and success metric.\n"
        "- Validate demand with early interviews.\n\n"
        "30-DAY PLAN:\n"
        "- Build a lean MVP and onboard pilot users.\n"
        "- Measure engagement, cost, and retention.\n\n"
        "90-DAY PLAN:\n"
        "- Improve the product, tighten positioning, and prepare to scale."
    ),
    "judge": (
        "- Problem: The user needs a practical way to turn an idea into an execution plan.\n"
        "- Solution: A multi-agent system that breaks goals into strategy, risk, finance, and action outputs.\n"
        "- Innovation: Recursive planning plus specialist agents and local AI execution.\n"
        "- Impact: Faster decisions, clearer plans, and stronger business readiness.\n"
        "- Why it wins: It is practical, visual, and demo-friendly."
    ),
}

HEADER_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^\s*tasks\s*:?\s*$", re.IGNORECASE), "tasks"),
    (re.compile(r"^\s*solutions?\s*:?\s*$", re.IGNORECASE), "solutions"),
    (re.compile(r"^\s*evaluation\s*:?\s*$", re.IGNORECASE), "evaluation"),
    (re.compile(r"^\s*risk(?:\s+analysis)?\s*:?\s*$", re.IGNORECASE), "risk"),
    (re.compile(r"^\s*financial(?:\s+estimation|\s+analysis)?\s*:?\s*$", re.IGNORECASE), "finance"),
    (re.compile(r"^\s*confidence(?:\s+score)?\s*:?\s*$", re.IGNORECASE), "confidence"),
    (re.compile(r"^\s*aggregate(?:\s+agent)?(?:\s+summary)?\s*:?\s*$", re.IGNORECASE), "aggregate"),
    (re.compile(r"^\s*recursive(?:\s+agent)?(?:\s+breakdown)?\s*:?\s*$", re.IGNORECASE), "recursive"),
    (re.compile(r"^\s*roadmap(?:\s+agent)?(?:\s+plan)?\s*:?\s*$", re.IGNORECASE), "roadmap"),
    (re.compile(r"^\s*judge(?:\s+summary)?\s*:?\s*$", re.IGNORECASE), "judge"),
]


def normalize_specialist_agents(selected_agents: list[str] | None) -> list[str]:
    if not selected_agents:
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for agent in selected_agents:
        name = normalize_text(agent, "")
        if name in SPECIALIST_AGENT_PROMPTS and name not in seen:
            seen.add(name)
            normalized.append(name)
    return normalized


def build_specialist_block(selected_agents: list[str] | None) -> str:
    agents = normalize_specialist_agents(selected_agents)
    if not agents:
        return "No extra specialist domain agents selected. Keep the analysis general but practical.\n"
    return "\n".join(SPECIALIST_AGENT_PROMPTS[agent] for agent in agents)


def build_prompt(goal: str, selected_agents: list[str] | None = None) -> str:
    clean_goal = normalize_text(goal, "Define a practical business strategy.")
    specialist_block = build_specialist_block(selected_agents)
    planner_guidance = get_planner_task_guidance(clean_goal)
    return f"""
Act like a senior consultant, startup founder, and product strategist.

You are an advanced multi-agent AI system.

Simulate these agents:

1. Planner:
   - Break the goal into as many strategic, real-world tasks as needed
   - Choose the number of tasks based on the complexity of the goal
   - Keep tasks distinct, practical, and execution-focused
   - Complexity guidance: {planner_guidance}

2. Worker:
   For EACH task provide:
   - Clear explanation
   - Step-by-step execution
   - Tools/technologies
   - Real-world example

3. Evaluator:
   - Strengths
   - Weaknesses
   - Improvements

4. Risk Analyst:
   - Business risks
   - Operational risks
   - Market risks
   - Mitigation strategies

5. Financial Analyst:
   - Initial investment (realistic estimate)
   - Monthly cost
   - Revenue potential
   - ROI outlook

6. Confidence Scorer:
   - Score (0-100%)
   - Justification

7. Aggregate Agent:
   - Combine all agent outputs into one final recommendation
   - Resolve contradictions and repeated points
   - Summarize top priorities and next actions

8. Recursive Agent:
   - Review the planner tasks
   - Break only broad tasks into smaller action-oriented subtasks
   - Keep simple tasks unchanged
   - Organize the breakdown as a readable hierarchy

9. Roadmap Agent:
   - Create a practical 7-day, 30-day, and 90-day execution roadmap
   - Focus on realistic milestones and measurable progress

10. Judge Summary Agent:
   - Summarize the project for a hackathon judge
   - Highlight problem, solution, innovation, impact, and why it stands out

Specialist domain agents to apply when relevant:
{specialist_block}

Goal: {clean_goal}

RULES:
- Be detailed and practical
- Avoid generic answers
- Use bullet points
- Think like a real business expert
- Return plain text only

OUTPUT FORMAT (STRICT):

TASKS:
- Task 1
- Task 2
- Add more tasks if the goal requires them

SOLUTIONS:
- For EVERY task listed in TASKS, create a matching solution block.
- If TASKS has 4 items, return Task 1, Task 2, Task 3, and Task 4.
- Do not stop at Task 2.

Task 1:
Explanation:
Steps:
Tools:
Example:

Task 2:
Explanation:
Steps:
Tools:
Example:

Task 3:
Explanation:
Steps:
Tools:
Example:

Task 4:
Explanation:
Steps:
Tools:
Example:

EVALUATION:
- Strengths
- Weaknesses
- Improvements

RISK ANALYSIS:
- Business risk
- Operational risk
- Market risk
- Mitigation

FINANCIAL ESTIMATION:
- Initial cost:
- Monthly cost:
- Revenue:
- ROI:

CONFIDENCE SCORE:
- Score:
- Reason:

AGGREGATE AGENT SUMMARY:
- Final recommendation:
- Why:
- Priority actions:

RECURSIVE AGENT BREAKDOWN:
- Parent task
  - Child subtask
  - Child subtask

ROADMAP AGENT:
7-DAY PLAN:
- Item

30-DAY PLAN:
- Item

90-DAY PLAN:
- Item

JUDGE SUMMARY:
- Problem:
- Solution:
- Innovation:
- Impact:
- Why it wins:
""".strip()


def get_recursion_config(mode: str) -> dict[str, int | str]:
    key = normalize_text(mode, "smart").lower()
    return RECURSION_MODES.get(key, RECURSION_MODES["smart"])


def estimate_complexity_score(text: str) -> int:
    normalized = normalize_text(text, "").lower()
    if not normalized:
        return 1

    score = 1
    word_count = len(normalized.split())
    if word_count >= 10:
        score += 1
    if word_count >= 18:
        score += 1
    if word_count >= 28:
        score += 1

    if "," in normalized:
        score += 1
    if " and " in normalized:
        score += 1

    for keyword, weight in COMPLEXITY_KEYWORDS.items():
        if keyword in normalized:
            score += weight

    return min(score, 10)


def get_planner_task_guidance(goal: str) -> str:
    score = estimate_complexity_score(goal)
    if score <= 3:
        return "Simple goals should usually have 3 to 4 tasks."
    if score <= 6:
        return "Moderately complex goals should usually have 4 to 6 tasks."
    if score <= 8:
        return "Complex goals should usually have 6 to 8 tasks."
    return "Highly complex goals should usually have 8 or more tasks."


def get_complexity_label(text: str) -> str:
    score = estimate_complexity_score(text)
    if score <= 3:
        return "Simple"
    if score <= 6:
        return "Medium"
    if score <= 8:
        return "Complex"
    return "Very Complex"


def get_dynamic_child_limit(task: str, mode: str, depth: int) -> int:
    config = get_recursion_config(mode)
    base_limit = int(config["max_child_tasks"])
    if base_limit == 0:
        return 0

    complexity_score = estimate_complexity_score(task)
    bonus = 0
    if complexity_score >= 5:
        bonus += 1
    if complexity_score >= 8:
        bonus += 1

    depth_penalty = depth
    dynamic_limit = max(2, base_limit + bonus - depth_penalty)
    return dynamic_limit


def get_dynamic_root_limit(tasks_text: str, mode: str) -> int:
    config = get_recursion_config(mode)
    base_limit = int(config["max_root_tasks"])
    if base_limit == 0:
        return 0

    complexity_score = estimate_complexity_score(tasks_text)
    if complexity_score >= 8:
        return base_limit + 2
    if complexity_score >= 5:
        return base_limit + 1
    return base_limit


def build_recursive_prompt(task: str, mode: str) -> str:
    clean_task = normalize_text(task, "Define the next practical action.")
    child_limit = get_dynamic_child_limit(clean_task, mode, depth=0)
    return f"""
You are a recursive planning agent.

Task: {clean_task}

Instructions:
- Decide whether this task is broad enough to split into smaller actionable subtasks.
- If it is already specific, return 1 bullet only with the original task.
- If it is broad, return 2 to {child_limit} subtasks.
- Keep each subtask concrete, short, and execution-focused.
- Return plain text bullets only.
- Do not add headings, explanations, numbering, or commentary.

Example output:
- Validate customer demand with 10 interviews
- Compare 3 competitors on pricing and features
- Define launch metrics for the pilot
""".strip()


def normalize_text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    text = value if isinstance(value, str) else str(value)
    cleaned = text.strip()
    return cleaned if cleaned else fallback


def is_error_text(text: str) -> bool:
    lowered = normalize_text(text, "").lower()
    return lowered.startswith("warning:") or lowered.startswith("error:") or lowered.startswith("request failed:")


def _request_payload(prompt: str, model_name: str | None = None) -> dict[str, Any]:
    resolved_model = normalize_text(model_name, OLLAMA_MODEL)
    return {
        "model": resolved_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": 220,
            "temperature": 0.3,
            "top_p": 0.85,
        },
    }


def call_llm(prompt: str, *, retries: int = MAX_RETRIES, model_name: str | None = None) -> str:
    last_error = "Unknown error"

    for attempt in range(1, retries + 1):
        try:
            response = requests.post(
                OLLAMA_URL,
                json=_request_payload(prompt, model_name=model_name),
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
        except requests.exceptions.Timeout:
            last_error = "request timed out while waiting for Ollama"
        except requests.exceptions.ConnectionError:
            last_error = "could not connect to Ollama at http://localhost:11434"
        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else "unknown"
            last_error = f"Ollama returned HTTP {status_code}"
        except requests.exceptions.RequestException as exc:
            last_error = f"request failed: {exc}"
        else:
            try:
                payload = response.json()
            except json.JSONDecodeError:
                last_error = "Ollama returned invalid JSON"
            else:
                text = normalize_text(payload.get("response"), "")
                if text:
                    return text
                last_error = "Ollama returned an empty response"

        if attempt < retries:
            time.sleep(min(2 ** (attempt - 1), 4))

    return f"Request failed: {last_error}"


def extract_bullets(text: str) -> list[str]:
    bullets: list[str] = []
    for line in normalize_text(text, "").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        cleaned = re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", stripped).strip()
        if cleaned:
            bullets.append(cleaned)
    return bullets


def looks_atomic(task: str) -> bool:
    normalized = normalize_text(task, "").lower()
    if not normalized:
        return True
    short_enough = len(normalized.split()) <= 8
    no_joiners = not re.search(r"\b(and|then|with|across|including|covering)\b", normalized)
    return short_enough and no_joiners


def recursively_decompose_task(task: str, mode: str, depth: int = 0, model_name: str | None = None) -> dict[str, Any]:
    clean_task = normalize_text(task, "")
    node: dict[str, Any] = {"task": clean_task, "children": []}
    config = get_recursion_config(mode)
    child_limit = get_dynamic_child_limit(clean_task, mode, depth)

    if (
        not clean_task
        or config["max_depth"] == 0
        or depth >= int(config["max_depth"])
        or looks_atomic(clean_task)
    ):
        return node

    response = call_llm(build_recursive_prompt(clean_task, mode), retries=1, model_name=model_name)
    if is_error_text(response):
        return node

    children = extract_bullets(response)
    unique_children: list[str] = []
    seen: set[str] = set()
    for child in children:
        lowered = child.lower()
        if lowered == clean_task.lower():
            continue
        if lowered in seen:
            continue
        seen.add(lowered)
        unique_children.append(child)
        if len(unique_children) >= child_limit:
            break

    if len(unique_children) < 2:
        return node

    for child in unique_children:
        node["children"].append(recursively_decompose_task(child, mode, depth + 1, model_name=model_name))

    return node


def build_recursive_tree(tasks_text: str, mode: str, model_name: str | None = None) -> list[dict[str, Any]]:
    config = get_recursion_config(mode)
    dynamic_root_limit = get_dynamic_root_limit(tasks_text, mode)
    root_tasks = extract_bullets(tasks_text)
    if not root_tasks:
        root_tasks = [
            "Define the target customer and problem statement.",
            "Launch a lean pilot and measure outcomes.",
        ]

    if int(config["max_depth"]) == 0:
        return [{"task": task, "children": []} for task in root_tasks]

    tree: list[dict[str, Any]] = []
    for task in root_tasks[:dynamic_root_limit]:
        tree.append(recursively_decompose_task(task, mode, depth=0, model_name=model_name))
    return tree


def format_recursive_tree(tree: list[dict[str, Any]], level: int = 0) -> str:
    lines: list[str] = []
    prefix = "  " * level + "- "
    for node in tree:
        lines.append(f"{prefix}{node['task']}")
        children = node.get("children", [])
        if children:
            lines.append(format_recursive_tree(children, level + 1))
    return "\n".join(line for line in lines if line.strip())


def build_fallback_response(goal: str, reason: str = "") -> str:
    clean_goal = normalize_text(goal, "the business objective")
    extra = f"Fallback reason: {reason}" if reason else "Fallback reason: model response was unavailable or malformed."

    return f"""
TASKS:
- Validate the demand, user need, and success metrics for {clean_goal}.
- Build a small pilot, measure performance, and improve based on feedback.

SOLUTIONS:
Task 1:
Explanation:
- Confirm the exact customer problem, buying trigger, and expected business value before major investment.
Steps:
- Define the target user and use case
- Interview potential users and buyers
- Review competitors and alternatives
- Write success metrics and decision criteria
Tools:
- Customer interviews, online forms, spreadsheets, CRM notes
Example:
- A startup tests whether operations teams will pay for an AI workflow assistant before building a full platform.

Task 2:
Explanation:
- Launch a low-cost pilot to prove demand, usability, and unit economics under real conditions.
Steps:
- Build a minimal prototype
- Run a pilot with a small user group
- Measure adoption, retention, and cost
- Improve the offer based on evidence
Tools:
- Streamlit, analytics, issue tracking, dashboards
Example:
- A founder launches a limited beta with five design partners and refines the workflow before scale.

EVALUATION:
- Strengths: Keeps cost controlled and encourages evidence-based decisions.
- Weaknesses: Pilot findings may not fully represent broader market behavior.
- Improvements: Add clearer go or no-go thresholds, stronger customer segmentation, and a feedback review cadence.

RISK ANALYSIS:
- Business risk: Weak willingness to pay.
- Operational risk: Delays caused by unclear requirements or manual work.
- Market risk: Competitors may already have distribution or brand trust.
- Mitigation: Run short iterations, track measurable outcomes, and limit upfront spend until traction is visible.

FINANCIAL ESTIMATION:
- Initial cost: Prototype, research, and setup budget.
- Monthly cost: Infrastructure, model usage, support, and iteration costs.
- Revenue: Dependent on pricing, retention, and lead quality.
- ROI: Improves when acquisition cost stays low and repeat usage is strong.

CONFIDENCE SCORE:
- Score: 58
- Reason: The approach is practical, but confidence is reduced because the model output required fallback generation.

AGGREGATE AGENT SUMMARY:
- Final recommendation: Start with market validation, then run a small pilot before scaling.
- Why: This lowers risk while preserving learning speed and budget control.
- Priority actions: Define the customer, validate demand, build the MVP, and measure results.

RECURSIVE AGENT BREAKDOWN:
- Validate the demand, user need, and success metrics for {clean_goal}.
  - Define the target user and problem statement.
  - Interview likely buyers and users.
  - Set measurable success criteria for the pilot.
- Build a small pilot, measure performance, and improve based on feedback.
  - Build the smallest useful prototype.
  - Launch with a limited user group.
  - Measure adoption, retention, and cost.

ROADMAP AGENT:
7-DAY PLAN:
- Define the target user, problem, and success metric.
- Interview likely users and validate demand.

30-DAY PLAN:
- Build a focused MVP and launch a small pilot.
- Measure adoption, retention, and operational cost.

90-DAY PLAN:
- Refine the product, improve positioning, and scale the highest-performing workflow.

JUDGE SUMMARY:
- Problem: Turning rough ideas into practical action plans is usually slow and fragmented.
- Solution: A multi-agent system that generates strategy, execution, risk, finance, and recursive breakdowns in one place.
- Innovation: Combines specialist agents, recursive planning, and local model execution.
- Impact: Helps users move faster from idea to validated execution.
- Why it wins: It is practical, visual, and shows real decision intelligence.

{extra}
""".strip()


def normalize_tasks(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    bullet_lines = [line for line in lines if re.match(r"^[-*]\s+", line)]

    if bullet_lines:
        return "\n".join(bullet_lines)

    extracted = []
    for line in lines:
        cleaned = re.sub(r"^\s*(task\s*\d+[:.)-]?\s*|[-*0-9.)]+\s*)", "", line, flags=re.IGNORECASE).strip()
        if cleaned:
            extracted.append(cleaned)

    if not extracted:
        extracted = [
            "Define the target customer, use case, and success metric.",
            "Research the market, constraints, and competition.",
            "Launch a lean pilot, measure results, and refine execution.",
        ]

    return "\n".join(f"- {item}" for item in extracted)


def merge_with_defaults(sections: dict[str, str]) -> dict[str, str]:
    merged: dict[str, str] = {}
    for key in SECTION_ORDER:
        merged[key] = normalize_text(sections.get(key), DEFAULT_SECTIONS[key])

    merged["tasks"] = normalize_tasks(merged["tasks"])
    return merged


def parse_output(text: str) -> dict[str, str]:
    raw = normalize_text(text, "")
    sections = {key: "" for key in SECTION_ORDER}

    if not raw:
        return merge_with_defaults(sections)

    current: str | None = None
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        matched_header = False
        for pattern, key in HEADER_PATTERNS:
            if pattern.match(stripped):
                current = key
                matched_header = True
                break

        if matched_header:
            continue

        if current is None:
            continue

        sections[current] += stripped + "\n"

    if not any(normalize_text(value, "") for value in sections.values()):
        inferred = infer_sections_from_freeform(raw)
        return merge_with_defaults(inferred)

    return merge_with_defaults(sections)


def infer_sections_from_freeform(text: str) -> dict[str, str]:
    inferred = DEFAULT_SECTIONS.copy()
    inferred["solutions"] = normalize_text(text, DEFAULT_SECTIONS["solutions"])

    task_candidates = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^[-*]\s+", stripped):
            task_candidates.append(stripped)
        elif stripped.lower().startswith("task "):
            task_candidates.append(f"- {stripped}")
        if len(task_candidates) >= 2:
            break

    if task_candidates:
        inferred["tasks"] = normalize_tasks("\n".join(task_candidates))

    score_match = re.search(r"(\d{1,3})\s*%?", text)
    if score_match:
        score = max(0, min(100, int(score_match.group(1))))
        inferred["confidence"] = f"- Score: {score}\n- Reason: Extracted from available model output."

    inferred["recursive"] = format_recursive_tree(build_recursive_tree(inferred["tasks"], "smart"))
    return inferred


def super_agent(
    goal: str,
    recursion_mode: str = "smart",
    selected_agents: list[str] | None = None,
    model_name: str | None = None,
) -> str:
    clean_goal = normalize_text(goal, "")
    if not clean_goal:
        return build_fallback_response(
            "the business objective",
            "no goal was provided",
        )

    prompt = build_prompt(clean_goal, selected_agents=selected_agents)
    response_text = call_llm(prompt, model_name=model_name)

    if is_error_text(response_text):
        return build_fallback_response(clean_goal, response_text)

    parsed = parse_output(response_text)
    if not parsed["solutions"]:
        return build_fallback_response(clean_goal, "model returned incomplete sections")

    parsed["recursive"] = format_recursive_tree(
        build_recursive_tree(parsed["tasks"], recursion_mode, model_name=model_name)
    )

    return format_sections(parsed)


def format_sections(sections: dict[str, str]) -> str:
    clean = merge_with_defaults(sections)
    return (
        "TASKS:\n"
        f"{clean['tasks']}\n\n"
        "SOLUTIONS:\n"
        f"{clean['solutions']}\n\n"
        "EVALUATION:\n"
        f"{clean['evaluation']}\n\n"
        "RISK ANALYSIS:\n"
        f"{clean['risk']}\n\n"
        "FINANCIAL ESTIMATION:\n"
        f"{clean['finance']}\n\n"
        "CONFIDENCE SCORE:\n"
        f"{clean['confidence']}\n\n"
        "AGGREGATE AGENT SUMMARY:\n"
        f"{clean['aggregate']}\n\n"
        "RECURSIVE AGENT BREAKDOWN:\n"
        f"{clean['recursive']}\n\n"
        "ROADMAP AGENT:\n"
        f"{clean['roadmap']}\n\n"
        "JUDGE SUMMARY:\n"
        f"{clean['judge']}"
    )
