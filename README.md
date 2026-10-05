# Starstruck Atelier

A Tkinter idle game framed by a parchment alchemist’s journal. Restore a luminous sanctuary, specialise its workshop, trade with a celestial courier, and carry Moon Seals into a new beginning. Artwork and moth animation are generated locally with Pillow. No network services or bundled music.

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
- Follow the skippable tutorial: buy a Well, observe Mana, plant a Garden, select its scene object, and open the Tome. Replay from Settings or the Tome.
- Buy stations using Mana. **×1 / ×10 / MAX** selects purchase quantity. Click an illustrated station for its card; scroll the journal for later stations.
- Research buys three inscriptions, each doubling production. Appearance progresses **Weathered → Restored → Awakened → Masterwork**. The final two both display Level 3 with distinct finishing effects.
- **F11** toggles fullscreen. **Escape** closes the foremost dialog, Tome, or Settings first, otherwise exits fullscreen. First launch is fullscreen; subsequent launches remember your preference and window size. Minimum window: 1100×720.
- **Settings**, available from archive and gameplay, contains 30/60 FPS, reduced motion, effect density, celestial visitors, music and help. Preferences are global across slots.
- **Spell Tome** has contextual chapters and gold unread markers. **View all chapters** previews future systems without unlocking gameplay. Read previews remain read.
- Hover over controls for tips. **Uses** on each resource opens its material guide and workshop.

The apprentice spark and Spirit Wells make Mana independently. The automatic chain is:

**Gardens → Shards → Distilleries → Essence → Crucibles → Elixirs → Circles → Stardust**

Each Essence consumes 3 Shards, each Elixir 4 Essence, each Stardust 5 Elixirs. Converters slow when ingredients run short. The top strip shows net inventory change; station cards show actual gross output and maximum capacity. Too many converters can consume all upstream surplus.

The five-minute purchase simulation unlocks distillation at 10 minutes, potions at 35, and astral production at 85. First Reawakening takes 165 minutes; the next run takes 175 with a Dawn memory legacy bonus. These are reference strategies, not enforced timers. Production needs no clicking and cannot deadlock because the apprentice always makes Mana.

## Materials and the Workshop

| Material | Identity | Main uses |
|---|---|---|
| Mana | Funds the work | Stations, crafting fees, transmutation |
| Shards | Physical construction | Restoration projects and charm bodies |
| Essence | Enchantment and specialisation | Charm targets/modes and spell tree |
| Elixirs | Sustaining magic | Charm infusion and recharging |
| Stardust | Reawakening | Prestige, research, Star Compass |

One **Workshop** landing page introduces activities gradually: first research reveals Charms and Construction; a Distillery reveals Enchantments and Transmutation; a Crucible reveals Infusion & Recharge; its second inscription reveals Deliveries. Talismans unlock individually through first inscriptions. New activities add a journal note and unread Tome chapter.

### Charms

Hold at most one charm per resource, with three different equipped charms. Stored charms do not tick. Equipping starts their clock; confirmed dismantling gives no refund.

| Tier | Unlock | Gentle, 60 minutes | Intense, 15 minutes | Construction | Infusion / first refill |
|---|---|---|---|---|---|
| I | First research | +10% | +25% | 300 Mana + 40 Shards | 10 Elixirs |
| II | Own Distillery | +20% | +50% | 1,800 Mana + 180 Shards | 25 Elixirs |
| III | Own Crucible | +30% | +75% | 9,000 Mana + 700 Shards | 60 Elixirs |
| IV | Own Circle | +40% | +100% | 40,000 Mana + 2,000 Shards | 150 Elixirs |

Own the target station. Mana and Shard targeting needs no Essence. Targeting Essence, Elixirs, or Stardust adds **8, 20, or 50 Essence × tier** respectively.

- **Online:** works and ticks while the slot is loaded, including minimized. No mode surcharge.
- **Offline:** works and ticks only away. Own a Distillery; add 10/40/120/300 Essence by tier.
- **Combined:** works and ticks in both cases. Own a Crucible; add 25/100/300/800 Essence by tier.

No generic mode multipliers or ordinary charm Stardust costs. Construction, Enchantment and optional Infusion are separately labelled. Ingredients are checked together; failed crafting spends nothing.

Own a Crucible to add optional Elixir **infusion**, increasing initial duration by 50%, or **recharge** an equipped, unexpired charm. Recharge restores its crafted maximum rather than banking time. The page shows time gained, current cost and next cost. Each refill doubles that charm’s next price; Charmcraft’s capstone changes growth to ×1.6. Expired charms disappear; replacements start at the base price. Crafted potency and full duration remain fixed after later spell purchases.

### Essence spell tree

Each branch has a three-rank root, two three-rank specialisations, and one capstone. Roots cost **250/750/2,250 Essence**, specialisations **1,000/3,000/9,000**, advanced nodes **5,000**, and capstones **25,000**. One root rank reveals specialisations; rank two in a specialisation unlocks its advanced node. Both advanced nodes unlock the capstone. All ranks reset at Reawakening. Existing ranks and purchased capstones remain yours after upgrading.

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

Reverse transmutation has only these lossy recipes. Own the source station, choose 1/10/Max, and review input/output totals:

- 1 Stardust + 50 Mana → 3 Elixirs
- 1 Elixir + 15 Mana → 2 Essence
- 1 Essence + 5 Mana → 2 Shards

Recovered materials never count as production or prestige earnings.

### Celestial deliveries

After the Crucible’s second inscription, a courier offers an untimed contract requesting **two intermediate materials**, never Mana or Stardust. Quantities use 12–18 minutes of sustainable net output with empty intermediate inventories and no temporary boosts. At least two of Shards, Essence and Elixirs must have positive surplus; otherwise the board explains the bottleneck.

Mana payment equals **20 minutes of baseline Mana production**, including permanent run bonuses and Moon Seals, plus Delivery spell bonuses. Requests and rewards are saved snapshots: improving production never moves an existing target. Material gifts use an owned, unrequested intermediate’s gross output. Rewards do not add to prestige counters.

Completing or declining starts a **15-minute cooldown**, reduced to 12 by spells. Cooldowns pass offline, but offers never accumulate. The capstone offers two alternatives; completing either removes both. A seeded delivery-enabled reference run preserves early unlock timing, adds about **1.02 million Mana**, and reaches Reawakening in 155 minutes. Crafting and visits remain optional; the crafting reference strategy finishes in 145 minutes.

### Talismans

All owned talismans are active and grant +20% to their resource. Their recipes unlock through the associated first research inscription and remain discoverable after rebirth.

| Talisman | Recipe |
|---|---|
| Dawn Vessel | 1,200 Mana + 600 Shards + 20 Essence |
| Violet Crown | 2,500 Mana + 1,200 Shards + 40 Essence |
| Tideglass | 6,000 Mana + 150 Shards + 400 Essence + 6 Elixirs |
| Ember Heart | 15,000 Mana + 300 Shards + 80 Essence + 120 Elixirs |
| Star Compass | 35,000 Mana + 800 Shards + 160 Essence + 30 Elixirs + 45 Stardust |

Trace the visible 6–10-star reference by clicking stars. Undo, Reset, Hint, mistakes and cancellation are free. **Bind talisman** rechecks ownership and all materials before paying. Existing talismans remain owned after upgrading the game.

## Celestial visitor

An ivory-and-lavender moth visits after 2–4 minutes of visible sanctuary time once two resources are available. Click its wings during its 15-second crossing to choose between two random resources, each independently offering +15/20/25/30/40/50% for two online minutes. The untimed choice is saved; reopening cannot reroll or claim twice.

One blessing can be active, stacking with crafting without taking a hook. It pauses away from the slot. Visit scheduling pauses in Settings, archive, Tome, dialogs and minimized windows. Missing a moth costs nothing. Reduced motion uses a stationary pose; density changes its trail.

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

Own every station and reach the current run’s Stardust goal. The first is 120; later goals rise. Spent Stardust still counts. Receive `floor((3 + completed_Reawakenings // 3) × sqrt(run-earned Stardust / current_goal))` Moon Seals. Each cumulative seal still adds 10% production.

The ritual clears Mana/materials, stations, research, charms, construction, spell ranks, delivery offers/cooldowns and blessings. Choose **zero to three talismans to retain**; unselected ones are explicitly listed as lost. Keep Moon Seals, discoveries, reading history, lifetime records and global preferences.

Versioned JSON saves use atomic replacement and per-slot last-good backups. Autosave runs every 30 seconds, after purchases and other gameplay transactions, after offline loading, and on exit. Switching is blocked if saving fails.

- Windows: `%LOCALAPPDATA%\StarstruckAtelier\slot-1.json` through `slot-3.json`
- Other platforms: `~/.local/share/StarstruckAtelier/slot-1.json` through `slot-3.json`
- Global preferences: `settings.json` in the same folder

The archive has New, Continue, Rename and confirmed Delete. Invalid primaries recover from their `.backup.json` with an explanation. If both copies fail, originals are preserved and a fresh start is offered. Deletion removes only the chosen primary and backup.

Moonveil saves migrate to the first empty slot, preserving originals; a marker prevents reimporting deleted progress. Save versions 1–6 upgrade without losing resources, research, talismans or reading history. Legacy charms keep potency, remaining time and original full duration, with Tier II refill pricing. Existing reduced motion carries into initial global preferences.

Offline earnings are full-rate and uncapped, with no automatic purchases/resets. The piecewise solver handles ingredient depletion and boost expiry identically online/offline. Online blessings pause offline. Negative clock differences award nothing. Local wall-clock time is trusted.

## Verification

```powershell
python -m unittest -v test_game test_workshop test_branching test_rebirth
python verify_ui.py --capture verification
```

Unit tests cover economy and optional progression, every spell node, material roles, atomic payment, charm modes/refills/expiry, delivery snapshots/cooldowns, migrations/backups, tutorial/Tome, encounter rewards, audio errors and preferences. The GUI walkthrough uses temporary saves and covers supported sizes, fullscreen, workshop pages, moth clicks, four station stages, scrolling, puzzles, retention, and actual playback of a temporary generated WAV. Windows is required for screenshots; omit `--capture` elsewhere.

Economy and persistence remain in `main.py`; `presentation.py` holds shared window/control/cursor presentation and `spell_graph.py` renders the tree. All modules are import-safe. Tuning is centralised in `BUILDINGS`, recipes, `TREE` and `PRESTIGE_TARGET`. Baseline station prices and production doublings are unchanged.


## Branching spells and parchment windows

**Workshop → Enchantments** opens a separate, connected 18-node constellation in an indigo astral void. Three branches radiate from the central star. Circular nodes show icons and multi-rank counts; hover for names or select a node to open its parchment detail card on the right. Drag the starfield to pan, use the wheel or +/− to zoom, and use Fit tree or Centre selected to recover your view. Click a node to compare current and next effects, prerequisites, holdings and missing ingredients. Only the explicit purchase button spends materials. All branches remain eventually purchasable.

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

Focused five-minute purchase simulations reach each branch's capstone at **135–145 minutes**, with most of that branch purchased by the **165-minute** first Reawakening. Prioritising rank-two paths and saving for the capstone achieves this; buying all rank-three specialisations first delays it.

The main game and auxiliary windows have parchment title bars. Windowed mode keeps minimise, maximise/restore, resizing and taskbar behaviour on Windows. Drag the title bar to move a window; double-click the main title bar to maximise/restore. Fullscreen remains the default and hides the title strip. Use F11 or Settings to switch.

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

Every Reawakening grants one **permanent, stackable legacy choice**, selected after choosing retained talismans and before the final reset confirmation. Cancelling either page spends nothing. These bonuses add to crafting/construction bonuses before the Moon Seal multiplier.

| Memory | Permanent bonus per choice | Available at Reawakening |
|---|---|---:|
| Dawn | +5% Mana | 1 |
| Crystal | +5% Shards | 1 |
| Tide | +5% Essence | 1 |
| Ember | +5% Elixirs | 2 |
| Astral | +5% Stardust | 3 |
| Moonweaver | +2% all resources | 5 |

Stardust goals for runs 1–12 are **120, 280, 520, 1,590, 3,960, 8,130, 13,500, 20,300, 29,500, 40,100, 51,800, 68,000**. Beyond that, goals continue on a cubic curve: `ceil(68000 × (1 + (completed_Reawakenings − 11) / 11)^3 / 100) × 100`. There are no enforced timers. The reference strategy purchasing every five minutes and choosing Dawn memory takes **165, 175, 185, 195, 205, 215, 225, 235 minutes** for its first eight runs. Different upgrades, retained talismans and choices can change those timings.

Base seal rewards increase from three to four after three completed Reawakenings, then to five after six, and so on. Waiting past the goal still grants extra seals with square-root scaling.

Migration leaves an existing save’s current 120-Stardust goal and Moon Seals untouched; higher goals begin after its next reset. Previous Reawakenings grant unclaimed legacy choices, redeemable from the Reawakening page without resetting. Legacy counts and unclaimed choices survive future resets.

Activity gates apply inside the purchase logic, not just the interface: Delivery enchantments require an owned Crucible with its second inscription, and Lasting Infusion requires the Crucible’s infusion activity. Locked nodes explain the missing unlock; existing purchased upgrades are preserved.
