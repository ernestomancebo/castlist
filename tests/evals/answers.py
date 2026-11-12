"""Scripted answers for AskUserQuestion. Pure functions; no model involved."""


def _norm(text):
    return str(text or "").casefold()


def rule_matches(question, rule):
    """A rule's `when` keys must all match (case-insensitive substring).

    `header` / `question` match those fields; `text` matches either. An empty
    `when` matches any question (use it last, as a catch-all)."""
    when = rule.get("when", {})
    header, text = _norm(question.get("header")), _norm(question.get("question"))
    if "header" in when and _norm(when["header"]) not in header:
        return False
    if "question" in when and _norm(when["question"]) not in text:
        return False
    if "text" in when and _norm(when["text"]) not in header + " " + text:
        return False
    return True


def _label_for(select, options):
    """Pick the option whose label equals, else contains, `select`; else treat
    `select` as free text (the SDK takes free text in the label slot)."""
    labels = [o.get("label", "") for o in options]
    for label in labels:
        if _norm(label) == _norm(select):
            return label
    for label in labels:
        if _norm(select) in _norm(label):
            return label
    return select


def answer_for(question, rule):
    options = question.get("options", [])
    select = rule["select"]
    if isinstance(select, list):
        return [_label_for(s, options) for s in select]
    return _label_for(select, options)


def answer_questions(questions, rules):
    """Return (answers keyed by question text, list of unmatched question texts).

    An unmatched question is answered with its first option so the run can
    finish, but the caller must fail the step for it."""
    answers, unmatched = {}, []
    for q in questions:
        rule = next((r for r in rules if rule_matches(q, r)), None)
        if rule is None:
            unmatched.append(q.get("question", ""))
            options = q.get("options", [])
            answers[q["question"]] = options[0]["label"] if options else ""
        else:
            answers[q["question"]] = answer_for(q, rule)
    return answers, unmatched
