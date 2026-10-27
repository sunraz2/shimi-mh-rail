# -*- coding: utf-8 -*-
import os, sys, json, base64, hashlib, hmac
sys.path.insert(0, ".")
from mh_rail import MHRail

# 1) keypair derivation (optional: set MH_SIGNER_SEED_B64 to verify your own wallet)
seed = os.environ.get("MH_SIGNER_SEED_B64")
if seed:
    kp = MHRail._keypair(seed); assert str(kp.pubkey()) == os.environ["MH_EXPECTED_ADDRESS"]
    print("PASS 1: keypair derives expected address")

# 2) 60/40 split exactness incl. floating point + remainder
r = MHRail(os.environ.get("MH_API_KEY", "mh_test_placeholder"))
for total, want in [(99.90,(59.94,39.96)),(0.03,(0.02,0.01)),(100.00,(60.00,40.00)),(7.77,(4.66,3.11))]:
    assert r.split_amounts(total) == want, (total, r.split_amounts(total))
print("PASS 2: 60/40 split exact")

# 3) webhook HMAC verification (positive + negative)
body = b'{"event":"transfer.completed"}'
sig = hmac.new(b"s3cret", body, hashlib.sha256).hexdigest()
assert MHRail.verify_webhook("s3cret", body, sig) and not MHRail.verify_webhook("x", body, sig)
print("PASS 3: webhook HMAC verification works")

print("ALL TESTS PASSED")
