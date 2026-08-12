import re


def simpleagg_yesno(batch_answers):
    """
    Deterministic aggregation baseline for yes/no questions.

    Rules:
    1. Extract valid yes/no labels.
    2. Apply majority voting.
    3. Break ties using the earliest valid prediction.
    4. If no valid label exists, return "no".
    """
    labels = []

    for answer in batch_answers:
        if answer is None:
            continue

        match = re.search(r"\b(yes|no)\b", str(answer).lower())
        if match:
            labels.append(match.group(1))

    if not labels:
        return "no"

    yes_count = labels.count("yes")
    no_count = labels.count("no")

    if yes_count > no_count:
        return "yes"
    if no_count > yes_count:
        return "no"

    # Tie: earliest valid prediction
    return labels[0]


def simpleagg_entities(batch_candidates, max_candidates):
    """
    Deterministic aggregation baseline for factoid/list questions.

    Concatenates candidates in their original order and performs
    exact-string deduplication while preserving the first occurrence.
    """
    merged = []
    seen = set()

    for candidates in batch_candidates:
        if not candidates:
            continue

        for entity in candidates:
            entity = str(entity).strip()

            if not entity:
                continue

            if entity not in seen:
                seen.add(entity)
                merged.append(entity)

            if len(merged) >= max_candidates:
                return merged

    return merged


def simpleagg_factoid(batch_candidates):
    return simpleagg_entities(batch_candidates, max_candidates=5)


def simpleagg_list(batch_candidates):
    return simpleagg_entities(batch_candidates, max_candidates=100)