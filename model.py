import tensorflow as tf
import random
import os

def model_fn(features, labels, mode):
    training = (mode == tf.estimator.ModeKeys.TRAIN)
    prev_layer = features
    for i, size in enumerate([16, 24, 32, 48]):
        with tf.variable_scope('convolution_%d'%i):
            prev_layer = tf.layers.conv2d(prev_layer, size, [5, 5], [2, 2], 'valid', activation=tf.nn.relu)
            #prev_layer = tf.layers.max_pooling2d(prev_layer, (2, 2), (1, 1), 'valid')
            prev_layer = tf.layers.batch_normalization(prev_layer, training=training)
    with tf.variable_scope('flatten'):
        prev_layer = tf.layers.conv2d(prev_layer, 64, [5, 5], [1, 1], 'valid', activation=tf.nn.relu)
        prev_layer = tf.contrib.layers.flatten(prev_layer)
    for i, size in enumerate([1024, 128, 16]):
        with tf.variable_scope('fully_connected_%d'%i):
            prev_layer = tf.layers.dense(prev_layer, size, tf.nn.relu, use_bias=True)
            prev_layer = tf.layers.dropout(prev_layer, 0.3, training=training)
    logits = tf.layers.dense(prev_layer, 1, tf.nn.relu, name="logits")
    predictions = tf.nn.sigmoid(logits, name="predictions")
    tf.summary.histogram('predictions', predictions)
    loss = None
    trainer = None
    if labels is not None:
        with tf.variable_scope('training'):
            loss = tf.losses.sigmoid_cross_entropy(labels, logits)
            adam = tf.train.AdamOptimizer(1e-5)
            trainer = adam.minimize(loss, global_step=tf.contrib.framework.get_global_step())
            tf.summary.scalar('sigmoid_loss', loss)
            tf.summary.scalar('mean_squared_error', tf.losses.mean_squared_error(labels, predictions))
    pred_dict = {
        "predictions": predictions,
        "logits": logits
    }
    with tf.variable_scope('eval'):
        eval_dict = {
            'accuracy': tf.metrics.accuracy(labels, predictions),
            'false negatives': tf.metrics.false_negatives(labels, predictions),
            'false positives': tf.metrics.false_positives(labels, predictions)
        }
    return tf.estimator.EstimatorSpec(
        mode=mode,
        predictions=pred_dict,
        loss=loss,
        train_op=trainer,
        eval_metric_ops=eval_dict)

def network():
    config = tf.estimator.RunConfig().replace(
        save_summary_steps = 20,
        tf_random_seed = random.randrange(0, 1<<30))
    return tf.estimator.Estimator(model_fn, 'network', config)
    #return tf.estimator.Estimator(model_fn, 'network')

def input_fn():
    with tf.variable_scope('input'):
        #Get file names
        sip = tf.train.string_input_producer(tf.train.match_filenames_once(os.path.join('data', 'unsorted', '*.png'), "files_with_signs"))
        nip = tf.train.string_input_producer(tf.train.match_filenames_once(os.path.join('data', 'none', "*.png"), "files_without_signs"))
        #Read files
        image_reader = tf.WholeFileReader()
        _, sif = image_reader.read(sip)
        _, nif = image_reader.read(nip)
        #Decode files
        si = tf.image.decode_png(sif)
        si = tf.reshape(tf.to_float(si)/255.0, [320, 240, 3])
        ni = tf.image.decode_png(nif)
        ni = tf.reshape(tf.to_float(ni)/255.0, [320, 240, 3])
        #batch
        #sb = tf.train.batch([si], 16, 200, 32, name="sign_batch")
        #nb = tf.train.batch([ni], 16, 200, 32, name="none_batch")
        #return tf.concat((sb, nb), 0), tf.concat((tf.ones([16,1]), tf.zeros([16,1])), 0)
        return tf.train.shuffle_batch([[si, ni], [[1], [0]]], 16, 400, 64, 4, enqueue_many=True)
