import tensorflow as tf
import random
import os

def model_fn(features, labels, mode):
    training = (mode == tf.estimator.ModeKeys.TRAIN)
    prev_layer = features['input']
    for i, size in enumerate([32, 48, 64]):
        with tf.variable_scope('convolution_%d'%i):
            prev_layer = tf.layers.conv2d(prev_layer, size, [5, 5], [1, 1], 'valid', activation=tf.nn.relu)
            prev_layer = tf.layers.max_pooling2d(prev_layer, (2, 2), (1, 1), 'valid')
            #if i == 1:
            #    prev_layer = tf.layers.batch_normalization(prev_layer, training=training)
    prev_layer = tf.contrib.layers.flatten(prev_layer, )
    for i, size in enumerate([1024, 128]):
        with tf.variable_scope('fully_connected_%d'%i):
            prev_layer = tf.layers.dense(prev_layer, size, tf.nn.relu, use_bias=True)
            if training:
                prev_layer = tf.layers.dropout(prev_layer, 0.3)
    logits = tf.layers.dense(prev_layer, 1, name="logits")
    predictions = tf.nn.sigmoid(logits, name="predictions")
    tf.summary.histogram('predictions', predictions)
    tf.summary.histogram('logits', logits)
    loss = None
    trainer = None
    eval_dict = None
    if labels is not None:
        labels = labels['labels']
        with tf.variable_scope('training'):
            loss = tf.losses.sigmoid_cross_entropy(labels, logits, weights=(labels+1))
            adam = tf.train.AdamOptimizer(1e-4)
            trainer = adam.minimize(loss, global_step=tf.contrib.framework.get_global_step())
            tf.summary.scalar('sigmoid_loss', loss)
            tf.summary.scalar('mean_squared_error', tf.losses.mean_squared_error(labels, predictions))
        with tf.variable_scope('eval'):
            eval_dict = {
                'accuracy': tf.metrics.accuracy(labels, predictions),
                'false negatives': tf.metrics.false_negatives(labels, predictions),
                'false positives': tf.metrics.false_positives(labels, predictions)
            }
    pred_dict = {
        "predictions": predictions,
        "logits": logits
    }
    output_dict = {
        'output': tf.estimator.export.PredictOutput(dict(output=predictions))
    }
    return tf.estimator.EstimatorSpec(
        mode=mode,
        predictions=pred_dict,
        loss=loss,
        train_op=trainer,
        eval_metric_ops=eval_dict,
        export_outputs=output_dict)

def network():
    config = tf.estimator.RunConfig().replace(
        #save_summary_steps = 20,
        tf_random_seed = random.randrange(0, 1<<30))
    return tf.estimator.Estimator(model_fn, 'network', config)

def input_fn():
    with tf.variable_scope('training_input'):
        image_reader = tf.WholeFileReader()
        crop_size = 60
        #no signs
        nip = tf.train.string_input_producer(tf.train.match_filenames_once(os.path.join('data', 'none', "*.png")), name="without_signs")
        _, nif = image_reader.read(nip)
        ni = tf.image.decode_png(nif)
        ni = [tf.random_crop(ni, (crop_size, crop_size, 3)) for _ in range(4)]
        ni = randomize_pictures(ni)
        ni = tf.reshape(tf.to_float(ni)/255.0, [4, crop_size, crop_size, 3])
        #cropped signs
        sip = tf.train.string_input_producer(tf.train.match_filenames_once(os.path.join('data', 'cropped', '*.png')), name="with_signs")
        _, sif = image_reader.read(sip)
        si = tf.image.decode_png(sif)
        si = [tf.random_crop(si, (crop_size, crop_size, 3)) for _ in range(4)]
        si = randomize_pictures(si)
        si = tf.reshape(tf.to_float(si)/255.0, [4, crop_size, crop_size, 3])
        #batch
        images = tf.concat((si, ni), 0)
        labels = [[1]]*4+[[0]]*4
        images, labels = tf.train.shuffle_batch([images, labels], 16, 800, 100, 4, enqueue_many=True)
        return dict(input=images), dict(labels=labels)

def randomize_pictures(tensors):
    tensors = [tf.image.random_flip_left_right(i) for i in tensors]
    tensors = [tf.image.random_brightness(i, 0.02) for i in tensors]
    tensors = [tf.image.random_contrast(i, 0.98, 1.02) for i in tensors]
    tensors = [tf.image.random_saturation(i, 0.98, 1.04) for i in tensors]
    return tensors
