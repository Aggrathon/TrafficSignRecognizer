from model import network, input_fn

print()
print(network().evaluate(input_fn, 1))
