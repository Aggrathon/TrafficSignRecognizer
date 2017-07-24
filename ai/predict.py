from model import network, randomize_pictures, model_fn, IMAGES_WITH_SIGNS_PATH, IMAGES_WITHOUT_SIGNS_PATH
import tensorflow as tf
import os


class PredictionStats():
    def __init__(self):
        self.true_negative = 0
        self.false_positive = 0
        self.false_negative = 0
        self.true_positive = 0
   
    def get_accuracy(self):
        right = float(self.true_positive+self.true_negative)
        wrong = float(self.false_negative+self.false_positive)
        return right / (right+wrong)

    def add_prediction(self, pred, label):
        if label < 0.5:
            if pred < 0.5:
                self.true_negative += 1
            else:
                self.false_positive += 1
        else:
            if pred > 0.5:
                self.true_positive += 1
            else:
                self.false_negative += 1

    def add_predictions(self, preds, labels):
        for p, l in zip(preds, labels):
            self.add_prediction(p, l)

    def print_result(self):
        print()
        print('__ No Signs __')
        print('True Negative:', self.true_negative)
        print('False Positive:', self.false_positive)
        print('Accuracy:', float(self.true_negative)/(self.true_negative+self.false_positive))
        print()
        print('__ Has Signs __')
        print('True Positive:', self.true_positive)
        print('False Negative:', self.false_negative)
        print('Accuracy:', float(self.true_positive)/(self.true_positive+self.false_negative))
        print()
        print('__ Overall __')
        print('Predictions:', (self.true_negative+self.true_positive+self.false_negative+self.false_positive))
        print('Accuracy:', self.get_accuracy())


def inputs():
    with tf.variable_scope('input'):
        image_reader = tf.WholeFileReader()
        crop_size = 60
        sip = tf.train.string_input_producer(tf.train.match_filenames_once(IMAGES_WITH_SIGNS_PATH), name="with_signs")
        _, sif = image_reader.read(sip)
        si = tf.image.decode_png(sif)
        si = tf.random_crop(si, (crop_size, crop_size, 3))
        nip = tf.train.string_input_producer(tf.train.match_filenames_once(IMAGES_WITHOUT_SIGNS_PATH), name="without_signs")
        _, nif = image_reader.read(nip)
        ni = tf.image.decode_png(nif)
        ni = tf.random_crop(ni, (crop_size, crop_size, 3))
        images = [ni, si]
        images = randomize_pictures(images)
        images = tf.reshape(tf.to_float(images)/255.0, [2, crop_size, crop_size, 3])
    inp, label = tf.train.batch([images, [0, 1]], 1, 1, 80, enqueue_many=True)
    return dict(input=inp), label

def get_session():
    sess = tf.Session()
    sess.run(tf.local_variables_initializer())
    sess.run(tf.global_variables_initializer())
    saver = tf.train.Saver()
    ckpt = tf.train.get_checkpoint_state('network')
    saver.restore(sess, ckpt.model_checkpoint_path)
    return sess

def main():
    tf.logging.set_verbosity(tf.logging.INFO)
    inp, label = inputs()
    nn = model_fn(inp, None, tf.estimator.ModeKeys.PREDICT)
    stats = PredictionStats()
    sess = get_session()
    coord = tf.train.Coordinator()
    tf.train.start_queue_runners(sess, coord)
    try:
        while True:
            pred, logits, act = sess.run([nn.predictions['predictions'], nn.predictions['logits'], label])
            stats.add_prediction(pred, act)
            print('Prediction:\t%.2f\t%.2f'%(pred, logits))
    except KeyboardInterrupt:
        pass
    finally:
        coord.request_stop()
        coord.join()
        sess.close()
    print()
    stats.print_result()


if __name__ == "__main__":
    main()
