"""La IA no inventa resultados.

Fallos que previene:
- Sin pesos, el servicio corría con pesos aleatorios y devolvía diagnósticos.
- Una ecografía normal (0,95 en la clase «normal») salía con score_global 0,95
  y el backend la marcaba como riesgo ALTO.
- Campos fijos que parecían medidos: actividad_cardiaca False (se lee como
  «sin latido») y líquido amniótico «normal».
- /health decía «healthy» siempre.

Ejecutar: python -m pytest test_ia_honesta.py -v
"""
import numpy as np
import pytest

torch = pytest.importorskip("torch")

from fastapi.testclient import TestClient  # noqa: E402

from app import config  # noqa: E402
from app.models import PATHOLOGY_CLASSES, ModelManager  # noqa: E402


def test_sin_pesos_no_hay_modelo(monkeypatch, tmp_path):
    monkeypatch.setitem(config.MODEL_PATHS, "efficientnet_b4", str(tmp_path / "no_existe.pth"))
    m = ModelManager()
    assert m.load_models() is False
    assert m.model is None
    r = m.analyze(np.zeros((64, 64, 3), dtype=np.uint8))
    assert r["status"] == "fallback"
    assert r["pathology_detection"]["pathologies"] == []


class _RedFalsa(torch.nn.Module):
    """Devuelve logits fijos: «normal» muy alta, el resto muy bajas."""

    def forward(self, x):
        logits = torch.full((1, len(PATHOLOGY_CLASSES)), -6.0)
        logits[0, PATHOLOGY_CLASSES.index("normal")] = 4.0
        return logits, torch.zeros((1, 5))


def _manager_con(red):
    m = ModelManager()
    m.model, m.device, m._loaded = red, torch.device("cpu"), True
    return m


def test_una_ecografia_normal_no_da_score_alto():
    """ESPERADO: score_global < 0,05 (antes 0,98, la probabilidad de «normal»)."""
    r = _manager_con(_RedFalsa()).analyze(np.full((384, 384, 3), 90, dtype=np.uint8), compute_cam=False)
    assert r["pathology_detection"]["pathologies"][0]["pathology"] == "normal"
    assert r["score_global"] < 0.05


def test_no_hay_campos_fijos_que_parezcan_medidos():
    r = _manager_con(_RedFalsa()).analyze(np.full((384, 384, 3), 90, dtype=np.uint8), compute_cam=False)
    assert r["pregnancy_assessment"]["actividad_cardiaca"] is None
    assert r["liquido_amniotico"]["evaluacion"] == "no evaluado"
    assert r["biometry"]["disponible"] is False
    assert r["uso"] == "experimental" and r["advertencia"]
    assert "no son valores SHAP" in r["metodo_riesgos"]


def test_health_dice_la_verdad_sin_modelo():
    from app.main import app

    r = TestClient(app).get("/health")  # sin lifespan: el modelo no se carga
    assert r.status_code == 503
    assert r.json()["model_loaded"] is False
    assert "redes_reales" in r.json()


def test_la_huella_identifica_el_archivo(tmp_path):
    """Cada resultado dice qué pesos exactos lo produjeron (auditoría)."""
    from app.config import huella_sha256

    a, b = tmp_path / "a.pth", tmp_path / "b.pth"
    a.write_bytes(b"pesos-1")
    b.write_bytes(b"pesos-2")
    assert huella_sha256(a) and len(huella_sha256(a)) == 64
    assert huella_sha256(a) != huella_sha256(b)
    assert huella_sha256(tmp_path / "no_existe.pth") is None
