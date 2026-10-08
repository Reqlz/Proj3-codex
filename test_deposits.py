import math
import tempfile
import unittest
import json
from pathlib import Path
from dataclasses import asdict
from main import State,Economy,SaveStore
from storage import capacities,banked_stardust

class DepositTests(unittest.TestCase):
    def test_deposit_frees_storage_and_accumulates_beyond_cap(self):
        e=Economy(State(owned=[10]*5,resources=[0,0,0,0,120]))
        self.assertEqual(e.reward(),0)
        for _ in range(12):
            e.state.resources[4]=120
            self.assertTrue(e.deposit_stardust('all'))
            self.assertEqual(e.state.resources[4],0)
        self.assertEqual(banked_stardust(e.state),1440)
        self.assertGreater(e.reward(),8)
        self.assertFalse(e.deposit_stardust('all'))
        self.assertTrue(e.reawaken())
        self.assertEqual(e.state.rebirth_dust,0)

    def test_goal_deposit_and_spending_are_independent(self):
        e=Economy(State(owned=[1]*5,resources=[60,0,0,0,500]))
        self.assertTrue(e.deposit_stardust('goal'))
        self.assertEqual(e.state.resources[4],380)
        self.assertEqual(e.reward(),3)
        self.assertFalse(e.deposit_stardust('goal'))
        e.state.resources[4]=0
        self.assertEqual(e.reward(),3)
        before=asdict(e.state)
        self.assertFalse(e.deposit_stardust('invalid'))
        self.assertEqual(asdict(e.state),before)

    def test_ui_controls_transfer_the_displayed_balance(self):
        import test_overhaul_ui
        a=test_overhaul_ui.OverhaulUIBehaviorTests().app()
        a.economy.state.resources[4]=240
        a.workshop_change=lambda callback:callback()
        a.prestige_page()
        buttons={c['label']:c for c in a.controls}
        self.assertTrue(buttons['Deposit to goal']['enabled'])
        buttons['Deposit to goal']['callback']()
        self.assertEqual(a.economy.state.rebirth_dust,120)
        self.assertEqual(a.economy.state.resources[4],120)
        a.controls=[];a.prestige_page()
        buttons={c['label']:c for c in a.controls}
        self.assertFalse(buttons['Deposit to goal']['enabled'])
        buttons['Deposit all']['callback']()
        self.assertEqual(a.economy.state.rebirth_dust,240)
        self.assertEqual(a.economy.state.resources[4],0)

    def test_deposit_balance_is_saved_and_slot_local(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=SaveStore(Path(tmp)/'a.json');b=SaveStore(Path(tmp)/'b.json')
            a.save(State(rebirth_dust=960));b.save(State(rebirth_dust=120))
            self.assertEqual(a.load()[0].rebirth_dust,960)
            self.assertEqual(b.load()[0].rebirth_dust,120)

    def test_offline_never_deposits(self):
        e=Economy(State(owned=[100]*5,research=[3]*5))
        e.advance(86400,True)
        self.assertEqual(e.state.resources[4],capacities(e.state)[4])
        self.assertEqual(e.state.rebirth_dust,0)
        self.assertEqual(e.reward(),0)

    def test_migration_preserves_stock_without_duplicate_credit(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=SaveStore(Path(tmp)/'slot.json');data=asdict(State(resources=[1e9]*5))
            data.pop('rebirth_dust')
            store.path.write_text(json.dumps(dict(version=11,state=data)))
            s=store.read(store.path)
            self.assertEqual(s.resources,[1e9]*5);self.assertEqual(s.rebirth_dust,0)
            e=Economy(s);e.deposit_stardust('all');store.save(s)
            self.assertEqual(store.read(store.path),s)
            for value in (-1,float('nan'),float('inf'),True):
                bad=asdict(s);bad['rebirth_dust']=value
                with self.assertRaises(ValueError):State.parse(bad)
