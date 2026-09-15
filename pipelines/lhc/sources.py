#!/usr/bin/env python3
"""Pinned inventory of the 134 LHC scripts on ``legacy-mill-lane``.

Blob SHAs are the preserve-commit objects (``vocabulary.PRESERVE_COMMIT``).
The 134 ``lhc-mill*.py`` blobs are byte-identical on ``e1d2e7b4`` and
``813f93f1`` (``origin/legacy-mill-lane`` tip). Paths are
``experiments/<mill_id>.py``. The mill publishers themselves are not vendored.
"""

from __future__ import annotations

from dataclasses import dataclass

from .vocabulary import KIND_PAIRS, SOURCE_COUNT


@dataclass(frozen=True)
class MillSource:
    mill_id: str
    path: str
    blob_sha: str
    kind: str = KIND_PAIRS


def _legacy_path(mill_id: str) -> str:
    return f"experiments/{mill_id}.py"


# (mill_id, blob_sha) — 134 preserve-commit pins.
_SOURCE_PINS: tuple[tuple[str, str], ...] = (
    ("lhc-mill-lll-lang-r4750", "3ae00f1db72ae6363111aeda2033212287ccfb9f"),
    ("lhc-mill-lll-r4654", "87785b3d5d90490f22fca45ca63e49f59d44c0c9"),
    ("lhc-mill-lll-r4688", "d4750cd733212bb05136420f1bde7098785cf273"),
    ("lhc-mill-w4bt-r4437", "53412c43e46a9f6d50f048402a6b932c8acde620"),
    ("lhc-mill-w4bu-r4453", "431c1a24104417a8f5247a89dbdd58c4870709aa"),
    ("lhc-mill-w4bv-r4461", "cb6ea843374b9d75089f3cbd8bf424412f7b7927"),
    ("lhc-mill-w4bw-r4469", "60f59b975c277b8dcf61c1831ac1178dc6b9959a"),
    ("lhc-mill-w4bx-r4477", "4c23dec83b60b46f832fd47c0e8916b388073ca2"),
    ("lhc-mill-w4by-r4485", "dfa5cad574842d2d6bbea33ec686e49fb9bf2077"),
    ("lhc-mill-w4bz-r4493", "af1c1e5a9bfaaa10e9bb2b346e1bd35358de656f"),
    ("lhc-mill-w4ca-r4501", "7059deaf62b2aa7d186bee0b1eba9fb7f25d39be"),
    ("lhc-mill-w4cb-r4509", "8cede7296917d3c4137ec914e2db14266fefd11e"),
    ("lhc-mill-w4cc-r4517", "3b1377d4c1b754e767858fd1b100a3cadc6e513f"),
    ("lhc-mill-w4cd-r4525", "8315c96d27f30d29c3924230538d00c3132fae94"),
    ("lhc-mill-w4ce-r4533", "885cdaec39a5ed5b56baa6e2a5fdfea6239d913d"),
    ("lhc-mill-w4cf-r4541", "acbf39d652c7bbcc28ffef8594f2ef97bef0daa4"),
    ("lhc-mill-w4cg-r4549", "29f232e078352a748e254a23a0217ad62215a763"),
    ("lhc-mill-w4ch-r4557", "993a12f3af8615e513461d855503b33210ccd183"),
    ("lhc-mill-w4ci-r4565", "d3df9b449c2e8dcaf696ba3fe8b8b6383fcd7427"),
    ("lhc-mill-w4cj-r4573", "55db21d5a57e2db69fbb42682b277f626af4e2f9"),
    ("lhc-mill-w4ck-r4581", "c9af465bc4fe8c4ec284a4f3a029b514d71f80eb"),
    ("lhc-mill-w4cl-r4605", "221cef84404e8249e80cdbb4bfb41ce1955a4c2f"),
    ("lhc-mill-w4cm-r4629", "fccb07b7b28267e6e2de313cfe37e050b803eecf"),
    ("lhc-mill-w4cn-r4653", "4d36ac450455029493a47a698bd15b64e6b9c616"),
    ("lhc-mill-w4co-r4676", "420ce127b6b60a22526967ff3d5477b96f75e158"),
    ("lhc-mill-w4cp-r4688", "6453601e279b5a7ec4a70b98d0e65c1c6617da18"),
    ("lhc-mill-w4cq-r4733", "397435eee4bf4e5831e006382a4ba59df51275b4"),
    ("lhc-mill-w4cr-r4785", "dc38ffea93e20cbcbec2f792052f1188782be416"),
    ("lhc-mill-w4cs-r4817", "1e614afbb2a009ca365840f5206235d32fe92597"),
    ("lhc-mill-w4ct-r4852", "51c1c6ef431ccd74aad63fb4c517ef820cfce219"),
    ("lhc-mill-w4cu-r4871", "e468cb3ef56ed1ed6db405ebf41e1647037d9dc3"),
    ("lhc-mill-w4cv-r4887", "8ede2fbc3d8ce2ebd231733e89ea50915c5653fa"),
    ("lhc-mill-w4cw-r4900", "39fc6152c3fe1e043ee8ad00f1d19aea9f2c60bc"),
    ("lhc-mill-w4cx-r4914", "4d5047e24ab2b6ad36ffff870526d0a3ad345e0f"),
    ("lhc-mill-w4cy-r4927", "26086394db4cad47dcedbf7c2c75ef27ead4b101"),
    ("lhc-mill-w4cz-r4937", "097592854e3c97346f089bd1dd56be2d03cfdec9"),
    ("lhc-mill-w4da-r4946", "0771028c77005227baf8187ac24e13b521a7a39a"),
    ("lhc-mill-w4db-r4954", "425a602ed87cb7cb9af14372b27c4cc925275ebe"),
    ("lhc-mill-w4dc-r4962", "a44da08156696725a83b1083b41ede4ab668b60c"),
    ("lhc-mill-w4dd-r4970", "6ebce27b98e0b55bb6bb6aa5a3c7ba29220110df"),
    ("lhc-mill-w4de-r4978", "20c0c89eb6f7252cea27082e041c1654ff42375c"),
    ("lhc-mill-w4df-r4986", "9db6d2af988d6b01d6b7498d0f5899019ce40a91"),
    ("lhc-mill-w4dg-r4994", "50431fab7753105bee555fbd690a3e307fc020cd"),
    ("lhc-mill-w4dh-r5002", "8013c2454d26cba4d2ba74dac92db7a5caf35cd0"),
    ("lhc-mill-w4di-r5010", "7500e6b5e648c28ceaf91946331f75d001053535"),
    ("lhc-mill-w4dj-r5018", "00e768189b4fb96a82b23a00ec748ee4ffaf4584"),
    ("lhc-mill-w4dk-r5026", "808cb6853b1b53c1c2511bbbacdb6b2e82b2c021"),
    ("lhc-mill-w4dl-r5034", "36e9328b57d15973375e1296ccd4019246117825"),
    ("lhc-mill-w4dm-r5042", "fc553f229621388f4f2a2553e8618d1bdc3174d1"),
    ("lhc-mill-w4dn-r5050", "23dd214824ef190beb8919c89e92a727c147a312"),
    ("lhc-mill-w4do-r5057", "b90d5bd20c3d792f33ceeb7d65f0aec02f7d62d5"),
    ("lhc-mill-w4dp-r5065", "5ea2189ff4ec12c0338ce9017c80c1d75fe34d78"),
    ("lhc-mill-w4dq-r5073", "e8fe018598058a3f0f0e9c421c64e3d1a113d87e"),
    ("lhc-mill-w4dr-r5081", "ef9b4dc545a6f188a14a0e542ada30751e658dfd"),
    ("lhc-mill-w4ds-r5089", "78aad973a636c75004d4882c85cebb9f3db4f3ba"),
    ("lhc-mill-w4dt-r5097", "6e5d019be5a8fd4f95282145c83afb575f993cdb"),
    ("lhc-mill-w4du-r5105", "f17c05b1887dff80832c80ca7b6e4dc6ff2caee9"),
    ("lhc-mill-w4dv-r5113", "f84e95e6b4d51e9121b141a6812965b1dbe156a7"),
    ("lhc-mill-w4dw-r5121", "4e31299c33c9a179b87372da3ebb8744abf74ce6"),
    ("lhc-mill-w4dx-r5129", "4935989e942b1032d71c97a7b50911a7b5d5441a"),
    ("lhc-mill-w4dy-r5137", "529efa1888c88711db93ed22dfebeef000b50b44"),
    ("lhc-mill-w4dz-r5145", "5f814ea81e8a22d9a79bcf440314f81cbb15fbee"),
    ("lhc-mill-w4ea-r5153", "5e7e289b39a42dfcb7a2fcf5a4cd32470af16c60"),
    ("lhc-mill-w4eb-r5161", "e9888f3e1beedbf198fab0008864c1bd68777d6e"),
    ("lhc-mill-w4ec-r5169", "cc809a0f00256841c4457c7e5ba04243814a84ca"),
    ("lhc-mill-w4ed-r5177", "56ed34b9c67b4075263be93745013bc355eb79b1"),
    ("lhc-mill-w4ee-r5185", "15cf42eda5c3e32d22b88974e86eddbf36a9a4be"),
    ("lhc-mill-w4ef-r5193", "c94ead0c82cbe8de6c49df95203e191ea2db994a"),
    ("lhc-mill-w4eg-r5201", "5559c78e5dc6b018252c176700aa27c676aff733"),
    ("lhc-mill-w4eh-r5209", "3fad0328d64f5142af2fc73001cbe499bf5afe92"),
    ("lhc-mill-w4ei-r5217", "ade379e7accebabe1913529116c9a18757ee13fb"),
    ("lhc-mill-w4ej-r5225", "dabcb9f7ab6aa26dcf9cc65e7de21e81de539128"),
    ("lhc-mill-w4ek-r5233", "3f4cdfb8f8cb9923cffc0a1705c2f85a4ed1aa06"),
    ("lhc-mill-w4el-r5241", "3abd7b3028d31884860affbdb2f318665ec97b82"),
    ("lhc-mill-w4em-r5249", "17da1884f31c4ca40087b131902be48950657456"),
    ("lhc-mill-w4en-r5257", "1c8042adde5bb05428406ca1ed2133ad5e032571"),
    ("lhc-mill-w4eo-r5265", "6b8ef2b97ab5024ffa40cb123bb70fe59bf95f5b"),
    ("lhc-mill-w4ep-r5273", "b9f593955627992bda535ba63a728eae79261b7c"),
    ("lhc-mill-w4eq-r5281", "8ef86b0e73d6c677f2e29a3573bc1c76d19a13f0"),
    ("lhc-mill-w4er-r5289", "2c1354bbf3e438cad4c892104b52806fdd8db28c"),
    ("lhc-mill-w4es-r5297", "1be1ea7f42b401117b8617b5cd6943d0f5635166"),
    ("lhc-mill-w4et-r5305", "c112fd385e228fd6f31f66cce2c1dde569226117"),
    ("lhc-mill-w4eu-r5313", "548bb7d58bd91c7a1eaa2d077965b3c5d01b91c4"),
    ("lhc-mill-w4ev-r5321", "874d52a7514b1800b5823bc1cc532f421fbe0d26"),
    ("lhc-mill-w4ew-r5329", "446574247627145ccb29713890618d0c11b26dab"),
    ("lhc-mill-w4ex-r5337", "3ec92d08cc7927e0a20870aeafd19b08a89a2686"),
    ("lhc-mill-w4ey-r5345", "a24684400636c0467a2d0ebf27b34d6efda5f685"),
    ("lhc-mill-w4ez-r5353", "4da83ef99f9bb3b10529344539b7db99be6d2830"),
    ("lhc-mill-w4fa-r5361", "74572160fdfcef5f8cdf9737778469abc08686bf"),
    ("lhc-mill-w4fb-r5369", "c972631b8eb97628c88bcdec0c4b8210c4908989"),
    ("lhc-mill-w4fc-r5377", "e688f0d57a76db7c9d385e64afd22a6c24716da3"),
    ("lhc-mill-w4fd-r5385", "825db5784aa19e00cf83f03722ab34e9dbb4a1ba"),
    ("lhc-mill-w4fe-r5393", "fb6819341e7aea4d9a6863d50286ccbebff89cfd"),
    ("lhc-mill-w4ff-r5401", "7000231f9606e1293aaf75f2ad37fc3dcd580ad5"),
    ("lhc-mill-w4fg-r5409", "f5f0d3e2daad5862b98008fa3be9322ed6782e56"),
    ("lhc-mill-w4fh-r5417", "d1f9a11d64acff0a843a77ff72accf343044d849"),
    ("lhc-mill-w4fi-r5425", "6cd15cb3bb7ccab2ab74dec6b87799e8c7f72ff8"),
    ("lhc-mill-w4fj-r5433", "ca4d7832ecdd7fbba4e61eb85cc18d41b892690b"),
    ("lhc-mill-w4fk-r5441", "f36f6609f95637ecdac67fc8718073ffb074d430"),
    ("lhc-mill-w4fl-r5449", "feb17e23c9bbace5adc3434f0e207b14dcee885f"),
    ("lhc-mill-w4fm-r5457", "68ed5e6295a4337f4c864a675ab2fc5a3c1d9a0f"),
    ("lhc-mill-w4fn-r5465", "942c97d48cb2b9796c049e8bf30999bfe0df2435"),
    ("lhc-mill-w4fo-r5473", "b7d5f3de14a5f3a7de65e392836c1f5f79001c50"),
    ("lhc-mill-w4fp-r5481", "56102fdd95b58210799645f3b438e4ff1bf6f6f6"),
    ("lhc-mill-w4fq-r5489", "d453fb2e33873d34e2916fd267fe717cbf755d45"),
    ("lhc-mill-w4fr-r5497", "f6e1e307715de8c40dd15f901d786c50166db193"),
    ("lhc-mill-w4fs-r5505", "c0fb20b067e2e10e55909383b05b33b701f809c8"),
    ("lhc-mill-w4ft-r5513", "1e4c41af988d1c31a2dd594c60526478059d8cf6"),
    ("lhc-mill-w4fu-r5521", "8eb869c0a8f9fb6ccaadfe948aa466ac90fdf0a1"),
    ("lhc-mill-w4fv-r5529", "a42aadfa15f718241fd93b426df90b74a23c0e6b"),
    ("lhc-mill-w4fw-r5537", "7cd6be93c5fcad72d0b9b5a2fdecb060346fe6e7"),
    ("lhc-mill-w4fx-r5545", "4476097d3799108453efd5789290d1c2889d9eeb"),
    ("lhc-mill-w4fy-r5553", "62d8d1f29ec8ec8125c43b9f9d32fa9237f9c1d2"),
    ("lhc-mill-w4fz-r5561", "74443cfc767e083b1a144ea2c6af78e3c3a63ddf"),
    ("lhc-mill-w4ga-r5569", "3131427726d680838f56f2770c4fa757e90f1335"),
    ("lhc-mill-w4gb-r5577", "b8798f4f6b960a05468bd0251f06785b3e573172"),
    ("lhc-mill-w4gc-r5585", "694947beee514c4b81c1fdefc102fed17f9fa55d"),
    ("lhc-mill-w4gd-r5593", "acf76f73af3987d0d065d1e8066033c7cb88731d"),
    ("lhc-mill-w4ge-r5601", "704d8fb110f7555c8d256ffa95014e59801661c8"),
    ("lhc-mill-w4gf-r5609", "70f09565f247bd213a9e6045df643847148340db"),
    ("lhc-mill-w4gg-r5617", "698fb18e20b91ff7541ee9738541be852d457572"),
    ("lhc-mill-w4gh-r5625", "bc73381828d72fcc0f1dfd810d707e379a75a2f1"),
    ("lhc-mill-w4gi-r5633", "ce2e2f5e43482de827809201d32c03c04e062cbb"),
    ("lhc-mill-w4gj-r5641", "74ffd26bfefc13256ccdb25b74d180f887654b34"),
    ("lhc-mill-w4gk-r5649", "8598271c955809a1acba9e2e872c6de4c787e99c"),
    ("lhc-mill-w4gl-r5657", "0cd789bae348b9919e199c4a81233d87ae93e786"),
    ("lhc-mill-w4gm-r5665", "63eb40b15a0affc822a67f319c9d644c4e83f788"),
    ("lhc-mill-w4gn-r5673", "6ffec68fbee86543adc2246b7412378de07a47fb"),
    ("lhc-mill-w4go-r5681", "3d047a53240c97c48220c6f328ee0bc344649ba4"),
    ("lhc-mill-w4gp-r5689", "0a480404a153effdc5efb7e631ed2c772c29f671"),
    ("lhc-mill-w4gq-r5697", "a19b74fb3a35fc5a722fc057903fd030fe133ba8"),
    ("lhc-mill-w4gr-r5705", "cc86c2ef92dc50945a4880e13a1280b1e4bf4a7d"),
    ("lhc-mill-w4gs-r5713", "f14cba1894363147f2397c15debd8fc56e5ff101"),
    ("lhc-mill-w4x-r4358", "d00546ac0dd866ee75b8ac7e09953f45d8b8425b"),
)


if len(_SOURCE_PINS) != SOURCE_COUNT:
    raise ValueError(
        f"expected {SOURCE_COUNT} LHC pins, found {len(_SOURCE_PINS)}"
    )

MILL_SOURCES: tuple[MillSource, ...] = tuple(
    MillSource(mill_id, _legacy_path(mill_id), blob_sha, KIND_PAIRS)
    for mill_id, blob_sha in _SOURCE_PINS
)


def catalog_sources() -> tuple[MillSource, ...]:
    return MILL_SOURCES


def source_by_id(mill_id: str) -> MillSource:
    for source in MILL_SOURCES:
        if source.mill_id == mill_id:
            return source
    raise KeyError(f"unknown lhc mill source {mill_id!r}")
