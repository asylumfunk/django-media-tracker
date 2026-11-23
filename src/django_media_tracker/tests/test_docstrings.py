"""
Check docstring layout across project Python files.
"""

import ast
import subprocess
from pathlib import Path
from unittest import TestCase


class DocstringStyleTests(TestCase):
    """
    Check the physical line count that Ruff's docstring rules leave unchecked.
    """

    def test_docstrings_span_multiple_lines(self) -> None:
        """
        Reject docstrings written on one physical line.
        """
        project_root = Path(__file__).resolve().parents[3]
        files = subprocess.check_output(
            [
                'git',
                'ls-files',
                '-z',
                '--cached',
                '--others',
                '--exclude-standard',
                '--',
                'src/**/*.py',
                'src/*.py',
            ],
            cwd=project_root,
            text=True,
        )
        violations: list[str] = []
        for filename in files.split('\0'):
            if not filename:
                continue
            path = project_root / filename
            tree = ast.parse(path.read_bytes(), filename=filename)
            for node in ast.walk(tree):
                if (
                    not isinstance(
                        node,
                        (
                            ast.Module,
                            ast.ClassDef,
                            ast.FunctionDef,
                            ast.AsyncFunctionDef,
                        ),
                    )
                    or ast.get_docstring(node, clean=False) is None
                ):
                    continue
                docstring = node.body[0]
                if docstring.lineno == docstring.end_lineno:
                    violations.append(f'{filename}:{docstring.lineno}')

        self.assertEqual(violations, [], 'Docstrings must span multiple lines.')
