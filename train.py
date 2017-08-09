
import sys
import tensorflow as tf
from model import network, input_fn

tf.logging.set_verbosity(tf.logging.INFO)
model = network()
if len(sys.argv) == 2 and sys.argv[1] == 's':
    model.train(input_fn, None, 1000)
else:
    model.train(input_fn, None, 80000)
