from model import network, input_fn

res = network().evaluate(input_fn, 10)
print()
for key in res:
    print(key+':', res[key])

