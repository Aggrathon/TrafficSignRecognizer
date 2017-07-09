import tensorflow as tf
import os
import random


def model_fn(features, labels, mode):
    training = (mode == tf.estimator.ModeKeys.TRAIN)
    prev_layer = features
    for size in [16, 24, 32, 48]:
        prev_layer = tf.layers.conv2d(prev_layer, size, [5, 5], [2, 2], 'valid', activation=tf.nn.relu)
        prev_layer = tf.layers.batch_normalization(prev_layer, training=training)
    prev_layer = tf.layers.conv2d(prev_layer, 64, [5, 5], [1, 1], 'valid', activation=tf.nn.relu)
    prev_layer = tf.contrib.layers.flatten(prev_layer)
    for size in [2048, 512, 128, 16]:
        prev_layer = tf.layers.dense(prev_layer, size, tf.nn.relu, use_bias=True)
        prev_layer = tf.layers.dropout(prev_layer, 0.3, training=training)
    logits = tf.layers.dense(prev_layer, 1, tf.nn.relu)
    loss = None
    trainer = None
    if labels is not None:
        loss = tf.losses.sigmoid_cross_entropy(labels, logits)
        adam = tf.train.AdamOptimizer()
        trainer = adam.minimize(loss, global_step=tf.contrib.framework.get_global_step())
    predictions = {
        "predictions": tf.nn.sigmoid(logits),
        "logits": logits
    }
    return tf.estimator.EstimatorSpec(mode=mode, predictions=predictions, loss=loss, train_op=trainer)

def network():
    return tf.estimator.Estimator(model_fn, 'network')

def input_fn():
    #Get file names
    sip = tf.train.string_input_producer(tf.train.match_filenames_once(os.path.join('data', 'unsorted', '*.png')))
    nip = tf.train.string_input_producer(tf.train.match_filenames_once(os.path.join('data', 'none', "*.png")))
    #Read files
    image_reader = tf.WholeFileReader()
    _, sif = image_reader.read(sip)
    _, nif = image_reader.read(nip)
    si = tf.image.decode_png(sif)
    ni = tf.image.decode_png(nif)
    si = tf.reshape(tf.to_float(si)/255.0, [320, 240, 3])
    ni = tf.reshape(tf.to_float(si)/255.0, [320, 240, 3])
    sb = tf.train.shuffle_batch([si], 16, 500, 100)
    nb = tf.train.shuffle_batch([ni], 16, 500, 100)
    return tf.concat((sb, nb), 0), tf.concat((tf.ones([16,1]), tf.zeros([16,1])), 0)

    