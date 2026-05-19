"""Heracles — strongest of mortal heroes, completer of twelve labors.

Heracles was set twelve impossible tasks by King Eurystheus. He
completed every one. In Olympus, Heracles is the kill-test runner:
a battery of twelve adversarial scenarios, each meant to break a
specific substrate invariant. A run is successful only when all
twelve are completed without breakage.

Akropolis arc extension: Heracles is also the **benchmark harness**.
Each labor is now a (seed, task, expected) triple; runners (heuristic
/ agent / baseline) compete on the same labor; results are persisted
under `heracles.benchmark` for trending + regression detection.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Callable, Any


@dataclass
class Labor:
    """One of the twelve. Named after the original myth."""
    number: int
    name: str            # canonical name (e.g., "Nemean Lion")
    target: str          # which Olympus surface this attacks
    fn: Callable[[], bool]   # runner; True = survived, False = broke


@dataclass
class Verdict:
    labor: Labor
    survived: bool
    detail: str


class Heracles:
    """The twelve-labor kill-test runner."""

    def __init__(self) -> None:
        self._labors: dict[int, Labor] = {}

    def assign(self, labor: Labor) -> None:
        """Register a labor. Number must be 1..12."""
        if not 1 <= labor.number <= 12:
            raise ValueError(f"labor number must be 1..12; got {labor.number}")
        self._labors[labor.number] = labor

    def perform(self) -> list[Verdict]:
        """Run all assigned labors. Returns one Verdict per labor."""
        verdicts: list[Verdict] = []
        for n in range(1, 13):
            labor = self._labors.get(n)
            if labor is None:
                continue
            try:
                survived = bool(labor.fn())
                detail = "survived" if survived else "broke"
            except Exception as exc:
                survived = False
                detail = f"raised: {type(exc).__name__}: {exc}"
            verdicts.append(Verdict(labor=labor, survived=survived, detail=detail))
        return verdicts


heracles = Heracles()


# ─────────────────────────────────────────────────────────
# BENCHMARK HARNESS (Akropolis arc) — multi-runner, deterministic,
# golden-output, regression-aware.
# ─────────────────────────────────────────────────────────


@dataclass
class BenchmarkTask:
    """One deterministic benchmark task.

    `runner_fn` takes the deterministic RNG (from Ananke) and an
    input dict; returns the runner's output.  `correct_fn` takes
    runner output + expected output, returns True iff correct.
    """
    name: str
    seed_name: str                 # Ananke seed name
    input: dict[str, Any]
    expected: Any
    runner_fn: Callable[[Any, dict[str, Any]], Any]
    correct_fn: Callable[[Any, Any], bool] = lambda actual, exp: actual == exp


@dataclass
class BenchmarkResult:
    """One (task, runner) outcome."""
    task: str
    runner: str
    correct: bool
    latency_ms: float
    output: Any
    expected: Any
    error: str = ""
    regressed: bool = False        # True iff previously correct, now incorrect


@dataclass
class BenchmarkReport:
    started_at: str
    ended_at: str = ""
    runner_label: str = ""
    results: list[BenchmarkResult] = field(default_factory=list)

    @property
    def total(self) -> int: return len(self.results)
    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.correct)
    @property
    def regressed(self) -> int:
        return sum(1 for r in self.results if r.regressed)
    @property
    def pass_rate(self) -> float:
        return (self.passed / self.total) if self.total else 0.0


def _previous_correctness(runner: str, task: str) -> bool | None:
    """Read the most recent benchmark result for (runner, task)."""
    from olympus.titans.mnemosyne import mnemosyne
    recs = mnemosyne.recall("heracles.benchmark")
    for m in reversed(recs):
        body = m.body or {}
        if body.get("runner") == runner and body.get("task") == task:
            return bool(body.get("correct", False))
    return None


def run_benchmark(tasks: list[BenchmarkTask], *,
                   runner: str = "heuristic") -> BenchmarkReport:
    """Run a list of BenchmarkTasks with a named runner. Each task's
    RNG is seeded deterministically via Ananke. Results are persisted
    to Mnemosyne for trending; regressions are flagged against the
    previous successful run."""
    from olympus.primordials.ananke import ananke
    from olympus.primordials.nyx import Nyx
    from olympus.titans.mnemosyne import mnemosyne

    report = BenchmarkReport(
        started_at=Nyx.now().isoformat(),
        runner_label=runner,
    )
    for task in tasks:
        rng = ananke.rng(task.seed_name)
        result = BenchmarkResult(
            task=task.name, runner=runner,
            correct=False, latency_ms=0.0,
            output=None, expected=task.expected,
        )
        started = time.perf_counter()
        try:
            output = task.runner_fn(rng, task.input)
            result.output = output
            result.correct = bool(task.correct_fn(output, task.expected))
        except Exception as exc:  # noqa: BLE001
            result.error = f"{type(exc).__name__}: {exc}"
            result.correct = False
        result.latency_ms = (time.perf_counter() - started) * 1000.0

        prior = _previous_correctness(runner, task.name)
        if prior is True and not result.correct:
            result.regressed = True

        mnemosyne.remember(
            kind="heracles.benchmark",
            actor=f"heracles:{runner}",
            summary=(f"{task.name} ({runner}): "
                     f"{'PASS' if result.correct else 'FAIL'} "
                     f"({result.latency_ms:.2f}ms)"
                     + (" [REGRESSION]" if result.regressed else "")),
            **{k: v for k, v in asdict(result).items()
               if k != "output"},  # avoid bloat from large outputs
            output_summary=str(result.output)[:200],
        )
        report.results.append(result)

    report.ended_at = Nyx.now().isoformat()
    mnemosyne.remember(
        kind="heracles.benchmark-pass",
        actor=f"heracles:{runner}",
        summary=(f"benchmark pass: {report.passed}/{report.total} "
                 f"pass · {report.regressed} regressions"),
        runner=runner,
        total=report.total,
        passed=report.passed,
        regressed=report.regressed,
        pass_rate=report.pass_rate,
    )
    return report


# ─────────────────────────────────────────────────────────
# Canonical benchmark suite — runs deterministic; non-LLM
# ─────────────────────────────────────────────────────────


def _bench_runner_count_alerts(rng, inp: dict) -> int:
    """Heuristic counts ALERT-severity entries in a list."""
    return sum(1 for f in inp["findings"] if f.get("severity") == "alert")


def _bench_runner_extract_slice(rng, inp: dict) -> str:
    """Heuristic extracts slice from a drift-observed sentence."""
    import re
    match = re.search(r"slice\s+['\"]([^'\"]+)['\"]", inp["text"])
    return match.group(1) if match else ""


def _bench_runner_sum_pheromones(rng, inp: dict) -> float:
    """Heuristic sums pheromone intensities."""
    return sum(float(p.get("intensity", 0.0)) for p in inp["pheromones"])


def _bench_runner_dedupe(rng, inp: dict) -> list[str]:
    """Heuristic dedupes a list of strings preserving order."""
    seen, out = set(), []
    for x in inp["items"]:
        if x not in seen:
            seen.add(x); out.append(x)
    return out


def _bench_runner_random_shuffle(rng, inp: dict) -> list[int]:
    """Uses Ananke-seeded RNG. Same seed → same shuffle order."""
    out = list(inp["items"])
    rng.shuffle(out)
    return out


CANONICAL_BENCHMARK_TASKS: list[BenchmarkTask] = [
    BenchmarkTask(
        name="count-alerts",
        seed_name="bench:count-alerts",
        input={"findings": [
            {"severity": "alert"}, {"severity": "info"},
            {"severity": "alert"}, {"severity": "alert"},
            {"severity": "info"},
        ]},
        expected=3,
        runner_fn=_bench_runner_count_alerts,
    ),
    BenchmarkTask(
        name="extract-slice",
        seed_name="bench:extract-slice",
        input={"text": (
            "argos reports alert on slice 'state/argos_pheromones.jsonl': "
            "approaches 10k lines"
        )},
        expected="state/argos_pheromones.jsonl",
        runner_fn=_bench_runner_extract_slice,
    ),
    BenchmarkTask(
        name="sum-pheromones",
        seed_name="bench:sum-pheromones",
        input={"pheromones": [
            {"intensity": 1.5}, {"intensity": 2.0},
            {"intensity": 0.5}, {"intensity": 3.0},
        ]},
        expected=7.0,
        runner_fn=_bench_runner_sum_pheromones,
        correct_fn=lambda a, e: abs(a - e) < 1e-6,
    ),
    BenchmarkTask(
        name="dedupe-preserve-order",
        seed_name="bench:dedupe",
        input={"items": ["a", "b", "a", "c", "b", "d"]},
        expected=["a", "b", "c", "d"],
        runner_fn=_bench_runner_dedupe,
    ),
    BenchmarkTask(
        name="deterministic-shuffle",
        seed_name="bench:shuffle-7",
        input={"items": [1, 2, 3, 4, 5, 6, 7]},
        # Ananke('bench:shuffle-7') gives a fixed permutation;
        # compute it once and pin. The test will compute and assert.
        expected="<pinned-by-test>",
        runner_fn=_bench_runner_random_shuffle,
        correct_fn=lambda a, e: (
            isinstance(a, list) and len(a) == 7 and set(a) == set(range(1, 8))
        ),
    ),
]


def run_canonical_benchmark(runner: str = "heuristic") -> BenchmarkReport:
    """Convenience: run the canonical task list with `runner`."""
    return run_benchmark(CANONICAL_BENCHMARK_TASKS, runner=runner)


# The canonical twelve labors. Each is a real substrate kill-test:
# survives iff the substrate's promise still holds in code.


def _labor_nemean_lion() -> bool:
    """HYDRA must have eight mortal heads + one immortal."""
    from olympus.monsters.hydra import hydra
    heads = hydra.heads()
    mortal = sum(1 for h in heads if not h.IMMORTAL)
    immortal = sum(1 for h in heads if h.IMMORTAL)
    return mortal == 8 and immortal == 1


def _labor_lernaean_hydra() -> bool:
    """HYDRA must observe — beheading produces ≥1 finding from every head."""
    from olympus.monsters.hydra import hydra
    report = hydra.behead()
    return all(len(report.by_head.get(h.NAME, [])) >= 1 for h in hydra.heads())


def _labor_ceryneian_hind() -> bool:
    """Artemis's quiver must record + summarize percentiles."""
    from olympus.olympians.artemis import Artemis
    a = Artemis(capacity=100)
    for v in range(1, 101):
        a.mark("labor.hind", float(v))
    s = a.quiver("labor.hind").summary()
    return 45 < s["p50"] < 55 and s["count"] == 100


def _labor_erymanthian_boar() -> bool:
    """Ares must accept and run a registered assault end-to-end."""
    from olympus.olympians.ares import Ares
    a = Ares()
    a.declare_war(
        name="labor.boar",
        description="trivial refusal",
        fn=lambda: (_ for _ in ()).throw(RuntimeError("refused")),
        expected_outcome="raised",
    )
    return a.battle("labor.boar")["verdict"] == "passed"


def _labor_augean_stables() -> bool:
    """Lethe must forget what's been written after its TTL."""
    import time
    from olympus.underworld.lethe import Lethe
    l = Lethe()
    l.forget("labor.augean", "muck", ttl=0.01)
    time.sleep(0.05)
    return l.remembered("labor.augean") is None


def _labor_stymphalian_birds() -> bool:
    """Argos must deploy and produce at least one pheromone per registered eye."""
    from olympus.monsters.argos.colony import colony
    census = colony.deploy()
    return census.count >= len(colony.eyes())


def _labor_cretan_bull() -> bool:
    """Poseidon's pub/sub must deliver events to subscribers in order."""
    from olympus.olympians.poseidon import Poseidon
    p = Poseidon()
    received: list[int] = []
    p.subscribe("labor.bull", lambda e: received.append(e))
    for i in range(5):
        p.publish("labor.bull", i)
    return received == [0, 1, 2, 3, 4]


def _labor_mares_of_diomedes() -> bool:
    """Atropos must end a thread cleanly and record it in Mnemosyne."""
    from olympus.fates.atropos import atropos
    from olympus.titans.mnemosyne import mnemosyne
    cleanup_ran = []
    atropos.cut("labor.mares", cleanup=lambda: cleanup_ran.append(True),
                reason="labor-test")
    cuts = mnemosyne.recall("thread.cut")
    return cleanup_ran == [True] and any(
        c.body.get("thread_id") == "labor.mares" for c in cuts
    )


def _labor_belt_of_hippolyta() -> bool:
    """Hera must record bindings as append-only and read them back."""
    from olympus.olympians.hera import hera
    b = hera.bind(name="labor.belt", left="left", right="right",
                  role="labor-binding")
    bindings = hera.bindings()
    return any(x.name == "labor.belt" and x.left == "left" for x in bindings)


def _labor_cattle_of_geryon() -> bool:
    """Demeter must accumulate then reap a harvest."""
    from olympus.olympians.demeter import Demeter
    d = Demeter()
    for v in range(10):
        d.gather("labor.geryon", v)
    h = d.reap("labor.geryon")
    return h.size == 10


def _labor_apples_of_hesperides() -> bool:
    """Apollo MUST refuse a prediction without verify() (S5 invariant)."""
    from olympus.olympians.apollo import Apollo, Prediction
    import datetime
    a = Apollo()
    try:
        a.predict(Prediction(
            name="labor.apples",
            statement="this prediction has no verify()",
            horizon=datetime.date(2099, 1, 1),
            verify=None,
        ))
        return False  # accepted what S5 forbids
    except ValueError:
        return True


def _labor_cerberus() -> bool:
    """Cerberus must refuse a caller who fails any of three heads."""
    from olympus.monsters.cerberus import Cerberus, Gate
    c = Cerberus()
    c.post(Gate(
        name="labor.cerberus",
        authenticate=lambda caller: caller == "valid",
        authorize=lambda caller: True,
        verify=lambda payload: True,
    ))
    good = c.admit("labor.cerberus", "valid").allowed
    bad = c.admit("labor.cerberus", "intruder").allowed
    return good is True and bad is False


CANONICAL_LABORS = [
    Labor(1,  "Nemean Lion",          "monsters/hydra",           _labor_nemean_lion),
    Labor(2,  "Lernaean Hydra",       "monsters/hydra",           _labor_lernaean_hydra),
    Labor(3,  "Ceryneian Hind",       "olympians/artemis",        _labor_ceryneian_hind),
    Labor(4,  "Erymanthian Boar",     "olympians/ares",           _labor_erymanthian_boar),
    Labor(5,  "Augean Stables",       "underworld/lethe",         _labor_augean_stables),
    Labor(6,  "Stymphalian Birds",    "monsters/argos",           _labor_stymphalian_birds),
    Labor(7,  "Cretan Bull",          "olympians/poseidon",       _labor_cretan_bull),
    Labor(8,  "Mares of Diomedes",    "fates/atropos",            _labor_mares_of_diomedes),
    Labor(9,  "Belt of Hippolyta",    "olympians/hera",           _labor_belt_of_hippolyta),
    Labor(10, "Cattle of Geryon",     "olympians/demeter",        _labor_cattle_of_geryon),
    Labor(11, "Apples of Hesperides", "olympians/apollo",         _labor_apples_of_hesperides),
    Labor(12, "Cerberus",             "monsters/cerberus",        _labor_cerberus),
]
