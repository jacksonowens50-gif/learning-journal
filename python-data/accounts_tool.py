# accounts_tool.py — Day 4: chart of accounts tool
# Fill in each function body. Run this file to test as you go.

# ---------------------------------------------------------------
# DATA — a list of dicts. Each dict is a row, each key is a column.
# ---------------------------------------------------------------
accounts = [
    {"name": "Cash",               "type": "asset",     "balance": 25000},
    {"name": "Accounts Receivable","type": "asset",     "balance": 18500},
    {"name": "Equipment",          "type": "asset",     "balance": 42000},
    {"name": "Accounts Payable",   "type": "liability", "balance": 12300},
    {"name": "Notes Payable",      "type": "liability", "balance": 30000},
    {"name": "Common Stock",       "type": "equity",    "balance": 50000},
    {"name": "Sales Revenue",      "type": "revenue",   "balance": 87000},
    {"name": "Rent Expense",       "type": "expense",   "balance": 9600},
]

# Dict used as a LOOKUP TABLE (instead of a giant if/elif chain).
NORMAL_SIDE = {
    "asset": "debit",
    "expense": "debit",
    "liability": "credit",
    "equity": "credit",
    "revenue": "credit",
}


# ---------------------------------------------------------------
# STEP 1 — think: WHERE account_type = ?    [DONE]
# ---------------------------------------------------------------
def filter_by_type(accounts, account_type):
    results = []
    for account in accounts:
        if account["type"] == account_type:
            results.append(account)
    return results


# ---------------------------------------------------------------
# STEP 2 — think: SUM(balance)    [DONE]
# ---------------------------------------------------------------
def sum_balances(accounts):
    total = 0
    for account in accounts:
        total += account["balance"]
    return total


# ---------------------------------------------------------------
# STEP 3 — think: SUM(balance) GROUP BY type    [DONE]
# ---------------------------------------------------------------
def group_totals(accounts):
    totals={}
    for account in accounts:
        acct_type = account["type"]
        if acct_type not in totals:
            totals[acct_type] = 0
        totals[acct_type] += account["balance"]
    return totals


# ---------------------------------------------------------------
# STEP 4 — try/except, uses the NORMAL_SIDE lookup dict    [DONE]
# ---------------------------------------------------------------
def normal_side(account_type):
    try:
        return NORMAL_SIDE[account_type]
    except KeyError:
        return "unknown"


# ---------------------------------------------------------------
# STEP 5 — the deliverable output    [DONE]
# ---------------------------------------------------------------
def format_report(accounts):
    lines = []
    lines.append(f"{'ACCOUNT':<22}{'TYPE':<12}{'SIDE':<8}{'BALANCE':>12}")
    lines.append("-" * 54)
    for account in accounts:
        lines.append(
            f"{account['name']:<22}"
            f"{account['type']:<12}"
            f"{normal_side(account['type']):<8}"
            f"{account['balance']:>12,}"
        )
    lines.append("-" * 54)
    lines.append(f"{'TOTAL':<42}{sum_balances(accounts):>12,}")
    return "\n".join(lines)

# ---------------------------------------------------------------
# STEP 6 — more error handling    [DONE]
# ---------------------------------------------------------------
def safe_balance(account):
    try:
        return float(account["balance"])
    except (KeyError, ValueError, TypeError):
        print(f"WARNING: bad balance on {account.get('name', 'unknown')}")
        return 0.0

# ---------------------------------------------------------------
# TESTS — uncomment as you finish each function
# ---------------------------------------------------------------
if __name__ == "__main__":
    print(filter_by_type(accounts, "asset"))
    print(sum_balances(filter_by_type(accounts, "asset")))     # expect 85500
    print(group_totals(accounts))
    print(normal_side("asset"), normal_side("bogus"))          # debit unknown
    print(format_report(accounts))
    print(safe_balance({"name": "Broken", "balance": "abc"}))  # expect 0.0
    pass
