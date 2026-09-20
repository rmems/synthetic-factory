#!/usr/bin/env python3
"""Verify the reviewed simulator executable sources without importing them.

Oracle implementation pins come from 6ca641465bbf8ce8339de1dce6ce77f77186e34a.
The package initializer includes the reviewed import-identity repair from
f98dd3e8facd282744136ca91040ae595cfdc6b7. The worker pin seals this PR's
reviewed streaming adapter separately; it is not historical producer evidence.
``distill_vocabulary.py`` binds the reviewed #285 integer-count bytes; the
remaining producer pins are unchanged.
No source is executed to verify it.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from types import MappingProxyType

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_identity_registry_sources")
    from .curate_identity_json import IdentityCurationError
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_identity_registry_sources"
    )
    from curate_identity_json import IdentityCurationError


_REPO_ROOT = Path(__file__).resolve().parents[1]
SIMULATOR_SOURCE_PINS = MappingProxyType({
    "pipelines/curate_identity_simulator_worker.py": "9f26fb3400cb222ed29c8f2ebf56fd1380e109cb4c582e3c1f227b6ad1289b17",
    "pipelines/exact_json.py": "ac923100a7bd857e2401355ce2cd05ef3ec6eeb835a3ab73f392392d80ec057d",
    "pipelines/exact_json_encoding.py": "56c8e47e70f2234ce68c26975279c5938d3c612c6d4fc79c98f0309c497b22ff",
    "pipelines/oracle_grounded/__init__.py": "0c79551ff1cb4421208f2ddeba25493b3400c27d47ec70a5a1c459d8563cc13b",
    "pipelines/oracle_grounded/canon.py": "c9f3f8f69cc48c3570eff1d7468316a5dfdfd7b5a13a2885d5fa91d7775cf954",
    "pipelines/oracle_grounded/distill_blocks.py": "7dcbd942dfb8383370c6f68347e24c4332692b5016769014d2353f1c079eae69",
    "pipelines/oracle_grounded/distill_builders.py": "b2f44d38d4a73ce9466d141e030f2cf535b5dcd58ee846497e09d01a2242a7f0",
    "pipelines/oracle_grounded/distill_energy_claims.py": "16a1fe6aa0d50bc5e53439f29a6c57809588a88091b865ccd0ac686ac0cc70e2",
    "pipelines/oracle_grounded/distill_labels.py": "7c4e102138efdba933995cea57b3c96ba92ad20064245c225d1a7f9bdca5d64c",
    "pipelines/oracle_grounded/distill_measurements.py": "dc2fd89567db0cb1a8ff0a9310f723ff8e80c5bf5e5f62149a788a55a707c2d2",
    "pipelines/oracle_grounded/distill_vocabulary.py": "87129b3817ef336264f00fb12a1343cc7930bb862c2b369442962555b6edb60e",
    "pipelines/oracle_grounded/envelope.py": "0ea00575ba81f9264c65ac975a762407353951c7b8bf35002c147971444f801b",
    "pipelines/oracle_grounded/families.py": "40040cfc128daeab99ddd75e200d9628d2a65bcbdb36abbb9e692421494e3259",
    "pipelines/oracle_grounded/family_common.py": "f1ae0eee93e14eca977411b7d4e90fb08aadf759708517d8fd4451cce03d1eff",
    "pipelines/oracle_grounded/family_credit.py": "51b009ec8a90d160ec8259a7270e6b7ad19883daddf04e655351d9aecac14b65",
    "pipelines/oracle_grounded/family_credit_checks.py": "33b8eb09aec80b294163d9705bcdba631ceb6ba7f2213cafd2008e1fff09dc0e",
    "pipelines/oracle_grounded/family_encoder.py": "2375417dd3578bbbce5a728152f5848cf577a0e62677f98d1249a3dd5a923ec7",
    "pipelines/oracle_grounded/family_memory.py": "beb547f127b8b62a52b3b788694548eaf82ec8f174c52425567611e8a87e11d8",
    "pipelines/oracle_grounded/family_memory_checks.py": "ad9fab757b86238241a3d60e6f30b6caee653482af502f952af8ecd2d0b2988a",
    "pipelines/oracle_grounded/family_mesh.py": "6dba06e8a4f7f53d96be5f4b2f606a88edf42c0999e6aa4f7337f177ecb9341c",
    "pipelines/oracle_grounded/family_neuron.py": "cf0efab3d24d6c63cdd77f18d1f8a8e75ae1eb7c6b6e49460f445fd6c2f3b1dd",
    "pipelines/oracle_grounded/fault_config.py": "815b535985057ea6e1ad2e4cb6c751612b21bdc153e284683e1dbba22c4292e4",
    "pipelines/oracle_grounded/fault_oracle.py": "a87611c2b25b91e72471190841227f207a41c2315edb7462634473ca57210828",
    "pipelines/oracle_grounded/fault_scenario.py": "4c81a14d479996b9cd76bb689782c0adaed62416154d906e14806d6421bc1fa5",
    "pipelines/oracle_grounded/fault_simulator.py": "be267e0720662cf1f8c79b24384bd335df9ec127fce8184459e2e64e31c8d3e4",
    "pipelines/oracle_grounded/fault_vocabulary.py": "066ebb41123e7fdf77fffbb77e70380348f549195f55963c7c64da6c0cfcffbe",
    "pipelines/oracle_grounded/generator_common.py": "825c96ae0e40b9881d8dccdf2768ff3be4f212caebba23cb6f6c348ff1fcc35f",
    "pipelines/oracle_grounded/generator_credit.py": "de488f34091d84a9e6d8ccca46f753a74d072aeb908fb5088b9719562b5e335b",
    "pipelines/oracle_grounded/generator_encoder.py": "d89e4a9180ad4defd445bcefbd5d26c5cb068149aecad43aa9fb0e390290f20c",
    "pipelines/oracle_grounded/generator_memory.py": "87d4a3c8c24c82d8170097061bd511381a4cd78770887e7cf9aad15e8e01c7e0",
    "pipelines/oracle_grounded/generator_mesh.py": "683c5adf340dc132b3b18c28b57199f8e8fdfbd6522d747a8dc6cc53090f17dd",
    "pipelines/oracle_grounded/generator_neuron.py": "8dcc07670af7e1cd3718061668505a3777cb0c0f8c248711ae929b0f5be9cedf",
    "pipelines/oracle_grounded/generators.py": "eb7a0b8cda45b734c1759bc61f7fbde8262769133342fd9b3de06399397a6393",
    "pipelines/oracle_grounded/import_twins.py": "0f28c2ed713360ad2a0f398ef15815fc6031eb9c79ea351171bb48eb368ed4f0",
    "pipelines/oracle_grounded/native_checks.py": "c5fcfae795513c398d94b653661b80912fa881f305c88278dcbbae5e9b2071c7",
    "pipelines/oracle_grounded/native_profiles.py": "f04a933789187b3a2d45b0098bfb5649dc8bc975545567083df80fef0d0918c0",
    "pipelines/oracle_grounded/native_runtime.py": "11bd1a0e738d3da5b48da9053741fa31814ac4975417d08ccfcccc5d2376e02a",
    "pipelines/oracle_grounded/oracle_adapters.py": "fe9b97a14b50a88a70a3ea321faebb0db5e290546a85ef762ee8a4a92dddedf6",
    "pipelines/oracle_grounded/oracle_binding.py": "fd59c4beaa2cad2f4fe6a5e7376080a27d6e0a4a2de13a1320abd9df4db8ee2b",
    "pipelines/oracle_grounded/oracle_core.py": "af75ef88d6eb9a17d41f2ea81bedb3f8a236e371aeefde1c1c8a07eeaeb9c404",
    "pipelines/oracle_grounded/oracle_protocol.py": "abff91117b7272f26d6670b7cb51d7b8afb438dd8cadf3d2058c845f7fa80cbe",
    "pipelines/oracle_grounded/oracles.py": "553c4362e28343bdd3f6d978ebcf49fe4837de727031f125ae61eb1006b25b0f",
    "pipelines/oracle_grounded/refusals.py": "ebbc9717871c02c00b3e764e7dc4961032ad8a44ca1a20c3a4386acac4d67e5b",
    "pipelines/oracle_grounded/rng.py": "e15ba942e81117a028519384aea0c92333122e9dd6b37620697194c77eac960f",
    "pipelines/oracle_grounded/sim.py": "ccdb48d5141a964760fb5eacf69c8e0eef10014ebecb1959c2634465141327b6",
    "pipelines/oracle_grounded/sim_common.py": "7e8e1d46f5c37951bdd35eae09ec030a64dff8abc0fcf08bd7730b7fdf325998",
    "pipelines/oracle_grounded/sim_credit.py": "634aa0c5aac394886f7251a34f8350c5a89db272081d860ed4e3ae7515a9758f",
    "pipelines/oracle_grounded/sim_encoder.py": "40867df9bad09a6b04de5eaf77d757bc6d483f35d120b66b876a7542ef3b5e3b",
    "pipelines/oracle_grounded/sim_memory.py": "d25eef187c2545d1aa0c13b52c196e9a8c9ef65abac12aae3c63f9b243724d23",
    "pipelines/oracle_grounded/sim_mesh.py": "b2704fee69f17e551b606096a1b7ed6a0cb64fe50f1ed5a0b9b5e7e1b0aa35a0",
    "pipelines/oracle_grounded/sim_neuron.py": "587c0c9154faa6364f5d7d01dfdeba690f1bec07cd710710f14f2b647b6f3a07",
    "pipelines/oracle_grounded/source_snapshot.py": "d97340d2ac6760cac2a4b1baae0ba677ffcc87539091582533b7acddbccb05b6",
    "pipelines/validate_run_provenance.py": "4bd36bc7c96336593eb4eaf330845db43add367b13772f7013aa4470fd2e1d28",
    "pipelines/validate_run_spikes.py": "6883519c0806996a6921116eadcb972fea07b6ee73e8db243c0a1c232e5f3a7f",
    "schemas/thalamic-trajectory.schema.json": "b577363500cab5362825968647d40deed279d8e19e6b73b96ae9b1404e414acd",
})


def simulator_source_snapshot() -> dict[str, bytes]:
    """Capture exactly the authenticated bytes that a replay may execute."""
    snapshot = {}
    for relative, expected in SIMULATOR_SOURCE_PINS.items():
        try:
            payload = (_REPO_ROOT / relative).read_bytes()
            normalized = payload.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
        except (OSError, UnicodeError) as exc:
            raise IdentityCurationError(f"reviewed simulator source is unavailable: {relative}") from exc
        if hashlib.sha256(normalized.encode("utf-8")).hexdigest() != expected:
            raise IdentityCurationError(f"reviewed simulator source digest differs: {relative}")
        snapshot[relative] = normalized.encode("utf-8")
    return snapshot


def require_simulator_sources() -> None:
    """Refuse registry authority if any reviewed executable dependency changed."""
    simulator_source_snapshot()


if __package__:
    _expose_package_sibling(__name__)
