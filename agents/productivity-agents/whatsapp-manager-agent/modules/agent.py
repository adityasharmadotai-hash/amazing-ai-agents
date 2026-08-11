"""
agent.py — the Gemini conversation brain.

A single `respond()` call takes the business knowledge, the qualifying questions,
what we've already collected, and the recent chat, then returns a structured
action the orchestrator can execute: the reply text, any new qualification data
it extracted, and whether to hand off to a human.

Design mirrors instagram-ad-manager/modules/agent.py: a small `_call` wrapper,
JSON-mode responses, and a defensive `_safe_json`.
"""

from __future__ import annotations

import json
import re
import time

from . import config

log = config.get_logger("wamanager.agent")
MODEL_NAME = config.GEMINI_MODEL


class AgentError(RuntimeError):
    pass


def _api_key() -> str:
    return config.get_secret("GEMINI_API_KEY") or config.get_secret("GOOGLE_API_KEY")


def is_configured() -> bool:
    return bool(_api_key())


def _model(json_mode: bool = True):
    import google.generativeai as genai

    genai.configure(api_key=_api_key())
    gen_config = {"temperature": 0.6}
    if json_mode:
        gen_config["response_mime_type"] = "application/json"
    return genai.GenerativeModel(MODEL_NAME, generation_config=gen_config)


def _call(prompt: str, json_mode: bool = True, retries: int = 2) -> str:
    if not is_configured():
        raise AgentError("GEMINI_API_KEY is not set.")
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            resp = _model(json_mode=json_mode).generate_content(prompt)
            return (resp.text or "").strip()
        except Exception as e:  # pragma: no cover - network/SDK errors
            last_err = e
            log.warning("Gemini call failed (attempt %d/%d): %s", attempt + 1, retries + 1, e)
            if attempt < retries:
                time.sleep(1.2 * (attempt + 1))
    raise AgentError(f"Gemini call failed after {retries + 1} attempts: {last_err}")


def _safe_json(text: str, default):
    cleaned = re.sub(r"```(?:json)?|```", "", text).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        m = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass
        return default


def transcribe_audio(audio_bytes: bytes, mime: str = "audio/ogg") -> str:
    """Transcribe a WhatsApp voice note to text using Gemini's audio understanding.

    Returns the transcription, or "" if it couldn't be transcribed.
    """
    if not is_configured():
        raise AgentError("GEMINI_API_KEY is not set.")
    import google.generativeai as genai

    genai.configure(api_key=_api_key())
    model = genai.GenerativeModel(MODEL_NAME)
    try:
        resp = model.generate_content([
            {"mime_type": mime, "data": audio_bytes},
            "Transcribe this voice message to text, verbatim, in its original language. "
            "Output ONLY the transcription — no quotes, no commentary.",
        ])
        return (resp.text or "").strip()
    except Exception as e:  # pragma: no cover - network/SDK errors
        log.warning("Audio transcription failed: %s", e)
        return ""


def relay_command(command: str, candidates: list[dict], profile: dict, cfg: dict,
                  target: dict | None = None) -> dict:
    """A teammate instructed the assistant in the internal group (e.g. 'Ax, tell
    Devraj that Ruchika will call 5-6pm PST, her number is 123'). Identify which
    candidate they mean and compose a short WhatsApp message to send that person.

    If `target` ({wa_id, name}) is given (the team REPLIED to a specific alert), we
    already know the candidate — just compose the message for them.

    Returns {found, wa_id, name, message, note}.
    """
    if not is_configured():
        raise AgentError("GEMINI_API_KEY is not set.")
    assistant = cfg.get("assistant_name", "Alex")
    biz = profile.get("business_name", "the company")

    if target and target.get("wa_id"):
        tname = target.get("name") or "there"
        cprompt = f"""You are {assistant} from {biz}. A teammate replied to a candidate's alert with an
instruction. Write a short, warm WhatsApp message to send to the candidate ({tname}) that carries out
the instruction — first person as {assistant} from {biz}, include EVERY specific detail (times, names,
phone numbers, next steps).

Instruction: "{command}"

Return ONLY JSON:
{{"found": true, "wa_id": {json.dumps(target["wa_id"])}, "name": {json.dumps(tname)},
  "message": "the message to send the candidate", "note": "one short line back to the team"}}""".strip()
        return _safe_json(_call(cprompt), {"found": False, "wa_id": target["wa_id"],
                                           "name": tname, "message": "", "note": "Could not compose."})

    prompt = f"""You are {assistant}, {biz}'s WhatsApp assistant. A teammate sent you an instruction
in the internal team group. Carry it out by (1) identifying which candidate they mean and (2) writing
a short, warm WhatsApp message to send to THAT candidate.

RECENT CANDIDATES you can message (match the instruction to one of these by name or number):
{json.dumps(candidates, ensure_ascii=False)}

Teammate's instruction: "{command}"

Return ONLY this JSON:
{{
  "found": true/false,        // true only if you can confidently match ONE candidate from the list
  "wa_id": "the matched candidate's wa_id EXACTLY as in the list, or empty string",
  "name": "the candidate's name",
  "message": "the WhatsApp message to send the candidate — first person as {assistant} from {biz}, warm and short, include every specific detail from the instruction (times, names, phone numbers, next steps). Empty if not found.",
  "note": "one short line back to the team: what you sent, or why you couldn't (e.g. name not found / ambiguous)"
}}""".strip()
    return _safe_json(_call(prompt), {"found": False, "wa_id": "", "name": "",
                                      "message": "", "note": "Could not parse the command."})


def _system_persona(profile: dict, cfg: dict) -> str:
    name = cfg.get("assistant_name", "the assistant")
    biz = profile.get("business_name", "our company")
    tone = cfg.get("tone", "warm, friendly, and concise")
    return (
        f"You are {name}, replying for {biz} on WhatsApp. People message this "
        f"number after seeing our Instagram ad. You're the first responder when "
        f"the rest of the team is unavailable. Introduce yourself simply as "
        f"'{name} from the {biz} team' — warm and human, not clinical. Sound like "
        f"a {tone} colleague texting. Make the person feel heard, gently collect a few "
        f"qualifying details, and answer using ONLY the business information "
        f"provided. Never invent facts, prices, guarantees, or promises.\n"
        f"HOW TO SOUND HUMAN:\n"
        f"- Say your name ONLY in your very first message to someone new. After that "
        f"NEVER re-introduce yourself or repeat your name — just talk naturally.\n"
        f"- Don't start every message with 'Great question!' / 'Thanks for sharing!' "
        f"or other canned filler. Vary it; sometimes just answer.\n"
        f"- Keep replies short and texty (usually 1–2 sentences). Ask at most ONE "
        f"question per message. Use their name at most occasionally, not every time.\n"
        f"- Match the person's energy; if they're brief, be brief.\n"
        f"HONESTY: You are an automated assistant, not a human. NEVER claim to be a "
        f"real person or human. If someone asks whether you're a bot / AI / real "
        f"person, answer briefly and honestly — e.g. you're {biz}'s automated "
        f"assistant and the team follows up personally — then continue helping. "
        f"Do not lie about this under any circumstances."
    )


def _questions_block(questions: list[dict], collected: dict) -> str:
    lines = []
    for q in questions:
        key = q.get("key")
        have = collected.get(key)
        status = f"ALREADY KNOWN: {have}" if have else "still needed"
        lines.append(f"- {key}: ask about {q.get('ask')} ({q.get('why', '')}) — {status}")
    return "\n".join(lines)


def _examples_block(examples: list[dict]) -> str:
    if not examples:
        return ""
    lines = ["STYLE EXAMPLES — match this human tone (do NOT copy verbatim):"]
    for ex in examples[:8]:
        cust = ex.get("customer", "").strip()
        rep = ex.get("reply", "").strip()
        if cust and rep:
            lines.append(f'  Customer: "{cust}"\n  You: "{rep}"')
    return "\n".join(lines) if len(lines) > 1 else ""


def respond(
    *,
    profile: dict,
    questions: list[dict],
    config_cfg: dict,
    collected: dict,
    history: list[dict],
    user_message: str,
    is_first_contact: bool,
    examples: list[dict] | None = None,
    wrap_up: bool = False,
    link_recently_sent: bool = False,
) -> dict:
    """Produce the agent's next action.

    Returns a dict:
    {
      "reply": str,                 # the WhatsApp message to send back
      "collected": {key: value},    # NEW qualification fields extracted this turn
      "answered": bool,             # did we answer a question they asked?
      "confidence": int 0-100,      # confidence in the factual accuracy of the reply
      "escalate": bool,             # hand off to a human?
      "escalation_reason": str,     # short internal note for the team
      "stage": str                  # greeting|qualifying|answering|escalated|closing
    }
    """
    persona = _system_persona(profile, config_cfg)
    conf_threshold = int(config_cfg.get("escalation_confidence", 55))

    convo = ""
    for turn in history[-config.HISTORY_TURNS:]:
        who = "Customer" if turn.get("role") == "user" else "You"
        convo += f"{who}: {turn.get('text', '')}\n"

    first_note = (
        "This is the FIRST message from this person. Open the conversation: "
        + config_cfg.get("greeting_style", "Introduce yourself briefly and ask one opening question.")
        if is_first_contact
        else "This is an ONGOING conversation. Do NOT re-introduce yourself and do NOT repeat your name."
    )

    # Pull out the richer fields so we can present them clearly, and keep the
    # core profile JSON focused on plain facts.
    jobs = profile.get("jobs") or []
    knowledge_doc = (profile.get("knowledge_doc") or "").strip()
    scheduling_link = (profile.get("scheduling_link") or "").strip()
    core = {k: v for k, v in profile.items()
            if k not in ("jobs", "knowledge_doc", "scheduling_link")}

    jobs_block = (
        "CURRENT OPEN ROLES you can mention when relevant:\n"
        + json.dumps(jobs, ensure_ascii=False, indent=2)
        if jobs else "CURRENT OPEN ROLES: (none listed — speak generally about the kinds of roles we place)"
    )
    doc_block = f"REFERENCE NOTES (extra facts you may use):\n{knowledge_doc}" if knowledge_doc else ""
    sched_block = (
        f"SCHEDULING (your MAIN goal): The best next step for any interested candidate is a "
        f"free 15-minute intro call with a recruiter. Once someone seems interested or is a fit, "
        f"warmly offer to book it and share this link: {scheduling_link} . If they ask for a "
        f"calendar/booking link, share it right away. Don't over-qualify over chat — a couple of "
        f"light questions is enough, then point them to the call where the recruiter goes deeper."
        if scheduling_link
        else "SCHEDULING: We have no self-serve booking link, so if they want to book a call, "
             "collect a good time and let them know the team will reach out."
    )
    examples_block = _examples_block(examples or [])

    behavior = (config_cfg.get("behavior") or "").strip()
    behavior_block = (
        "HOW YOU MUST BEHAVE (HIGHEST PRIORITY — this controls the whole conversation, "
        "follow it over any other style guidance):\n" + behavior
    ) if behavior else ""

    if wrap_up:
        state_note = (
            "STATUS: The candidate has asked plenty over chat without booking. WRAP UP NOW. Do NOT "
            "answer this latest message in detail. Send ONE short, friendly closing that says the best "
            "way to get into the details is the quick intro call, share the link one final time, and "
            "that you're around if they need anything. 1–2 sentences max. Set stage=closing."
        )
    elif collected.get("booked"):
        state_note = (
            "STATUS: This candidate has ALREADY BOOKED the intro call. If they JUST told you they "
            "booked, reply with a warm one-line confirmation (e.g. 'Perfect, thanks for booking — see "
            "you on the call!') — do NOT stay silent on that. Otherwise do NOT share the calendar link "
            "again or nudge them to book; just answer any real questions briefly. Only stay silent "
            "(send=false) for pure filler like 'ok'/'thanks' or noise."
        )
    elif collected.get("ended"):
        state_note = (
            "STATUS: This conversation has already been wound down. Keep it minimal. If they ask a real "
            "new question, reply in ONE short line and suggest the call for details. If it's noise, "
            "repetition, or small talk, set send=false. Do NOT re-send the link unless they ask for it."
        )
    else:
        state_note = ""

    if link_recently_sent and not wrap_up:
        state_note = (state_note + "\n" if state_note else "") + (
            "NOTE: You already sent the calendar link in your previous message. Do NOT paste it again "
            "this time unless the candidate explicitly asks for the link or how to book."
        )

    prompt = f"""{persona}

{behavior_block}

BUSINESS INFORMATION (the ONLY facts you may state):
{json.dumps(core, ensure_ascii=False, indent=2)}

{jobs_block}

{doc_block}

{sched_block}

QUALIFYING DETAILS to collect naturally over the conversation (one at a time):
{_questions_block(questions, collected)}

TOPICS YOU MUST NOT ANSWER — escalate to a human instead:
{json.dumps(profile.get("escalate_topics", []), ensure_ascii=False)}

{examples_block}

CONVERSATION SO FAR:
{convo if convo else "(none yet)"}

{first_note}
{state_note}
Customer's latest message: "{user_message}"

DECIDE the single best next reply, then return ONLY this JSON:
{{
  "reply": "the WhatsApp message to send back — short, human, {config_cfg.get('tone','warm')}, at most one question (empty string if send is false)",
  "send": true/false,               // DEFAULT true — reply. Set false ONLY for: (a) pure gibberish/keyboard-mashing ("aaa","hhh", random letters); (b) a message PURELY off-topic with no job/career content (bare math, joke, trivia, forwarded spam); (c) a bare acknowledgment that needs no response ("ok","k","hmm","cool","👍", a lone emoji). NEVER false for a real question, a greeting or well-wish (good morning, have a nice weekend, take care), a self-introduction, a booking confirmation, or anything about jobs/careers/the company. When unsure, REPLY.
  "collected": {{}},                // any NEW qualifying details you learned from THIS message, as key:value using the keys above; {{}} if none
  "answered": true/false,           // true if the customer asked something and you answered it from the business info
  "confidence": 0-100,              // how sure you are the reply is factually correct & within what the business info supports
  "escalate": true/false,           // true when the TEAM needs to act: booking-link problem (no slots / broken), the person gives their availability expecting the team to schedule or call them, a callback request, they're upset, they ask for a human, or anything you cannot resolve from the business info
  "escalation_reason": "specific note for the team — include what they need AND concrete details: their stated availability, the exact issue (e.g. 'booking link shows no slots'), timezone, or callback request",
  "stage": "greeting | qualifying | answering | escalated | closing"
}}

RULES:
- RELEVANCE GATE: only engage with messages relevant to the company, jobs, or the candidate's career/job search. STAY SILENT (send=false, empty reply — do not answer or redirect) when a message is NOT relevant, e.g. bank/payment/bill alerts, ads or promotions, math or trivia, jokes, news, politics, weather, general chit-chat, or forwarded spam. Also stay silent for pure gibberish ("aaa","hhh") and content-free filler ("ok","thanks","hmm", a lone emoji) when nothing is pending.
- BUT these ARE relevant and MUST be answered: greetings, self-introductions, questions about roles/process/salary/visa/companies/timeline, trust questions ("is this a scam?", "are you legit?"), eligibility ("I'm in India", "I'm a designer"), booking/scheduling, and anything about their engineering background — answer briefly even if asked before. When unsure whether a message is relevant, REPLY.
- PLEASANTRIES: briefly and warmly reciprocate genuine greetings and well-wishes from someone you're chatting with — "good morning" → "Good morning!", "have a nice weekend" → "You too, thanks!", "thank you" → "Anytime!". Keep it to ONE short line. (Bare acknowledgments like "ok"/"hmm"/"👍" still get no reply.)
- Follow the HOW YOU MUST BEHAVE section above as the primary guide for the flow (lead toward booking the intro call and sharing the calendar link — don't interrogate).
- NEVER open by asking for their name, and never make "what's your name?" a question on its own. If their name is in the known details above, use it naturally; if not, don't ask — it'll come up.
- ALWAYS respond to what the customer JUST said. If they greet you ("hi", "hello"), greet back warmly and follow the behavior flow — do not ignore it or recycle an earlier topic.
- NEVER repeat a sentence or phrase you have already used earlier in this conversation. Say things a fresh way each time. In particular, never reuse lines like "we're having trouble connecting over text."
- Do NOT nag about booking a phone call. Suggest a call at most ONCE, and only if it genuinely fits (e.g. they're ready, or they explicitly ask). Otherwise keep helping over chat.
- If the conversation earlier went sideways (gibberish, an escalation) but the customer now sends a normal greeting or question, treat it as a fresh restart: be warm and helpful, don't dwell on the earlier mess.
- Don't over-qualify. If they haven't answered a question after a try or two, move on gracefully instead of asking the same thing again.
- If you must escalate, still write a warm, natural holding reply — do NOT pretend you can't help at all, and don't sound like a form letter.
- If confidence would be below {conf_threshold} for a factual claim, set escalate=true rather than guessing.
- Vague or unclear messages are NOT a reason to escalate — just ask a friendly clarifying question. Only escalate for real reasons (can't answer from the business info, a must-not-answer topic, they ask for a human, or they're upset).
- Never output anything except the JSON object.
""".strip()

    default = {
        "reply": "Thanks for reaching out! Someone from our team will get back to you shortly. 🙏",
        "send": True,
        "collected": {},
        "answered": False,
        "confidence": 0,
        "escalate": True,
        "escalation_reason": "Agent could not generate a reply.",
        "stage": "escalated",
    }
    data = _safe_json(_call(prompt), default)
    if not isinstance(data, dict):
        return default

    # Normalise / harden the fields.
    data.setdefault("reply", default["reply"])
    data["send"] = bool(data.get("send", True))
    # If the model chose not to reply, make sure there's nothing to send.
    if not data["send"]:
        data["reply"] = ""
    data["collected"] = data.get("collected") if isinstance(data.get("collected"), dict) else {}
    data["answered"] = bool(data.get("answered"))
    try:
        data["confidence"] = max(0, min(100, int(data.get("confidence", 0))))
    except Exception:
        data["confidence"] = 0
    data["escalate"] = bool(data.get("escalate"))
    data.setdefault("escalation_reason", "")
    data.setdefault("stage", "qualifying")

    # Safety net: low confidence always escalates.
    if data["confidence"] < conf_threshold and data["answered"]:
        data["escalate"] = True
        if not data["escalation_reason"]:
            data["escalation_reason"] = "Low confidence in the answer."
    return data
