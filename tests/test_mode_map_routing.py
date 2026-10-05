from pathlib import Path
import tempfile
import unittest
from server.assaultfire_ds_spawner import (
    AFDEV_MODE_IDS,
    DedicatedServerSpawner,
    SpawnerConfig,
    TANK_BATTLE_UI_MODE_ID,
    TANK_SIEGE_MODE_ID,
    TANK_TDM_MODE_ID,
    resolve_room_target,
)

MAPS = [(39, 'Bio-Capital_4_Main', 'TGBioGame'), (60, 'Bio-Maya_6_Main', 'TGBioGame'), (74, 'Bio-Factory_22_Main', 'TGBioGame'), (118, 'Bio-Capital_12_Main', 'TGBioGame'), (122, 'Bio-Maya_7_Main', 'TGBioGame'), (72, 'Bio2-Capital_12_Main', 'TGBio2Game'), (115, 'Bio2-Capital_4_Main', 'TGBio2Game'), (116, 'Bio2-Factory_22_Main', 'TGBio2Game'), (117, 'Bio2-Maya_6_Main', 'TGBio2Game'), (144, 'Bio2-Maya_7_Main', 'TGBio2Game'), (96, 'ATD-Capital_17_Main', 'ATDGame'), (141, 'ATD-Capital_22_B_Main', 'ATDGame')]

class ModeRoutingTests(unittest.TestCase):
    def test_every_uploaded_catalog_target_routes_to_its_family(self):
        modes = {'TGBioGame': (0x204, 'TGBioMatch'),
                 'TGBio2Game': (0x209, 'TGBio2Match'),
                 'ATDGame': (0x2005, 'ATDGameInfo')}
        for wire_id, world, package in MAPS:
            mode, cls = modes[package]
            with self.subTest(mode=mode, map=wire_id):
                self.assertEqual(resolve_room_target(mode, wire_id, '', ''),
                                 (world, package + '.' + cls))

    def test_room_changes_replace_world_and_game_class(self):
        with tempfile.TemporaryDirectory() as td:
            spawner = DedicatedServerSpawner(SpawnerConfig(
                enabled=True, max_instances=1, public_port_base=0,
                target_port_base=0, runtime_dir=Path(td), create_cooldown=0))
            try:
                room = spawner.reserve_lobby(owner_id=1, mode_id=0x204, map_id=60)
                self.assertEqual(room.map_name, 'Bio-Maya_6_Main')
                for mode, map_id, world, game in (
                    (0x209, 117, 'Bio2-Maya_6_Main', 'TGBio2Game.TGBio2Match'),
                    (0x2005, 96, 'ATD-Capital_17_Main', 'ATDGame.ATDGameInfo')):
                    room = spawner.update_lobby_settings(room.room_id, mode_id=mode,
                        map_id=map_id, sub_mode_id=0x1001, room_flags=0)
                    self.assertEqual((room.map_name, room.game_class), (world, game))
                room = spawner.update_lobby_settings(room.room_id, mode_id=0x209,
                    map_id=65535, sub_mode_id=0, room_flags=0)
                self.assertEqual(room.map_name, '')
                self.assertEqual(room.game_class, 'TGBio2Game.TGBio2Match')
            finally:
                spawner.shutdown_all()

    def test_tank_battle_alias_and_native_game_modes_route(self):
        self.assertIn(TANK_BATTLE_UI_MODE_ID, AFDEV_MODE_IDS)
        self.assertEqual(
            resolve_room_target(TANK_BATTLE_UI_MODE_ID, 26),
            ('TTM-Tank_01_Main', 'TGTankGame.TGTankTeamMatch'),
        )
        self.assertEqual(
            resolve_room_target(TANK_TDM_MODE_ID, 105),
            ('TTM-Tank_03_Main', 'TGTankGame.TGTankTeamMatch'),
        )
        self.assertEqual(
            resolve_room_target(TANK_SIEGE_MODE_ID, 44),
            ('TDB-Tank_02_Main', 'TGTankGame.TGTankDBMatch'),
        )

    def test_tank_lobby_selection_normalizes_before_afdev_handoff(self):
        with tempfile.TemporaryDirectory() as td:
            spawner = DedicatedServerSpawner(SpawnerConfig(
                enabled=True, max_instances=1, public_port_base=0,
                target_port_base=0, runtime_dir=Path(td), create_cooldown=0))
            try:
                room = spawner.reserve_lobby(
                    owner_id=1, mode_id=TANK_BATTLE_UI_MODE_ID, map_id=26,
                    sub_mode_id=0, map_name='Wilderness Battle')
                self.assertEqual((room.mode_id, room.map_id), (TANK_TDM_MODE_ID, 34))
                self.assertEqual((room.map_name, room.game_class), (
                    'TTM-Tank_01_Main', 'TGTankGame.TGTankTeamMatch'))
                room = spawner.update_lobby_settings(
                    room.room_id, mode_id=TANK_BATTLE_UI_MODE_ID, map_id=26,
                    sub_mode_id=TANK_SIEGE_MODE_ID, room_flags=0)
                self.assertEqual((room.mode_id, room.map_id), (TANK_SIEGE_MODE_ID, 44))
                self.assertEqual((room.map_name, room.game_class), (
                    'TDB-Tank_02_Main', 'TGTankGame.TGTankDBMatch'))
            finally:
                spawner.shutdown_all()

    def test_afdev_loader_skips_pve_difficulty_writes_for_tanks(self):
        loader = (Path(__file__).resolve().parents[1] / 'tools' / 'server_spawner'
                  / 'AFDevLoader_v48_spawner_multi_instance.py').read_text(encoding='utf-8')
        self.assertIn('elif int(args.mode_id) in TANK_GAME_MODE_IDS:', loader)
        self.assertIn('[AFDEV-TANK] Native TGTankGame startup', loader)


if __name__=='__main__':unittest.main()
