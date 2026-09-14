#!/usr/bin/env python3
"""NTP unique leftover leftover leftover leftover mill wave 13: NEW dest plants. BAN dnsmasq leftover clones."""
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
    s_from(0, "rustc-rlib-leftover-as-dest", "rcrl", "rustc rlib leftover", "target/lib.rlib", "rustc rlib leftover", "rustc leftover && ls target/lib.rlib", "not rust leftover; rustc rlib leftover is not dest", "treat rustc leftover rlib as dest then CLI parquet.", "rustc leftover; # rlib claimed dest", "rustc leftover|target/lib.rlib"),
    s_from(1, "gcc-obj-leftover-as-dest", "gcob", "gcc obj leftover", "build/foo.o", "gcc object leftover", "gcc leftover && ls build/foo.o", "not gcc leftover; gcc object leftover is not dest", "treat gcc leftover object as dest then CLI parquet.", "gcc leftover; # .o claimed dest", "gcc leftover|build/foo.o"),
    s_from(2, "clang-pch-leftover-as-dest", "clpc", "clang pch leftover", "build/foo.pch", "clang PCH leftover", "clang leftover && ls build/foo.pch", "not clang leftover; clang PCH leftover is not dest", "treat clang leftover PCH as dest then CLI parquet.", "clang leftover; # pch claimed dest", "clang leftover|build/foo.pch"),
    s_from(3, "llvm-bitcode-leftover-as-dest", "lvbc", "llvm bitcode leftover", "build/foo.bc", "LLVM bitcode leftover", "opt leftover && ls build/foo.bc", "not llvm leftover; LLVM bitcode leftover is not dest", "treat LLVM leftover bitcode as dest then CLI parquet.", "llvm leftover; # bc claimed dest", "llvm leftover|build/foo.bc"),
    s_from(4, "zig-cache-leftover-as-dest", "zgch", "zig cache leftover", "zig-cache", "Zig cache leftover", "zig leftover && ls zig-cache", "not zig leftover; Zig cache leftover is not dest", "treat Zig leftover cache as dest then CLI parquet.", "zig leftover; # zig-cache claimed dest", "zig leftover|zig-cache"),
    s_from(5, "nim-cache-leftover-as-dest", "nmch", "nim cache leftover", "nimcache", "Nim cache leftover", "nim leftover && ls nimcache", "not nim leftover; Nim cache leftover is not dest", "treat Nim leftover cache as dest then CLI parquet.", "nim leftover; # nimcache claimed dest", "nim leftover|nimcache"),
    s_from(6, "gfortran-mod-leftover-as-dest", "gfmd", "gfortran mod leftover", "build/foo.mod", "gfortran module leftover", "gfortran leftover && ls build/foo.mod", "not gfortran leftover; gfortran module leftover is not dest", "treat gfortran leftover module as dest then CLI parquet.", "gfortran leftover; # mod claimed dest", "gfortran leftover|build/foo.mod"),
    s_from(7, "ocaml-cmi-leftover-as-dest", "ocmi", "ocaml cmi leftover", "_build/foo.cmi", "OCaml cmi leftover", "ocamlc leftover && ls _build/foo.cmi", "not ocaml leftover; OCaml cmi leftover is not dest", "treat OCaml leftover cmi as dest then CLI parquet.", "ocaml leftover; # cmi claimed dest", "ocaml leftover|_build/foo.cmi"),
    s_from(8, "ghc-hi-leftover-as-dest", "gchi", "ghc hi leftover", "dist/foo.hi", "GHC hi leftover", "ghc leftover && ls dist/foo.hi", "not ghc leftover; GHC hi leftover is not dest", "treat GHC leftover hi as dest then CLI parquet.", "ghc leftover; # hi claimed dest", "ghc leftover|dist/foo.hi"),
    s_from(9, "javac-class-leftover-as-dest", "jvcl", "javac class leftover", "target/Foo.class", "javac class leftover", "javac leftover && ls target/Foo.class", "not javac leftover; javac class leftover is not dest", "treat javac leftover class as dest then CLI parquet.", "javac leftover; # class claimed dest", "javac leftover|target/Foo.class"),
    s_from(10, "kotlinc-class-leftover-as-dest", "ktcl", "kotlinc class leftover", "build/Foo.class", "kotlinc class leftover", "kotlinc leftover && ls build/Foo.class", "not kotlinc leftover; kotlinc class leftover is not dest", "treat kotlinc leftover class as dest then CLI parquet.", "kotlinc leftover; # class claimed dest", "kotlinc leftover|build/Foo.class"),
    s_from(11, "scalac-class-leftover-as-dest", "sccl", "scalac class leftover", "target/Foo.class", "scalac class leftover", "scalac leftover && ls target/Foo.class", "not scalac leftover; scalac class leftover is not dest", "treat scalac leftover class as dest then CLI parquet.", "scalac leftover; # class claimed dest", "scalac leftover|target/Foo.class"),
    s_from(12, "csc-dll-leftover-as-dest", "csdl", "csc dll leftover", "bin/Foo.dll", "csc dll leftover", "csc leftover && ls bin/Foo.dll", "not csc leftover; csc dll leftover is not dest", "treat csc leftover dll as dest then CLI parquet.", "csc leftover; # dll claimed dest", "csc leftover|bin/Foo.dll"),
    s_from(13, "swiftc-swiftmodule-leftover-as-dest", "swsm", "swiftc swiftmodule leftover", "build/Foo.swiftmodule", "swiftc swiftmodule leftover", "swiftc leftover && ls build/Foo.swiftmodule", "not swift leftover; swiftc swiftmodule leftover is not dest", "treat swiftc leftover swiftmodule as dest then CLI parquet.", "swiftc leftover; # swiftmodule claimed dest", "swiftc leftover|build/Foo.swiftmodule"),
    s_from(14, "dart-kernel-leftover-as-dest", "dtkn", "dart kernel leftover", "build/app.dill", "Dart kernel leftover", "dart leftover && ls build/app.dill", "not dart leftover; Dart kernel leftover is not dest", "treat Dart leftover kernel as dest then CLI parquet.", "dart leftover; # dill claimed dest", "dart leftover|build/app.dill"),
    s_from(15, "elixir-beam-leftover-as-dest", "exbm", "elixir beam leftover", "_build/foo.beam", "Elixir BEAM leftover", "elixirc leftover && ls _build/foo.beam", "not elixir leftover; Elixir BEAM leftover is not dest", "treat Elixir leftover BEAM as dest then CLI parquet.", "elixir leftover; # beam claimed dest", "elixir leftover|_build/foo.beam"),
    s_from(16, "erlang-beam-leftover-as-dest", "erbm", "erlang beam leftover", "ebin/foo.beam", "Erlang BEAM leftover", "erlc leftover && ls ebin/foo.beam", "not erlang leftover; Erlang BEAM leftover is not dest", "treat Erlang leftover BEAM as dest then CLI parquet.", "erlang leftover; # beam claimed dest", "erlang leftover|ebin/foo.beam"),
    s_from(17, "crystal-o-leftover-as-dest", "croo", "crystal o leftover", "build/foo.o", "Crystal object leftover", "crystal leftover && ls build/foo.o", "not crystal leftover; Crystal object leftover is not dest", "treat Crystal leftover object as dest then CLI parquet.", "crystal leftover; # .o claimed dest", "crystal leftover|build/foo.o"),
    s_from(18, "v-o-leftover-as-dest", "voo", "v o leftover", "build/foo.o", "V object leftover", "v leftover && ls build/foo.o", "not v leftover; V object leftover is not dest", "treat V leftover object as dest then CLI parquet.", "v leftover; # .o claimed dest", "v leftover|build/foo.o"),
    s_from(19, "odin-o-leftover-as-dest", "odoo", "odin o leftover", "build/foo.o", "Odin object leftover", "odin leftover && ls build/foo.o", "not odin leftover; Odin object leftover is not dest", "treat Odin leftover object as dest then CLI parquet.", "odin leftover; # .o claimed dest", "odin leftover|build/foo.o"),
    s_from(20, "mojo-pkg-leftover-as-dest", "mjpk", "mojo pkg leftover", "build/foo.mojopkg", "Mojo package leftover", "mojo leftover && ls build/foo.mojopkg", "not mojo leftover; Mojo package leftover is not dest", "treat Mojo leftover package as dest then CLI parquet.", "mojo leftover; # mojopkg claimed dest", "mojo leftover|build/foo.mojopkg"),
    s_from(21, "julia-ji-leftover-as-dest", "jlji", "julia ji leftover", "compiled/foo.ji", "Julia ji leftover", "julia leftover && ls compiled/foo.ji", "not julia leftover; Julia ji leftover is not dest", "treat Julia leftover ji as dest then CLI parquet.", "julia leftover; # ji claimed dest", "julia leftover|compiled/foo.ji"),
    s_from(22, "r-rds-leftover-as-dest", "rrds", "r rds leftover", "data/foo.rds", "R rds leftover", "R leftover && ls data/foo.rds", "not r leftover; R rds leftover is not dest", "treat R leftover rds as dest then CLI parquet.", "r leftover; # rds claimed dest", "r leftover|data/foo.rds"),
    s_from(23, "matlab-mex-leftover-as-dest", "mlmx", "matlab mex leftover", "mex/foo.mexa64", "MATLAB mex leftover", "matlab leftover && ls mex/foo.mexa64", "not matlab leftover; MATLAB mex leftover is not dest", "treat MATLAB leftover mex as dest then CLI parquet.", "matlab leftover; # mex claimed dest", "matlab leftover|mex/foo.mexa64"),
    s_from(24, "octave-oct-leftover-as-dest", "ococ", "octave oct leftover", "oct/foo.oct", "Octave oct leftover", "octave leftover && ls oct/foo.oct", "not octave leftover; Octave oct leftover is not dest", "treat Octave leftover oct as dest then CLI parquet.", "octave leftover; # oct claimed dest", "octave leftover|oct/foo.oct"),
    s_from(25, "stata-dta-leftover-as-dest", "stdt", "stata dta leftover", "data/foo.dta", "Stata dta leftover", "stata leftover && ls data/foo.dta", "not stata leftover; Stata dta leftover is not dest", "treat Stata leftover dta as dest then CLI parquet.", "stata leftover; # dta claimed dest", "stata leftover|data/foo.dta"),
    s_from(26, "sas-sas7bdat-leftover-as-dest", "ss7b", "sas sas7bdat leftover", "data/foo.sas7bdat", "SAS sas7bdat leftover", "sas leftover && ls data/foo.sas7bdat", "not sas leftover; SAS sas7bdat leftover is not dest", "treat SAS leftover sas7bdat as dest then CLI parquet.", "sas leftover; # sas7bdat claimed dest", "sas leftover|data/foo.sas7bdat"),
    s_from(27, "spss-sav-leftover-as-dest", "spsv", "spss sav leftover", "data/foo.sav", "SPSS sav leftover", "spss leftover && ls data/foo.sav", "not spss leftover; SPSS sav leftover is not dest", "treat SPSS leftover sav as dest then CLI parquet.", "spss leftover; # sav claimed dest", "spss leftover|data/foo.sav"),
    s_from(28, "nasm-o-leftover-as-dest", "nsoo", "nasm o leftover", "build/foo.o", "NASM object leftover", "nasm leftover && ls build/foo.o", "not nasm leftover; NASM object leftover is not dest", "treat NASM leftover object as dest then CLI parquet.", "nasm leftover; # .o claimed dest", "nasm leftover|build/foo.o"),
    s_from(29, "yasm-o-leftover-as-dest", "ysoo", "yasm o leftover", "build/foo.o", "YASM object leftover", "yasm leftover && ls build/foo.o", "not yasm leftover; YASM object leftover is not dest", "treat YASM leftover object as dest then CLI parquet.", "yasm leftover; # .o claimed dest", "yasm leftover|build/foo.o"),
    s_from(30, "fasm-o-leftover-as-dest", "fsoo", "fasm o leftover", "build/foo.o", "FASM object leftover", "fasm leftover && ls build/foo.o", "not fasm leftover; FASM object leftover is not dest", "treat FASM leftover object as dest then CLI parquet.", "fasm leftover; # .o claimed dest", "fasm leftover|build/foo.o"),
    s_from(31, "fortran-mod-leftover-as-dest", "ftmd", "fortran mod leftover", "build/foo.mod", "Fortran module leftover", "ifort leftover && ls build/foo.mod", "not fortran leftover; Fortran module leftover is not dest", "treat Fortran leftover module as dest then CLI parquet.", "fortran leftover; # mod claimed dest", "fortran leftover|build/foo.mod"),
]

LEFTOVER = [
    l_from(0, "rustc-rmeta-leftover-handoff", "rcrm", "target/lib.rmeta", "rustc rmeta leftover", "rustc rmeta leftover", "not rustc rlib leftover; leftover rustc rmeta as dest", "ship leftover rustc rmeta as dest.", "rmeta leftover; # rmeta on disk", "rustc leftover|target/lib.rmeta"),
    l_from(1, "gcc-dwo-leftover-handoff", "gcdw", "build/foo.dwo", "gcc dwo leftover", "gcc dwo leftover", "not gcc obj leftover; leftover gcc dwo as dest", "ship leftover gcc dwo as dest.", "dwo leftover; # dwo on disk", "gcc leftover|build/foo.dwo"),
    l_from(2, "clang-ast-leftover-handoff", "clas", "build/foo.ast", "clang ast leftover", "clang AST leftover", "not clang pch leftover; leftover clang AST as dest", "ship leftover clang AST as dest.", "ast leftover; # ast on disk", "clang leftover|build/foo.ast"),
    l_from(3, "llvm-ir-leftover-handoff", "lvir", "build/foo.ll", "llvm ir leftover", "LLVM IR leftover", "not llvm bitcode leftover; leftover LLVM IR as dest", "ship leftover LLVM IR as dest.", "ir leftover; # ll on disk", "llvm leftover|build/foo.ll"),
    l_from(4, "zig-o-leftover-handoff", "zgoo", "zig-out/foo.o", "zig o leftover", "Zig object leftover", "not zig cache leftover; leftover Zig object as dest", "ship leftover Zig object as dest.", "o leftover; # .o on disk", "zig leftover|zig-out/foo.o"),
    l_from(5, "nim-c-leftover-handoff", "nmc", "nimcache/foo.c", "nim c leftover", "Nim C leftover", "not nim cache leftover; leftover Nim C as dest", "ship leftover Nim C as dest.", "c leftover; # .c on disk", "nim leftover|nimcache/foo.c"),
    l_from(6, "gfortran-o-leftover-handoff", "gfoo", "build/foo.o", "gfortran o leftover", "gfortran object leftover", "not gfortran mod leftover; leftover gfortran object as dest", "ship leftover gfortran object as dest.", "o leftover; # .o on disk", "gfortran leftover|build/foo.o"),
    l_from(7, "ocaml-cmo-leftover-handoff", "ocmo", "_build/foo.cmo", "ocaml cmo leftover", "OCaml cmo leftover", "not ocaml cmi leftover; leftover OCaml cmo as dest", "ship leftover OCaml cmo as dest.", "cmo leftover; # cmo on disk", "ocaml leftover|_build/foo.cmo"),
    l_from(8, "ghc-o-leftover-handoff", "gcoo", "dist/foo.o", "ghc o leftover", "GHC object leftover", "not ghc hi leftover; leftover GHC object as dest", "ship leftover GHC object as dest.", "o leftover; # .o on disk", "ghc leftover|dist/foo.o"),
    l_from(9, "javac-h-leftover-handoff", "jvh", "target/Foo.h", "javac h leftover", "javac header leftover", "not javac class leftover; leftover javac header as dest", "ship leftover javac header as dest.", "h leftover; # .h on disk", "javac leftover|target/Foo.h"),
    l_from(10, "kotlinc-klib-leftover-handoff", "ktkl", "build/foo.klib", "kotlinc klib leftover", "kotlinc klib leftover", "not kotlinc class leftover; leftover kotlinc klib as dest", "ship leftover kotlinc klib as dest.", "klib leftover; # klib on disk", "kotlinc leftover|build/foo.klib"),
    l_from(11, "scalac-tasty-leftover-handoff", "scts", "target/Foo.tasty", "scalac tasty leftover", "scalac TASTy leftover", "not scalac class leftover; leftover scalac TASTy as dest", "ship leftover scalac TASTy as dest.", "tasty leftover; # tasty on disk", "scalac leftover|target/Foo.tasty"),
    l_from(12, "csc-pdb-leftover-handoff", "cspd", "bin/Foo.pdb", "csc pdb leftover", "csc PDB leftover", "not csc dll leftover; leftover csc PDB as dest", "ship leftover csc PDB as dest.", "pdb leftover; # pdb on disk", "csc leftover|bin/Foo.pdb"),
    l_from(13, "swiftc-swiftdoc-leftover-handoff", "swsd", "build/Foo.swiftdoc", "swiftc swiftdoc leftover", "swiftc swiftdoc leftover", "not swiftc swiftmodule leftover; leftover swiftc swiftdoc as dest", "ship leftover swiftc swiftdoc as dest.", "swiftdoc leftover; # swiftdoc on disk", "swiftc leftover|build/Foo.swiftdoc"),
    l_from(14, "dart-dill-leftover-handoff", "dtdl", "build/kernel.dill", "dart dill leftover", "Dart dill leftover", "not dart kernel leftover; leftover Dart dill as dest", "ship leftover Dart dill as dest.", "dill leftover; # dill on disk", "dart leftover|build/kernel.dill"),
    l_from(15, "elixir-plt-leftover-handoff", "expl", "_build/dialyzer.plt", "elixir plt leftover", "Elixir PLT leftover", "not elixir beam leftover; leftover Elixir PLT as dest", "ship leftover Elixir PLT as dest.", "plt leftover; # plt on disk", "elixir leftover|_build/dialyzer.plt"),
    l_from(16, "erlang-app-leftover-handoff", "erap", "ebin/foo.app", "erlang app leftover", "Erlang app leftover", "not erlang beam leftover; leftover Erlang app as dest", "ship leftover Erlang app as dest.", "app leftover; # app on disk", "erlang leftover|ebin/foo.app"),
    l_from(17, "crystal-cache-leftover-handoff", "crch", ".crystal/cache", "crystal cache leftover", "Crystal cache leftover", "not crystal o leftover; leftover Crystal cache as dest", "ship leftover Crystal cache as dest.", "cache leftover; # crystal cache on disk", "crystal leftover|.crystal/cache"),
    l_from(18, "v-c-leftover-handoff", "vcc", "build/foo.c", "v c leftover", "V C leftover", "not v o leftover; leftover V C as dest", "ship leftover V C as dest.", "c leftover; # .c on disk", "v leftover|build/foo.c"),
    l_from(19, "odin-pdb-leftover-handoff", "odpd", "build/foo.pdb", "odin pdb leftover", "Odin PDB leftover", "not odin o leftover; leftover Odin PDB as dest", "ship leftover Odin PDB as dest.", "pdb leftover; # pdb on disk", "odin leftover|build/foo.pdb"),
    l_from(20, "mojo-ll-leftover-handoff", "mjll", "build/foo.ll", "mojo ll leftover", "Mojo LLVM IR leftover", "not mojo pkg leftover; leftover Mojo LLVM IR as dest", "ship leftover Mojo LLVM IR as dest.", "ll leftover; # ll on disk", "mojo leftover|build/foo.ll"),
    l_from(21, "julia-so-leftover-handoff", "jlso", "compiled/foo.so", "julia so leftover", "Julia so leftover", "not julia ji leftover; leftover Julia so as dest", "ship leftover Julia so as dest.", "so leftover; # so on disk", "julia leftover|compiled/foo.so"),
    l_from(22, "r-rdx-leftover-handoff", "rrdx", "data/foo.rdx", "r rdx leftover", "R rdx leftover", "not r rds leftover; leftover R rdx as dest", "ship leftover R rdx as dest.", "rdx leftover; # rdx on disk", "r leftover|data/foo.rdx"),
    l_from(23, "matlab-mat-leftover-handoff", "mlmt", "data/foo.mat", "matlab mat leftover", "MATLAB mat leftover", "not matlab mex leftover; leftover MATLAB mat as dest", "ship leftover MATLAB mat as dest.", "mat leftover; # mat on disk", "matlab leftover|data/foo.mat"),
    l_from(24, "octave-mat-leftover-handoff", "ocmt", "data/foo.mat", "octave mat leftover", "Octave mat leftover", "not octave oct leftover; leftover Octave mat as dest", "ship leftover Octave mat as dest.", "mat leftover; # mat on disk", "octave leftover|data/foo.mat"),
    l_from(25, "stata-do-leftover-handoff", "stdo", "scripts/foo.do", "stata do leftover", "Stata do leftover", "not stata dta leftover; leftover Stata do as dest", "ship leftover Stata do as dest.", "do leftover; # do on disk", "stata leftover|scripts/foo.do"),
    l_from(26, "sas-log-leftover-handoff", "sslg", "logs/foo.log", "sas log leftover", "SAS log leftover", "not sas sas7bdat leftover; leftover SAS log as dest", "ship leftover SAS log as dest.", "log leftover; # log on disk", "sas leftover|logs/foo.log"),
    l_from(27, "spss-sps-leftover-handoff", "spss", "scripts/foo.sps", "spss sps leftover", "SPSS sps leftover", "not spss sav leftover; leftover SPSS sps as dest", "ship leftover SPSS sps as dest.", "sps leftover; # sps on disk", "spss leftover|scripts/foo.sps"),
    l_from(28, "nasm-lst-leftover-handoff", "nsls", "build/foo.lst", "nasm lst leftover", "NASM listing leftover", "not nasm o leftover; leftover NASM listing as dest", "ship leftover NASM listing as dest.", "lst leftover; # lst on disk", "nasm leftover|build/foo.lst"),
    l_from(29, "yasm-lst-leftover-handoff", "ysls", "build/foo.lst", "yasm lst leftover", "YASM listing leftover", "not yasm o leftover; leftover YASM listing as dest", "ship leftover YASM listing as dest.", "lst leftover; # lst on disk", "yasm leftover|build/foo.lst"),
    l_from(30, "fasm-lst-leftover-handoff", "fsls", "build/foo.lst", "fasm lst leftover", "FASM listing leftover", "not fasm o leftover; leftover FASM listing as dest", "ship leftover FASM listing as dest.", "lst leftover; # lst on disk", "fasm leftover|build/foo.lst"),
    l_from(31, "fortran-o-leftover-handoff", "ftoo", "build/foo.o", "fortran o leftover", "Fortran object leftover", "not fortran mod leftover; leftover Fortran object as dest", "ship leftover Fortran object as dest.", "o leftover; # .o on disk", "fortran leftover|build/foo.o"),
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
        print("usage: ntp-mill-unique-llll13.py ROUND STAGING_DIR", file=sys.stderr)
        return 2
    round_n = int(argv[0])
    staging = Path(argv[1])
    staging.mkdir(parents=True, exist_ok=True)
    i1, i2 = write_stage(staging, round_n)
    print(f"wrote r{round_n} {i1} {i2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
