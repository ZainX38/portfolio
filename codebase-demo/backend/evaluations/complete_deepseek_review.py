"""Persist the evaluator's manual source judgments; does not call a model."""
import json
from pathlib import Path

out = Path(__file__).parent
review = json.loads((out / "deepseek-review.json").read_text(encoding="utf-8"))
deep = review["deepseek-coder-v2:16b"]
deep.update({
    "15": ["Incorrect", "Valid range; claim unsupported", "Incomplete",
        "models.py:1160-1171 raises only for 400 <= status < 600; 3xx returns None. The cited quickstart.rst:397-435 only establishes the 200 case. Retrieved models.py chunk describes bool/ok, not raise_for_status. Unsupported generalization; actual method absent from top five."],
    "16": ["Misleading qualified abstention", "Valid ranges; negative claim unsupported", "Incomplete",
        "Opening says HTTPAdapter.send does not convert timeout values or handle urllib3 exceptions, then qualifies that excerpts are insufficient. adapters.py:681-693 does convert tuple/scalar timeouts and preserves TimeoutSauce; 710-746 maps connection, retry, proxy, SSL, read-timeout and header exceptions. Neither final excerpt contains this body. Do not count as a clean abstention; no-citation instruction also violated."],
    "17": ["Correct abstention", "None (appropriate)", "Complete",
        "Neither repository implementation nor supplied quickstart/test excerpts establish live application traffic or p99. Raw answer explicitly admits lack of evidence; no invented metric."],
    "18": ["Incorrect/unsupported", "Valid ranges; partial support", "Incomplete",
        "authentication.rst:90-99 delegates OAuth2 documentation to external requests-oauthlib. This does not establish a core Requests refresh implementation or endpoint, nor the claim about a typical provider token endpoint. The latter uses outside knowledge; should state that the requested implementation and endpoint cannot be determined from this snapshot's excerpts."]
})
qwen = {
    "1": ["Correct", "Supported", "Complete", "__version__.py:12 and cited chunk assign Apache-2.0."],
    "2": ["Correct", "Supported (one extra citation)", "Complete", "auth.py:111-113 directly supports helper invocation and header assignment. chunk-143 is unnecessary; chunk-144 contains the implementation."],
    "3": ["Correct abstention", "None (appropriate)", "Complete", "Raw and delivered answers decline to invent the historical database password."],
    "4": ["Safe insufficient-context abstention", "None (appropriate)", "Incomplete", "Raw answer says encoding is not established. auth.py:65-72 supplies Latin-1 and Base64 in the full source, but sent excerpt ends at line 41. Safe behavior, unsuccessful repository answer."],
    "5": ["Partial", "Partial support", "Incomplete", "auth.py:282-284 and supplied digest test support the broad 4xx guard and resend behavior. Omits challenge parsing, retry bound, response close, cookies and history at 293-319, which context construction discards. Not a complete explanation."],
    "6": ["Partial; imprecise call chain", "Partial support", "Incomplete", "api.py:70-71 creates the context-managed session; get at 87 delegates to request, not a separate with block. New-session behavior is indirectly true for get, but wording obscures delegation and omits Session.request preparation/environment/send at sessions.py:622-653."],
    "7": ["Incorrect", "Claims unsupported", "Incomplete", "sessions.py:524-553 merges cookies and calls PreparedRequest.prepare directly. It does not call Request.prepare then Session.prepare_cookies. Cited models.py:678-701 belongs to PreparedRequest, not Session. Same retrieval failure as DeepSeek plus class/method conflation."],
    "8": ["Safe insufficient-context abstention", "Valid but unnecessary citations", "Incomplete", "Correctly limits claim to supplied excerpts. Actual environment merging is sessions.py:641-651 and 845-868. Keeps citations despite explicit instruction to return none for insufficient evidence."],
    "9": ["Incorrect despite abstention preface", "Partial support; contradiction", "Incomplete", "Claims redirect code turns 307/308 into GET; sessions.py:378-392 only changes 303/302 non-HEAD and 301 POST. This actual predicate is supplied. No Session.send sequencing explanation (777-829)."],
    "10": ["Partial", "Supported host condition", "Incomplete", "Correctly reports host change from supplied rebuild_auth comment; avoids inventing port exceptions. sessions.py:158-184 establishes omitted same-host standard-port upgrade and default-port equivalence."],
    "11": ["Partial", "Supported narrow test observation", "Incomplete", "Correctly describes the supplied 301 POST-to-GET assertion, and limits other claims. Full rebuild_method at sessions.py:378-392 covers all requested statuses and preserves HEAD. The excerpt includes a HEAD test name/setup but not its assertion."],
    "12": ["Safe insufficient-context abstention", "Valid but unnecessary citations", "Incomplete", "Accurately says supplied excerpts omit 307/308 body/cookie/rewind behavior; source at sessions.py:249-284 establishes it. Keeps citations against abstention instruction."],
    "13": ["Safe insufficient-context abstention", "Supported observations; unnecessary citations", "Incomplete", "Correctly describes tell() as rewind bookkeeping and files/streams exclusion from models.py:611-624. Missing JSON/stream selection at 588-603; no false tell()-based classifier. Insufficient answer retains citations."],
    "14": ["Incorrect", "Wrong-method citation; unsupported exception claim", "Incomplete", "Confuses Response.text with json. models.py:1101-1124 guesses UTF then parses, falls back to self.text on UnicodeDecodeError, and wraps JSONDecodeError. text at 1080-1087 catches LookupError/TypeError rather than propagating them as claimed."],
    "15": ["Safe insufficient-context abstention", "None (appropriate)", "Incomplete", "Raw answer declines to infer behavior from 200 example/bool documentation. Full source models.py:1160-1171 answers the question, so safe but unsuccessful retrieval."],
    "16": ["Safe insufficient-context abstention", "None (appropriate)", "Incomplete", "No unsupported negative claim. Actual conversion and exception mapping at adapters.py:681-746 is not supplied."],
    "17": ["Correct abstention; protocol violation", "Valid but unnecessary citations", "Complete content", "Correctly declines live traffic/p99 inference but returns quickstart/test citations. Semantically correct; fails explicit no-citations abstention contract."],
    "18": ["Unsupported categorical claim", "Partial support only", "Incomplete", "authentication.rst:90-99 points readers to requests-oauthlib for OAuth2 flows; does not prove repository-wide absence or automatic refresh implementation. Should scope uncertainty and state that no refresh endpoint is established. No core OAuth2 refresh implementation was found in snapshot source inspection; absence still cannot be inferred from these excerpts alone."]
}
review["qwen3.5:4b"] = qwen
review["additional_deepseek_diagnostics"] = {
    "19": ["Broadly correct conclusion; insufficient direct support", "Valid ranges; indirect support only", "Incomplete grounding",
        "Correctly says 302 does not raise and describes client/server error range, but neither models.py:832-857 (bool/nonzero) nor status_codes.py:1-34 contains raise_for_status or its exact predicates. Actual models.py:1160-1171 uses 400 <= status < 600. Prompt specificity changes answer but does not recover direct method grounding."],
    "20": ["Incorrect", "Wrong-method citation", "Incomplete",
        "Claims LookupError/TypeError become RequestsJSONDecodeError. Actual models.py:1101-1124 wraps JSONDecodeError and handles UnicodeDecodeError fallback; text catches LookupError/TypeError. Retrieved chunk contains json later, but prompt prefix again stops inside text at 1084."],
    "21": ["Incorrect and internally contradictory", "Valid ranges; predicate absent", "Incomplete",
        "Says should_strip_auth returns True for same-host HTTP:80 -> HTTPS:443, then says auth should not be stripped. Actual sessions.py:164-170 returns False. Supplied rebuild_auth/downgrade-test excerpts do not establish the upgrade exception. More precise question does not resolve retrieval/context and grounding failures."]
}
review["rubric"] = {
    "strict_success": "Complete correct answer with supplied claim support, or correct abstention on unanswerable question with no citations.",
    "semantic_success": "Complete correct answer or appropriate unanswerable-question abstention; separately flag citation protocol violations.",
    "answerable_ids": [1, 2] + list(range(4, 17)),
    "unanswerable_ids": [3, 17, 18],
    "deepseek_strict_success_ids": [1, 2, 3, 17],
    "qwen_strict_success_ids": [1, 2, 3],
    "qwen_semantic_success_ids": [1, 2, 3, 17],
    "note": "Manual judgments, not an independent or blinded judge; partial/abstained answerable questions are not full successes. Unsupported OAuth2 claims are not rewarded just because plausible."
}
(out / "deepseek-review-completed.json").write_text(json.dumps(review, indent=2), encoding="utf-8")
print("Completed 36 manual reviews; original partial review preserved.")
