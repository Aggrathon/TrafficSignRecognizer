
import os
import sys
import tensorflow as tf
import numpy as np
import pygame
from model import model_fn, CROPPED_IMAGE_SIZE
from predict import get_session
from data.config import DIR_CROPPED_SIGNS, DIR_FRAMES_NO_SIGNS, DIR_FRAMES_SIGNS, CROPPED_SIZE, IMAGE_HEIGHT, IMAGE_WIDTH, DIR_CROPPED_NO_SIGNS
from data.window import Window, crop_image, save_image

X_SPLITS = 6
Y_SPLITS = 4


def main(in_folder):
    os.makedirs(DIR_CROPPED_SIGNS, exist_ok=True)
    os.makedirs(DIR_CROPPED_NO_SIGNS, exist_ok=True)
    os.makedirs(DIR_FRAMES_SIGNS, exist_ok=True)
    window = Window("P: No Sign    O: Has Sign    L: Don't know")
    actions = {
        pygame.K_o: on_sign,
        pygame.K_p: on_none,
        pygame.K_l: on_unknown
    }
    window.iterate2(check_images(in_folder), actions)

def on_sign(window, image, name):
    save_image(image, DIR_CROPPED_SIGNS)
    try:
        os.rename(name, os.path.join(DIR_FRAMES_SIGNS, os.path.basename(name)))
    except Exception as e:
        pass

def on_none(window, image, name):
    save_image(image, DIR_CROPPED_NO_SIGNS)

def on_unknown(window, image, name):
    pass

def check_images(in_folder):
    image_reader = tf.WholeFileReader()
    sip = tf.train.string_input_producer(tf.train.match_filenames_once(os.path.join(in_folder, "*.png")), num_epochs=1)
    image_name, image_file = image_reader.read(sip)
    image = tf.image.decode_png(image_file)
    images = []
    dx = (IMAGE_WIDTH - CROPPED_IMAGE_SIZE)/(X_SPLITS-1)
    dy = (IMAGE_HEIGHT - CROPPED_IMAGE_SIZE)/(Y_SPLITS-1)
    for x in range(X_SPLITS):
        for y in range(Y_SPLITS):
            images.append(tf.slice(image, [int(dy*y), int(dx*x), 0], [CROPPED_IMAGE_SIZE, CROPPED_IMAGE_SIZE, -1]))
    images = tf.reshape(tf.to_float(images)/255.0, (X_SPLITS*Y_SPLITS, CROPPED_IMAGE_SIZE, CROPPED_IMAGE_SIZE, 3))
    nn = model_fn(dict(input=images), None, tf.estimator.ModeKeys.PREDICT)
    preds = tf.reshape(nn.predictions['predictions'], (X_SPLITS, Y_SPLITS))
    sess = get_session()
    coord = tf.train.Coordinator()
    tf.train.start_queue_runners(sess, coord)
    try:
        while True:
            name, predictions = sess.run([image_name, preds])
            print(name, 'analysed')
            signs = get_signs(predictions)
            if signs:
                image = pygame.image.load(os.path.join(name))
                for rect in signs:
                    crop = crop_image(image, rect)
                    yield crop, name
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(e)
    finally:
        coord.request_stop()
        coord.join()
        sess.close()


def get_signs(predictions):
    signs = []
    dx = (IMAGE_WIDTH - CROPPED_IMAGE_SIZE)/(X_SPLITS-1)
    dy = (IMAGE_HEIGHT - CROPPED_IMAGE_SIZE)/(Y_SPLITS-1)
    for (x, y), value in np.ndenumerate(predictions):
        if value > 0.5:
            x = x*dx + CROPPED_IMAGE_SIZE/2
            y = y*dy + CROPPED_IMAGE_SIZE/2
            for i, (x1, y1, x2, y2) in enumerate(signs):
                if x >= x1 and x <= x2 and y >= y1 and y <= y2:
                    signs[i] = (
                        min(x1, x-CROPPED_IMAGE_SIZE/2),
                        min(y1, y-CROPPED_IMAGE_SIZE/2),
                        max(x2, x+CROPPED_IMAGE_SIZE/2),
                        max(y2, y+CROPPED_IMAGE_SIZE/2)
                    )
                    break
            signs.append((
                x-CROPPED_IMAGE_SIZE/2,
                y-CROPPED_IMAGE_SIZE/2,
                x+CROPPED_IMAGE_SIZE/2,
                y+CROPPED_IMAGE_SIZE/2
            ))
    if len(signs) > 0:
        signs2 = []
        def add_sign(x, y):
            x = int(min(IMAGE_WIDTH-CROPPED_SIZE, max(0, x - CROPPED_SIZE/2)))
            y = int(min(IMAGE_HEIGHT-CROPPED_SIZE, max(0, y - CROPPED_SIZE/2)))
            signs2.append((x, y, CROPPED_SIZE, CROPPED_SIZE))
        for (x1, y1, x2, y2) in signs:
            w = x2 - x1
            h = y2 - y1
            if w*2 >= CROPPED_SIZE * 3:
                if h*2 >= CROPPED_SIZE * 3:
                    add_sign(x1 + w/4, y1 + w/4)
                    add_sign(x2 - w/4, y1 + w/4)
                    add_sign(x2 - w/4, y2 - w/4)
                    add_sign(x1 + w/4, y2 - w/4)
                else:
                    add_sign(x1 + w/4, y1 + w/2)
                    add_sign(x2 - w/4, y1 + w/2)
            elif h*2 >= CROPPED_SIZE * 3:
                    add_sign(x2 - w/2, y1 + w/4)
                    add_sign(x2 - w/2, y2 - w/4)
            else:
                add_sign(x1 + w/2, y1 + w/2)
        return signs2
    return None


if __name__ == "__main__":
    main(DIR_FRAMES_NO_SIGNS)