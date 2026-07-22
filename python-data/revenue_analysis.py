revenue_L = [10,15,20,12,10,18]

for i in range(1, len(revenue_L)):
    growth = (revenue_L[i] - revenue_L[i-1]) / revenue_L[i-1]
    print("Month",i, round((growth*100),2),"%")
    if growth < 0:
        print("DECLINE")
    else:
        print("INCREASE")

avg_rev = sum(revenue_L) / len(revenue_L)
print("Avg Rev",round(avg_rev,1))
