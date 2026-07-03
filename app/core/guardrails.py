import re
import os
import math
import json
import logging
import logging.handlers
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple
from datetime import datetime, timezone

# ============================================================
# Configuration (env-var driven)
# ============================================================
GUARDRAILS_THRESHOLD = int(os.environ.get("GUARDRAILS_THRESHOLD", "65"))
MAX_INPUT_LENGTH = int(os.environ.get("GUARDRAILS_MAX_INPUT", "2000"))
DEFENSIVE_RESPONSE = "No puedo procesar esta solicitud. Por favor, reformula tu pregunta."
from app.core.config import LOGS_DIR
LOG_FILE = os.environ.get("GUARDRAILS_LOG_FILE", os.path.join(LOGS_DIR, "guardrails.log"))

LAYER_WEIGHTS = {"regex": 1.0, "heuristic": 0.8, "delimiter": 1.0}


# ============================================================
# Data Structures
# ============================================================
class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PatternEntry:
    id: str
    category: str
    severity: Severity
    score: int
    regex: "re.Pattern"
    description: str


@dataclass
class Finding:
    category: str
    pattern_id: str
    description: str
    severity: Severity
    score_contribution: int
    matched_text: str


@dataclass
class GuardrailResult:
    blocked: bool
    score: int
    reasons: List[str]
    response: str
    findings: List[Finding] = field(default_factory=list)
    layer_breakdown: dict = field(default_factory=dict)


# ============================================================
# Pattern Registry — Layer 1 (regex)
# ============================================================
def _build_patterns() -> List[PatternEntry]:
    P = []
    C = re.compile

    # ── Category A: Instruction Leak (IL) ──────────────────────
    IL = [
        ("IL-001", Severity.HIGH, 50, r'(?i)\bignora\s+(las\s+)?instrucciones\s+(anteriores|previas|del\s+sistema)\b', "ES: Ignorar instrucciones del sistema"),
        ("IL-002", Severity.HIGH, 50, r'(?i)\bignora\s+(todo\s+)?lo\s+que\s+(te|le)\s+(he|han)\s+(dicho|instruido)\b', "ES: Ignorar lo dicho/instruido"),
        ("IL-003", Severity.HIGH, 45, r'(?i)\bno\s+(siga|sigas|escuche|escuches)\s+(las\s+)?instrucciones\b', "ES: No seguir instrucciones"),
        ("IL-004", Severity.CRITICAL, 70, r'(?i)\brevela\s+(tu|el|su)\s+(system\s*prompt|prompt\s+del?\s+sistema|instrucciones)\b', "ES: Revelar system prompt"),
        ("IL-005", Severity.CRITICAL, 70, r'(?i)\b(muestra|dime|cu[aá]l\s+es)\s+(tus?|el|su|sus)\s+(system\s*prompt|prompt\s+del?\s+sistema|instrucciones)\b', "ES: Mostrar/decir system prompt"),
        ("IL-006", Severity.CRITICAL, 70, r'(?i)\bcopia\s+(y\s+pega|exactamente)\s+(tu|el|su)\s+(prompt|instrucciones)\b', "ES: Copiar prompt"),
        ("IL-007", Severity.HIGH, 55, r'(?i)\brepite\s+(despu[eé]s\s+de\s+m[ií]|literalmente|exactamente)\b', "ES: Repetir después de mí"),
        ("IL-008", Severity.HIGH, 50, r'(?i)\b(traduce|convierte)\s+(tu\s+)?(prompt|instrucciones|system)\b', "ES: Traducir prompt/instrucciones"),
        ("IL-009", Severity.CRITICAL, 70, r'(?i)\b(api\s*key|contrase[nñ]a|clave\s+secreta|token\s+de\s+acceso|password)\b', "ES: Solicitar credenciales"),
        ("IL-010", Severity.HIGH, 50, r'(?i)\b(omite|salta|pasa\s+por\s+alto)\s+(las\s+)?(reglas|restricciones|filtros)\b', "ES: Omitir reglas/filtros"),
        ("IL-010b", Severity.HIGH, 50, r'(?i)\bignora\s+(todas\s+las\s+)?(reglas|restricciones)\b', "ES: Ignorar reglas/restricciones"),
        ("IL-010c", Severity.HIGH, 50, r'(?i)\bignore\s+(all\s+)?(the\s+)?(rules|restrictions)\b', "EN: Ignore all rules"),
        ("IL-011", Severity.HIGH, 50, r'(?i)\bignore\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions|rules|prompts|guidelines)\b', "EN: Ignore previous instructions"),
        ("IL-012", Severity.HIGH, 50, r'(?i)\bignore\s+(your|the)\s+(instructions|rules|programming|constraints|guidelines)\b', "EN: Ignore your instructions"),
        ("IL-013", Severity.HIGH, 50, r'(?i)\bdisregard\s+(all\s+)?(previous|your|the)\s+(instructions|rules|guidelines)\b', "EN: Disregard instructions"),
        ("IL-014", Severity.HIGH, 50, r'(?i)\boverride\s+(your|the)\s+(instructions|programming|rules|constraints)\b', "EN: Override instructions"),
        ("IL-015", Severity.CRITICAL, 70, r'(?i)\breveal\s+(your|the)\s+(system\s*prompt|instructions|rules|configuration)\b', "EN: Reveal system prompt"),
        ("IL-016", Severity.CRITICAL, 70, r'(?i)\bshow\s+me\s+(your|the)\s+(system\s*prompt|instructions|initial\s+prompt)\b', "EN: Show system prompt"),
        ("IL-017", Severity.CRITICAL, 70, r'(?i)\b(what|tell)\s+(is|are|me)\s+(your|the)\s+(system\s*prompt|instructions|initial\s+prompt|hidden\s+prompt)\b', "EN: What is your system prompt"),
        ("IL-018", Severity.CRITICAL, 70, r'(?i)\bprint\s+(your|the)\s+(system\s*prompt|instructions)\b', "EN: Print system prompt"),
        ("IL-019", Severity.HIGH, 55, r'(?i)\brepeat\s+(after\s+me|exactly|word\s+for\s+word|verbatim)\b', "EN: Repeat after me/verbatim"),
        ("IL-020", Severity.CRITICAL, 70, r'(?i)\b(copy|paste)\s+(and\s+paste\s+)?(your|the)\s+(prompt|instructions|system)\b', "EN: Copy/paste prompt"),
        ("IL-021", Severity.HIGH, 50, r'(?i)\b(extrae|extraer|saca|sacar)\s+(tu|el|su|las)\s+(prompt|instrucciones|configuraci[oó]n)\b', "ES: Extraer prompt"),
        ("IL-022", Severity.HIGH, 50, r'(?i)\b(dump|extract|leak)\s+(your|the)\s+(prompt|instructions|memory|context|config)\b', "EN: Dump/extract/leak prompt"),
        ("IL-023", Severity.CRITICAL, 70, r'(?i)\bwhat\s+(are|were)\s+you\s+(told|instructed|programmed|designed)\s+to\s+do\b', "EN: What were you instructed to do"),
        ("IL-024", Severity.HIGH, 50, r'(?i)\b(cu[aá]les?\s+son|dime)\s+(tus?\s+)?(reglas|restricciones|directrices|limitaciones)\b', "ES: Cuáles son tus reglas"),
    ]
    for id_, sev, score, pattern, desc in IL:
        P.append(PatternEntry(id_, "instruction_leak", sev, score, C(pattern), desc))

    # ── Category B: Jailbreak (JB) ─────────────────────────────
    JB = [
        ("JB-001", Severity.HIGH, 50, r'(?i)\basume\s+(el\s+)?rol\s+de\b', "ES: Asumir rol de"),
        ("JB-002", Severity.MEDIUM, 35, r'(?i)\bact[uú]a\s+como\s+si\s+(fueras|fuera|seas|sea)\b', "ES: Actúa como si fueras"),
        ("JB-003", Severity.MEDIUM, 35, r'(?i)\beres\s+ahora\s+un[ao]?\b', "ES: Eres ahora un/una"),
        ("JB-004", Severity.MEDIUM, 30, r'(?i)\bpretendes?\s+ser\b', "ES: Pretendes ser"),
        ("JB-005", Severity.HIGH, 50, r'(?i)\bfinge\s+(que|ser)\b', "ES: Finge que/ser"),
        ("JB-006", Severity.CRITICAL, 75, r'(?i)\bmodo\s+(desarrollador|developer|jailbreak|libre|sin\s+filtros|prueba)\b', "ES: Modo desarrollador/jailbreak"),
        ("JB-007", Severity.HIGH, 55, r'(?i)\bDAN\b', "DAN reference"),
        ("JB-008", Severity.CRITICAL, 75, r'(?i)\bentra\s+en\s+modo\s+(desarrollador|developer|libre)\b', "ES: Entrar en modo desarrollador"),
        ("JB-009", Severity.HIGH, 55, r'(?i)\b(ayuda|asistente)\s+(malvad[oa]|sin\s+[eé]tica|villano)\b', "ES: Asistente malvado"),
        ("JB-010", Severity.LOW, 20, r'(?i)\bhipot[eé]ticamente.*\b(podr[ií]as|ser[ií]a\s+posible)\b', "ES: Hipotéticamente podrías"),
        ("JB-011", Severity.HIGH, 55, r'(?i)\b(imagina|sup[oó]n)\b.*\bque\s+no\s+(hay|tienes)\b.*\b(restricciones|l[ií]mites|reglas)\b', "ES: Imagina que no tienes restricciones"),
        ("JB-012", Severity.MEDIUM, 35, r'(?i)\bassume\s+the\s+role\s+of\b', "EN: Assume the role of"),
        ("JB-013", Severity.MEDIUM, 30, r'(?i)\bact\s+as\s+(if\s+you\s+were\s+)?(a|an|the)\b', "EN: Act as if you were"),
        ("JB-014", Severity.MEDIUM, 30, r'(?i)\bpretend\s+(you\s+are|to\s+be)\b', "EN: Pretend you are"),
        ("JB-015", Severity.MEDIUM, 35, r'(?i)\byou\s+are\s+now\s+(a|an|the|in)\b', "EN: You are now"),
        ("JB-016", Severity.MEDIUM, 35, r'(?i)\bfrom\s+now\s+on\s+you\s+(are|will|must)\b', "EN: From now on you are/will"),
        ("JB-017", Severity.CRITICAL, 75, r'(?i)\b(developer|jailbreak|DAN)\s+mode\b', "EN: Developer/jailbreak/DAN mode"),
        ("JB-018", Severity.CRITICAL, 75, r'(?i)\benter\s+(developer|jailbreak|god)\s+mode\b', "EN: Enter developer/jailbreak mode"),
        ("JB-019", Severity.HIGH, 55, r'(?i)\b(evil|unethical|unrestricted)\s+(assistant|helper|AI|mode)\b', "EN: Evil/unethical assistant"),
        ("JB-020", Severity.HIGH, 55, r'(?i)\b(imagine|suppose|hypothetically)\b.*\b(no\s+)?(restrictions|rules|limits|constraints|boundaries)\b', "EN: Imagine no restrictions"),
        ("JB-021", Severity.CRITICAL, 75, r'(?i)\bdo\s+anything\s+now\b', "EN: Do Anything Now (DAN)"),
        ("JB-022", Severity.HIGH, 60, r'(?i)\btoken\s+smuggling\b|\bsmuggle\b.*\btokens?\b', "Token smuggling attempt"),
        ("JB-023", Severity.CRITICAL, 75, r'(?i)\b(bypass|circumvent|evade)\s+(your|the|all)\s+(safety|content|ethical|moderation)\s+(filters?|restriction|policy|guard)s?\b', "EN: Bypass safety filters"),
        ("JB-024", Severity.CRITICAL, 75, r'(?i)\b(elude|evita|esquiva|evade|evadir)\s+(tus?\s+)?(filtros?|restricciones?|seguridad)\b', "ES: Evadir filtros/restricciones"),
        ("JB-025", Severity.HIGH, 55, r'(?i)\b(sin\s+reglas|sin\s+restricciones|sin\s+l[ií]mites|sin\s+censura)\b', "ES: Sin reglas/restricciones/censura"),
        ("JB-026", Severity.HIGH, 55, r'(?i)\b(no\s+rules|no\s+restrictions|no\s+limits|uncensored|unfiltered)\b', "EN: No rules/restrictions/uncensored"),
        ("JB-027", Severity.HIGH, 55, r'(?i)\b(opposite\s+day|modo\s+opuesto|responde\s+al\s+rev[eé]s)\b', "Opposite day / reverse mode"),
        ("JB-028", Severity.HIGH, 55, r'(?i)\b(actually|realmente|en\s+realidad)\s+(you\s+can|puedes|tienes\s+permiso)\b', "Actually you can override"),
    ]
    for id_, sev, score, pattern, desc in JB:
        P.append(PatternEntry(id_, "jailbreak", sev, score, C(pattern), desc))

    # ── Category C: Harm Prevention (HS) ──────────────────────────
    HS = [
        ("HS-001", Severity.CRITICAL, 80, r'(?i)\b(da[nñ]ar|herir|matar|golpear|maltratar|envenenar|torturar|hacer\s+da[nñ]o)\s+(a\s+|al\s+)?(un([ao]s?)?|el|la|los|las|mi|tu|su|sus)?\s*(animal(es)?|perros?|gatos?|mascotas?|personas?|humanos?)\b', "ES: Daño/violencia hacia personas o animales"),
        ("HS-002", Severity.CRITICAL, 80, r'(?i)\b(harm|hurt|kill|abuse|poison|torture|strike)\s+(a\s+)?(an?|the|my|your|his|her|their)?\s*(animals?|pets?|dogs?|cats?|people|humans?)\b', "EN: Harm/violence towards humans or animals"),
    ]
    for id_, sev, score, pattern, desc in HS:
        P.append(PatternEntry(id_, "harm_prevention", sev, score, C(pattern), desc))

    return P


ALL_PATTERNS = _build_patterns()


# ============================================================
# Delimiter Patterns — Layer 3
# ============================================================
def _build_delimiter_patterns() -> List[PatternEntry]:
    C = re.compile
    DI = [
        ("DI-001", Severity.CRITICAL, 80, r'(?i)^\s*system:\s*', "Role injection: system: at start"),
        ("DI-002", Severity.CRITICAL, 80, r'(?i)\n\s*system:\s*', "Role injection: system: after newline"),
        ("DI-003", Severity.HIGH, 60, r'(?i)^\s*assistant:\s*', "Role injection: assistant: at start"),
        ("DI-004", Severity.HIGH, 60, r'(?i)\n\s*assistant:\s*', "Role injection: assistant: after newline"),
        ("DI-005", Severity.MEDIUM, 40, r'(?i)^\s*user:\s*', "Role injection: user: at start"),
        ("DI-006", Severity.CRITICAL, 85, r'(?i)<\|im_start\|>\s*system', "ChatML template injection: im_start system"),
        ("DI-007", Severity.CRITICAL, 85, r'(?i)<\|im_end\|>', "ChatML template injection: im_end"),
        ("DI-008", Severity.CRITICAL, 80, r'(?i)\{\s*"role"\s*:\s*"system"', "JSON role injection: system role"),
        ("DI-009", Severity.CRITICAL, 85, r'(?i)\[INST\].*\[/INST\]', "Llama template injection: [INST]"),
        ("DI-010", Severity.CRITICAL, 80, r'(?i)###\s*(System|Human|Assistant)\s*:', "Markdown role delimiter injection"),
        ("DI-011", Severity.CRITICAL, 85, r'(?i)<\|system\|>', "Special token injection: <|system|>"),
        ("DI-012", Severity.HIGH, 65, r'(?i)\[SYSTEM\]|\[ASSISTANT\]', "Bracket role marker: [SYSTEM]/[ASSISTANT]"),
        ("DI-013", Severity.CRITICAL, 85, r'(?i)<\|(system|assistant|user)\|>', "Special token injection: <|role|>"),
        ("DI-014", Severity.HIGH, 60, r'(?i)\{\{SYSTEM\}\}|\{\{ASSISTANT\}\}', "Template variable injection: {{SYSTEM}}"),
    ]
    return [PatternEntry(id_, "delimiter_injection", sev, score, C(pattern), desc)
            for id_, sev, score, pattern, desc in DI]


DELIMITER_PATTERNS = _build_delimiter_patterns()


# ============================================================
# Layer 1: FastRegexScanner
# ============================================================
class FastRegexScanner:
    def __init__(self, patterns: List[PatternEntry]):
        self.patterns = patterns

    def scan(self, text: str) -> List[Finding]:
        findings = []
        for entry in self.patterns:
            match = entry.regex.search(text)
            if match:
                findings.append(Finding(
                    category=entry.category,
                    pattern_id=entry.id,
                    description=entry.description,
                    severity=entry.severity,
                    score_contribution=entry.score,
                    matched_text=match.group()[:80]
                ))
        return findings


# ============================================================
# Layer 2: HeuristicScorer
# ============================================================
IMPERATIVE_VERBS_ES = {
    "ignora", "revela", "muestra", "dime", "olvida", "resetea", "omite",
    "cambia", "elimina", "destruye", "borra", "desactiva", "anula",
    "ejecuta", "compila", "genera", "imprime", "expulsa", "confirma",
    "repite", "traduce", "copia", "pega", "escribe", "declara",
    "extrae", "saca", "pasa", "salta", "omite", "desactiva",
}

IMPERATIVE_VERBS_EN = {
    "ignore", "reveal", "show", "tell", "forget", "reset", "override",
    "bypass", "disable", "delete", "destroy", "remove", "execute",
    "compile", "generate", "print", "output", "dump", "leak",
    "repeat", "translate", "copy", "paste", "write", "declare",
    "extract", "extract", "skip", "circumvent", "evade",
}


class HeuristicScorer:
    def score(self, text: str) -> List[Finding]:
        findings = []
        findings.extend(self._check_entropy(text))
        findings.extend(self._check_length_anomaly(text))
        findings.extend(self._check_imperative_density(text))
        findings.extend(self._check_question_bombardment(text))
        findings.extend(self._check_repetition(text))
        findings.extend(self._check_mixed_script(text))
        findings.extend(self._check_encoding_anomalies(text))
        return findings

    def _check_entropy(self, text: str) -> List[Finding]:
        if len(text) < 20:
            return []
        entropy = self._shannon_entropy(text)
        if entropy > 5.5:
            return [Finding("heuristic", "H-001", f"Entropía extremadamente alta ({entropy:.2f} bits/car)",
                            Severity.HIGH, 50, text[:80])]
        elif entropy > 5.0:
            return [Finding("heuristic", "H-001", f"Entropía alta ({entropy:.2f} bits/car)",
                            Severity.MEDIUM, 30, text[:80])]
        return []

    def _shannon_entropy(self, text: str) -> float:
        if not text:
            return 0.0
        freq = Counter(text)
        length = len(text)
        return -sum((c / length) * math.log2(c / length) for c in freq.values())

    def _check_length_anomaly(self, text: str) -> List[Finding]:
        length = len(text)
        if length > 10000:
            return [Finding("heuristic", "H-002", f"Entrada extremadamente larga ({length} chars)",
                            Severity.HIGH, 50, text[:80])]
        elif length > 5000:
            return [Finding("heuristic", "H-002", f"Entrada muy larga ({length} chars)",
                            Severity.MEDIUM, 30, text[:80])]
        elif length > MAX_INPUT_LENGTH:
            return [Finding("heuristic", "H-002", f"Entrada excede límite ({length} chars)",
                            Severity.LOW, 10, text[:80])]
        return []

    def _check_imperative_density(self, text: str) -> List[Finding]:
        words = set(text.lower().split())
        count = len(words & IMPERATIVE_VERBS_ES) + len(words & IMPERATIVE_VERBS_EN)
        if count >= 3:
            score = min(50, (count - 2) * 20)
            return [Finding("heuristic", "H-003",
                            f"Alta densidad de verbos imperativos ({count} encontrados)",
                            Severity.MEDIUM, score, text[:80])]
        return []

    def _check_question_bombardment(self, text: str) -> List[Finding]:
        q_count = text.count('?') + text.count('\u00bf')
        if q_count > 5:
            score = min(45, (q_count - 3) * 15)
            return [Finding("heuristic", "H-004",
                            f"Densidad excesiva de preguntas ({q_count})",
                            Severity.LOW, score, text[:80])]
        return []

    def _check_repetition(self, text: str) -> List[Finding]:
        if re.search(r'(.{20,}?)(\s*\1){2,}', text, re.DOTALL):
            return [Finding("heuristic", "H-005", "Patrón de texto repetido detectado",
                            Severity.MEDIUM, 35, text[:80])]
        if re.search(r'(.)\1{9,}', text):
            return [Finding("heuristic", "H-005", "Inundación de caracteres detectada",
                            Severity.LOW, 25, text[:80])]
        return []

    def _check_mixed_script(self, text: str) -> List[Finding]:
        if len(text) < 10:
            return []
        non_latin = sum(1 for c in text if (0x024F < ord(c) < 0x1E00) or (ord(c) > 0x1EFF))
        if len(text) > 0 and non_latin / len(text) > 0.3:
            return [Finding("heuristic", "H-006",
                            "Mezcla sospechosa de scripts no-latinos",
                            Severity.MEDIUM, 40, text[:80])]
        return []

    def _check_encoding_anomalies(self, text: str) -> List[Finding]:
        findings = []
        # Zero-width characters
        zw_count = sum(1 for c in text if c in '\u200b\u200c\u200d\ufeff\u2060\u180e')
        if zw_count > 0:
            findings.append(Finding("heuristic", "ET-004",
                                    f"Caracteres de ancho cero detectados ({zw_count})",
                                    Severity.HIGH, 55, text[:80]))
        # Base64-like strings
        if re.search(r'[A-Za-z0-9+/]{40,}={0,2}', text):
            findings.append(Finding("heuristic", "ET-001",
                                    "Cadena codificada en Base64 detectada",
                                    Severity.HIGH, 50, text[:80]))
        # Excessive hex encoding
        if len(re.findall(r'\\x[0-9a-fA-F]{2}', text)) >= 3:
            findings.append(Finding("heuristic", "ET-005",
                                    "Codificación hex excesiva detectada",
                                    Severity.HIGH, 50, text[:80]))
        return findings


# ============================================================
# Layer 3: DelimiterInjectionDetector
# ============================================================
class DelimiterInjectionDetector:
    def __init__(self):
        self.patterns = DELIMITER_PATTERNS

    def detect(self, text: str) -> List[Finding]:
        findings = []
        for entry in self.patterns:
            match = entry.regex.search(text)
            if match:
                findings.append(Finding(
                    category="delimiter_injection",
                    pattern_id=entry.id,
                    description=entry.description,
                    severity=entry.severity,
                    score_contribution=entry.score,
                    matched_text=match.group()[:80]
                ))
        return findings


# ============================================================
# Audit Logger
# ============================================================
class GuardrailLogger:
    def __init__(self):
        self.logger = logging.getLogger("guardrails")
        self.logger.setLevel(logging.DEBUG)

        if not self.logger.handlers:
            console = logging.StreamHandler()
            console.setLevel(logging.INFO)
            console.setFormatter(logging.Formatter('[GUARDRAILS] %(levelname)s: %(message)s'))
            self.logger.addHandler(console)

            try:
                os.makedirs(os.path.dirname(LOG_FILE) or ".", exist_ok=True)
                fh = logging.handlers.RotatingFileHandler(
                    LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
                )
                fh.setLevel(logging.DEBUG)
                fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
                self.logger.addHandler(fh)
            except OSError:
                self.logger.warning(f"No se pudo crear log en {LOG_FILE}, modo consola únicamente")

    def log(self, result: GuardrailResult, original_text: str):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "blocked" if result.blocked else "passed",
            "score": result.score,
            "threshold": GUARDRAILS_THRESHOLD,
            "layer_scores": result.layer_breakdown,
            "reasons": result.reasons,
            "input_preview": original_text[:120],
            "input_length": len(original_text),
            "finding_ids": [f.pattern_id for f in result.findings],
        }

        if result.blocked:
            level = "CRITICAL" if result.score >= 80 else "HIGH" if result.score >= 70 else "BLOCKED"
            self.logger.warning(f"[{level}] score={result.score} | {json.dumps(log_entry, ensure_ascii=False)}")
        else:
            self.logger.debug(f"[PASS] score={result.score} | len={len(original_text)}")


# ============================================================
# Scoring Pipeline (orchestrator)
# ============================================================
class GuardrailPipeline:
    def __init__(self):
        self.regex_scanner = FastRegexScanner(ALL_PATTERNS)
        self.heuristic_scorer = HeuristicScorer()
        self.delimiter_detector = DelimiterInjectionDetector()
        self.logger = GuardrailLogger()

    def analyze(self, text: str) -> GuardrailResult:
        if not text or not isinstance(text, str):
            return GuardrailResult(blocked=False, score=0, reasons=[], response="")

        normalized = text.strip()

        # Absolute length hard-block
        if len(normalized) > MAX_INPUT_LENGTH * 5:
            result = GuardrailResult(
                blocked=True, score=100,
                reasons=[f"Entrada excede longitud absoluta ({len(normalized)} chars)"],
                response=DEFENSIVE_RESPONSE,
                layer_breakdown={"regex": 0, "heuristic": 100, "delimiter": 0},
            )
            self.logger.log(result, normalized)
            return result

        # Layer 1: Fast regex
        l1_findings = self.regex_scanner.scan(normalized)
        l1_score = sum(f.score_contribution for f in l1_findings) * LAYER_WEIGHTS["regex"]

        # Early exit: HIGH or CRITICAL regex match → block immediately
        has_high_or_critical = any(
            f.severity in (Severity.HIGH, Severity.CRITICAL) for f in l1_findings
        )
        if has_high_or_critical:
            result = self._build_result(l1_findings, [], [], normalized, l1_score, 0, 0)
            result.blocked = True
            result.score = min(100, int(l1_score))
            result.reasons = [f.description for f in l1_findings]
            result.response = DEFENSIVE_RESPONSE
            self.logger.log(result, normalized)
            return result

        # Layer 2: Heuristics
        l2_findings = self.heuristic_scorer.score(normalized)
        l2_score = sum(f.score_contribution for f in l2_findings) * LAYER_WEIGHTS["heuristic"]

        # Layer 3: Delimiter injection
        l3_findings = self.delimiter_detector.detect(normalized)
        l3_score = sum(f.score_contribution for f in l3_findings) * LAYER_WEIGHTS["delimiter"]

        total_score = min(100, int(l1_score + l2_score + l3_score))
        all_findings = l1_findings + l2_findings + l3_findings

        result = self._build_result(l1_findings, l2_findings, l3_findings,
                                     normalized, l1_score, l2_score, l3_score)
        result.score = total_score
        result.blocked = total_score >= GUARDRAILS_THRESHOLD
        result.reasons = [f.description for f in all_findings]
        result.response = DEFENSIVE_RESPONSE if result.blocked else ""

        self.logger.log(result, normalized)
        return result

    def _build_result(self, l1, l2, l3, text, s1, s2, s3):
        return GuardrailResult(
            blocked=False, score=0, reasons=[], response="",
            findings=l1 + l2 + l3,
            layer_breakdown={"regex": int(s1), "heuristic": int(s2), "delimiter": int(s3)},
        )


# ============================================================
# Singleton & Public API
# ============================================================
_pipeline = GuardrailPipeline()


def validar_entrada(texto: str) -> Tuple[bool, Optional[str]]:
    """
    Analiza el texto contra el pipeline de guardrails.
    Retorna (True, mensaje_error) si se bloquea, (False, None) si pasa.
    Mantener compatibilidad con la API existente.
    """
    result = _pipeline.analyze(texto)
    return result.blocked, result.response if result.blocked else None


# ============================================================
# FastAPI Middleware
# ============================================================
async def middleware_guardrails(request, call_next):
    """Middleware HTTP que intercepta endpoints de chat antes del LLM."""
    if request.method == "POST" and request.url.path in ("/api/chat", "/api/chat/stream"):
        try:
            body = await request.json()
            pregunta = body.get("question", "")

            result = _pipeline.analyze(pregunta)
            if result.blocked:
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=403,
                    content={
                        "blocked": True,
                        "score": result.score,
                        "reasons": result.reasons,
                        "response": DEFENSIVE_RESPONSE,
                    },
                )
        except Exception:
            pass

    response = await call_next(request)
    return response
