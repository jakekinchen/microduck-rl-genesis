# V40 match the native convex detector to Genesis MPR

V34 preserves authored collision hulls but uses different algorithms in the two
lanes: Genesis MPR versus native MuJoCo GJK/EPA. Prior Genesis GJK/patch attempts
did not resolve that difference; Euler alone also failed. Change only the native
box lane's detector to its supported legacy MPR (`mjDSBL_NATIVECCD`), preserving
multi-contact generation, native solver/settings and the V34 Genesis lane.
The native plane reproduction control remains unchanged and is still required.

Reuse all five action prefixes, original geometry audit and 2-mm/5-degree gates.
Record this as a changed-native-algorithm diagnostic, not validation of original
native GJK behavior. It cannot alter V30 scores or establish calibrated physics.
The detector toggle and raw contacts are retained with source-bound receipts.
