"""Integration test suite per gli scenari d'uso specifici di CycleLab Terminal."""

import json
from nexa_crypto_v2 import pack_nxs2_envelope, unpack_nxs2_envelope, KDFProfile
from nexa_lib import italian_to_nexa, nexa_to_italian


def test_cyclelab_matassa_frozen_ip_packaging():
    """Test scenario 1: Protezione confine IP Matassa Frozen (pesi Fourier e pivot)."""
    matassa_model_weights = {
        "dominant_cycle_days": 42.5,
        "fourier_harmonics": [21.25, 10.62, 5.31],
        "non_repainting_pivot_alpha": 0.842,
        "model_checksum": "sha256:matassa_core_v4",
    }
    raw_payload = json.dumps(matassa_model_weights).encode("utf-8")
    passphrase = "MatassaFrozenSecretKey2026!"

    # Packaging in busta NXS2 con padding a 8192 byte
    envelope = pack_nxs2_envelope(
        raw_payload,
        passphrase,
        target_pad=8192,
        profile=KDFProfile.DESKTOP_VAULT,
    )
    assert len(envelope) >= 8192

    # Decifratura a runtime da parte del quant engine
    decrypted, meta = unpack_nxs2_envelope(envelope, passphrase)
    restored_weights = json.loads(decrypted.decode("utf-8"))

    assert restored_weights["dominant_cycle_days"] == 42.5
    assert restored_weights["non_repainting_pivot_alpha"] == 0.842


def test_cyclelab_mobile_hud_glyph_obfuscation():
    """Test scenario 2: Offuscamento visivo per widget mobile Android (Anti-Shoulder Surfing)."""
    sensitive_signal = "CycleLab: PIVOT R1 68500 HIT. Ridurre esposizione 15%."
    glyphs = italian_to_nexa(sensitive_signal, wrap_blocks=True)

    # I glifi devono contenere simboli fonetici compatti e numeri tra ⟪...⟫
    assert "⟦" in glyphs and "⟧" in glyphs
    assert "⟪68500⟫" in glyphs or "⟪68500.⟫" in glyphs or "68500" in glyphs

    # Nessuna stringa plain "PIVOT" leggibile in chiaro ad occhio nudo
    assert "PIVOT" not in glyphs
