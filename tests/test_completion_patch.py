import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('completion_patch', Path(__file__).resolve().parents[1]/'scripts/patch_omnigent_completion.py')
patch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch)

class CompletionPatchTests(unittest.TestCase):
    def test_exact_source_only_and_idempotent(self):
        changed = patch.patch_text(patch.OLD)
        self.assertEqual(patch.patch_text(changed), changed)
        self.assertEqual(changed, patch.NEW)
        for unexpected in ('different upstream', patch.OLD*2, patch.NEW+patch.OLD):
            with self.assertRaises(ValueError):
                patch.patch_text(unexpected)
