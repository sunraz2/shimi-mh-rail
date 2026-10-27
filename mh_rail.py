#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shimi Network — AI-agent-treasury rail on MultiHopper
Integration module v1.0 (Shimi Pituaḥ, 27/10/2026)
Contract per dev-docs.multihopper.com (verified against source 27/10):
- POST {base}/transfers            create transfer (up to 20 destinations)
- POST {base}/transfers/:id/prepare get serialized tx bundles to sign
- POST {base}/transfers/:id/confirm-broadcast  after client-side signing
- GET  {base}/transfers/:id        monitor
- Webhooks: HMAC-signed events (header per docs)
Signing is client-side (per their agentic guide): solders Keypair.
"""
import json, hmac, hashlib, base64, urllib.request, os, uuid

DEVNET = "https://devnet.multihopper.com/api/v1"
MAINNET = "https://multihopper.com/api/v1"
TREASURY_SOL = "4vMwaTsgjvhxe8sRVwKYsDdktAY25t3FZ8H9UdSNNrdf"  # official treasury address (public-addresses.json)

class MHRail:
    def __init__(self, api_key, base=DEVNET, signer_seed_b64=None, agent_wallet=None, split=(0.6, 0.4)):
        self.api_key, self.base = api_key, base
        self.signer = self._keypair(signer_seed_b64) if signer_seed_b64 else None
        self.agent_wallet, self.treasury = agent_wallet, TREASURY_SOL
        self.split = split  # (agent, treasury)

    @staticmethod
    def _keypair(seed_b64):
        from solders.keypair import Keypair
        seed = base64.b64decode(seed_b64)
        return Keypair.from_seed(seed) if len(seed) == 32 else None

    def _call(self, method, path, payload=None):
        req = urllib.request.Request(self.base + path,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={"Content-Type": "application/json", "x-api-key": self.api_key,
                     "User-Agent": "Mozilla/5.0"}, method=method)
        try:
            return json.loads(urllib.request.urlopen(req, timeout=60).read())
        except urllib.error.HTTPError as e:
            return {"ok": False, "http": e.code, "error": e.read().decode()[:300]}

    def split_amounts(self, total, unit=2):
        """60/40 split with exact remainder handling (agorot-style, no floating loss)."""
        s = int(round(total * 100))  # work in whole units of 0.01
        a = int(s * self.split[0] + 0.5); t = s - a
        return round(a / 100, unit), round(t / 100, unit)

    def estimate(self, token, amount, hop_count=5):
        return self._call("POST", "/transfers/estimate",
            {"token": token, "amount": amount, "hopCount": hop_count})

    def create_settlement(self, token, total, external_id=None):
        """The core product: one route, two destinations — agent 60% + treasury 40%."""
        a, t = self.split_amounts(total)
        return self._call("POST", "/transfers", {
            "token": token, "externalId": external_id or f"shimi-{uuid.uuid4().hex[:12]}",
            "destinations": [
                {"recipientWallet": self.agent_wallet, "amount": a},
                {"recipientWallet": self.treasury,     "amount": t}]})

    def prepare(self, transfer_id):
        return self._call("POST", f"/transfers/{transfer_id}/prepare", {})

    def sign_bundle(self, bundle_b64):
        """Client-side signing per the agentic guide."""
        from solders.transaction import VersionedTransaction
        from solders.message import VersionedMessage
        raw = base64.b64decode(bundle_b64)
        vm = VersionedMessage.deserialize(raw)
        vt = VersionedTransaction.try_sign(vm, [self.signer])
        return base64.b64encode(bytes(vt)).decode()

    def confirm_broadcast(self, transfer_id, signed_bundle):
        return self._call("POST", f"/transfers/{transfer_id}/confirm-broadcast",
            {"signedTransaction": signed_bundle})

    def status(self, transfer_id):
        return self._call("GET", f"/transfers/{transfer_id}")

    @staticmethod
    def verify_webhook(secret, body_bytes, signature_hex):
        expected = hmac.new(secret.encode(), body_bytes, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature_hex)
