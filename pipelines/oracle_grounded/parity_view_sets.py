"""Set-level authentication of parity training-view batches.

Split out of ``parity_contract`` by responsibility; ``view_set_errors`` and
``catalog_batch_errors`` are re-exported from there. ``training_view_errors``
judges one view against one record; this module judges the whole batch: the
view set must be a faithful one-to-one image of the record set, and each round
of records must cover the fixed scenario catalog exactly once.
"""

from __future__ import annotations

from collections import Counter


def _non_string_ids(ids):
    """The entries that cannot serve as record or view identifiers."""
    return [item for item in ids if not isinstance(item, str)]


def _view_id_validity_errors(record_ids, view_ids, where):
    """Both sides must carry string IDs before they can be compared as sets."""
    errors = []
    invalid_view_ids = _non_string_ids(view_ids)
    if invalid_view_ids:
        errors.append(
            f"{where}: training view set contains invalid non-string view IDs "
            f"{invalid_view_ids!r} [TRAINING_VIEW_HIDES_FAILURE]"
        )
    invalid_record_ids = _non_string_ids(record_ids)
    if invalid_record_ids:
        errors.append(
            f"{where}: source record set contains invalid non-string IDs "
            f"{invalid_record_ids!r} [TRAINING_VIEW_HIDES_FAILURE]"
        )
    return errors


def _dropped_record_errors(record_ids, view_id_counts, where):
    """Every source record must still have a view."""
    # Only string record IDs are hashable-safe to check against view_id_counts;
    # a malformed ID (e.g. a list) is already reported by the validity pass and
    # must not reach `in` on a dict, which raises TypeError for unhashable keys.
    dropped = [rid for rid in record_ids if isinstance(rid, str) and rid not in view_id_counts]
    if not dropped:
        return []
    return [
        f"{where}: training view set drops records {dropped} "
        f"[TRAINING_VIEW_HIDES_FAILURE]"
    ]


def _orphan_view_errors(view_id_counts, record_id_set, where):
    """Every view must have a record behind it."""
    orphans = sorted(vid for vid in view_id_counts if vid not in record_id_set)
    if not orphans:
        return []
    return [
        f"{where}: training view set contains views with no record behind them: "
        f"{orphans} [TRAINING_VIEW_HIDES_FAILURE]"
    ]


def _duplicate_view_errors(view_id_counts, where):
    """A repeated view reweights the corpus away from what the oracles found."""
    duplicates = sorted(vid for vid, count in view_id_counts.items() if count > 1)
    if not duplicates:
        return []
    return [
        f"{where}: training view set repeats {duplicates}, which reweights the "
        f"corpus away from what the oracles found [TRAINING_VIEW_HIDES_FAILURE]"
    ]


def _view_id_mapping_errors(record_ids, view_ids, where):
    """Nothing dropped, nothing unsourced, nothing repeated."""
    record_id_set = {rid for rid in record_ids if isinstance(rid, str)}
    view_id_counts = Counter(vid for vid in view_ids if isinstance(vid, str))
    return (
        _dropped_record_errors(record_ids, view_id_counts, where)
        + _orphan_view_errors(view_id_counts, record_id_set, where)
        + _duplicate_view_errors(view_id_counts, where)
    )


def view_set_errors(records, views, where="training-view"):
    """The view set must be a faithful one-to-one image of the record set.

    Checking only that no record was dropped is not enough: duplicating the
    agreeable half of a corpus dilutes the failures just as effectively as
    deleting them, and a view with no record behind it is unsourced.
    """
    record_ids = [record.get("id") for record in records]
    view_ids = [view.get("id") for view in views]
    errors = _view_id_validity_errors(record_ids, view_ids, where)
    errors += _view_id_mapping_errors(record_ids, view_ids, where)
    return errors


def catalog_batch_errors(records, catalog_ids, where="training-view"):
    """Each round in the batch must cover the fixed scenario catalog exactly.

    `view_set_errors` proves the views mirror the records it was handed, but
    that is vacuous when the input file was already filtered: a batch with
    only the agreeable scenarios retained projects into a view set that
    passes every per-record and set check while silently omitting the
    failures the round actually produced. Generation always emits exactly
    one record per catalog scenario per round, so that catalog is the ground
    truth this authentication replays. Callers run it only after per-record
    validation, which is what binds each record's scenario id and round to
    its own evidence.
    """
    expected = Counter(catalog_ids)
    scenario_ids_by_round = _scenario_ids_by_round(records)
    if not scenario_ids_by_round:
        return [
            f"{where}: no records to project; a training-view batch must carry "
            "at least one complete catalog round [TRAINING_VIEW_HIDES_FAILURE]"
        ]
    return [
        _round_coverage_error(round_number, got, expected, where)
        for round_number, got in sorted(
            scenario_ids_by_round.items(), key=lambda item: repr(item[0])
        )
        if got != expected
    ]


def _declared_field(record, section, key):
    """``record[section][key]`` when both levels are objects, else ``None``."""
    block = record.get(section) if isinstance(record, dict) else None
    return block.get(key) if isinstance(block, dict) else None


def _scenario_ids_by_round(records):
    """Count each declared scenario id per declared round."""
    scenario_ids_by_round = {}
    for record in records:
        round_number = _declared_field(record, "meta", "round")
        scenario_id = _declared_field(record, "scenario", "id")
        scenario_ids_by_round.setdefault(round_number, Counter())[scenario_id] += 1
    return scenario_ids_by_round


def _round_coverage_error(round_number, got, expected, where):
    """Describe how one round's scenario ids diverge from the catalog."""
    missing = sorted((expected - got).elements(), key=repr)
    surplus = sorted((got - expected).elements(), key=repr)
    detail = []
    if missing:
        detail.append(f"missing catalog scenarios {missing}")
    if surplus:
        detail.append(f"carrying scenarios outside the catalog count {surplus}")
    return (
        f"{where}: round {round_number!r} does not cover the scenario catalog "
        f"exactly once ({'; '.join(detail)}); a filtered batch cannot be "
        "projected into training views [TRAINING_VIEW_HIDES_FAILURE]"
    )
