from pathlib import Path
import tempfile
import unittest
from server.assaultfire_ds_spawner import DedicatedServerSpawner, SpawnerConfig, resolve_room_target

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


if __name__=='__main__':unittest.main()
