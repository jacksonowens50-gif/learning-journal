"""Flatten nested JSON order data into tabular form."""

import json
import pandas as pd

JSON_PATH = "sample_orders.json"


def load_json(path):
  with open(path) as f:
    return json.load(f)

def flatten_orders(data):
    """One row per order. Nested customer fields become flat columns."""
    rows = []

    for order in data["results"]:
        cust = order.get("customer", {})
        addr = cust.get("address", {})

        rows.append({
            "order_id":       order["order_id"],
            "order_date":     order["order_date"],
            "status":         order.get("status"),
            "order_total":    order["order_total"],
            "discount_pct":   order.get("discount_pct") or 0,
            "customer_id":    cust.get("id"),
            "customer_name":  cust.get("name"),
            "customer_city":  addr.get("city"),
            "customer_state": addr.get("state"),
            "n_line_items":   len(order.get("line_items", [])),
        })

    return pd.DataFrame(rows)

def flatten_line_items(data):
    """One row per line item. Order-level fields repeat down each row."""
    rows = []

    for order in data["results"]:
        cust = order.get("customer", {})

        for item in order.get("line_items", []):
            rows.append({
                "order_id":      order["order_id"],
                "order_date":    order["order_date"],
                "customer_name": cust.get("name"),
                "sku":           item["sku"],
                "description":   item.get("description"),
                "quantity":      item["quantity"],
                "unit_price":    item["unit_price"],
            })


    df = pd.DataFrame(rows)

    # Force numeric — strings like "219.00" become real numbers
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["line_total"] = df["quantity"] * df["unit_price"]

    return df


def main():
    data = load_json(JSON_PATH)

    orders = flatten_orders(data)
    items = flatten_line_items(data)

    print(orders)
    print()
    print(items)
    print()
    print("orders:", orders.shape, "| items:", items.shape)
    print(items.dtypes)
    print("qty x price:", (items["quantity"] * items["unit_price"]).head(4).tolist())

if __name__ == "__main__":
    main()
