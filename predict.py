from model import network
import tensorflow as tf
import os

def no_signs_input_fn():
    with tf.variable_scope('input'):
        image_reader = tf.WholeFileReader()
        crop_size = 60
        nip = tf.train.string_input_producer(tf.train.match_filenames_once(os.path.join('data', 'none', "*.png")), name="without_signs")
        _, nif = image_reader.read(nip)
        ni = tf.image.decode_png(nif)
        ni = [tf.random_crop(ni, (crop_size, crop_size, 3)) for _ in range(8)]
        ni = tf.reshape(tf.to_float(ni)/255.0, [8, crop_size, crop_size, 3])
    return tf.train.batch([ni], 1, 4, 80, enqueue_many=True)

def signs_input_fn():
    with tf.variable_scope('input'):
        image_reader = tf.WholeFileReader()
        crop_size = 60
        nip = tf.train.string_input_producer(tf.train.match_filenames_once(os.path.join('data', 'cropped', "*.png")), name="with_signs")
        _, nif = image_reader.read(nip)
        ni = tf.image.decode_png(nif)
        ni = [tf.random_crop(ni, (crop_size, crop_size, 3)) for _ in range(4)]
        ni = tf.reshape(tf.to_float(ni)/255.0, [4, crop_size, crop_size, 3])
    return tf.train.batch([ni], 1, 4, 80, enqueue_many=True)

def main():
    nn = network()
    true_negative = 0
    false_positive = 0
    false_negative = 0
    true_positive = 0
    try:
        for r in nn.predict(no_signs_input_fn):
            pred = r['predictions'][0]
            print('Prediction:', pred)
            if pred < 0.5:
                true_negative += 1
            else:
                false_positive += 1
    except KeyboardInterrupt:
        pass
    try:
        for r in nn.predict(signs_input_fn):
            pred = r['predictions'][0]
            print('Prediction:', pred)
            if pred > 0.5:
                true_positive += 1
            else:
                false_negative += 1
    except KeyboardInterrupt:
        pass
    print()
    print('Correct No Signs:', true_negative)
    print('False Positive:', false_positive)
    print('Correct With Signs:', true_positive)
    print('False Negative:', false_negative)


if __name__ == "__main__":
    main()
