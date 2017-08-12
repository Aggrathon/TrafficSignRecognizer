
import os
import sys
import tensorflow as tf
import numpy as np
from model import input_fn, model_fn, IMAGES_WITH_SIGNS_PATH, IMAGES_WITHOUT_SIGNS_PATH, CROPPED_IMAGE_SIZE, IMAGES_WITHOUT_SIGNS_CROPPED_PATH
from data.config import DIR_CROPPED_NO_SIGNS, DIR_CROPPED_SIGNS, DIR_FRAMES_SIGNS, CROPPED_SIZE, DIR_FRAMES_POTENTIAL
from data.window import Window, crop_image, save_image


class PredictionStats():
    """
        Class for tracking and outputting stats about the prediction accuracy
    """
    def __init__(self):
        self.true_negative = 0
        self.false_positive = 0
        self.false_negative = 0
        self.true_positive = 0
   
    def get_accuracy(self):
        right = float(self.true_positive+self.true_negative)
        wrong = float(self.false_negative+self.false_positive)
        return right / (right+wrong)

    def get_amount(self):
        return self.true_negative + self.true_positive + self.false_negative + self.false_positive

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


def get_session():
    sess = tf.Session()
    sess.run(tf.local_variables_initializer())
    sess.run(tf.global_variables_initializer())
    saver = tf.train.Saver()
    ckpt = tf.train.get_checkpoint_state('network')
    saver.restore(sess, ckpt.model_checkpoint_path)
    return sess

def evaluate():
    tf.logging.set_verbosity(tf.logging.INFO)
    input_dict, label_dict = input_fn()
    nn = model_fn(input_dict, None, tf.estimator.ModeKeys.PREDICT)
    stats = PredictionStats()
    sess = get_session()
    coord = tf.train.Coordinator()
    tf.train.start_queue_runners(sess, coord)
    try:
        while True:
            pred, act = sess.run([nn.predictions['predictions'], label_dict['labels']])
            stats.add_predictions(pred, act)
            print('Predictions: %00000d, Accuracy: %.4f'%(stats.get_amount(), stats.get_accuracy()))
    except KeyboardInterrupt:
        pass
    finally:
        coord.request_stop()
        coord.join()
        sess.close()
    print()
    stats.print_result()


def evaluate_files(pattern, x_splits=7, y_splits=5):
    """
       Evaluates the images matching the pattern and outputs the results as a generator
    """
    image_reader = tf.WholeFileReader()
    sip = tf.train.string_input_producer(tf.train.match_filenames_once(pattern), num_epochs=1)
    image_name, image_file = image_reader.read(sip)
    image = tf.image.decode_png(image_file)
    images = []
    shape = tf.shape(image)
    height, width = shape[0], shape[1]
    dx = (width - CROPPED_IMAGE_SIZE)/(x_splits-1)
    dy = (height - CROPPED_IMAGE_SIZE)/(y_splits-1)
    for x in range(x_splits):
        for y in range(y_splits):
            images.append(tf.image.crop_to_bounding_box(
                image,
                tf.minimum(tf.to_int32(dy*y), height - CROPPED_IMAGE_SIZE), tf.minimum(tf.to_int32(dx*x), width-CROPPED_IMAGE_SIZE),
                CROPPED_IMAGE_SIZE, CROPPED_IMAGE_SIZE
            ))
    images = tf.reshape(tf.to_float(images)/255.0, (-1, CROPPED_IMAGE_SIZE, CROPPED_IMAGE_SIZE, 3))
    nn = model_fn(dict(input=images), None, tf.estimator.ModeKeys.PREDICT)
    preds = tf.reshape(nn.predictions['predictions'], (x_splits, y_splits))
    sess = get_session()
    coord = tf.train.Coordinator()
    tf.train.start_queue_runners(sess, coord)
    try:
        while True:
            name, predictions = sess.run([image_name, preds])
            yield name, predictions
    except KeyboardInterrupt:
        pass
    except tf.errors.OutOfRangeError:
        pass
    finally:
        coord.request_stop()
        coord.join()
        sess.close()

def check_images(pattern):
    for name, pred in evaluate_files(pattern):
        if np.max(pred) > 0.5:
            print(name, 'has a sign')
        else:
            print(name, 'has no signs')

def check_classification():
    import pygame
    os.makedirs(DIR_CROPPED_SIGNS, exist_ok=True)
    os.makedirs(DIR_CROPPED_NO_SIGNS, exist_ok=True)
    os.makedirs(DIR_FRAMES_SIGNS, exist_ok=True)
    window = Window("P: No Sign   O: Has Sign   L: Maybe not   K: Maybe has")
    def yield_signs_in_folder(folder, x=7, y=5):
        for name, pred in evaluate_files(folder, x, y):
            if np.max(pred) > 0.6:
                print(name, 'is suspicious')
                image = pygame.image.load(name)
                for x, y in get_sign_centers(pred):
                    yield crop_image(image, (
                        max(0, min(image.get_width()-CROPPED_SIZE, int(x*image.get_width()-CROPPED_SIZE/2))),
                        max(0, min(image.get_height()-CROPPED_SIZE, int(y*image.get_height()-CROPPED_SIZE/2))),
                        CROPPED_SIZE, CROPPED_SIZE
                    )), name
    def has_sign(w, image, name):
        try:
            os.rename(name, os.path.join(DIR_FRAMES_SIGNS, os.path.basename(name)))
        except Exception:
            pass
    def crop_sign(w, image, name):
        save_image(image, DIR_CROPPED_SIGNS)
        has_sign(w, image, name)
    #Checking cropped no signs
    tf.reset_default_graph()
    print("Checking cropped no signs")
    for name, pred in evaluate_files(IMAGES_WITHOUT_SIGNS_CROPPED_PATH, 3, 3):
        if np.max(pred) < 0.4:
            os.remove(name)
    #Checking potential frames
    tf.reset_default_graph()
    print("Checking potential frames")
    window.iterate2(yield_signs_in_folder(os.path.join(DIR_FRAMES_POTENTIAL, "*.png"), 8, 6), {
        pygame.K_o: crop_sign,
        pygame.K_k: has_sign,
        pygame.K_p: lambda a, b, c: None,
        pygame.K_l: lambda a, b, c: None
    })
    #Checking cropped signs
    tf.reset_default_graph()
    print("Checking cropped signs")
    def check_signs():
        for name, pred in evaluate_files(IMAGES_WITH_SIGNS_PATH, 3, 3):
            if np.max(pred) < 0.6:
                print(name, 'is suspicious')
                yield None, name
    def remove_image(w, i, name):
        os.remove(name)
    window.iterate2(check_signs(), {
        pygame.K_o: lambda a, b, c: None,
        pygame.K_p: remove_image,
        pygame.K_l: remove_image,
        pygame.K_k: lambda a, b, c: None
    })
    # Check none frames
    tf.reset_default_graph()
    print("Checking no signs classification")
    def no_sign(w, image, n):
        save_image(image, DIR_CROPPED_NO_SIGNS)
    window.iterate2(yield_signs_in_folder(IMAGES_WITHOUT_SIGNS_PATH), {
        pygame.K_o: crop_sign,
        pygame.K_k: has_sign,
        pygame.K_p: no_sign,
        pygame.K_l: lambda a, b, c: None
    })

def get_sign_centers(predictions):
    w, h = np.shape(predictions)
    dx = 1.0/float(w)
    dy = 1.0/float(h)
    for (x, y), value in np.ndenumerate(predictions):
        if value > 0.5:
            cx = float(x)
            cy = float(y)
            if x < w-1 and (predictions[x+1, y] > 0.5 or predictions[x+1, y] == -1):
                cx += 0.5
                predictions[x+1, y] = -1
            if x > 0 and (predictions[x-1, y] > 0.5 or predictions[x-1, y] == -1):
                cx -= 0.5
                predictions[x-1, y] = -1
            if y < h-1 and (predictions[x, y+1] > 0.5 or predictions[x, y+1] == -1):
                cy += 0.5
                predictions[x, y+1] = -1
            if y > 0 and (predictions[x, y-1] > 0.5 or predictions[x, y-1] == -1):
                cy -= 0.5
                predictions[x, y-1] = -1
            predictions[x, y] = -1
            yield cx*dx, cy*dy


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Arguments:")
        print(' e  evaluate model using the training data')
        print(' c  use the network to find images with the wrong class in the training data')
        print(' <pattern>  evaluate the matching files')
    elif sys.argv[1] == 'e':
        evaluate()
    elif sys.argv[1] == 'c':
        check_classification()
    else:
        check_images(sys.argv[1])
