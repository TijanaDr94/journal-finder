"""
Integration and unit tests for the Journal Finder API.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.scorer_bm25 import score_bm25
from app.orchestrator import _blend

client = TestClient(app)


TITLE_AI = (
    "Machine Learning Models for Predicting Post-Hepatectomy Liver Failure:"
    " A Systematic Review"
)
TITLE_MOLECULES = (
    "Atomic-Scale Molecular Dynamics Modeling of Iron Oxides:"
    " Surface Properties and Methodologies"
)
TITLE_PHYSICS = (
    "Transverse Dynamics of Strange Hadrons in Relativistic Heavy-Ion Collisions"
)
TITLE_ENERGIES = (
    "Determinants of Energy Consumption in South Africa:"
    " Evidence from an ARDL Model (1980–2023)"
)


ABSTRACT_AI = (
    "Post-hepatectomy liver failure (PHLF) remains the leading cause of mortality "
    "following hepatic resection, with reported incidence rates ranging from 1.2% to 32%. "
    "Traditional scoring systems such as the Child–Pugh score, Model for End-Stage Liver "
    "Disease (MELD), and Albumin–Bilirubin (ALBI) grade have demonstrated limited predictive "
    "accuracy for PHLF. Machine learning (ML) algorithms have emerged as promising tools "
    "capable of integrating complex, multidimensional clinical data to improve predictive "
    "performance. Gradient boosting approaches (LightGBM/XGBoost) were the most frequent "
    "best-performing architectures, while ANN/deep learning, radiomics-integrated, and "
    "ensemble approaches also showed clinically relevant discrimination. Best reported "
    "non-training AUCs ranged from 0.7927 to 0.981 (median, 0.873). Common predictor "
    "domains included bilirubin-based liver function measures, coagulation variables, "
    "platelet count, volumetry or extent of resection, imaging-derived radiomics features, "
    "and perioperative dynamic data."
)

ABSTRACT_MOLECULES = (
    "Iron oxides, including hematite (alpha-Fe2O3), magnetite (Fe3O4), and maghemite "
    "(gamma-Fe2O3), play central roles in catalysis, corrosion, environmental remediation, "
    "magnetic nanotechnology, and energy storage. Molecular dynamics simulations have become "
    "an essential tool for understanding their structural, magnetic, and interfacial behavior "
    "at the atomic scale. This review provides a comprehensive overview of MD methodologies "
    "applied to these materials, spanning classical force fields, reactive force fields, "
    "ab initio molecular dynamics, and emerging machine learning interatomic potentials. "
    "Particular emphasis is placed on facet-dependent surface chemistry, especially the "
    "contrast between compact (111) and open (110) planes, and on adsorption processes "
    "involving water, nitrogen-containing molecules, and representative organic compounds. "
    "The review highlights recent advances in force field development, redox modeling, and "
    "multiscale simulation strategies while critically identifying limitations related to "
    "charge transfer, mixed valence, vacancy ordering, and magnetic–chemical coupling."
)

ABSTRACT_PHYSICS = (
    "We present a study of the mean transverse momentum of identified strange hadrons "
    "(K0S, Lambda, Xi, phi, Omega) produced in Au+Au collisions at RHIC-BES energies "
    "(sqrt(s_NN) = 7.7–39 GeV). The mean transverse momentum is obtained from transverse "
    "momentum spectra measured by the STAR experiment and its dependence on the number of "
    "participants N_part is studied. A centrality dependence of mean pT is observed, with "
    "an increase towards central collisions described using a power-law function. Special "
    "emphasis is placed on the phi-meson, which has a smaller interaction cross-section, "
    "reflecting properties of the early stages of system evolution. Results are compared "
    "with predictions of the default and string-melting versions of the AMPT generator."
)

ABSTRACT_ENERGIES = (
    "This study examines the determinants of energy consumption in South Africa over the "
    "period 1980–2023 using a multivariate time-series framework. The Autoregressive "
    "Distributed Lag (ARDL) approach is employed to estimate both short-run and long-run "
    "relationships. Industrialization and population growth emerge as the most significant "
    "drivers of energy demand, reflecting South Africa's energy-intensive economic structure "
    "and rising demographic pressures. Financial development is found to have a positive and "
    "statistically significant effect, suggesting that improved access to credit stimulates "
    "energy consumption through increased investment and economic activity. The error "
    "correction term is negative and statistically significant, confirming convergence to "
    "long-run equilibrium. The findings underscore the importance of industrial energy "
    "efficiency and population-responsive energy planning for sustainable development."
)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_config():
    resp = client.get("/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "scoring_mode" in data
    assert "llm_available" in data


def test_find_journal_rejects_short_abstract():
    resp = client.post(
        "/find-journal",
        json={"title": TITLE_AI, "abstract": "Too short."},
    )
    assert resp.status_code == 422


def test_find_journal_rejects_missing_title():
    resp = client.post("/find-journal", json={"abstract": ABSTRACT_AI})
    assert resp.status_code == 422


def test_find_journal_rejects_short_title():
    resp = client.post(
        "/find-journal",
        json={"title": "ab", "abstract": ABSTRACT_AI},
    )
    assert resp.status_code == 422


def test_find_journal_returns_four_journals():
    resp = client.post(
        "/find-journal",
        json={"title": TITLE_AI, "abstract": ABSTRACT_AI},
    )
    assert resp.status_code == 200
    assert len(resp.json()["ranked_journals"]) == 4


def test_find_journal_ranks_are_1_to_4():
    resp = client.post(
        "/find-journal",
        json={"title": TITLE_AI, "abstract": ABSTRACT_AI},
    )
    ranks = [journal["rank"] for journal in resp.json()["ranked_journals"]]
    assert ranks == [1, 2, 3, 4]


def test_find_journal_scores_in_0_1():
    resp = client.post(
        "/find-journal",
        json={"title": TITLE_AI, "abstract": ABSTRACT_AI},
    )
    for journal in resp.json()["ranked_journals"]:
        assert 0.0 <= journal["score"] <= 1.0


def test_find_journal_response_shape():
    resp = client.post(
        "/find-journal",
        json={"title": TITLE_AI, "abstract": ABSTRACT_AI},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "ranked_journals" in data
    assert "scoring_method" in data
    first = data["ranked_journals"][0]
    for field in ("journal_id", "journal_name", "score", "rank"):
        assert field in first


def test_find_journal_scoring_method_is_known():
    resp = client.post(
        "/find-journal",
        json={"title": TITLE_AI, "abstract": ABSTRACT_AI},
    )
    assert resp.json()["scoring_method"] in ("bm25", "llm", "hybrid")


@pytest.mark.parametrize("title,abstract,expected_top", [
    (TITLE_AI, ABSTRACT_AI, "ai"),
    (TITLE_MOLECULES, ABSTRACT_MOLECULES, "molecules"),
    (TITLE_PHYSICS, ABSTRACT_PHYSICS, "physics"),
    (TITLE_ENERGIES, ABSTRACT_ENERGIES, "energies"),
])
def test_bm25_top_journal(title, abstract, expected_top):
    results = score_bm25(title=title, abstract=abstract)
    assert results[0]["journal_id"] == expected_top, (
        f"Expected top journal '{expected_top}', got '{results[0]['journal_id']}'. "
        f"Full ranking: {[result['journal_id'] for result in results]}"
    )


def test_bm25_returns_four_results():
    results = score_bm25(title=TITLE_AI, abstract=ABSTRACT_AI)
    assert len(results) == 4


def test_bm25_scores_descending():
    results = score_bm25(title=TITLE_AI, abstract=ABSTRACT_AI)
    scores = [result["score"] for result in results]
    assert scores == sorted(scores, reverse=True)


def test_bm25_scores_sum_to_positive():
    results = score_bm25(title=TITLE_AI, abstract=ABSTRACT_AI)
    assert sum(result["score"] for result in results) > 0


def test_bm25_all_journal_ids_known():
    from app.journals import JOURNAL_MAP
    results = score_bm25(title=TITLE_AI, abstract=ABSTRACT_AI)
    for result in results:
        assert result["journal_id"] in JOURNAL_MAP


def test_blend_alpha_zero_returns_llm_scores():
    bm25 = [
        {"journal_id": "ai", "score": 1.0},
        {"journal_id": "molecules", "score": 0.0},
    ]
    llm = [
        {"journal_id": "molecules", "score": 1.0, "reasoning": "..."},
        {"journal_id": "ai", "score": 0.0, "reasoning": "..."},
    ]
    blended = _blend(bm25, llm, alpha=0.0)
    by_id = {entry["journal_id"]: entry["score"] for entry in blended}
    assert by_id["molecules"] == 1.0
    assert by_id["ai"] == 0.0


def test_blend_alpha_one_returns_bm25_scores():
    bm25 = [
        {"journal_id": "ai", "score": 1.0},
        {"journal_id": "molecules", "score": 0.0},
    ]
    llm = [
        {"journal_id": "molecules", "score": 1.0, "reasoning": "..."},
        {"journal_id": "ai", "score": 0.0, "reasoning": "..."},
    ]
    blended = _blend(bm25, llm, alpha=1.0)
    by_id = {entry["journal_id"]: entry["score"] for entry in blended}
    assert by_id["ai"] == 1.0
    assert by_id["molecules"] == 0.0


def test_blend_alpha_half_averages_scores():
    bm25 = [
        {"journal_id": "ai", "score": 1.0},
        {"journal_id": "molecules", "score": 0.0},
    ]
    llm = [
        {"journal_id": "molecules", "score": 1.0, "reasoning": "..."},
        {"journal_id": "ai", "score": 0.0, "reasoning": "..."},
    ]
    blended = _blend(bm25, llm, alpha=0.5)
    by_id = {entry["journal_id"]: entry["score"] for entry in blended}
    assert by_id["ai"] == 0.5
    assert by_id["molecules"] == 0.5


def test_blend_preserves_llm_reasoning():
    bm25 = [{"journal_id": "ai", "score": 0.5}]
    llm = [{"journal_id": "ai", "score": 0.5, "reasoning": "transformer architecture fits"}]
    blended = _blend(bm25, llm, alpha=0.3)
    assert blended[0]["reasoning"] == "transformer architecture fits"