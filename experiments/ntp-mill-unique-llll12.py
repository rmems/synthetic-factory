#!/usr/bin/env python3
"""NTP unique leftover leftover leftover leftover mill wave 12: NEW dest plants. BAN dnsmasq leftover clones."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "ntp_mill_unique_llll2",
    ROOT / "experiments/ntp-mill-unique-llll2.py",
)
mod2 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod2)

s_from = mod2.s_from
l_from = mod2.l_from

SUCCESS = [
    s_from(0, "cargo-lock-leftover-as-dest", "crlk", "cargo lock leftover", "Cargo.lock", "Cargo lock leftover", "cargo leftover && cat Cargo.lock", "not cargo leftover; Cargo lock leftover is not dest", "treat Cargo leftover lock as dest then CLI parquet.", "cargo leftover; # Cargo.lock claimed dest", "cargo leftover|Cargo.lock"),
    s_from(1, "go-mod-leftover-as-dest", "gomd", "go mod leftover", "go.mod", "Go mod leftover", "go leftover && cat go.mod", "not go leftover; Go mod leftover is not dest", "treat Go leftover mod as dest then CLI parquet.", "go leftover; # go.mod claimed dest", "go leftover|go.mod"),
    s_from(2, "npm-lock-leftover-as-dest", "nplk", "npm lock leftover", "package-lock.json", "npm lock leftover JSON", "npm leftover && cat package-lock.json", "not npm leftover; npm lock leftover is not dest", "treat npm leftover lock as dest then CLI parquet.", "npm leftover; # package-lock json claimed dest", "npm leftover|package-lock.json"),
    s_from(3, "yarn-lock-leftover-as-dest", "ynlk", "yarn lock leftover", "yarn.lock", "Yarn lock leftover", "yarn leftover && cat yarn.lock", "not yarn leftover; Yarn lock leftover is not dest", "treat Yarn leftover lock as dest then CLI parquet.", "yarn leftover; # yarn.lock claimed dest", "yarn leftover|yarn.lock"),
    s_from(4, "pnpm-lock-leftover-as-dest", "pnlk", "pnpm lock leftover", "pnpm-lock.yaml", "pnpm lock leftover YAML", "pnpm leftover && cat pnpm-lock.yaml", "not pnpm leftover; pnpm lock leftover is not dest", "treat pnpm leftover lock as dest then CLI parquet.", "pnpm leftover; # pnpm-lock yaml claimed dest", "pnpm leftover|pnpm-lock.yaml"),
    s_from(5, "bun-lock-leftover-as-dest", "bnlk", "bun lock leftover", "bun.lockb", "Bun lock leftover", "bun leftover && ls bun.lockb", "not bun leftover; Bun lock leftover is not dest", "treat Bun leftover lock as dest then CLI parquet.", "bun leftover; # bun.lockb claimed dest", "bun leftover|bun.lockb"),
    s_from(6, "maven-pom-leftover-as-dest", "mvpom", "maven pom leftover", "pom.xml", "Maven POM leftover XML", "mvn leftover && cat pom.xml", "not maven leftover; Maven POM leftover is not dest", "treat Maven leftover POM as dest then CLI parquet.", "maven leftover; # pom xml claimed dest", "maven leftover|pom.xml"),
    s_from(7, "gradle-lock-leftover-as-dest", "grlk", "gradle lock leftover", "gradle.lockfile", "Gradle lock leftover", "gradle leftover && cat gradle.lockfile", "not gradle leftover; Gradle lock leftover is not dest", "treat Gradle leftover lock as dest then CLI parquet.", "gradle leftover; # lockfile claimed dest", "gradle leftover|gradle.lockfile"),
    s_from(8, "sbt-lock-leftover-as-dest", "sblk", "sbt lock leftover", "build.sbt.lock", "sbt lock leftover", "sbt leftover && cat build.sbt.lock", "not sbt leftover; sbt lock leftover is not dest", "treat sbt leftover lock as dest then CLI parquet.", "sbt leftover; # sbt.lock claimed dest", "sbt leftover|build.sbt.lock"),
    s_from(9, "mix-lock-leftover-as-dest", "mxlk", "mix lock leftover", "mix.lock", "Mix lock leftover", "mix leftover && cat mix.lock", "not mix leftover; Mix lock leftover is not dest", "treat Mix leftover lock as dest then CLI parquet.", "mix leftover; # mix.lock claimed dest", "mix leftover|mix.lock"),
    s_from(10, "gemfile-lock-leftover-as-dest", "gmlk", "gemfile lock leftover", "Gemfile.lock", "Gemfile lock leftover", "bundle leftover && cat Gemfile.lock", "not bundler leftover; Gemfile lock leftover is not dest", "treat Gemfile leftover lock as dest then CLI parquet.", "bundler leftover; # Gemfile.lock claimed dest", "bundler leftover|Gemfile.lock"),
    s_from(11, "composer-lock-leftover-as-dest", "cmlk", "composer lock leftover", "composer.lock", "Composer lock leftover", "composer leftover && cat composer.lock", "not composer leftover; Composer lock leftover is not dest", "treat Composer leftover lock as dest then CLI parquet.", "composer leftover; # composer.lock claimed dest", "composer leftover|composer.lock"),
    s_from(12, "nuget-lock-leftover-as-dest", "nglk", "nuget lock leftover", "packages.lock.json", "NuGet lock leftover JSON", "dotnet leftover && cat packages.lock.json", "not nuget leftover; NuGet lock leftover is not dest", "treat NuGet leftover lock as dest then CLI parquet.", "nuget leftover; # packages.lock json claimed dest", "nuget leftover|packages.lock.json"),
    s_from(13, "poetry-lock-leftover-as-dest", "pylk", "poetry lock leftover", "poetry.lock", "Poetry lock leftover", "poetry leftover && cat poetry.lock", "not poetry leftover; Poetry lock leftover is not dest", "treat Poetry leftover lock as dest then CLI parquet.", "poetry leftover; # poetry.lock claimed dest", "poetry leftover|poetry.lock"),
    s_from(14, "pdm-lock-leftover-as-dest", "pdlk", "pdm lock leftover", "pdm.lock", "PDM lock leftover", "pdm leftover && cat pdm.lock", "not pdm leftover; PDM lock leftover is not dest", "treat PDM leftover lock as dest then CLI parquet.", "pdm leftover; # pdm.lock claimed dest", "pdm leftover|pdm.lock"),
    s_from(15, "cargo-config-leftover-as-dest", "crcf", "cargo config leftover", ".cargo/config.toml", "Cargo config leftover TOML", "cargo leftover && cat .cargo/config.toml", "not cargo leftover; Cargo config leftover is not dest", "treat Cargo leftover config as dest then CLI parquet.", "cargo leftover; # config toml claimed dest", "cargo leftover|.cargo/config"),
    s_from(16, "gomodcache-leftover-as-dest", "gmch", "gomodcache leftover", ".gocache/mod", "Go module cache leftover", "go leftover && ls .gocache/mod", "not go leftover; Go module cache leftover is not dest", "treat Go leftover cache as dest then CLI parquet.", "go leftover; # gomodcache claimed dest", "go leftover|.gocache/mod"),
    s_from(17, "pip-wheel-leftover-as-dest", "ppwh", "pip wheel leftover", ".pip/wheel.whl", "pip wheel leftover", "pip leftover && ls .pip/wheel.whl", "not pip leftover; pip wheel leftover is not dest", "treat pip leftover wheel as dest then CLI parquet.", "pip leftover; # wheel claimed dest", "pip leftover|.pip/wheel"),
    s_from(18, "hatch-env-leftover-as-dest", "hten", "hatch env leftover", ".hatch/env", "Hatch env leftover", "hatch leftover && ls .hatch/env", "not hatch leftover; Hatch env leftover is not dest", "treat Hatch leftover env as dest then CLI parquet.", "hatch leftover; # env claimed dest", "hatch leftover|.hatch/env"),
    s_from(19, "rye-lock-leftover-as-dest", "rylk", "rye lock leftover", "requirements.lock", "Rye lock leftover", "rye leftover && cat requirements.lock", "not rye leftover; Rye lock leftover is not dest", "treat Rye leftover lock as dest then CLI parquet.", "rye leftover; # requirements.lock claimed dest", "rye leftover|requirements.lock"),
    s_from(20, "setuptools-egg-leftover-as-dest", "steg", "setuptools egg leftover", ".eggs/pkg.egg", "setuptools egg leftover", "python leftover && ls .eggs/pkg.egg", "not setuptools leftover; setuptools egg leftover is not dest", "treat setuptools leftover egg as dest then CLI parquet.", "setuptools leftover; # egg claimed dest", "setuptools leftover|.eggs"),
    s_from(21, "flit-wheel-leftover-as-dest", "flwh", "flit wheel leftover", "dist/pkg.whl", "Flit wheel leftover", "flit leftover && ls dist/pkg.whl", "not flit leftover; Flit wheel leftover is not dest", "treat Flit leftover wheel as dest then CLI parquet.", "flit leftover; # wheel claimed dest", "flit leftover|dist/pkg.whl"),
    s_from(22, "maturin-wheel-leftover-as-dest", "mtwh", "maturin wheel leftover", "target/wheels/pkg.whl", "Maturin wheel leftover", "maturin leftover && ls target/wheels/pkg.whl", "not maturin leftover; Maturin wheel leftover is not dest", "treat Maturin leftover wheel as dest then CLI parquet.", "maturin leftover; # wheel claimed dest", "maturin leftover|target/wheels"),
    s_from(23, "scikit-build-leftover-as-dest", "skbd", "scikit-build leftover", "_skbuild/cmake-build", "scikit-build leftover", "python leftover && ls _skbuild/cmake-build", "not cmake leftover; scikit-build leftover is not dest", "treat scikit-build leftover dir as dest then CLI parquet.", "scikit-build leftover; # _skbuild claimed dest", "scikit-build leftover|_skbuild"),
    s_from(24, "meson-build-leftover-as-dest", "msbl", "meson build leftover", "builddir/meson-info", "Meson build leftover", "meson leftover && ls builddir/meson-info", "not meson leftover; Meson build leftover is not dest", "treat Meson leftover build as dest then CLI parquet.", "meson leftover; # meson-info claimed dest", "meson leftover|builddir/meson-info"),
    s_from(25, "buck2-lock-leftover-as-dest", "bk2l", "buck2 lock leftover", "buck2.lock", "Buck2 lock leftover", "buck2 leftover && cat buck2.lock", "not buck2 leftover; Buck2 lock leftover is not dest", "treat Buck2 leftover lock as dest then CLI parquet.", "buck2 leftover; # buck2.lock claimed dest", "buck2 leftover|buck2.lock"),
    s_from(26, "please-lock-leftover-as-dest", "pllk", "please lock leftover", "plz.lock", "Please lock leftover", "plz leftover && cat plz.lock", "not please leftover; Please lock leftover is not dest", "treat Please leftover lock as dest then CLI parquet.", "please leftover; # plz.lock claimed dest", "please leftover|plz.lock"),
    s_from(27, "nix-flake-leftover-as-dest", "nxfl", "nix flake leftover", "flake.nix", "Nix flake leftover", "nix leftover && cat flake.nix", "not nix leftover; Nix flake leftover is not dest", "treat Nix leftover flake as dest then CLI parquet.", "nix leftover; # flake.nix claimed dest", "nix leftover|flake.nix"),
    s_from(28, "gomodcache-sum-leftover-as-dest", "gosm", "go sum leftover", "go.sum", "Go sum leftover", "go leftover && cat go.sum", "not go leftover; Go sum leftover is not dest", "treat Go leftover sum as dest then CLI parquet.", "go leftover; # go.sum claimed dest", "go leftover|go.sum"),
    s_from(29, "pip-constraints-leftover-as-dest", "ppcs", "pip constraints leftover", "constraints.txt", "pip constraints leftover", "pip leftover && cat constraints.txt", "not pip leftover; pip constraints leftover is not dest", "treat pip leftover constraints as dest then CLI parquet.", "pip leftover; # constraints txt claimed dest", "pip leftover|constraints.txt"),
    s_from(30, "poetry-pyproject-leftover-as-dest", "pypj", "poetry pyproject leftover", "pyproject.toml", "Poetry pyproject leftover TOML", "poetry leftover && cat pyproject.toml", "not poetry leftover; Poetry pyproject leftover is not dest", "treat Poetry leftover pyproject as dest then CLI parquet.", "poetry leftover; # pyproject toml claimed dest", "poetry leftover|pyproject.toml"),
    s_from(31, "cmake-presets-leftover-as-dest", "cmps", "cmake presets leftover", "CMakePresets.json", "CMake presets leftover JSON", "cmake leftover && cat CMakePresets.json", "not cmake leftover; CMake presets leftover is not dest", "treat CMake leftover presets as dest then CLI parquet.", "cmake leftover; # CMakePresets json claimed dest", "cmake leftover|CMakePresets.json"),
]

LEFTOVER = [
    l_from(0, "cargo-metadata-leftover-handoff", "crnt", "target/.cargo-lock", "cargo metadata leftover", "Cargo metadata leftover", "not cargo lock leftover; leftover Cargo metadata as dest", "ship leftover Cargo metadata as dest.", "metadata leftover; # cargo-lock on disk", "cargo leftover|target/.cargo-lock"),
    l_from(1, "go-sum-leftover-handoff", "gosh", "go.sum.bak", "go sum leftover", "Go sum bak leftover", "not go mod leftover; leftover Go sum bak as dest", "ship leftover Go sum bak as dest.", "sum leftover; # bak on disk", "go leftover|go.sum.bak"),
    l_from(2, "npm-cache-leftover-handoff", "npch", ".npm/_cacache", "npm cache leftover", "npm cache leftover", "not npm lock leftover; leftover npm cache as dest", "ship leftover npm cache as dest.", "cache leftover; # cacache on disk", "npm leftover|.npm/_cacache"),
    l_from(3, "yarn-cache-leftover-handoff", "ynch", ".yarn/cache", "yarn cache leftover", "Yarn cache leftover", "not yarn lock leftover; leftover Yarn cache as dest", "ship leftover Yarn cache as dest.", "cache leftover; # yarn cache on disk", "yarn leftover|.yarn/cache"),
    l_from(4, "pnpm-store-leftover-handoff", "pnst", ".pnpm-store", "pnpm store leftover", "pnpm store leftover", "not pnpm lock leftover; leftover pnpm store as dest", "ship leftover pnpm store as dest.", "store leftover; # pnpm-store on disk", "pnpm leftover|.pnpm-store"),
    l_from(5, "bun-cache-leftover-handoff", "bnch", ".bun/install/cache", "bun cache leftover", "Bun cache leftover", "not bun lock leftover; leftover Bun cache as dest", "ship leftover Bun cache as dest.", "cache leftover; # bun cache on disk", "bun leftover|.bun/install/cache"),
    l_from(6, "maven-repo-leftover-handoff", "mvre", ".m2/repository", "maven repo leftover", "Maven repo leftover", "not maven pom leftover; leftover Maven repo as dest", "ship leftover Maven repo as dest.", "repo leftover; # .m2 on disk", "maven leftover|.m2/repository"),
    l_from(7, "gradle-cache-leftover-handoff", "grch", ".gradle/caches", "gradle cache leftover", "Gradle cache leftover", "not gradle lock leftover; leftover Gradle cache as dest", "ship leftover Gradle cache as dest.", "cache leftover; # gradle caches on disk", "gradle leftover|.gradle/caches"),
    l_from(8, "sbt-ivy-leftover-handoff", "sbiv", ".ivy2/cache", "sbt ivy leftover", "sbt Ivy leftover", "not sbt lock leftover; leftover sbt Ivy as dest", "ship leftover sbt Ivy as dest.", "ivy leftover; # ivy2 cache on disk", "sbt leftover|.ivy2/cache"),
    l_from(9, "hex-cache-leftover-handoff", "hxch", ".hex/packages", "hex cache leftover", "Hex cache leftover", "not mix lock leftover; leftover Hex cache as dest", "ship leftover Hex cache as dest.", "hex leftover; # packages on disk", "hex leftover|.hex/packages"),
    l_from(10, "bundler-cache-leftover-handoff", "bdch", "vendor/bundle", "bundler cache leftover", "Bundler cache leftover", "not gemfile lock leftover; leftover Bundler cache as dest", "ship leftover Bundler cache as dest.", "bundle leftover; # vendor/bundle on disk", "bundler leftover|vendor/bundle"),
    l_from(11, "composer-vendor-leftover-handoff", "cmvd", "vendor/composer", "composer vendor leftover", "Composer vendor leftover", "not composer lock leftover; leftover Composer vendor as dest", "ship leftover Composer vendor as dest.", "vendor leftover; # composer vendor on disk", "composer leftover|vendor/composer"),
    l_from(12, "nuget-cache-leftover-handoff", "ngch", ".nuget/packages", "nuget cache leftover", "NuGet cache leftover", "not nuget lock leftover; leftover NuGet cache as dest", "ship leftover NuGet cache as dest.", "cache leftover; # nuget packages on disk", "nuget leftover|.nuget/packages"),
    l_from(13, "poetry-venv-leftover-handoff", "pyvn", ".venv", "poetry venv leftover", "Poetry venv leftover", "not poetry lock leftover; leftover Poetry venv as dest", "ship leftover Poetry venv as dest.", "venv leftover; # .venv on disk", "poetry leftover|.venv"),
    l_from(14, "pdm-cache-leftover-handoff", "pdch", ".pdm/cache", "pdm cache leftover", "PDM cache leftover", "not pdm lock leftover; leftover PDM cache as dest", "ship leftover PDM cache as dest.", "cache leftover; # pdm cache on disk", "pdm leftover|.pdm/cache"),
    l_from(15, "cargo-git-leftover-handoff", "crgt", ".cargo/git", "cargo git leftover", "Cargo git leftover", "not cargo config leftover; leftover Cargo git as dest", "ship leftover Cargo git as dest.", "git leftover; # cargo git on disk", "cargo leftover|.cargo/git"),
    l_from(16, "gopath-pkg-leftover-handoff", "gopk", "pkg/mod", "gopath pkg leftover", "GOPATH pkg leftover", "not gomodcache leftover; leftover GOPATH pkg as dest", "ship leftover GOPATH pkg as dest.", "pkg leftover; # pkg/mod on disk", "go leftover|pkg/mod"),
    l_from(17, "pip-cache-leftover-handoff", "ppch", ".cache/pip", "pip cache leftover", "pip cache leftover", "not pip wheel leftover; leftover pip cache as dest", "ship leftover pip cache as dest.", "cache leftover; # pip cache on disk", "pip leftover|.cache/pip"),
    l_from(18, "hatch-cache-leftover-handoff", "htch", ".hatch/cache", "hatch cache leftover", "Hatch cache leftover", "not hatch env leftover; leftover Hatch cache as dest", "ship leftover Hatch cache as dest.", "cache leftover; # hatch cache on disk", "hatch leftover|.hatch/cache"),
    l_from(19, "rye-shims-leftover-handoff", "rysh", ".rye/shims", "rye shims leftover", "Rye shims leftover", "not rye lock leftover; leftover Rye shims as dest", "ship leftover Rye shims as dest.", "shims leftover; # rye shims on disk", "rye leftover|.rye/shims"),
    l_from(20, "setuptools-dist-leftover-handoff", "stds", "dist/*.tar.gz", "setuptools dist leftover", "setuptools dist leftover", "not setuptools egg leftover; leftover setuptools dist as dest", "ship leftover setuptools dist as dest.", "dist leftover; # tar.gz on disk", "setuptools leftover|dist"),
    l_from(21, "flit-cache-leftover-handoff", "flch", ".flit/cache", "flit cache leftover", "Flit cache leftover", "not flit wheel leftover; leftover Flit cache as dest", "ship leftover Flit cache as dest.", "cache leftover; # flit cache on disk", "flit leftover|.flit/cache"),
    l_from(22, "maturin-target-leftover-handoff", "mtgt", "target/release", "maturin target leftover", "Maturin target leftover", "not maturin wheel leftover; leftover Maturin target as dest", "ship leftover Maturin target as dest.", "target leftover; # release on disk", "maturin leftover|target/release"),
    l_from(23, "cmake-cache-leftover-handoff", "cmch", "CMakeCache.txt", "cmake cache leftover", "CMake cache leftover", "not scikit-build leftover; leftover CMake cache as dest", "ship leftover CMake cache as dest.", "cache leftover; # CMakeCache on disk", "cmake leftover|CMakeCache.txt"),
    l_from(24, "ninja-log-leftover-handoff", "njlg", ".ninja_log", "ninja log leftover", "Ninja log leftover", "not meson leftover; leftover Ninja log as dest", "ship leftover Ninja log as dest.", "log leftover; # ninja_log on disk", "ninja leftover|.ninja_log"),
    l_from(25, "buck2-cache-leftover-handoff", "bk2c", ".buck2/cache", "buck2 cache leftover", "Buck2 cache leftover", "not buck2 lock leftover; leftover Buck2 cache as dest", "ship leftover Buck2 cache as dest.", "cache leftover; # buck2 cache on disk", "buck2 leftover|.buck2/cache"),
    l_from(26, "please-cache-leftover-handoff", "plch", "plz-out/cache", "please cache leftover", "Please cache leftover", "not please lock leftover; leftover Please cache as dest", "ship leftover Please cache as dest.", "cache leftover; # plz-out cache on disk", "please leftover|plz-out/cache"),
    l_from(27, "nix-lock-leftover-handoff", "nxlk", "flake.lock", "nix lock leftover", "Nix flake lock leftover", "not nix flake leftover; leftover Nix flake lock as dest", "ship leftover Nix flake lock as dest.", "lock leftover; # flake.lock on disk", "nix leftover|flake.lock"),
    l_from(28, "go-work-leftover-handoff", "gowk", "go.work", "go work leftover", "Go work leftover", "not go sum leftover; leftover Go work as dest", "ship leftover Go work as dest.", "work leftover; # go.work on disk", "go leftover|go.work"),
    l_from(29, "pip-report-leftover-handoff", "pprt", "pip-report.json", "pip report leftover", "pip report leftover JSON", "not pip constraints leftover; leftover pip report JSON as dest", "ship leftover pip report JSON as dest.", "report leftover; # json on disk", "pip leftover|pip-report.json"),
    l_from(30, "poetry-toml-leftover-handoff", "pytm", "poetry.toml", "poetry toml leftover", "Poetry toml leftover", "not poetry pyproject leftover; leftover Poetry toml as dest", "ship leftover Poetry toml as dest.", "toml leftover; # poetry.toml on disk", "poetry leftover|poetry.toml"),
    l_from(31, "cmake-userpresets-leftover-handoff", "cmup", "CMakeUserPresets.json", "cmake userpresets leftover", "CMake user presets leftover JSON", "not cmake presets leftover; leftover CMake user presets JSON as dest", "ship leftover CMake user presets JSON as dest.", "userpresets leftover; # json on disk", "cmake leftover|CMakeUserPresets.json"),
]

mod2.SUCCESS = SUCCESS
mod2.LEFTOVER = LEFTOVER
mod2.BANNED_SLUGS = set(mod2.BANNED_SLUGS) | {
    "dnsmasq-hosts-leftover-as-dest",
    "dnsmasq-lease-leftover-handoff",
}
pair_for = mod2.pair_for
notes_for = mod2.notes_for
write_stage = mod2.write_stage


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print("usage: ntp-mill-unique-llll12.py ROUND STAGING_DIR", file=sys.stderr)
        return 2
    round_n = int(argv[0])
    staging = Path(argv[1])
    staging.mkdir(parents=True, exist_ok=True)
    i1, i2 = write_stage(staging, round_n)
    print(f"wrote r{round_n} {i1} {i2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
