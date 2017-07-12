import tensorflow as tf
from model import network, input_fn

tf.logging.set_verbosity(tf.logging.INFO)
model = network()
model.train(input_fn, None, 8000)
