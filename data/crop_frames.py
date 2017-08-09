
import os
import pygame
from config import DIR_FRAMES_POTENTIAL, DIR_FRAMES_SIGNS, DIR_CROPPED_SIGNS, DIR_FRAMES_NO_SIGNS, IMAGE_HEIGHT, IMAGE_WIDTH, IMAGES_PER_SECOND, CROPPED_SIZE
from window import Window, get_rnd_filename, save_cropped


def no_sign(images, window, index, last):
    os.rename(os.path.join(DIR_FRAMES_POTENTIAL, images[index]), os.path.join(DIR_FRAMES_NO_SIGNS, images[index]))
    window.show_image(images[index + 1], DIR_FRAMES_POTENTIAL)
    return index + 1, index

def has_sign(images, window, index, last):
    os.rename(os.path.join(DIR_FRAMES_POTENTIAL, images[index]), os.path.join(DIR_FRAMES_SIGNS, images[index]))
    window.show_image(images[index+1], DIR_FRAMES_POTENTIAL)
    return index+1, index

def undo(images, window, index, last):
    index = max(0, index-IMAGES_PER_SECOND)
    for i in range(index, last+1):
        try:
            os.rename(os.path.join(DIR_FRAMES_NO_SIGNS, images[i]), os.path.join(DIR_FRAMES_POTENTIAL, images[i]))
        except:
            pass
        try:
            os.rename(os.path.join(DIR_FRAMES_SIGNS, images[i]), os.path.join(DIR_FRAMES_POTENTIAL, images[i]))
        except:
            pass
    window.show_image(images[index], DIR_FRAMES_POTENTIAL)
    return index, index

def on_mouse_move(images, window, index, last):
    x, y = pygame.mouse.get_pos()
    size = CROPPED_SIZE*IMAGE_WIDTH//window.screen.get_width()
    x = min(max(0, x-size//2), window.screen.get_width()-size)
    y = min(max(0, y-size//2), window.screen.get_height()-size)
    window.draw_rects([
        ((255, 0, 0), (x, y, size, size), 1),
        ((128, 128, 128), (x+20, y+20, size-20, size-20), 1),
    ])
    return index, last

def on_mouse_click(images, window, index, last):
    #DRAW
    x, y = pygame.mouse.get_pos()
    size_x = CROPPED_SIZE*window.screen.get_width()//IMAGE_WIDTH
    size_y = CROPPED_SIZE*window.screen.get_height()//IMAGE_HEIGHT
    x = min(max(0, x-size_x//2), window.screen.get_width()-size_x)
    y = min(max(0, y-size_y//2), window.screen.get_height()-size_y)
    window.draw_rects([((0, 0, 255), (x, y, size_x, size_y), 1)])
    #SAVE
    x, y = pygame.mouse.get_pos()
    x = max(0, min(x*IMAGE_WIDTH//window.screen.get_width()-CROPPED_SIZE//2, IMAGE_WIDTH-CROPPED_SIZE))
    y = max(0, min(y*IMAGE_HEIGHT//window.screen.get_height()-CROPPED_SIZE//2, IMAGE_HEIGHT-CROPPED_SIZE))
    img = pygame.image.load(os.path.join(DIR_FRAMES_POTENTIAL, images[index]))
    save_cropped(img, (x, y, CROPPED_SIZE, CROPPED_SIZE), DIR_CROPPED_SIGNS)
    return index, last


def main():
    os.makedirs(DIR_FRAMES_NO_SIGNS, exist_ok=True)
    os.makedirs(DIR_FRAMES_SIGNS, exist_ok=True)
    os.makedirs(DIR_CROPPED_SIGNS, exist_ok=True)
    imgs = os.listdir(DIR_FRAMES_POTENTIAL)
    imgs.sort(reverse=True)
    window = Window("P: No Sign    O: Has Sign    <=: Undo    M1: Crop Sign")
    actions = {
        pygame.K_p: no_sign,
        pygame.K_o: has_sign,
        pygame.K_BACKSPACE: undo,
        -12: on_mouse_move,
        -10: on_mouse_click
    }
    window.iterate(imgs, actions, DIR_FRAMES_POTENTIAL)

if __name__ == "__main__":
    main()
