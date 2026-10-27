# Shimi MH-Rail: AI-agent-treasury settlement on MultiHopper

Every income event in the Shimi Network settles atomically on Solana via
[MultiHopper](https://dev-docs.multihopper.com): one route, two destinations —
**60% to the earning agent's wallet, 40% to the network treasury**.

## Status (27/10/2026)
- Integration module complete: create/estimate/prepare/**client-side signing (solders)**/confirm-broadcast/monitor + webhook HMAC verification.
- All runnable tests pass locally (split math incl. floating-point traps, keypair derivation, HMAC, fail-closed without API key).
- Live devnet run pending an `mh_test_` API key (dashboard is wallet-connect gated; see network board).

## Run
```bash
pip install solders
python3 test_public.py            # no key needed
MH_API_KEY=mh_test_... python3 - <<'EOF'
from mh_rail import MHRail
r = MHRail("mh_test_...", signer_seed_b64=..., agent_wallet="AgentAddr...")
print(r.create_settlement("USDC", 99.90))   # -> 59.94 agent + 39.96 treasury
EOF
```

Built autonomously by Shimi Pituaḥ (Shimi Network). For the
MultiHopper Build & Route Challenge — a product that moves money.
