
import random
import os
import tensorflow as tf

from data.config import DIR_CROPPED_SIGNS, DIR_CROPPED_NO_SIGNS, DIR_FRAMES_NO_SIGNS


IMAGES_WITH_SIGNS_PATH = os.path.join(DIR_CROPPED_SIGNS, '*.png')
IMAGES_WITHOUT_SIGNS_CROPPED_PATH = os.path.join(DIR_CROPPED_NO_SIGNS, '*.png')
IMAGES_WITHOUT_SIGNS_PATH = os.path.join(DIR_FRAMES_NO_SIGNS, '*.png')
CROPPED_IMAGE_SIZE = 60


def model_fn(features, labels, mode):
    """
        The function that generates the network for the estimator
    """
    training = (mode == tf.estimator.ModeKeys.TRAIN)
    prev_layer = features['input']
    for i, size in enumerate([32, 48, 64]):
        with tf.variable_scope('convolution_%d'%i):
            prev_layer = tf.layers.conv2d(prev_layer, size, 5, 1, 'valid', activation=tf.nn.relu)
            prev_layer = tf.layers.max_pooling2d(prev_layer, 3, 2, 'same')
            prev_layer = tf.nn.local_response_normalization(prev_layer, 4, 1.0, 1e-4, 0.75)
    prev_layer = tf.contrib.layers.flatten(prev_layer, )
    for i, size in enumerate([256, 64]):
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
            loss = tf.losses.sigmoid_cross_entropy(labels, logits)
            tf.summary.scalar('sigmoid_loss', loss)
            boolean = tf.round(predictions)
            tf.summary.scalar('false_positive', tf.reduce_sum(boolean * (1.0 - tf.to_float(labels))))
            tf.summary.scalar('false_negative', tf.reduce_sum((1.0 - boolean) * tf.to_float(labels)))
            tf.summary.scalar('mean_squared_error', tf.losses.mean_squared_error(labels, predictions))
            adam = tf.train.AdamOptimizer(1e-4)
            trainer = adam.minimize(loss, global_step=tf.contrib.framework.get_global_step())
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
    """
        Create the estimator
    """
    config = tf.estimator.RunConfig().replace(
        #save_summary_steps = 20,
        tf_random_seed=random.randrange(0, 1<<30))
    return tf.estimator.Estimator(model_fn, 'network', config)

def input_fn():
    """
        Creates input dictionaries for the estimator
    """
    num_signs = 6
    num_none = 12
    num_none_diff = 2
    with tf.variable_scope('training_input'):
        ni1 = produce_images_from_folder(IMAGES_WITHOUT_SIGNS_PATH, num_none, name="without_signs")
        ni2 = produce_images_from_folder(IMAGES_WITHOUT_SIGNS_CROPPED_PATH, num_none_diff, name="without_signs_difficult")
        si1 = produce_images_from_folder(IMAGES_WITH_SIGNS_PATH, num_signs, central_crop=0.8, name="with_signs_1")
        si2 = produce_images_from_folder(IMAGES_WITH_SIGNS_PATH, num_signs, central_crop=0.8, name="with_signs_2")
        images = tf.concat((si1, si2, ni1, ni2), 0)
        labels = [[0.95]]*num_signs*2 + [[0]]*num_none + [[0]]*num_none_diff
        images, labels = tf.train.shuffle_batch([images, labels], 48, 2000, 100, 4, enqueue_many=True)
        return dict(input=images), dict(labels=labels)


def produce_images_from_folder(folder, num_variants=6, size=CROPPED_IMAGE_SIZE, randomise=True, central_crop=1, name=None):
    """
        Reads files from the folder, converts them to images and applies some randomization and cropping
    """
    image_reader = tf.WholeFileReader()
    sip = tf.train.string_input_producer(tf.train.match_filenames_once(folder), name=name)
    _, image_file = image_reader.read(sip)
    image = tf.image.decode_png(image_file)
    if central_crop < 1:
        image = tf.image.central_crop(image, central_crop)
    image = [tf.random_crop(image, (size, size, 3)) for _ in range(num_variants)]
    if randomise:
        image = randomize_pictures(image)
    return tf.reshape(tf.to_float(image)/255.0, [num_variants, size, size, 3])

def randomize_pictures(tensors):
    """
        Randomises images in the list
    """
    tensors = [tf.image.random_flip_left_right(i) for i in tensors]
    tensors = [tf.image.random_brightness(i, 0.05) for i in tensors]
    tensors = [tf.image.random_contrast(i, 0.95, 1.05) for i in tensors]
    tensors = [tf.image.random_saturation(i, 0.95, 1.1) for i in tensors]
    return tensors
