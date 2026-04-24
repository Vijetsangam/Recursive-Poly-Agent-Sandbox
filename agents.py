import requests


# 🔥 REAL AI using Ollama (optimized)
def call_llm(prompt):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 350  # 🔥 better detail
                }
            }
        )
        return response.json()["response"]

    except Exception as e:
        return f"⚠️ Error: {str(e)}"


# 🧠 SUPER AGENT
def super_agent(goal):
    prompt = f"""
    Act like a senior consultant from McKinsey, startup founder, and product strategist.

    You are an advanced multi-agent AI system.

    Simulate these agents:

    1. Planner:
       - Break the goal into EXACTLY 2 strategic, real-world tasks

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
       - Score (0–100%)
       - Justification

    Goal: {goal}

    RULES:
    - Be detailed and practical
    - Avoid generic answers
    - Use bullet points
    - Think like a real business expert

    OUTPUT FORMAT (STRICT):

    TASKS:
    - Task 1
    - Task 2

    SOLUTIONS:

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

    EVALUATION:
    - Strengths
    - Weaknesses
    - Improvements

    RISK ANALYSIS:
    - Risk 1
    - Risk 2
    - Mitigation

    FINANCIAL ESTIMATION:
    - Initial cost:
    - Monthly cost:
    - Revenue:
    - ROI:

    CONFIDENCE SCORE:
    - Score:
    - Reason:
    """

    return call_llm(prompt)


# 🔍 ROBUST PARSER
def parse_output(text):
    sections = {
        "tasks": "",
        "solutions": "",
        "evaluation": "",
        "risk": "",
        "finance": "",
        "confidence": ""
    }

    current = None

    for line in text.split("\n"):
        l = line.strip().lower()

        if l.startswith("tasks"):
            current = "tasks"
            continue
        elif l.startswith("solutions"):
            current = "solutions"
            continue
        elif l.startswith("evaluation"):
            current = "evaluation"
            continue
        elif "risk analysis" in l:
            current = "risk"
            continue
        elif "financial estimation" in l:
            current = "finance"
            continue
        elif "confidence score" in l:
            current = "confidence"
            continue

        if current and line.strip():
            sections[current] += line + "\n"

    return sections