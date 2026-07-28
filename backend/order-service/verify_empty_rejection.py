import urllib.request
import urllib.error
import json
import paho.mqtt.client as mqtt
import time

def trigger_zero_stock_event():
    payload = {
        "event_type": "PURCHASE",
        "transaction_id": "TX-ZERO-STOCK-TEST",
        "machine_id": "VM-101",
        "slot_id": "A1",
        "product_name": "Nitro Cold Brew",
        "price": 4.50,
        "remaining_stock": 0,
        "max_capacity": 15,
        "payment_method": "NFC_TAP"
    }
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="ZeroStockTestPub")
    client.connect("broker.emqx.io", 1883, 30)
    client.publish("machine/VM-101/events", json.dumps(payload), qos=1)
    client.disconnect()
    time.sleep(1.5)

def main():
    print("=== 1. PUBLISHING MQTT EVENT: SETTING SLOT A1 STOCK TO 0 ===")
    trigger_zero_stock_event()

    print("\n=== 2. QUERYING INVENTORY FOR SLOT A1 ===")
    res = urllib.request.urlopen("http://localhost:8080/machines/VM-101/inventory")
    inv = json.loads(res.read().decode("utf-8"))
    print(json.dumps(inv, indent=2))

    print("\n=== 3. ATTEMPTING ORDER (POST /orders) ON EMPTY SLOT A1 ===")
    url = "http://localhost:8081/orders"
    order_payload = {"machine_id": "VM-101", "slot_id": "A1", "payment_method": "NFC_TAP_APPLE_PAY"}
    req = urllib.request.Request(url, data=json.dumps(order_payload).encode("utf-8"), headers={"Content-Type": "application/json"})

    try:
        urllib.request.urlopen(req)
        print("[FAIL] Order succeeded when slot was empty.")
    except urllib.error.HTTPError as e:
        print(f"\n[REJECTED AS EXPECTED] HTTP STATUS: {e.code}")
        print("Response JSON Detail:")
        print(json.dumps(json.loads(e.read().decode("utf-8")), indent=2))

if __name__ == "__main__":
    main()
