"""Scénarios de recette finale — NON validés à ce stade.

Ces tests documentent la chaîne attendue (attaque contrôlée → dégradation →
détection ML → remédiation → nouvelle transaction). Ils restent sautés tant
que la calibration et un modèle entraîné sur métriques réelles ne sont pas
en place. Un skip n'est pas un succès de reprise.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.resilience

REASON = (
    "Recette finale non exécutée : modèle réel, calibration de charge et "
    "mesure MTTD/MTTR encore TODO (voir tests/resilience/README.md)."
)


@pytest.mark.skip(reason=REASON)
def test_controlled_attack_from_second_pc() -> None:
    raise AssertionError("non exécuté")


@pytest.mark.skip(reason=REASON)
def test_measurable_degradation() -> None:
    raise AssertionError("non exécuté")


@pytest.mark.skip(reason=REASON)
def test_real_ml_detection_not_synthetic() -> None:
    raise AssertionError("non exécuté")


@pytest.mark.skip(reason=REASON)
def test_automatic_remediation_enables_rate_limit() -> None:
    raise AssertionError("non exécuté")


@pytest.mark.skip(reason=REASON)
def test_legitimate_transaction_succeeds_after_recovery() -> None:
    raise AssertionError("non exécuté")


@pytest.mark.skip(reason=REASON)
def test_no_duplicate_payments_after_incident() -> None:
    raise AssertionError("non exécuté")


@pytest.mark.skip(reason=REASON)
def test_incident_and_actions_are_journaled() -> None:
    raise AssertionError("non exécuté")


@pytest.mark.skip(reason=REASON)
def test_mttd_and_mttr_are_measured() -> None:
    raise AssertionError("non exécuté")
