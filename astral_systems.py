"""Shared charm descriptions and deterministic, UI-independent astral challenges."""
import math
import random

TALISMAN_NAMES = ("Dawn Vessel", "Violet Crown", "Tideglass", "Ember Heart", "Star Compass")
RESOURCE_NAMES = ("Mana", "Shards", "Essence", "Elixirs", "Stardust")
TALISMAN_ABILITIES = (
    "Stations cost 10% less Mana. An active Mana charm links +10% Shards.",
    "Construction costs 15% fewer Shards. A built project adds 2 percentage points to its active charm.",
    "Distilleries use 10% fewer Shards. An active Shard charm links +10% Essence.",
    "New charms gain 20% base duration; refills cost 15% less. An active Essence charm links +10% Elixirs.",
    "An active Elixir charm links +10% Stardust. Three active charm targets grant +10% all resources.",
)
PATTERNS = {
    "standard": "100% potency on its target. Available after first research.",
    "relay": "75% potency on its target; 25% on the next resource. Requires a Distillery; cannot target Stardust.",
    "chorus": "75% potency on its target; 10% on each other active charm target. Requires a Crucible.",
}
TALISMAN_BASE = .20
ATTUNEMENT_STEP = .05
DAWN_DISCOUNT = .10
VIOLET_DISCOUNT = .15
TIDE_EFFICIENCY = .10
EMBER_DURATION = .20
EMBER_DISCOUNT = .15
LINK_BONUS = .10
PROJECT_CHARM_BONUS = .02
ATTUNEMENT_PRICES = (.5, 1., 2.)

def charm_contributions(charm, active_targets, built=False):
    result = [0.] * 5
    target, potency = charm["target"], charm["bonus"]
    pattern = charm.get("pattern", "standard")
    result[target] = potency * (1 if pattern == "standard" else .75)
    if built:
        result[target] += PROJECT_CHARM_BONUS
    if pattern == "relay" and target < 4:
        result[target + 1] += potency * .25
    if pattern == "chorus":
        for other in active_targets - {target}:
            result[other] += potency * .10
    return result

def effect_text(values):
    return "; ".join(f"+{v*100:g}% {RESOURCE_NAMES[i]}" for i, v in enumerate(values) if v) or "No active production bonus"

class Constellation:
    """A seeded graph with a guaranteed route and optional branches, not an ordered-copy test."""
    def __init__(self, target, rank=0, seed=None, practice=False):
        if type(target) is not int or not 0 <= target < 5 or type(rank) is not int or not 0 <= rank <= 3:
            raise ValueError("Invalid challenge")
        self.target, self.rank, self.practice = target, rank, practice
        self.seed = random.randrange(2**31) if seed is None else seed
        rng = random.Random(self.seed)
        self.count = 7 + rank * 2 + (target % 2)
        self.order = list(range(self.count - 2))
        rng.shuffle(self.order)
        self.start, self.end = self.order[0], self.order[-1]
        self.required = set(self.order[1:-1:2])
        self.runes = self.order[2:-1:2] if rank else []
        self.required.update(self.runes)
        self.edges = {tuple(sorted((a, b))) for a, b in zip(self.order, self.order[1:])}
        self.colours = {star: pos % 2 for pos, star in enumerate(self.order)}
        for star in range(self.count):
            self.colours.setdefault(star, rng.randrange(2))
        # Extra edges create choices and alternative valid routes. The backbone is never blocked.
        for a in range(self.count):
            for b in range(a + 1, self.count):
                if rng.random() < .15:
                    self.edges.add((a, b))
        for decoy in range(self.count - 2, self.count):
            self.edges.add(tuple(sorted((decoy, rng.choice(self.order[1:-1])))))
        backbone = {tuple(sorted((a,b))) for a,b in zip(self.order,self.order[1:])}
        extras = sorted(self.edges - backbone)
        self.blocked = set(rng.sample(extras, min(rank - 1, len(extras)))) if rank >= 2 else set()
        # Jittered grid keeps labels apart, with shuffled labels and motifs varying each board.
        cells = list(range(self.count)); rng.shuffle(cells)
        cols = math.ceil(self.count / 3)
        self.points = [(-.88 + (cell % cols) * 1.76 / (cols-1) + rng.uniform(-.035,.035),
                        -.75 + (cell // cols) * .75 + rng.uniform(-.04,.04)) for cell in cells]
        self.path = []
        self.message = "Begin at START. Visit every marked star, then reach END."
        self.claimed = False

    @property
    def rules(self):
        text = "Follow connections; visit all ★ stars before END. Stars cannot be revisited."
        if self.rank: text += " Visit rune numbers in order."
        if self.rank >= 2: text += " Dashed red connections are blocked."
        if self.rank >= 3: text += " Alternate sun (○) and moon (◇) stars."
        return text

    def reason(self, star, path=None):
        path = self.path if path is None else path
        if type(star) is not int or not 0 <= star < self.count: return "Choose a star on this board."
        if not path: return "Begin at START." if star != self.start else ""
        if path[-1] == self.end: return "This route has ended. Undo to change it."
        if star in path: return "Stars cannot be revisited. Undo to try another branch."
        edge = tuple(sorted((path[-1], star)))
        if edge not in self.edges: return "Those stars have no connection."
        if edge in self.blocked: return "That connection is blocked. Find another route."
        if self.rank >= 3 and self.colours[star] == self.colours[path[-1]]: return "Alternate sun circles and moon diamonds."
        if star in self.runes and any(r not in path for r in self.runes[:self.runes.index(star)]):
            return "Visit the numbered runes in order."
        if star == self.end and not self.required.issubset(path): return "Visit every marked star before END."
        return ""

    @property
    def complete(self):
        if not self.path or self.path[-1] != self.end: return False
        return all(not self.reason(star, self.path[:i]) for i, star in enumerate(self.path))

    def select(self, star):
        self.message = self.reason(star)
        if self.message: return False
        self.path.append(star)
        self.message = "Route complete. Confirm below." if self.complete else f"{len(self.required.intersection(self.path))}/{len(self.required)} marked stars reached."
        return True

    def undo(self):
        if self.path: self.path.pop()

    def solution(self, path=None):
        initial = self.path[:] if path is None else path[:]
        failed = set()
        def visit(route):
            if route and route[-1] == self.end: return route
            key = (route[-1] if route else -1, frozenset(route))
            if key in failed: return None
            candidates = [self.start] if not route else sorted(b if a == route[-1] else a for a,b in self.edges if route[-1] in (a,b))
            for star in candidates:
                if not self.reason(star, route):
                    result = visit(route + [star])
                    if result is not None: return result
            failed.add(key)
            return None
        return visit(initial)

    def hint(self):
        if self.complete:
            self.message = "The route is complete."
            return None
        solution = self.solution()
        if solution:
            self.message = "The next star is framed in gold."
            return solution[len(self.path)]
        for count in range(len(self.path)-1, -1, -1):
            if self.solution(self.path[:count]):
                self.message = f"This branch cannot finish. Undo {len(self.path)-count} step(s), then ask again."
                return None
        return None

    def snapshot(self):
        return dict(target=self.target, rank=self.rank, seed=self.seed, practice=self.practice, path=self.path[:])

    @classmethod
    def restore(cls, data):
        if not isinstance(data,dict) or set(data) != {"target","rank","seed","practice","path"}: raise ValueError("Invalid astral challenge")
        if type(data["seed"]) is not int or not 0 <= data["seed"] < 2**31 or type(data["practice"]) is not bool: raise ValueError("Invalid challenge seed")
        puzzle = cls(data["target"],data["rank"],data["seed"],data["practice"])
        if not isinstance(data["path"],list) or len(data["path"]) > puzzle.count: raise ValueError("Invalid route")
        for star in data["path"]:
            if not puzzle.select(star): raise ValueError("Invalid saved route")
        return puzzle
