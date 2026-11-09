"""Testes às regras de durabilidade e scoring (núcleo da decisão)."""

import unittest

from core.durability_check import evaluate


def _signal(strength, durable=True, stype="analyst"):
    return {
        "ticker": "TEST",
        "signal_type": stype,
        "catalyst_strength": strength,
        "horizon": "10d",
        "durability_12h": durable,
        "convergence_detected": False,
        "reasoning": "teste",
    }


class TestDurability(unittest.TestCase):
    def test_durability_false_descarta_sempre(self):
        # strength alto mas não durável → descarta independentemente do score
        r = evaluate(_signal(10, durable=False), convergence=True)
        self.assertFalse(r.kept)
        self.assertEqual(r.priority, "discard")

    def test_score_baixo_descarta(self):
        r = evaluate(_signal(5), convergence=False)
        self.assertFalse(r.kept)
        self.assertEqual(r.priority, "discard")
        self.assertEqual(r.final_score, 5)

    def test_monitor_6_a_7(self):
        for s in (6, 7):
            r = evaluate(_signal(s), convergence=False)
            self.assertTrue(r.kept)
            self.assertEqual(r.priority, "monitor")

    def test_alta_prioridade_8_mais(self):
        r = evaluate(_signal(8), convergence=False)
        self.assertTrue(r.kept)
        self.assertEqual(r.priority, "high")

    def test_convergencia_soma_3(self):
        # strength 5 (descartaria) + convergência (+3) = 8 → alta prioridade
        r = evaluate(_signal(5), convergence=True)
        self.assertEqual(r.final_score, 8)
        self.assertEqual(r.priority, "high")
        self.assertTrue(r.kept)

    def test_convergencia_empurra_para_monitor(self):
        # strength 4 + 3 = 7 → monitorização
        r = evaluate(_signal(4), convergence=True)
        self.assertEqual(r.final_score, 7)
        self.assertEqual(r.priority, "monitor")


if __name__ == "__main__":
    unittest.main()
