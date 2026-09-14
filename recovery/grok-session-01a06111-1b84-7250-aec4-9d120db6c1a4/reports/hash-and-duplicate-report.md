# Hash and duplicate report

Recovered versions hashed: 2,038

Every emitted recovered version is listed in `hashes.sha256`. The digest in that file was recomputed from the read-only recovered bytes during static validation and matched the digest stored at reconstruction time.

Exact byte-duplicate groups: 39

Normalized-AST duplicate groups: 39

Normalized AST grouping uses `ast.dump(..., include_attributes=False)` only for files that parsed successfully; it does not import or execute source.

## Largest exact duplicate groups

| SHA-256 | Members | Representative original paths |
|---|---:|---|
| `45e30cbeb52b1afe02a3d4f9b1c8f024afbc88c932a58779f8d56c528c7c0864` | 4 | `/tmp/ttf-r38/gen_r38.py`, `/tmp/ttf-r48/gen_r48.py`, `/tmp/ttf-r56/gen_r56.py` |
| `95bf8ecdc689312f4b4e5f9b81e48273d25d9f641b62c4e78292f2d11267e770` | 4 | `/tmp/ffpc-r29-build-session-a.py`, `/tmp/ffpc-r30-build-session-a.py`, `/tmp/ffpc-r31-build-session-a.py` |
| `bdf62869e73ac3f65f71f05e1a30fae6d6b832861e167c6fe657b016af8559ab` | 4 | `/tmp/ttf-r35/gen_r35.py`, `/tmp/ttf-r39/gen_r39.py`, `/tmp/ttf-r45/gen_r45.py` |
| `c334ac62c3a51415271ff91c67355611acfbbf02d71f019f2571e9ee29bdd7f0` | 4 | `/tmp/ttf-r34/gen_r34.py`, `/tmp/ttf-r40/gen_r40.py`, `/tmp/ttf-r41/gen_r41.py` |
| `02239fc4353019b4a921bdac790ac8f3e580b6a19545c800f66330fa1f816b19` | 3 | `/tmp/nelb-r63-live/gen_r63.py`, `/tmp/nelb-r64-live/gen_r64.py`, `/tmp/nelb-r66-live/gen_r66.py` |
| `023b2af693aa0508690f87b5bc62507d105e29bd4399264d2c56727cb650526e` | 3 | `/tmp/nelb-r19/gen_r19.py`, `/tmp/nelb-r23/gen_r23.py`, `/tmp/nelb-r25/gen_r25.py` |
| `5572a51149df22a7fa2c2f6d0d694750747dd587c767e023c672bb79c6fe6855` | 3 | `/tmp/nelb-r03-live/gen_r03.py`, `/tmp/nelb-r05-live/gen_r05.py`, `/tmp/nelb-r23-live/gen_r23.py` |
| `5de722d2e6fed33367e225de45e1a07d5c1a71b622e01eef07613e8430756c78` | 3 | `/tmp/maos-r67/build_r67.py`, `/tmp/maos-r68/build_r68.py`, `/tmp/maos-r69/build_r69.py` |
| `7d946fbf00e8091ca76ed2dd0e180545548168f82a34354b56d711e284339f55` | 3 | `/tmp/ttf-r04/gen_r04.py`, `/tmp/ttf-r06/gen_r06.py`, `/tmp/ttf-r24-live/gen_r24.py` |
| `abf5e140da613b77899983fd07e684395a8a9e0e97a756097e0a4d619cfd070e` | 3 | `/tmp/gen_ttf_r02.py`, `/tmp/gen_ttf_r03.py`, `/tmp/ttf-r04/gen_r04.py` |
| `c71d0f97a3049cd930949c2df453b66316d3b3c7f37ca2255d1bd4693304713d` | 3 | `/tmp/actf-r32/gen.py`, `/tmp/actf-r34/gen.py`, `/tmp/actf-r35/gen.py` |
| `fe7963963f1e08e67432505e10fe30f9aebdf55705fd3d8d9073aab372eaa9ca` | 3 | `/tmp/ttf-r39/gen_r39.py`, `/tmp/ttf-r49/gen_r49.py`, `/tmp/ttf-r53/gen_r53.py` |
| `06ed4f9114c60deb249d586bc6ce851d9689c8ff2a21f1de949cb13e34169d78` | 2 | `/tmp/maos-r31/build_r31.py`, `/tmp/maos-r34/build_r34.py` |
| `18463e1afa5a121060a87550b5f298263905fcef9d96f5d8b5ea5d6ebedb7e99` | 2 | `/tmp/nelb-r20/gen_r20.py`, `/tmp/nelb-r29/gen_r29.py` |
| `19e582b3c0f17dbec7656ad421fdcefbe217d8ac150992893b81f2c28192a9d4` | 2 | `/tmp/nelb-r25/gen_r25.py`, `/tmp/nelb-r31/gen_r31.py` |
| `1d116cac35a513797dfeecc3ecfc584df186193daf6a6f2c0ffbc3b708ad5e2a` | 2 | `/tmp/nelb-r01-live/gen_r01.py`, `/tmp/nelb-r22c/gen_r22c.py` |
| `22dd88340bf98887c6620c96b4d873ab18d1aa2794c1d1df81ef00e0394f2b64` | 2 | `/tmp/ttf-r58/gen_r58.py`, `/tmp/ttf-r70/gen_r70.py` |
| `33b2d71d6a7c2bed78ede341b6ab46c3594bf25e77b8381f2cb7a1f05c240c5a` | 2 | `/tmp/ttf-r40/gen_r40.py` |
| `40d6fc32a8ad6b17cf951176d0dd594e3f8b70dc5579f175ce598c3ab0796c54` | 2 | `/tmp/maos-r45/build_r45.py`, `/tmp/maos-r50/build_r50.py` |
| `4309f32bb690f876acf491e4f1a81c15f4e82e8b27f1ff6df7744b735467661e` | 2 | `/tmp/nelb-r13/gen_r13.py`, `/tmp/nelb-r14/gen_r14.py` |

The complete member lists are in `duplicates.json`. Duplicate membership is not evidence that a version is safe, correct, or training-admissible.
