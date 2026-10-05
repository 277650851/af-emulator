# PH Mutation, Hero Mutation and Tower Defense routing

Room creation and settings changes resolve the stock ModeId/MapId to the matching
installed world and GameInfo. An empty MapString uses the verified registry; an
unknown map ID in a known family stays unresolved instead of launching an unrelated
default map. An explicit map name uses that family's matching GameInfo.

| Mode | ModeId | GameInfo |
| --- | --- | --- |
| Mutation | 0x0204 | TGBioGame.TGBioMatch |
| Hero Mutation / Queen | 0x0209 | TGBio2Game.TGBio2Match |
| Tower Defense | 0x2005 | ATDGame.ATDGameInfo |

The added maps include Mutation Maya 6 (Archaeology), Factory 22 and Maya 7; the
five stock Bio2 worlds; and ATD Capital 17 / Capital 22 B. TDB worlds belong to
Tank Siege, not Tower Defense. Hero Mutation retains native match settings rather
than interpreting SubModeId as PvE difficulty. Tower Defense uses the reflected
PvE settings path. Both new families require the verified shared native ServerMove
v4 body, without guessed controller vtable patches.

The captured client runs reached SESSION_READY and active UDP relay for Mutation,
Hero Mutation and Tower Defense. New routing tests cover all twelve intended
catalog worlds and room switches between families. This is server-side support;
client catalog visibility is a separate configuration choice.
