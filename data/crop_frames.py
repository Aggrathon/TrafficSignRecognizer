
import os
import uuid
import pygame
from config import SIGN_FRAMES_DIR, CROPPED_SIGNS_DIR, NO_SIGNS_FRAMES_DIR, IMAGE_HEIGHT, IMAGE_WIDTH, SORTING_SCALE

RECT_SIZE = 100

def main():
    os.makedirs(NO_SIGNS_FRAMES_DIR, exist_ok=True)
    os.makedirs(CROPPED_SIGNS_DIR, exist_ok=True)
    imgs = os.listdir(SIGN_FRAMES_DIR)
    imgs.sort(reverse=True)
    last = 0
    current = 0

    pygame.init()
    font = pygame.font.SysFont("monospace", 15)
    label = font.render("P: No Sign    O: Has Sign    <=: Undo    M1: Crop Sign", 1, (255,64,127))
    screen = pygame.display.set_mode((IMAGE_WIDTH*SORTING_SCALE, IMAGE_HEIGHT*SORTING_SCALE))
    img = next_frame(screen, label, imgs[0])
    while current < len(imgs):
        pygame.time.wait(50)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_p:
                    for i in range(last, current):
                        os.rename(os.path.join(SIGN_FRAMES_DIR, imgs[i]), os.path.join(NO_SIGNS_FRAMES_DIR, imgs[i]))
                    last = current
                    current += 1
                if event.key == pygame.K_BACKSPACE:
                    current -= 2
                    for i in range(current, last+1):
                        try:
                            os.rename(os.path.join(NO_SIGNS_FRAMES_DIR, imgs[i]), os.path.join(SIGN_FRAMES_DIR, imgs[i]))
                        except:
                            pass
                    last = current
                elif event.key == pygame.K_o:
                    current += 1
                    last = current
                img = next_frame(screen, label, imgs[current])
            elif event.type == pygame.MOUSEBUTTONUP:
                save_cropped(imgs[current])
            if pygame.mouse.get_pressed()[0]:
                draw_rect(screen, img)

def next_frame(screen, label, image):
    img = pygame.image.load(os.path.join(SIGN_FRAMES_DIR, image))
    img = pygame.transform.scale(img, (IMAGE_WIDTH*SORTING_SCALE, IMAGE_HEIGHT*SORTING_SCALE))
    img.blit(label, (10, 10))
    screen.blit(img, (0, 0))
    pygame.display.update()
    return img

def draw_rect(screen, img):
    screen.blit(img, (0, 0))
    rect = get_rect_screen()
    rect2 = (rect[0]+20*SORTING_SCALE, rect[1]+20*SORTING_SCALE, rect[2]-40*SORTING_SCALE, rect[3]-40*SORTING_SCALE)
    pygame.draw.rect(screen, (255, 0, 0), rect, 1)
    pygame.draw.rect(screen, (128, 128, 128), rect2, 1)
    pygame.display.update()

def get_rect_screen():
    x, y = pygame.mouse.get_pos()
    x = max(0, min(x-RECT_SIZE*SORTING_SCALE/2, IMAGE_WIDTH*SORTING_SCALE-RECT_SIZE*SORTING_SCALE))
    y = max(0, min(y-RECT_SIZE*SORTING_SCALE/2, IMAGE_HEIGHT*SORTING_SCALE-RECT_SIZE*SORTING_SCALE))
    return x, y, RECT_SIZE*SORTING_SCALE, RECT_SIZE*SORTING_SCALE

def get_rect_image():
    x, y = pygame.mouse.get_pos()
    x = max(0, min(x-RECT_SIZE*SORTING_SCALE/2, IMAGE_WIDTH*SORTING_SCALE-RECT_SIZE*SORTING_SCALE))
    y = max(0, min(y-RECT_SIZE*SORTING_SCALE/2, IMAGE_HEIGHT*SORTING_SCALE-RECT_SIZE*SORTING_SCALE))
    return x//SORTING_SCALE, y//SORTING_SCALE, RECT_SIZE, RECT_SIZE

def get_rnd_filename():
    return str(hex(uuid.uuid4().time))[2:]+".png"

def save_cropped(image):
    img = pygame.image.load(os.path.join(SIGN_FRAMES_DIR, image))
    nimg = pygame.Surface((RECT_SIZE, RECT_SIZE))
    nimg.blit(img, (0, 0), get_rect_image())
    pygame.image.save(nimg, os.path.join(CROPPED_SIGNS_DIR, get_rnd_filename()))


if __name__ == "__main__":
    main()
