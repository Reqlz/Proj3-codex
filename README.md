# Starstruck Atelier

A Tkinter idle game framed by a parchment alchemist’s journal. Restore a luminous sanctuary, specialise its workshop, trade with a celestial courier, and carry Moon Seals into a new beginning. Artwork and moth animation are generated locally with Pillow. Offline by default, with an optional online-service scaffold. No bundled music.

## Setup and launch

Use Python 3.10+ with Tkinter, Pillow and pygame-ce:

```powershell
cd Proj3-codex
python -m pip install -r requirements.txt
python main.py
```

If Python is not on PATH, use your IDE’s interpreter, or on the development machine:

```powershell
& 'C:\Users\tobyf\AppData\Local\Python\pythoncore-3.14-64\python.exe' main.py
```

Importing `main.py` does not open a window. The Windows Python installer includes Tkinter; Linux may need `python3-tk`.

## Controls and first steps

- Choose one of three named sanctuaries. **Sanctuaries** saves before returning to the archive. Each slot has independent progress and offline production.
- Follow the ten-step spotlight tour: purchase stations, read stock and net income, select the illustrated Garden, discover research and the Workshop, then preview converters and Reawakening. Replay from Settings or the Tome. Later discoveries introduce themselves with dismissible lessons: click their highlighted control or hover over the highlighted area briefly to acknowledge them. Action steps still require their actual action; the Suggested next step card explains shortages and useful waiting.
- Buy stations using Mana. **×1 / ×10 / MAX** selects purchase quantity. Click an illustrated station for its card; scroll the journal for later stations.
- Research buys three inscriptions, each doubling production. Appearance progresses **Weathered → Restored → Awakened → Masterwork**. The final two both display Level 3 with distinct finishing effects.
- **F11** toggles fullscreen. **Escape** closes the foremost dialog, Tome, or Settings first, otherwise exits fullscreen. First launch is fullscreen; subsequent launches remember your preference and window size. Minimum window: 1100×720.
- **Settings**, available from archive and gameplay, contains 30/60 FPS, reduced motion, effect density, celestial visitors, music and help. Preferences are global across slots.
- **Spell Tome** has contextual chapters and gold unread markers. **View all chapters** previews future systems without unlocking gameplay. Read previews remain read.
- Hover the circled information icon beside each resource for its concise material role. The Tome contains the full guide.

The apprentice spark and Spirit Wells make Mana independently. The automatic chain is:

**Gardens → Shards → Distilleries → Essence → Crucibles → Elixirs → Circles → Stardust**

Each Essence consumes 3 Shards (2.7 with Tideglass), each Elixir 4 Essence, each Stardust 5 Elixirs. Converters slow when ingredients run short. The top strip shows net inventory change; station cards show actual gross output and maximum capacity. Too many converters can consume all upstream surplus.

The five-minute purchase simulation unlocks distillation at 10 minutes, potions at 35, and astral production at 85. First Reawakening takes 165 minutes; the next run takes 175 with a Dawn memory legacy bonus. These are reference strategies, not enforced timers. Production needs no clicking and cannot deadlock because the apprentice always makes Mana.

## Materials and the Workshop

| Material | Identity | Main uses |
|---|---|---|
| Mana | Funds the work | Stations, crafting fees, transmutation |
| Shards | Physical construction | Restoration projects and charm bodies |
| Essence | Enchantment and specialisation | Charm targets/modes and spell tree |
| Elixirs | Sustaining magic | Charm infusion and recharging |
| Stardust | Reawakening | Prestige, research, Star Compass |

One **Workshop** landing page introduces activities gradually: first research reveals Charms and Construction; a Distillery reveals Enchantments and Transmutation; a Crucible reveals Infusion & Recharge; its second inscription reveals Deliveries; an Astral Circle reveals the Workbench. Talismans unlock individually through first inscriptions. New activities add a journal note and unread Tome chapter.

### Charms

Hold at most one charm per resource. The physical two-row Astral Cabinet is clickable in the sanctuary and displays equipped charms. Start each run with **one base place plus legacy places**. Build two shelf expansions in Construction for **600 Mana + 120 Shards**, then **2,400 Mana + 600 Shards**, before construction discounts. Each adds one place for the current run. The first two Astral cabinet legacy choices permanently unlock the fourth and fifth positions; the third unlocks the sixth as an Astral Lantern. Stored charms do not tick. Equipping starts their clock; confirmed dismantling gives no refund.

| Tier | Unlock | Gentle, 60 minutes | Intense, 15 minutes | Construction | Infusion | First refill |
|---|---|---|---|---|---|---|
| I | First research | +10% | +25% | 300 Mana + 40 Shards | 15 Elixirs | 10 Elixirs |
| II | Own Distillery | +20% | +50% | 1,800 Mana + 180 Shards | 60 Elixirs | 25 Elixirs |
| III | Own Crucible | +30% | +75% | 9,000 Mana + 700 Shards | 240 Elixirs | 60 Elixirs |
| IV | Own Circle | +40% | +100% | 40,000 Mana + 2,000 Shards | 960 Elixirs | 150 Elixirs |

Own the target station. Mana and Shard targeting needs no Essence. Targeting Essence, Elixirs, or Stardust adds **8, 20, or 50 Essence × tier** respectively.

- **Online:** works and ticks while the slot is loaded, including minimized. No mode surcharge.
- **Offline:** works and ticks only away. Own a Distillery; add 10/40/120/300 Essence by tier.
- **Combined:** works and ticks in both cases. Own a Crucible; add 25/100/300/800 Essence by tier.

No generic mode multipliers or ordinary charm Stardust costs. Construction, Enchantment and optional Infusion are separately labelled. Ingredients are checked together; failed crafting spends nothing.

Own a Crucible to add optional Elixir **infusion**, increasing initial duration by 50%, or **recharge** an equipped, unexpired charm. Recharge restores its crafted maximum rather than banking time. The page shows time gained, current cost and next cost. Each refill doubles that charm’s next price; Charmcraft’s capstone changes growth to ×1.6. Expired charms disappear; replacements start at the base price. Crafted potency and full duration remain fixed after later spell purchases.

### Essence spell tree

Each of three branches has nine nodes: a three-rank root, two three-rank specialisations, two advanced nodes, the former capstone (now a milestone), two further upgrades and a stronger final capstone. Roots cost 250/750/2,250 Essence; specialisations 1,000/3,000/9,000; advanced nodes 5,000; milestones 25,000. Root rank one unlocks specialisations; their second ranks unlock advanced nodes; both advanced nodes unlock the milestone. Late prices and effects are listed below. Skills reset at Reawakening; existing purchases remain effective after migration.

| Branch | Root per rank | Specialisation A per rank | Specialisation B per rank | Capstone |
|---|---|---|---|---|
| Charmcraft | −5% charm ingredients | +10% new charm duration | +5 percentage points potency | Refill growth ×1.6 |
| Deliveries | +10% Mana payout | Gift: 1/2/3 minutes’ baseline gross output | −1 minute cooldown | Two contract choices |
| Sanctuary | −5% construction costs | +1 percentage point restoration bonus | −10% transmutation Mana fees | +10% Mana production |

### Construction and transmutation

Each project has **five levels**, granting **+5/10/15/20/25% production**. Sanctuary spells add their extra percentage points once per built project. Own its associated station and complete a research inscription. Every upgrade adds terrace detail; all levels reset at Reawakening. The table below lists Level I prices. Later levels cost **6× the previous Shards and 2× the previous Mana**, before skill discounts. The full workshop contains 25 construction upgrades.

| Project | Resource | Mana + Shards |
|---|---|---|
| Lantern Path | Mana | 600 + 100 |
| Crystal Planters | Shards | 1,800 + 400 |
| Glasswork Shelves | Essence | 6,000 + 1,600 |
| Hearth Mosaic | Elixirs | 16,000 + 6,400 |
| Celestial Inlay | Stardust | 45,000 + 25,000 |

Reverse transmutation has only these lossy recipes. Own the source station, choose **1 / 100 / 1,000 / 10,000 / MAX**, and review input/output totals:

- 1 Stardust + 500 Mana → 3 Elixirs
- 1 Elixir + 100 Mana → 2 Essence
- 1 Essence + 25 Mana → 2 Shards

Recovered materials never count as production or prestige earnings.

### Celestial deliveries

After the Crucible’s second inscription, a courier offers an untimed contract requesting **two intermediate materials**, never Mana or Stardust. Quantities use 12–18 minutes of sustainable net output with empty intermediate inventories and no temporary boosts. At least two of Shards, Essence and Elixirs must have positive surplus; otherwise the board explains the bottleneck.

Mana payment equals **20 minutes of baseline Mana production**, including permanent run bonuses and Moon Seals, plus Delivery spell bonuses. Requests and rewards are saved snapshots: improving production never moves an existing target. Material gifts use an owned, unrequested intermediate’s gross output. Rewards do not add to prestige counters.

Completing or declining starts a **15-minute cooldown**, reduced to 12 by early spells and 10 by the late Moonroad routes upgrade. Cooldowns pass offline, but offers never accumulate. The original milestone offers two alternatives; completing either removes both. A seeded delivery-enabled reference run preserves early unlock timing, reaches Reawakening in approximately 165 minutes with banked-Stardust accounting. Crafting and visits remain optional; the crafting reference strategy also finishes in approximately 165 minutes.

### Talismans and astral attunement

All owned talismans work together without timers or cabinet places. Each grants +20% to its resource, rising to +25/+30/+35% at attunement ranks 1/2/3. Their first-inscription unlocks and base recipes are unchanged.

| Talisman | Base recipe | Build ability |
|---|---|---|
| Dawn Vessel | 1,200 Mana + 600 Shards + 20 Essence | Station Mana costs −10%; an active Mana charm links +10% Shards |
| Violet Crown | 2,500 Mana + 1,200 Shards + 40 Essence | Construction Shards −15%; a built project adds 2 percentage points to its resource's active charm |
| Tideglass | 6,000 Mana + 150 Shards + 400 Essence + 6 Elixirs | Distilleries use 2.7 Shards per Essence; an active Shard charm links +10% Essence |
| Ember Heart | 15,000 Mana + 300 Shards + 80 Essence + 120 Elixirs | New charms gain 20% base duration; refills cost −15%; an active Essence charm links +10% Elixirs |
| Star Compass | 35,000 Mana + 800 Shards + 160 Essence + 30 Elixirs + 45 Stardust | An active Elixir charm links +10% Stardust; three active charm targets grant +10% all resources |

Bonuses add before Moon Seal multiplication. Discounts multiply with existing discounts and round upward once. Existing charm potency and maximum duration never change retrospectively.

**Astral connection:** route from START to END over visible connections, visiting every marked star without revisiting. Attunements add ordered rune checkpoints, blocked connections, then alternating sun-circle and moon-diamond stars. Seeded layouts contain optional branches and decoys with a guaranteed solution. Free hints find a continuation or explain how far to backtrack. There is no timer or penalty for mistakes.

Binding charges the base recipe only on confirmation. Three optional attunements cost 50%, 100%, and 200% of that recipe, rounded upward per ingredient. Ownership, current rank, solution, and funds are rechecked before payment. A slot saves its current challenge and route; reopening the same talisman resumes it. Starting a different challenge replaces that unfinished route. Maximum-rank talismans offer free practice without rewards or upkeep.

**Carry one:** at Reawakening explicitly choose one talisman, or Keep none. The chosen talisman retains full mastery. Every unchosen talisman's stored mastery loses one rank (3→2, 2→1, 1→0), including currently uncrafted talismans. Unchosen items are lost; recrafting restores remaining mastery. The confirmation previews item losses and rank changes.

### Temporary charm patterns

Choose a pattern in addition to the existing tier, duration, activity mode, and infusion. Patterns have the same ingredient price and cabinet rules.

- **Standard:** 100% of crafted potency to its target.
- **Relay:** 75% to its target and 25% to the next resource in Mana → Shards → Essence → Elixirs → Stardust. Requires a Distillery; cannot target Stardust.
- **Chorus:** 75% to its target and 10% to each other distinct resource with an active charm. Requires a Crucible.

These percentages divide the crafted potency, including spell bonuses. Only equipped, unexpired charms in the relevant Online/Offline/Combined mode count as active. Secondary bonuses never trigger additional links. Stored and inactive charms do not supply synergies. Cards, information icons, and resource details explain current effects.

## Celestial visitor

An ivory-and-lavender moth visits after 2–4 minutes of visible sanctuary time once two resources are available. The smaller sprite fades in from beyond the scene edge and has a slightly larger clickable area. A quiet arrival notice appears briefly. Click it during its 15-second crossing to choose between two random resources, each independently offering +15/20/25/30/40/50% for two online minutes. The untimed choice is saved; reopening cannot reroll or claim twice.

One blessing can be active, stacking with crafting without taking a hook. It pauses away from the slot. Visit scheduling pauses in Settings, archive, Tome, dialogs and minimized windows. Missing a moth costs nothing. Reduced motion uses a stationary fading pose. The trail is kept short and subtle.

Charm, talisman, construction and blessing bonuses add per resource, then multiply by Moon Seals. Mana boosts affect the apprentice spark; ingredient ratios never change.

## Add your own music

1. Copy `.ogg`, `.mp3`, or `.wav` tracks into **`Proj3-codex/assets/music/`**.
2. Edit that folder’s `playlist.json`, using exact filenames:

   ```json
   {
     "tracks": [
       "night-garden.ogg",
       "starlight.mp3"
     ]
   }
   ```

3. Open **Settings → Audio → Reload playlist**.
4. Enable music and set volume. Pause/Resume, Next and ordered/shuffled playback are available.

Use double quotation marks. Commas separate entries; no comma follows the final filename. Spelling and extensions must match your files. Example tracks are not included. **Practice:** add a second song, reload, then swap their order and reload with Shuffle off.

The playlist loops continuously through slot switches. Tracks stream locally through pygame-ce; nothing is uploaded. Missing files, malformed JSON or unavailable audio hardware produce Settings messages while gameplay continues silently. See [the music-folder guide](assets/music/README.md) for more examples.

## Reawakening, saves and compatibility

Own every station and reach the current run’s Stardust goal. The first is 120; later goals rise. Deposit stored Stardust in Reawakening; spending the remaining stock does not reduce deposited progress. Receive `floor((3 + completed_Reawakenings // 3) × sqrt(deposited Stardust / current_goal))` Moon Seals. Repeated deposits can exceed storage capacity.

The ritual clears Mana/materials, stations, research, charms, construction, all spell ranks, delivery offers/cooldowns, workbench cooldowns, lantern charge and blessings. Choose **zero or one talisman to retain**; unselected ones are explicitly listed as lost. Keep permanent legacies and cabinet unlocks, Moon Seals, discoveries, tutorial/reading history, lifetime records and global preferences.

Versioned JSON saves use atomic replacement and per-slot last-good backups. Autosave runs every 30 seconds, after purchases and other gameplay transactions, after offline loading, and on exit. Switching is blocked if saving fails.

- Windows: `%LOCALAPPDATA%\StarstruckAtelier\slot-1.json` through `slot-3.json`
- Other platforms: `~/.local/share/StarstruckAtelier/slot-1.json` through `slot-3.json`
- Global preferences: `settings.json` in the same folder

The archive has New, Continue, Rename and confirmed Delete. Invalid primaries recover from their `.backup.json` with an explanation. If both copies fail, originals are preserved and a fresh start is offered. Deletion removes only the chosen primary and backup.

Moonveil saves migrate to the first empty slot, preserving originals; a marker prevents reimporting deleted progress. Save versions 1–11 upgrade to version 12 without losing resources, research, talismans, legacies or reading history. Saves older than version 9 start existing talismans at attunement rank zero; old charms become Standard without changes to potency or timers. Returning players receive an update lesson. The one-item retention limit takes effect at their next Reawakening. Legacy charms keep potency, remaining time and original full duration, with Tier II refill pricing. Existing reduced motion carries into initial global preferences.

Offline production has no time limit, but storage capacity bounds material accumulation. There are no automatic purchases/resets. The piecewise solver handles full storage, ingredient depletion and boost expiry identically online/offline. Full converters pause without wasting ingredients. Online blessings pause offline. Negative clock differences award nothing. Local wall-clock time is trusted.

## Verification

```powershell
python -m unittest -v test_game test_workshop test_branching test_rebirth test_future
python verify_ui.py --capture verification
python verify_windows.py
```

Unit tests cover economy and optional progression, every spell node, material roles, atomic payment, charm modes/refills/expiry, delivery snapshots/cooldowns, migrations/backups, tutorial/Tome, encounter rewards, audio errors and preferences. The GUI walkthrough uses temporary saves and covers supported sizes, fullscreen, workshop pages, moth clicks, four station stages, scrolling, puzzles, retention, and actual playback of a temporary generated WAV. Windows is required for screenshots; omit `--capture` elsewhere.

Economy and persistence remain in `main.py`; `presentation.py` holds shared window/control/cursor presentation and `spell_graph.py` renders the tree. All modules are import-safe. Tuning is centralised in `BUILDINGS`, recipes, `TREE` and `PRESTIGE_TARGET`. Baseline station prices and production doublings are unchanged.


## Branching spells and parchment windows

**Workshop → Enchantments** opens a separate, connected 27-node constellation in an indigo astral void. Three branches radiate from the central star. Circular nodes show icons and multi-rank counts; hover for names or select a node to open its parchment detail card on the right. Drag the starfield to pan, use the wheel or +/− to zoom, and use Fit tree or Centre selected to recover your view. Click a node to compare current and next effects, prerequisites, holdings and missing ingredients. Only the explicit purchase button spends materials. All branches remain eventually purchasable.

Secondary ingredients, in addition to the Essence prices above:

| Branch | Root ranks | First specialisation | Second specialisation | Capstone |
|---|---|---|---|---|
| Charmcraft | 250/750/2,250 Shards | 10/30/90 Elixirs | 1,000/3,000/9,000 Shards | 10,000 Shards + 200 Elixirs |
| Deliveries | 250/750/2,250 Shards | 10/30/90 Elixirs | 500/1,500/4,500 Shards | 8,000 Shards + 150 Elixirs |
| Sanctuary | 1,000/3,000/9,000 Shards | 1,000/3,000/9,000 Shards | Essence only | 20,000 Shards |

Each new advanced node has one rank, costing 5,000 Essence plus:

| Node | Effect | Additional cost |
|---|---|---|
| Lasting Infusion | Newly infused charms receive +75% duration instead of +50% | 80 Elixirs |
| Crystal Cutting | Another 15 percentage points off charm Shard costs | 6,000 Shards |
| Generous Parcels | Supplementary delivery gifts +50% | 80 Elixirs |
| Efficient Packing | Future contract requests −10% | 6,000 Shards |
| Resonant Masonry | Another +2 percentage points to built construction bonuses | 10,000 Shards |
| Careful Recovery | Reverse-transmutation output +20%, still lossy | 80 Elixirs |

Focused five-minute purchase simulations reach each branch's milestone at **135–145 minutes**, with most of that branch purchased by the **165-minute** first Reawakening. Prioritising rank-two paths and saving for the milestone achieves this; buying all rank-three specialisations first delays it.

The main game and auxiliary windows have centred parchment title bars. Dragging, resizing and maximising are disabled. The main window retains minimise, taskbar behaviour and save-on-close. Auxiliary windows are built hidden, centred, then raised above the game. On Windows they retain managed ownership while native caption changes and painting are suppressed, preventing ghost popups and frame flicker. Fullscreen hides the main title strip; F11 and Settings still switch display mode.

Clicking the game behind an auxiliary window closes only the foremost popup and consumes that click. Switching apps preserves it. Escape and outside clicks never approve deletion, Reawakening or discarding an unsaved sanctuary. Unfinished puzzles cancel without payment; celestial choices remain saved. Opening the tree replaces the Tome and vice versa.

Buttons highlight on hover and depress while held; release outside to cancel. Tab cycles controls on the focused Canvas and Enter/Space activates the focused control. Successful purchases display a brief teal confirmation. Reduced motion removes movement while retaining hover and pressed states.

Settings includes **System/Celestial cursor** and **station motifs**. The celestial pointer becomes a droplet, crystal, flask, vial or astral star over an established station, keeping the same pointing tip. Text and resizing retain conventional cursors. Windows cursor files are generated locally in the application-data folder; other platforms use system cursors.

### Long-term construction prices

| Project | Level I Shards | Level II | Level III | Level IV | Level V |
|---|---:|---:|---:|---:|---:|
| Lantern Path | 100 | 600 | 3,600 | 21,600 | 129,600 |
| Crystal Planters | 400 | 2,400 | 14,400 | 86,400 | 518,400 |
| Glasswork Shelves | 1,600 | 9,600 | 57,600 | 345,600 | 2,073,600 |
| Hearth Mosaic | 6,400 | 38,400 | 230,400 | 1,382,400 | 8,294,400 |
| Celestial Inlay | 25,000 | 150,000 | 900,000 | 5,400,000 | 32,400,000 |

These are prices for each individual level, not cumulative totals. Existing constructed projects migrate to Level I with their original bonus intact. Later levels are optional goals for long runs; no construction purchase is required to Reawaken.


## Rising Reawakenings and permanent memories

Reawakenings 1–6 award **1 / 1 / 2 / 2 / 3 / 3 permanent legacy points**; later Reawakenings award three each. Select the first memory before confirming the reset, then allocate remaining points afterwards or leave them unclaimed. Cancelling either page spends nothing. These bonuses add to crafting/construction bonuses before the Moon Seal multiplier.

| Memory | Permanent bonus per choice | Available at Reawakening |
|---|---|---:|
| Dawn | +5% Mana | 1 |
| Crystal | +5% Shards | 1 |
| Tide | +5% Essence | 1 |
| Ember | +5% Elixirs | 2 |
| Astral | +5% Stardust | 3 |
| Moonweaver | +2% all resources | 5 |

Stardust goals for runs 1–12 are **120, 280, 520, 1,590, 3,960, 8,130, 13,500, 20,300, 29,500, 40,100, 51,800, 68,000**. Beyond that, goals continue on a cubic curve: `ceil(68000 × (1 + (completed_Reawakenings − 11) / 11)^3 / 100) × 100`. There are no enforced timers. The reference strategy purchasing every five minutes and choosing Dawn memory takes approximately **185–240 minutes** for its first eight runs. Different upgrades, retained talismans and choices can change those timings.

Base seal rewards increase from three to four after three completed Reawakenings, then to five after six, and so on. Waiting past the goal still grants extra seals with square-root scaling.

Migration leaves an existing save’s current 120-Stardust goal and Moon Seals untouched; higher goals begin after its next reset. Previous Reawakenings grant unclaimed legacy choices, redeemable from the Reawakening page without resetting. Legacy counts and unclaimed choices survive future resets.

Activity gates apply inside the purchase logic, not just the interface: Delivery enchantments require an owned Crucible with its second inscription, and Lasting Infusion requires the Crucible’s infusion activity. Locked nodes explain the missing unlock; existing purchased upgrades are preserved.

## Extended workshop and permanent cabinet

The Astral cabinet legacy choice unlocks at the second Reawakening and can be selected three times. Its first two selections add charm places, keeping the one-per-target restriction. The third unlocks an **Astral Lantern** in the sixth place. Charge it with **10 held Stardust** for **+10% all production for 20 minutes**, online and offline. It cannot be recharged before expiry or bank unused charges. Reawakening extinguishes the Lantern and clears both Construction shelf upgrades. Permanent cabinet places remain unlocked.

Infusion now scales separately from refill pricing: **15 / 60 / 240 / 960 Elixirs** before Charmcraft discounts. Existing charms retain potency, remaining time and crafted maximum duration.

### Beyond the spell milestones

Each branch extends its original milestone with two single-rank upgrades and a final capstone. The two upgrades require the milestone and an Astral Circle. The final capstone requires both upgrades and **three completed Reawakenings**. All choices remain nonexclusive. Existing contract snapshots and crafted charm stats stay fixed.

| Purchase | Essence | Shards | Elixirs | Stardust |
|---|---:|---:|---:|---:|
| First late upgrade | 50,000 | 20,000 | 500 | 75 |
| Second late upgrade | 100,000 | 50,000 | 1,000 | 150 |
| Final capstone | 250,000 | 100,000 | 2,500 | 500 |

| Branch | First upgrade | Second upgrade | Final capstone |
|---|---|---|---|
| Charmcraft | New duration: +50% of base | New potency: +20 percentage points | New potency: another +25 percentage points |
| Deliveries | Future Mana payouts: +50% of baseline | Future cooldowns: -2 minutes, minimum 10 minutes | Future requests: another -30% materials |
| Sanctuary | Shards: +50% production | Built construction: another +5 percentage points | All production: +25% |

These are extended-run goals. A third-awakening reference run can afford its first late Sanctuary upgrade after 24 hours, using lossy reverse conversion to recover Elixirs for crafting; completing the whole tree requires longer investment. The optional new systems do not raise the baseline first-Reawakening requirement.

### Moonlit workbench

Owning an Astral Circle unlocks two repeatable trades in **Workshop > Workbench**:

- **Stardust to Mana:** pay five minutes of baseline gross Stardust production, rounded up with a minimum of 5, for **30 minutes of baseline Mana production**.
- **Quarry commission:** pay two minutes of baseline Mana production, rounded up, plus **2 Elixirs**, for **10 minutes of baseline gross Shard production**, rounded up with a minimum of 100.

Each trade has its own **20-minute cooldown**, saved across slot switches and progressing offline. No automatic trades or backlog. Quotes exclude charms, visitor blessings and the lantern; the complete payment and reward are displayed. Recovered materials and Mana do not inflate lifetime production or prestige counters. Spending stored Stardust does not affect committed deposits.

The reference five-minute strategy remains **165 minutes** without these activities. Quarry-only commissions also finish in 165 minutes; using both trades finishes in **150 minutes**. Individual choices and production balance change these timings.

### Paid memory reallocation

**Reawakening > Reallocate memories** previews a new allocation of all existing permanent choices. It costs **25% of the current Stardust goal, rounded up, minimum 100 Stardust**. No free resets. Unclaimed choices remain separate. Locked memories cannot receive points; the cabinet has a three-choice limit. To shrink the cabinet, dismantle any excess equipped charms first and let a lit lantern expire. Cancel, Escape and outside clicks charge nothing. Final confirmation checks the full allocation and affordability again before atomic payment.

### Help, ground and window fixes

Completing the opening tutorial offers an optional six-page materials walkthrough. Skip freely; its progress is per sanctuary and retained through Reawakening. Replay from **Settings > Help** or the Tome. Resource strips now use concise circled information tooltips.

A seeded grass texture covers the meadow beneath the sanctuary while preserving existing shrubs and terrace artwork. Fixed auxiliary windows use only the parchment frame, preventing Tk's native caption from reappearing during tree interaction.

## Overhaul verification

Run `python -m unittest discover -v` for economy, progression, migrations, seeded puzzles, hints, and learning-state checks. `python verify_overhaul.py` exercises real Tk windows at 1100×720, 1440×900, and fullscreen with temporary saves, writing captures under `verification/`. It requires a complete Tcl/Tk installation.

## Living sanctuary update

Each Reawakening embeds a stone in the central pedestal. Six empty sockets form the first ring; later stones continue around the base, with a compact ring count for long-running sanctuaries. Click the pedestal for progress and the next legacy-point reward. Small background constellations appear after Reawakenings 2, 4, and 6. Quiet plants and stones add detail without additional animated clutter.

**Optional station discoveries:** after 4–7 minutes of visible sanctuary time (five minutes for a fresh run), one owned, producing station may show a discovery marker for one minute. Click it to collect a saved snapshot of 20 seconds of that resource's gross output and open its normal production card. Missing it costs nothing. There is only one offer at a time; ordinary clicks cannot farm bonuses. Timers pause offline, while minimized, during guides, and while dialogs/Tome/settings are open. Gifts fill available storage, reporting overflow, and do not count as historical production. Stardust gifts enter storage and must be deposited manually to count toward prestige. Reawakening clears the offer.

**Information windows:** material information now explains purpose, production, and uses with a small flow diagram. Detailed stock and rates remain in the resource strip and Production cards. Related station, charm, cabinet, and talisman information also includes diagrams.

**Astral clarity:** legal next connections are highlighted, required stars are marked, and selected paths glow. Every generated board retains its guaranteed solution, including after restoring a saved route. After successful payment and saving, the traced constellation remains alone for a short flare before the window closes. Reduced motion uses a brief static completion display. Closing the animation never repeats or reverses the reward.

**Existing saves:** version 10 grants both Construction shelf levels for the current run, preserving previously available places and equipped charms. The next Reawakening uses the new shelf reset rule. Older Reawakenings receive the difference between the old and new legacy-point schedules as unclaimed points, once when the save migrates. Existing allocations, talismans, attunement, resources, and ongoing astral routes remain intact.

**Online groundwork:** [service setup](online_service/README.md) documents the disabled-by-default client and read-only API scaffold for atelier-api.reqlabs.co.uk. No game state is sent, local saves stay authoritative, and no VPS deployment is performed. Network failures do not interrupt gameplay.

Update validation: `python -m unittest discover` includes a six-run simulation that spends all 12 legacy points and reaches every distinct permanent upgrade without optional puzzles. `python verify_sanctuary.py` checks the new UI with temporary saves at 1100×720, 1440×900 and fullscreen; it requires a working Tcl/Tk installation.

## Storage and banked prestige

The sanctuary cabinet is now a freestanding wooden sprite beside the Crystal Garden, with depth, feet, a ground shadow, six visible places and equipped charms. Click it to open Charms.

Construction offers separate storage expansions after first research and ownership of the matching station. Base capacities are **250,000 Mana; 100,000 Shards; 15,000 Essence; 500 Elixirs**. Multiply these by `1 + 0.5 × completed Reawakenings`. Each ordinary material has ten doubling upgrades costing 10% of current capacity in that material. Stardust starts at the current Reawakening goal; three doubling upgrades reach **2×, 4×, and 8×** the goal, costing 25% of current capacity. Construction discounts apply. Purchased expansions reset each run; automatic capacity growth remains.

Full storage throttles production; converters consume only ingredients for actual output. Paid conversions, workbench trades and deliveries require room for the complete payout after payment. MAX transmutation accounts for free space. Free discoveries fill available room and report overflow.

Reawakening counts **manually deposited Stardust**. **Deposit to goal** commits only what is needed to fill the bar; **Deposit all** commits all held Stardust, including beyond the goal. Deposits free storage, cannot be withdrawn, and reset at Reawakening. They have no gameplay cap: storage limits unattended accumulation, while repeated visits and deposits can keep raising the reward. Buying research, spells or storage never reduces deposits. Production never deposits automatically.

Moon Seals give +10% production each through 250 owned Seals. Above that, effective Seals are `250 + 500 × (sqrt(1 + (seals − 250) / 250) − 1)`, capped at 10,000 effective Seals. Production is `1 + 0.1 × effective Seals`: 500 owned gives about 46.71×; 1,000 gives 76×; the distant ceiling is 1,001× at approximately 105,063 owned Seals. The owned Seal count is never reduced or capped.

Version 11 migration preserves all existing stocks, including surplus above the new limits, and queues a dismissible explanation. Surplus remains spendable, cannot accumulate further, and none counts toward prestige until manually deposited. New storage levels start at zero; slots remain independent.

Version 12 adds a separate saved deposit balance, initially zero for older saves. Existing Stardust stays in storage; migration neither removes it nor duplicates it as deposit credit. A dismissible update lesson explains the new buttons.

## Balance and readability update

The apprentice spark produces **2 Mana/second**. The first five Spirit Wells each receive **50% extra output**, including their research and resource bonuses. Later Wells keep their normal rates; bulk previews include the exact combined increase. Smaller ordinary storage limits unattended accumulation, with ten optional expansions for longer runs. Existing surplus and unlimited manual Stardust deposits remain intact.

Settings now have a persistent category sidebar. **Concise** is the default; **Classic** keeps additional explanations. Choose compact/full numbers, storage indicators, suggestions, tooltip delay, text size, contrast, motion, visitor cues and audio separately. Short tutorials offer **More detail** without adding stages. The Tome uses a resizable scrolling reading area and a separate walkthrough footer.

Each sanctuary saves its own **Moonlit Ruins**, **Reflecting Pond**, or **Glowing Hay Field** scenery. Motion preferences remain global; reduced motion overrides scenery animation without erasing individual choices. Visitor notices last for the visit and share the visitor's single capture action. Optional arrival chimes have their own volume and fail quietly when audio is unavailable.

Save version **13** adds scenery and preserves resources, storage expansions, deposits, charms and tutorial history. Old sanctuaries default to Moonlit Ruins.

Validation: use `python -m unittest discover` and `python -m compileall -q .`. UI verification requires complete Tcl/Tk libraries; headless tests are not visual or pointer checks.
