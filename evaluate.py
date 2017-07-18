from model import network, input_fn
import tensorflow as tf

tf.logging.set_verbosity(tf.logging.INFO)
res = network().evaluate(input_fn, 10)
print()
for key in res:
    print(key+':', res[key])

