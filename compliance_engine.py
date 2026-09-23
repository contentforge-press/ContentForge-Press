"""
🧠 合规检测引擎 — Compliance Rule Engine
检测英文营销内容（邮件/广告/文案）在以下法规下的合规问题：
- FTC AI 披露规则
- 欧盟 AI Act 透明度（AI生成须披露）
- CAN-SPAM Act（退订/真实发件人/主题不误导）
- GDPR（同意/数据权利措辞）
- 欺骗性声明（收益保证/绝对化用语）
纯规则 + 关键词/正则，可离线运行，确定性输出。
"""
import re

# ─────────────────────────────────────────────
# 规则定义
# 每条规则: id, name, severity, category, why, detector(text)->bool|match, fix
# ─────────────────────────────────────────────

# 退订相关表达
UNSUBSCRIBE_PATTERNS = [
    r"unsubscribe", r"opt[-\s]?out", r"stop receiving",
    r"remove me", r"no longer (wish|want) to receive",
]

# AI 披露表达
AI_DISCLOSURE_PATTERNS = [
    r"\bAI[-\s]?(generated|assisted|powered|written|created|drafted|reviewed)\b",
    r"\bartificial intelligence\b",
    r"\b(generated|created|written|drafted|reviewed).{0,25}\b(AI|artificial intelligence|automated)\b",
    r"\bwith AI assistance\b",
    r"\bgenerated (by|with) ai\b",
    r"\bAI assistant\b",
    r"\bautomated (message|email)\b",
]

# 物理地址（CAN-SPAM 要求真实邮政地址）
POSTAL_ADDRESS_PATTERN = re.compile(
    r"\d{1,5}\s+[A-Za-z0-9 .,'-]{3,40}(street|st\.?|avenue|ave\.?|road|rd\.?|boulevard|blvd\.?|lane|ln\.?|drive|dr\.?|way|suite|ste\.?|unit|floor)",
    re.IGNORECASE,
)

# 物理地址兜底：ZIP 码
ZIP_PATTERN = re.compile(r"\b\d{5}(-\d{4})?\b")

# 真实发件人/公司名
SENDER_IDENTITY_PATTERNS = [
    r"\b(best|regards|sincerely|thanks|cheers)\b.{0,40}\b[A-Z][a-z]+ [A-Z][a-z]+\b",
    r"\b[A-Z][a-z]+ [A-Z][a-z]+\b.{0,30}\b(inc|llc|ltd|gmbh|corp|co\.?|company)\b",
]

# 欺骗性/高风险声明
DECEPTIVE_CLAIMS = [
    (r"\bguarantee(d)?\b.{0,30}\b(profit|return|income|results?|sale|deal|weight loss)\b",
     "Guarantee of results/profit is a high-risk deceptive claim under FTC."),
    (r"\b(make|earn)\s+\$?\d[\d,]*(?:\s*\+)?\s*(per|/|a)\s*(day|week|month)\b",
     "Specific earnings claim requires substantiation; high FTC enforcement risk."),
    (r"\b100%\s+(guaranteed|risk[-\s]?free|effective|free)\b",
     "Absolute '100%' claim is generally unsubstantiable."),
    (r"\b(risk[-\s]?free|no risk|zero risk)\b",
     "'Risk-free' claim triggers FTC cooling-off / disclosure requirements."),
    (r"\b(get[-\s]?rich|financial freedom guaranteed|double your money)\b",
     "Classic get-rich-quick language; near-certain FTC red flag."),
    (r"\bcure[ds]?\b.{0,20}\b(cancer|disease|diabetes|covid|illness)\b",
     "Unsubstantiated medical cure claim; FDA/FTC high risk."),
]

# 误导性主题（Re: / Fwd: 伪装）
MISLEADING_SUBJECT_PATTERNS = [
    (r"^(re|fw|fwd)\s*:", "Subject uses 'Re:/Fwd:' which implies an existing conversation."),
]

# GDPR 数据权利措辞
GDPR_RIGHTS_PATTERNS = [
    r"\bunsubscribe\b", r"\bopt[-\s]?out\b",
    r"\bdata (protection|rights|privacy)\b",
    r"\bprivacy policy\b",
    r"\bmanage your (data|preferences)\b",
]

# 同意/合法利益措辞（针对已有客户 vs 冷邮件）
CONSENT_HINTS = [r"\byou (subscribed|opted in|signed up)\b", r"\byour consent\b"]


def _find_any(text, patterns):
    """返回第一个匹配的 pattern 字符串，否则 None"""
    for p in patterns:
        if re.search(p, text, re.IGNORECASE):
            return p
    return None


def _snippet_for(text, pattern, window=60):
    m = re.search(pattern, text, re.IGNORECASE)
    if not m:
        return ""
    start = max(0, m.start() - window)
    end = min(len(text), m.end() + window)
    snip = text[start:end].replace("\n", " ").strip()
    return ("..." if start > 0 else "") + snip + ("..." if end < len(text) else "")


def analyze_content(text, content_type="email", is_ai_generated=True, subject=""):
    """
    分析内容合规性。
    参数:
      text: 正文
      content_type: email | ad | social | webpage
      is_ai_generated: 该内容是否由AI生成（若是，则必须披露）
      subject: 邮件主题（email 时检测误导性）
    返回: dict(compliance_score, is_compliant, violations[], summary)
    """
    text = text or ""
    violations = []

    def add(rule_id, name, severity, category, message, fix, snippet=""):
        violations.append({
            "rule": rule_id, "name": name, "severity": severity,
            "category": category, "message": message, "fix": fix,
            "snippet": snippet,
        })

    # ── 1. AI 披露（AI Act + FTC）──
    if is_ai_generated:
        if not _find_any(text, AI_DISCLOSURE_PATTERNS):
            add(
                "AI_DISCLOSURE_MISSING", "AI Disclosure", "high",
                "EU AI Act / FTC",
                "Content is AI-generated but contains no AI disclosure. EU AI Act and FTC require users to be told when content is machine-generated.",
                "Add a clear line such as: 'This message was drafted with AI assistance and reviewed by a human.'",
            )

    # ── 2. CAN-SPAM: 退订机制（仅邮件）──
    if content_type == "email":
        if not _find_any(text, UNSUBSCRIBE_PATTERNS):
            add(
                "CANSPAM_UNSUBSCRIBE", "Unsubscribe Mechanism", "high",
                "CAN-SPAM Act",
                "Email contains no unsubscribe / opt-out method. CAN-SPAM requires a clear way for recipients to stop future emails.",
                "Add: 'You can unsubscribe at any time — just reply \"unsubscribe\" or use the link below.'",
            )

        # ── 3. CAN-SPAM: 真实邮政地址 ──
        if not POSTAL_ADDRESS_PATTERN.search(text) and not ZIP_PATTERN.search(text):
            add(
                "CANSPAM_POSTAL_ADDRESS", "Physical Postal Address", "medium",
                "CAN-SPAM Act",
                "No valid physical postal address found. CAN-SPAM requires a legitimate physical mailing address.",
                "Add your company's real street address or a registered P.O. Box, including ZIP code.",
            )

        # ── 4. CAN-SPAM: 主题不误导 ──
        for pat, msg in MISLEADING_SUBJECT_PATTERNS:
            if subject and re.search(pat, subject.strip(), re.IGNORECASE):
                add(
                    "CANSPAM_SUBJECT", "Non-misleading Subject", "medium",
                    "CAN-SPAM Act", msg,
                    "Remove 'Re:/Fwd:' unless there is a genuine prior conversation.",
                    subject,
                )

    # ── 5. 欺骗性声明（所有类型）──
    for pat, msg in DECEPTIVE_CLAIMS:
        if re.search(pat, text, re.IGNORECASE):
            add(
                "FTC_DECEPTIVE_CLAIM", "Deceptive / Unsubstantiated Claim", "high",
                "FTC Act §5", msg,
                "Remove the absolute/guaranteed claim or replace with qualified, substantiated language (e.g. 'many customers see... results may vary').",
                _snippet_for(text, pat),
            )

    # ── 6. GDPR 退订/数据权利（邮件/广告）──
    if content_type in ("email", "ad"):
        if not _find_any(text, GDPR_RIGHTS_PATTERNS):
            add(
                "GDPR_DATA_RIGHTS", "Data Rights / Privacy Notice", "low",
                "GDPR",
                "No reference to data rights, privacy policy or opt-out. Recommended when contacting EU recipients.",
                "Add a short privacy line: 'Learn how we handle your data in our privacy policy, and opt out at any time.'",
            )

    # ── 评分 ──
    weights = {"high": 28, "medium": 14, "low": 6}
    penalty = sum(weights[v["severity"]] for v in violations)
    score = max(0, 100 - penalty)

    highs = sum(1 for v in violations if v["severity"] == "high")
    is_compliant = highs == 0

    return {
        "compliance_score": score,
        "is_compliant": is_compliant,
        "violations": violations,
        "counts": {
            "high": sum(1 for v in violations if v["severity"] == "high"),
            "medium": sum(1 for v in violations if v["severity"] == "medium"),
            "low": sum(1 for v in violations if v["severity"] == "low"),
        },
        "summary": (
            "Compliant — no high-severity issues found."
            if is_compliant else
            f"{highs} high-severity issue(s) must be fixed before sending."
        ),
    }


def auto_fix(text, analysis, is_ai_generated=True, content_type="email"):
    """
    根据检测结果生成一个"尽量修复"的版本（追加缺失的必要声明）。
    注意：欺骗性声明需要人工删除，这里只做安全的"追加"，不篡改原句。
    """
    fixed = text.rstrip()
    additions = []

    rule_ids = {v["rule"] for v in analysis["violations"]}

    if "AI_DISCLOSURE_MISSING" in rule_ids and is_ai_generated:
        additions.append(
            "—\nThis message was drafted with AI assistance and reviewed by a human before sending."
        )
    if "CANSPAM_UNSUBSCRIBE" in rule_ids:
        additions.append(
            "You're receiving this because of your business. Reply \"unsubscribe\" to opt out at any time."
        )
    if "CANSPAM_POSTAL_ADDRESS" in rule_ids:
        additions.append("[INSERT YOUR COMPANY PHYSICAL ADDRESS + ZIP CODE]")
    if "GDPR_DATA_RIGHTS" in rule_ids:
        additions.append(
            "See how we handle your data in our privacy policy. You can opt out at any time."
        )

    if additions:
        fixed = fixed + "\n\n" + "\n\n".join(additions)

    notes = []
    if "FTC_DECEPTIVE_CLAIM" in rule_ids:
        notes.append(
            "High-risk deceptive/guarantee claims were detected and cannot be auto-fixed — please remove or rewrite them manually."
        )
    if "CANSPAM_SUBJECT" in rule_ids:
        notes.append("Subject line uses misleading Re:/Fwd: — edit the subject manually.")

    return {"fixed_version": fixed, "manual_actions_required": notes}
