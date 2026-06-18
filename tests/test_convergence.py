"""
Testes à detecção de convergência (lógica, com Airtable mockado).

Não faz rede: substitui AirtableClient._list por uma função que devolve
registos falsos.
"""

import unittest

from core.airtable_writer import AirtableClient, build_record


class _FakeAirtable(AirtableClient):
    def __init__(self, fake_records):
        # Não chamamos super().__init__ para não exigir env vars/rede.
        self._fake = fake_records

    def _list(self, params):  # noqa: D401 — override
        return self._fake


def _rec(stype):
    return {"fields": {"signal_type": stype, "ticker": "NVDA"}}


class TestConvergence(unittest.TestCase):
    def test_sem_registos_sem_convergencia(self):
        at = _FakeAirtable([])
        c = at.detect_convergence("NVDA", "analyst")
        self.assertFalse(c.detected)
        self.assertFalse(c.distinct_types)

    def test_um_registo_mesmo_tipo_convergencia_sem_distinct(self):
        at = _FakeAirtable([_rec("analyst")])
        c = at.detect_convergence("NVDA", "analyst")
        self.assertTrue(c.detected)
        self.assertFalse(c.distinct_types)  # mesmo tipo, não é prioridade máxima

    def test_tipo_diferente_e_prioridade_maxima(self):
        at = _FakeAirtable([_rec("earnings")])
        c = at.detect_convergence("NVDA", "analyst")
        self.assertTrue(c.detected)
        self.assertTrue(c.distinct_types)  # dois tipos diferentes


class _DummyScored:
    final_score = 9
    priority = "high"


class TestBuildRecord(unittest.TestCase):
    def test_campos_do_airtable(self):
        signal = {
            "ticker": "AMD",
            "signal_type": "earnings",
            "catalyst_strength": 9,
            "horizon": "3d",
            "durability_12h": True,
            "headline": "AMD EPS beat 25%",
        }
        rec = build_record(signal, _DummyScored(), convergence=True, source="benzinga.com")
        # Todos os campos exigidos pela spec presentes
        for field in (
            "date", "ticker", "signal_type", "catalyst_strength", "horizon",
            "durability_12h", "convergence", "headline", "source",
            "raw_score", "alerted",
        ):
            self.assertIn(field, rec)
        self.assertEqual(rec["ticker"], "AMD")
        self.assertTrue(rec["convergence"])
        self.assertTrue(rec["alerted"])  # priority == high
        self.assertEqual(rec["raw_score"], 9)


if __name__ == "__main__":
    unittest.main()
