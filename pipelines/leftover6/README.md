# Leftover6 catalog recovery

This package preserves 32 pair rows and 65 plant rows from the three sealed
GQL, SSL, and SBOX source files. It provides catalog extraction and validation;
it does not generate new records, run publishers, compose datasets, authorize
training, or export a training corpus.

Unpinned input supports literal assignments, unshadowed `dict` keyword
constructors, and `_row` calls bound to the exact reviewed pure helper AST.
Function and lambda bodies remain deferred; their defaults and annotations
must be proven inert. The exact `if __name__ == "__main__"` body remains deferred,
and its import-time `else` branch is checked. Unknown calls, imports, class
creation, control flow, and mutation are refused even when they do not name a
catalog variable. Typed rows must have distinct source identities.

The three preserved sources have a separate, narrow AST text projection:
source path and full UTF-8 SHA-256 must match independently verified Git-byte
pins in `catalog_ast.py`. Caller-supplied blob labels do not grant this exception.
The SBOX archive includes a module-time plant-building call, so its recovered
`_ROWS` are a text projection, not a claim about runtime equivalence. No source
is imported or executed. Any byte change, including an appended call or comment,
loses the archive exception and must satisfy the strict literal-input contract.

The archive regression compares complete extracted rows and source metadata
against the committed catalogs when the immutable Git objects are available.
Literal-input and refusal regressions also run without those Git objects.
