"""Pin the proof inputs retained by the relocated preparation procedures."""
from pathlib import Path
import hashlib
import unittest


ROOT = Path(__file__).resolve().parents[2] / "tools/qualification"
FIXTURE_IDENTITIES = {
    'fixtures/deterministic-support.json': '1db3ba09bc31aa8d8e6bf8fbca73116ad81f760c874908d865b3b905b3b979a6',
    'pre-adoption/eventstore/fixtures/planned-configuration.json': 'b7a6538611813290c1d10286863a47bfee8039d0a6f33028d342e87adce977b0',
    'pre-adoption/folders/fixtures/attempt-1/product-verification.json': 'f1ebb8d194e1fb8e3e53a76970abeb473fed558e32f692f7f1640b186c53605a',
    'pre-adoption/folders/fixtures/attempt-2/product-verification.json': 'd6fdfba8dee398cc02e2484b4b559b0dd4cfa2c6578159975fb3843b40f085b8',
    'pre-adoption/folders/fixtures/attempt-3/product-verification.json': 'd6a1d18ac24ea6863cccadaec1c706badbbb8e3bf10a934ce6faf10d904d64a5',
    'pre-adoption/folders/fixtures/registration-candidate/rendered/Hexalith.Folders/.github/hexalith-ci.json': '06f062f45c547b3015ddc50e0d1ad0e2c5014078c266ff598b40100f86d2f85d',
    'pre-adoption/parties/fixtures/accepted-local-verification.json': '7a4812fa48b67bfbad4ba7add404431de96cf1aabd0d151440dcb67a3d3dd92a',
    'pre-adoption/parties/fixtures/current-preparation-state.json': '946572e3f2ddac6de0c114618739b43f2ad5149b17cba575dd2712b41bc5c66a',
    'pre-adoption/parties/fixtures/current-preparation.patch': '376fe76acb58d3f03428be884c55c999e3559786da67ed628fbc49c784cb7370',
    'pre-adoption/parties/fixtures/runs/20261116T191919Z-3711f8e4/unit-only-preparation.json': '72e0a9a17707488278491642ed823a9b33e834594fdb6bb0ebf7e2007cabd365',
    'pre-adoption/parties/fixtures/whitespace-normalization.json': 'f90c93ea6bf998036befbfe415b700749e14663fb861ba6eed08804dd0ff5c84',
}


class QualificationFixtureTests(unittest.TestCase):
    def test_frozen_proof_inputs_keep_their_recorded_bytes(self):
        for relative, expected in FIXTURE_IDENTITIES.items():
            with self.subTest(path=relative):
                self.assertEqual(expected, hashlib.sha256((ROOT / relative).read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
