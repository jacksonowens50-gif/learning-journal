
import json

with open("sample_orders.json") as f:
    data = json.load(f)

cust = data["results"][1]["customer"]     # ORD-1002 — no address

# A. Square brackets — let it break
try:
    print("A:", cust["address"])
except Exception as e:
    print("A: KeyError ->", e)

# B. .get() with no default
print("B:", cust.get("address"))

# C. .get() with a default
print("C:", cust.get("address", "NOT PROVIDED"))

# D. .get() on a key that EXISTS but holds null
order = data["results"][2]              # ORD-1003
discount = order.get("discount_pct") or 0
print(discount)

# Looks safe. Isn't.
print(cust.get("address", {}).get("city", "UNKNOWN"))