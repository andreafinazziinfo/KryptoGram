"""Unit test suite per i 6 Pilastri di Sicurezza Avanzata (cyclelab_bridge.py).

Verifica formale conforme al Framework Operativo (1_DESIGN - 9 Pilastri):
1. Proof-of-Work Challenge (Anti-DoS / CPU Exhaustion)
2. Canary Tripwire & Honeypot Manager
3. Memory Locking (VirtualLock/mlock)
4. Duress Vault Anti-Coercizione Fisica
5. Audit Trail Immutabile Append-Only firmato Ed25519
6. Web Defense & CSP Headers
"""

from typing import Any, Dict, List
import pytest
from cyclelab_bridge import (
    ProofOfWorkChallenge,
    CanaryTripwireManager,
    MemoryLock,
    DuressVaultManager,
    AuditTrailChain,
    WebSecurityHeaders,
    VaultMode,
)
from nexa_crypto_v2 import generate_ed25519_keypair


def test_pow_challenge_generation_and_solving() -> None:
    """Verifica generazione, risoluzione e validazione del puzzle Proof-of-Work."""
    challenge_data = ProofOfWorkChallenge.generate_challenge(difficulty=3, ttl_seconds=60)
    chal = challenge_data["challenge"]
    diff = challenge_data["difficulty"]
    ts = challenge_data["timestamp"]

    # Risoluzione
    nonce = ProofOfWorkChallenge.solve_challenge(chal, diff)
    assert ProofOfWorkChallenge.verify_solution(chal, nonce, diff, ts, ttl_seconds=60) is True

    # Rifiuto nonce errato
    assert ProofOfWorkChallenge.verify_solution(chal, nonce + 1, diff, ts, ttl_seconds=60) is False

    # Rifiuto sfida scaduta
    assert ProofOfWorkChallenge.verify_solution(chal, nonce, diff, ts - 120, ttl_seconds=60) is False


def test_canary_tripwire_manager() -> None:
    """Verifica registrazione di token esca e attivazione immediata dei callback di emergenza."""
    canary = CanaryTripwireManager()
    token = canary.register_canary_token()

    assert canary.is_canary(token) is True
    assert canary.is_canary("LEGIT_TOKEN_123") is False

    incidents: List[Dict[str, Any]] = []
    canary.register_emergency_callback(lambda meta: incidents.append(meta))

    # Attivazione honeypot
    triggered = canary.trigger_if_canary(token, {"source_ip": "198.51.100.23", "action": "UNAUTHORIZED_DB_READ"})
    assert triggered is True
    assert len(incidents) == 1
    assert incidents[0]["source_ip"] == "198.51.100.23"

    # Token non esca non attiva allarmi
    assert canary.trigger_if_canary("LEGIT_TOKEN_123") is False
    assert len(incidents) == 1


def test_memory_lock_and_unlock() -> None:
    """Verifica invocazione delle API di sistema VirtualLock/mlock sui buffer sensibili."""
    data = bytearray(b"MatassaSecretHarmonicsAndPivotCoefficients")
    # L'invocazione deve completare senza eccezioni
    locked = MemoryLock.lock_memory(data)
    assert isinstance(locked, bool)
    unlocked = MemoryLock.unlock_memory(data)
    assert isinstance(unlocked, bool)


def test_duress_vault_switching_and_panic_alarm() -> None:
    """Verifica separazione tra caveau reale e caveau di emergenza sotto minaccia fisica."""
    real_data = {"matassa_ip": "FORMULA_PROPRIETARIA_SEGRETISSIMA", "btc_balance": 15.5}
    decoy_data = {"matassa_ip": "MEDIA_MOBILE_SEMPLICE_SIMULATA", "btc_balance": 0.05}

    vault = DuressVaultManager(
        real_payload=real_data,
        decoy_payload=decoy_data,
        real_passphrase="RealEnclavePassword2026!",
        duress_passphrase="PanicDuressPassword911!",
    )

    # 1. Accesso Reale
    mode, payload = vault.unlock("RealEnclavePassword2026!")
    assert mode == VaultMode.REAL
    assert payload["matassa_ip"] == "FORMULA_PROPRIETARIA_SEGRETISSIMA"
    assert vault.panic_triggered is False

    # 2. Accesso sotto Coercizione (Duress)
    panic_alert_called: List[bool] = []
    mode_duress, payload_duress = vault.unlock(
        "PanicDuressPassword911!",
        panic_alert_callback=lambda: panic_alert_called.append(True),
    )
    assert mode_duress == VaultMode.DURESS
    assert payload_duress["matassa_ip"] == "MEDIA_MOBILE_SEMPLICE_SIMULATA"
    assert payload_duress["btc_balance"] == 0.05
    assert vault.panic_triggered is True
    assert len(panic_alert_called) == 1

    # 3. Password errata
    with pytest.raises(ValueError):
        vault.unlock("CompletelyWrongPassword!")


def test_audit_trail_immutable_chain_and_tamper_detection() -> None:
    """Verifica append-only ledger firmato con Ed25519 e rilevamento di manomissioni."""
    vk, sk = generate_ed25519_keypair()
    audit = AuditTrailChain(signing_key=sk, verify_key=vk)

    audit.append_event("ADMIN_LOGIN", {"user": "andrea", "ip": "127.0.0.1"})
    audit.append_event("MATASSA_MODEL_LOADED", {"model_id": "matassa-v4-fourier"})
    audit.append_event("TRADE_ORDER_PLACED", {"symbol": "BTCUSDT", "action": "BUY", "qty": 0.5})

    assert len(audit.chain) == 3
    assert audit.verify_integrity() is True

    # Simulazione Manomissione: un hacker modifica il secondo record
    audit._chain[1]["record"]["details"]["model_id"] = "TAMPERED_FAKE_MODEL"
    assert audit.verify_integrity() is False


def test_web_security_headers_compliance() -> None:
    """Verifica conformità degli header CSP e HSTS per frontend web."""
    headers = WebSecurityHeaders.get_hardened_headers()

    assert "Content-Security-Policy" in headers
    assert "default-src 'self'" in headers["Content-Security-Policy"]
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert "Strict-Transport-Security" in headers
    assert "max-age=63072000" in headers["Strict-Transport-Security"]
