"""Pure seeded proposal planning shared by generation and RUN validation."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from . import catalog as cat, mutate, vocabulary as cv
from ._contract import bind_import_twin, oc, rng


@dataclass(frozen=True)
class Proposal:
    program: cat.Program
    record_id: str
    mutation: mutate.Mutation
    repaired: str
    index: int

    def binding(self) -> tuple:
        site = self.mutation.site
        return self.program.program_id, self.index, site.operator, site.as_json(), site.variant


def _sites_by_operator(program: cat.Program) -> dict[str, tuple[mutate.Site, ...]]:
    grouped: dict[str, list[mutate.Site]] = {}
    for site in mutate.sites(program.text, program.function, program.want_kind):
        grouped.setdefault(site.operator, []).append(site)
    return {operator: tuple(found) for operator, found in grouped.items()}


class ProposalPlan:
    """One incremental DrawStream; syntax checks compile but never execute source."""

    def __init__(self, catalog: cat.Catalog, seed: int, cap: int):
        self.catalog, self.seed, self.cap = catalog, seed, cap
        self.stream = rng.DrawStream(seed)
        self.sites = {p.program_id: _sites_by_operator(p) for p in catalog.programs}
        self.per_program: Counter[str] = Counter()
        self.skips = Counter({cv.SKIP_MUTATION_NO_SITES: sum(not s for s in self.sites.values())})
        self.seen: set[tuple[str, str]] = set()

    def _draw_program(self) -> cat.Program | None:
        eligible = [p for p in self.catalog.programs
                    if self.sites[p.program_id] and self.per_program[p.program_id] < self.cap]
        return self.stream.choice(eligible) if eligible else None

    def _proposal(self, program: cat.Program, index: int) -> Proposal | str:
        by_operator = self.sites[program.program_id]
        operator = self.stream.choice(sorted(by_operator))
        site = mutate.choose(self.stream, by_operator[operator])
        mutated = mutate.apply(program.text, site)
        skip = mutate.verify(program.text, mutated, site, program.function)
        if skip is not None:
            return skip
        key = (program.program_id, cat.sha256_text(mutated))
        if key in self.seen:
            return cv.SKIP_DUPLICATE_MUTANT_IN_RUN
        self.seen.add(key)
        identity = cat.sha256_text(oc.canonical_json(
            [self.catalog.catalog_id, self.catalog.programs_sha256]))
        record_id = f"{cv.RECORD_ID_PREFIX}-{identity}-{self.seed}-{index:05d}"
        return Proposal(program, record_id, mutate.Mutation(site, program.text, mutated),
                        mutate.repair(mutated, site), index)

    def proposals(self, count: int):
        """Yield proposals in original draw order, retaining skips and cap accounting."""
        for index in range(count):
            program = self._draw_program()
            if program is None:
                self.skips[cv.SKIP_PROGRAM_CAP_EXHAUSTED] += count - index
                break
            outcome = self._proposal(program, index)
            if isinstance(outcome, str):
                self.skips[outcome] += 1
                continue
            yield outcome
            self.per_program[program.program_id] += 1


bind_import_twin(__name__)
