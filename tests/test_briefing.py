"""Testes ao gerador de briefing markdown."""

import unittest

from core import briefing


def _sig(ticker, score, stype="analyst", conv=False):
    return {
        "ticker": ticker,
        "signal_type": stype,
        "raw_score": score,
        "horizon": "10d",
        "convergence": conv,
        "source": "benzinga.com",
        "headline": f"{ticker} catalisador",
    }


class TestBriefing(unittest.TestCase):
    def setUp(self):
        self.signals = [
            _sig("NVDA", 9, "analyst", conv=True),
            _sig("AMD", 8, "earnings"),
            _sig("TSLA", 6, "rotation"),
            _sig("AAPL", 7, "product"),
        ]
        self.md = briefing.build_briefing(self.signals)

    def test_tem_as_tres_seccoes(self):
        self.assertIn("🔴 Alta Prioridade", self.md)
        self.assertIn("🟡 Monitorização", self.md)
        self.assertIn("📊 Stats do dia", self.md)

    def test_alta_prioridade_contem_score_8_mais(self):
        # NVDA (9) e AMD (8) devem aparecer; secção alta antes da monitorização
        idx_alta = self.md.index("🔴 Alta Prioridade")
        idx_monitor = self.md.index("🟡 Monitorização")
        alta = self.md[idx_alta:idx_monitor]
        self.assertIn("NVDA", alta)
        self.assertIn("AMD", alta)
        self.assertNotIn("TSLA", alta)  # TSLA é 6 → monitorização

    def test_stats_contagens(self):
        self.assertIn("**Total de sinais (score >= 6):** 4", self.md)
        self.assertIn("**Alta prioridade (>= 8):** 2", self.md)
        self.assertIn("**Monitorização (6-7):** 2", self.md)
        self.assertIn("**Convergências detectadas:** 1", self.md)

    def test_briefing_vazio_nao_rebenta(self):
        md = briefing.build_briefing([])
        self.assertIn("Sem sinais de alta prioridade hoje.", md)
        self.assertIn("**Total de sinais (score >= 6):** 0", md)


if __name__ == "__main__":
    unittest.main()
