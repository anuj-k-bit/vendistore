import urllib.request
import urllib.error
import json

def test_rejection():
    url = "http://localhost:8081/orders"
    payload = {
        "machine_id": "VM-101",
        "slot_id": "A1",
        "payment_method": "NFC_TAP"
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    print("=== 1. DEPLETING SLOT A1 (14 ITEMS) ===")
    for i in range(14):
        try:
            urllib.request.urlopen(req)
        except Exception:
            pass

    print("=== 2. QUERYING INVENTORY FOR SLOT A1 ===")
    inv_res = urllib.request.urlopen("http://localhost:8080/machines/VM-101/inventory")
    print(json.dumps(json.loads(inv_res.read()), indent=2))

    print("\n=== 3. ATTEMPTING ORDER ON EMPTY SLOT A1 ===")
    try:
        urllib.request.urlopen(req)
        print("FAIL: Expected 400 rejection but order succeeded.")
    except urllib.error.HTTPError as e:
        print(f"✅ REJECTED AS EXPECTED! HTTP {e.code}:")
        print(json.dumps(json.loads(e.read().decode("utf-8")), indent=2))

if __name__ == "__main__":
    test_rejection()
