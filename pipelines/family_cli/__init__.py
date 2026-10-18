"""Subcommand runner shared by the plant-family ``cli`` modules.

``runner`` holds the dispatch, exit-code, refusal and output code that the
nelb, maos, pkg, ffpc and mill ``cli`` modules used to repeat. Like the
packages it serves, every module here ends with ``bind_import_twin(__name__)``,
so ``family_cli.x`` (with ``pipelines/`` on ``sys.path``) and
``pipelines.family_cli.x`` are one object.
"""

from .runner import bind_import_twin

__all__ = ["runner"]

bind_import_twin(__name__)
