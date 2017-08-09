
import os
import pygame

from config import DIR_FRAMES_NO_SIGNS, DIR_FRAMES_POTENTIAL, SOURCE_FRAMES_DIR, IMAGES_PER_SECOND
from window import Window


def no_sign(images, window, index, last):
    for i in range(last, index):
        os.rename(os.path.join(SOURCE_FRAMES_DIR, images[i]), os.path.join(DIR_FRAMES_NO_SIGNS, images[i]))
    window.show_image(images[index + IMAGES_PER_SECOND], SOURCE_FRAMES_DIR)
    return index + IMAGES_PER_SECOND, index

def has_sign(images, window, index, last):
    index += IMAGES_PER_SECOND
    for i in range(last, index):
        os.rename(os.path.join(SOURCE_FRAMES_DIR, images[i]), os.path.join(DIR_FRAMES_POTENTIAL, images[i]))
    window.show_image(images[index], SOURCE_FRAMES_DIR)
    return index, index

def undo(images, window, index, last):
    index = max(0, index-IMAGES_PER_SECOND*3-3)
    for i in range(index, last+1):
        try:
            os.rename(os.path.join(DIR_FRAMES_NO_SIGNS, images[i]), os.path.join(SOURCE_FRAMES_DIR, images[i]))
        except:
            pass
        try:
            os.rename(os.path.join(DIR_FRAMES_POTENTIAL, images[i]), os.path.join(SOURCE_FRAMES_DIR, images[i]))
        except:
            pass
    window.show_image(images[index], SOURCE_FRAMES_DIR)
    return index, index


def main():
    os.makedirs(DIR_FRAMES_NO_SIGNS, exist_ok=True)
    os.makedirs(DIR_FRAMES_POTENTIAL, exist_ok=True)
    window = Window("P: No Sign    O: Has Sign    <=: Undo")
    images = os.listdir(SOURCE_FRAMES_DIR)
    images.sort(reverse=True)
    actions = {
        pygame.K_BACKSPACE:undo,
        pygame.K_o:has_sign,
        pygame.K_p:no_sign
    }
    window.iterate(images, actions, SOURCE_FRAMES_DIR)


if __name__ == "__main__":
    main()
