import json
import tempfile
from pathlib import Path
from dataclasses import asdict
import unittest

from main import Economy,State,SaveStore,rebirth_target
from test_game import simulated_run


class RebirthTests(unittest.TestCase):
    def test_rising_goals_and_reference_pacing(self):
        game=Economy()
        previous=0
        for run in range(8):
            minutes=simulated_run(game)[0]/60
            self.assertGreater(minutes,previous)
            if previous:self.assertLessEqual(minutes-previous,20)
            goal=game.state.rebirth_goal
            self.assertTrue(game.reawaken(legacy_choice=0))
            self.assertGreater(game.state.rebirth_goal,goal)
            self.assertEqual(game.state.legacies[0],run+1)
            self.assertEqual(game.state.legacy_pending,0)
            print(f"Reawakening {run+1}: {goal:g} Stardust, {minutes:g} minutes")
            previous=minutes
        self.assertGreater(rebirth_target(20),rebirth_target(19))

    def test_legacy_unlocks_stacking_and_no_duplicate_reward(self):
        e=Economy(State(owned=[1]*5,run_dust=120))
        self.assertFalse(e.reawaken(legacy_choice=3))
        self.assertTrue(e.reawaken(legacy_choice=0))
        self.assertAlmostEqual(e.flows()[0][0],1.05*1.3)
        self.assertFalse(e.choose_legacy(0))
        self.assertFalse(e.reawaken(legacy_choice=0))
        e.state.owned=[1]*5;e.state.run_dust=e.state.rebirth_goal
        self.assertTrue(e.reawaken(legacy_choice=3))
        self.assertEqual(e.state.legacies,[1,0,0,1,0,0])
        e.state.owned=[1]*5;e.state.run_dust=e.state.rebirth_goal
        self.assertTrue(e.reawaken(legacy_choice=4))
        e.state.owned=[1]*5;e.state.run_dust=e.state.rebirth_goal*4
        self.assertEqual(e.reward(),8)

    def test_old_save_keeps_current_goal_and_receives_legacy_choices(self):
        with tempfile.TemporaryDirectory() as temp:
            store=SaveStore(Path(temp)/"save.json")
            original=State(awakenings=3,seals=10,owned=[1]*5,run_dust=130)
            data=asdict(original)
            for key in ("rebirth_goal","legacies","legacy_pending"):data.pop(key)
            store.path.write_text(json.dumps(dict(version=6,state=data)))
            state=store.read(store.path)
            self.assertEqual(state.rebirth_goal,120)
            self.assertEqual(state.legacy_pending,3)
            self.assertEqual(state.seals,10)
            e=Economy(state)
            self.assertTrue(e.choose_legacy(4))
            self.assertTrue(e.choose_legacy(0))
            self.assertTrue(e.choose_legacy(0))
            self.assertFalse(e.choose_legacy(0))
            self.assertEqual(state.legacies,[2,0,0,0,1,0])
            store.save(state)
            self.assertEqual(store.load()[0],state)
            self.assertTrue(e.reawaken(legacy_choice=0))
            self.assertEqual(e.state.rebirth_goal,rebirth_target(4))


if __name__=="__main__":unittest.main(verbosity=2)
