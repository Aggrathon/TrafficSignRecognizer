from model import network, randomize_pictures
import tensorflow as tf
import os


def input_fn():
    with tf.variable_scope('input'):
        image_reader = tf.WholeFileReader()
        crop_size = 60
        sip = tf.train.string_input_producer(tf.train.match_filenames_once(os.path.join('data', 'cropped', "*.png")), name="with_signs")
        _, sif = image_reader.read(sip)
        si = tf.image.decode_png(sif)
        si = tf.random_crop(si, (crop_size, crop_size, 3))
        nip = tf.train.string_input_producer(tf.train.match_filenames_once(os.path.join('data', 'none', "*.png")), name="without_signs")
        _, nif = image_reader.read(nip)
        ni = tf.image.decode_png(nif)
        ni = tf.random_crop(ni, (crop_size, crop_size, 3))
        images = [ni, si]
        images = randomize_pictures(images)
        images = tf.reshape(tf.to_float(images)/255.0, [2, crop_size, crop_size, 3])
    return dict(input=tf.train.batch([images], 1, 1, 80, enqueue_many=True))

def main():
    tf.logging.set_verbosity(tf.logging.INFO)
    nn = network()
    true_negative = 0
    false_positive = 0
    false_negative = 0
    true_positive = 0
    try:
        sign = False
        for r in nn.predict(input_fn):
            pred = r['predictions'][0]
            print('Prediction:', pred, '\t', r['logits'][0])
            if sign:
                if pred < 0.5:
                    true_negative += 1
                else:
                    false_positive += 1
                sign = False
            else:
                if pred > 0.5:
                    true_positive += 1
                else:
                    false_negative += 1
                sign = True
    except KeyboardInterrupt:
        pass
    print()
    print('Correct No Signs:', true_negative)
    print('False Positive:', false_positive)
    print('Correct With Signs:', true_positive)
    print('False Negative:', false_negative)


if __name__ == "__main__":
    main()
