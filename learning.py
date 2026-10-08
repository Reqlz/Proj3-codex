from storage import capacities as storage_capacities, banked_stardust
"""Progression-aware lessons: no Tk dependency, no timed interruptions."""
OPENING = (
    ("Your first Spirit Well", "buy-0", "Buy a Spirit Well using Mana. The highlighted button shows its price. Your apprentice keeps making Mana while you wait.", "action"),
    ("Stock and income", "resource-0", "The numbers show stored materials / storage capacity. Stored materials are what you can spend. The /s number is net change each second. Wells produce automatically; clicking is not required.", "next"),
    ("Plant a Crystal Garden", "buy-1", "Buy a Crystal Garden. It produces Shards for construction and charm bodies. If you are short of Mana, wait for your Wells.", "action"),
    ("This is your Crystal Garden", "building-1", "Select this illustrated Garden to find its production card. Every station in the scene has its own matching card.", "action"),
    ("Research doubles capacity", "tab-Research", "Open Research. Each inscription doubles a station's capacity. It spends that station's output resource, not always Mana.", "action"),
    ("Your first inscription", "research-0", "This is the Spirit Well inscription. The first inscription opens charms, construction and talismans. You can return when you can afford it.", "next"),
    ("Your Workshop", "tab-Workshop", "Open the Workshop to see upcoming activities. Locked activities explain exactly what unlocks them.", "action"),
    ("The production chain", "resource-1", "Gardens → Shards → Essence → Elixirs → Stardust. Converters consume the previous material. Expand upstream supply when production slows.", "next"),
    ("Magic worth keeping", "tab-Workshop", "Temporary charms provide strong timed boosts. Talismans have lasting abilities and combine with charms. Astral puzzles improve them; one talisman survives Reawakening.", "next"),
    ("Your reference book", "tome", "Open the Spell Tome for the full guide. New features get short lessons when needed. Information icons explain items; Suggested next step helps when you feel stuck.", "action"),
)
LESSONS = {
    "storage_update": ("Deposit Stardust for Reawakening", "tab-Reawakening", "Use Deposit to goal or Deposit all to commit stored Stardust to Reawakening. Deposits free storage, cannot be withdrawn, and can grow beyond storage capacity. Purchases never reduce deposited progress. Deposits reset at Reawakening; existing stored Stardust stays yours until you deposit it."),
    "storage_full": ("Your storage is full", "tab-Workshop", "Full storage pauses excess production without wasting converter ingredients. Spend materials or expand storage in Construction. Purchased storage upgrades reset each run; starting capacity grows with Reawakenings."),
    "update": ("A new kind of magic", "tab-Workshop", "Talismans now have distinct abilities and three attunement ranks. Try Relay and Chorus charm patterns. Reawakening keeps one talisman; others lose one mastery rank."),
    "research": ("The Workshop is open", "tab-Workshop", "Your first inscription opens charms, construction and talismans. Start with the Workshop overview; you do not need to buy everything at once."),
    "converter": ("Converters need ingredients", "resource-1", "The Distillery consumes Shards to make Essence. Net rates include this consumption. A shortage slows conversion; improve Gardens before buying more hungry converters."),
    "shortage": ("A supply bottleneck", "tab-Production", "A converter cannot reach its capacity. Check its ingredient label, then buy or research the upstream station. A temporary charm on that upstream resource can also help."),
    "crafted": ("Stored magic is waiting", "activity-Charms", "New charms are stored with their clocks paused. Open Charms and Equip one to activate it. Its Online, Offline or Combined mode controls when it works and ticks."),
    "equipped": ("Your charm is active", "activity-Charms", "Equipped charms occupy cabinet places. Their cards show pattern contributions and talisman links. Expiry removes their effects immediately; stored charms do not tick."),
    "bound": ("A talisman joins your build", "activity-Talismans", "All owned talismans work together without cabinet places or timers. Their unique abilities can help a whole build, not just one resource."),
    "attunement": ("Return to the stars", "activity-Talismans", "Attune an owned talisman through three harder logic challenges for +5 percentage points per rank. Materials are charged only when you confirm success. Hints and mistakes are free."),
    "spells": ("Choose your specialisation", "activity-Enchantments", "Select spell nodes to read their effects and prerequisites before buying. Roots lead to specialised branches. Skills reset at Reawakening."),
    "recharge": ("Sustain your magic", "activity-Infusion & Recharge", "Infusion extends new charms. Recharge restores an equipped, unexpired charm to its crafted maximum; each refill costs more. It never banks extra time."),
    "deliveries": ("The courier has arrived", "activity-Deliveries", "Contracts trade two intermediate materials for Mana and possible gifts. Their quotes stay fixed. Accept when your upstream supply can spare the materials."),
    "rebirth": ("Choose what survives", "tab-Reawakening", "Reawakening resets your workshop and grants permanent Moon Seals and a legacy. Keep one talisman at full mastery; all unchosen mastery loses one rank. Review the loss preview."),
    "Restoration": ("Build lasting improvements for this run", "activity-Restoration", "Construction includes charm shelves, material storage expansions, and five-level production projects. Shard costs rise steeply. Violet Crown reduces those costs and links built projects to active charms."),
    "Transmutation": ("Recover earlier materials", "activity-Transmutation", "Transmutation converts advanced materials backwards at a loss and charges Mana. It is useful for shortages, not a source of free production or prestige."),
    "Workbench": ("Late workshop commissions", "activity-Workbench", "Trade held Stardust for Mana or commission Shards. Review costs and cooldowns. Payouts need free storage. Only Stardust deposited in Reawakening counts toward the reward."),
}

SHORT_OPENING=(
 'Buy a Spirit Well. Mana grows automatically while you wait.',
 'Stock is what you can spend; /s is your net income. The bar shows storage room.',
 'Buy a Crystal Garden to start making Shards.',
 'Select the highlighted Garden to see its production card.',
 'Open Research to double station output.',
 'Your first inscription opens the Workshop. Return when you can afford it.',
 'Open the Workshop. Locked activities show their requirements.',
 'Shards → Essence → Elixirs → Stardust. Keep upstream stations supplied.',
 'Charms give timed boosts; talismans add lasting abilities. Keep one talisman at Reawakening.',
 'Open the Spell Tome for help. Information buttons and Suggested next step are always available.')
SHORT_LESSONS={
 'storage_update':'Deposit Stardust in Reawakening to free storage and fill the bar. Deposits are unlimited and cannot be withdrawn.',
 'storage_full':'Spend materials or expand storage in Construction. Full storage pauses excess production.',
 'update':'Try talisman abilities and new charm patterns. Reawakening keeps one talisman.',
 'research':'The Workshop is open. Choose an activity to see its costs and unlocks.',
 'converter':'Distilleries need Shards. Improve Gardens when supply runs short.',
 'shortage':'Improve the upstream station shown on the converter card. A charm can also boost its supply.',
 'crafted':'Open Charms and Equip your new charm. Stored charms have paused clocks.',
 'equipped':'Your charm is active. Its card shows remaining time and linked effects.',
 'bound':'Your talisman is active without a timer or cabinet place. Combine it with charms.',
 'attunement':'Attune this talisman for stronger production. Pay only after completing the puzzle.',
 'spells':'Choose a spell node to inspect its effect and requirements.',
 'recharge':'Infusion extends new charms; recharge restores active ones. Repeated refills cost more.',
 'deliveries':'Review the courier’s fixed quote. Deliver only materials you can spare.',
 'rebirth':'Review what resets, then keep one talisman or choose none. Unchosen mastery loses one rank.',
 'Restoration':'Buy shelves, storage, or production projects here. These upgrades last for this run.',
 'Transmutation':'Convert advanced materials backwards to cover shortages. Each trade loses material and costs Mana.',
 'Workbench':'Trade spare materials after reviewing costs and cooldowns. Payouts require storage room.'}

def lesson_content(step=None,key=None):
 record=LESSONS[key] if key else OPENING[step]
 return dict(title=record[0],target=record[1],full=record[2],short=SHORT_LESSONS[key] if key else SHORT_OPENING[step])

class LearningGuide:
    def update_learning(self):
        s=self.economy.state
        if s.tutorial_skipped or s.tutorial_invite: return
        while s.guide_step < len(OPENING):
            done = {0:s.owned[0]>0, 2:s.owned[1]>0, 3:s.garden_selected, 9:s.tome_opened}.get(s.guide_step,False)
            if not done: break
            s.guide_step += 1

    def acknowledge(self):
        s=self.economy.state
        if s.guide_step < len(OPENING): s.guide_step += 1
        self.update_learning()

    def pending_lesson(self):
        s=self.economy.state
        flows,_=self.economy.flows()
        caps=self.economy.capacities()
        conditions=(
            ("storage_update",s.storage_update), ("storage_full",any(stock>=limit-1e-7 for stock,limit in zip(s.resources,storage_capacities(s)))), ("update",s.update_tour), ("research",any(s.research)),
            ("converter",s.owned[2]>0),
            ("shortage",not any(stock>=limit-1e-7 for stock,limit in zip(s.resources,storage_capacities(s))) and any(s.owned[i] and flows[i]<caps[i]-1e-8 for i in range(2,5))),
            ("crafted",bool(s.charms)), ("equipped",any(c["equipped"] for c in s.charms)),
            ("bound",bool(s.talismans)), ("attunement",bool(s.talismans)),
            ("spells",s.owned[2]>0), ("recharge",s.owned[3]>0),
            ("deliveries",s.owned[3]>0 and s.research[3]>=2),
            ("rebirth",all(s.owned) and banked_stardust(s)>=s.rebirth_goal*.8),
        )
        return next((key for key,ready in conditions if ready and key not in s.lessons_seen),None)

    def suggested(self):
        s=self.economy.state
        if not s.tutorial_skipped and s.guide_step<len(OPENING): return OPENING[s.guide_step][2]
        flows,_=self.economy.flows();caps=self.economy.capacities()
        names=("Spirit Wells","Crystal Gardens","Distilleries","Crucibles","Astral Circles")
        full=[i for i,(stock,limit) in enumerate(zip(s.resources,storage_capacities(s))) if stock>=limit-1e-7]
        if full:
            if 4 in full:return "Stardust storage is full. Deposit it in Reawakening to free space and increase the reward, or spend it. Deposits can grow beyond storage capacity."
            material=("Mana","Shards","Essence","Elixirs","Stardust")[full[0]]
            return f"{material} storage is full. Spend it or expand storage in Construction. Excess production is paused; converters do not waste ingredients."
        for i in range(2,5):
            if s.owned[i] and flows[i]<caps[i]-1e-8:
                return f"Improve {names[i-1]}: {names[i]} are short of ingredients. More converter capacity would not fix this."
        if self.economy.reward(): return "Reawakening is ready. Review which single talisman to keep and the mastery losses before confirming."
        if all(s.owned) and s.resources[4]>0:return "Deposit stored Stardust in the Reawakening tab to fill the bar. Deposits free storage and cannot be withdrawn."
        for i in range(5):
            if not s.owned[i]:
                if not self.economy.unlocked(i): return f"Keep producing Mana to reveal {names[i]}. Research or expand your current stations while you wait."
                price=self.economy.cost(i)
                if s.resources[0]>=price: return f"Buy your first {names[i]} to open the next stage of production."
                wait=(price-s.resources[0])/max(flows[0],1e-8)
                return f"Save Mana for {names[i]}: about {max(1,round(wait/60))} minute(s) at the current rate. Production continues automatically."
        return "Balance upstream supply and research your stations. Earn Stardust toward Reawakening; optional charms and talismans can accelerate the journey."
