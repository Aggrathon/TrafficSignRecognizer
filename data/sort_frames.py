#!/usr/bin/python3

import os
import pygame

SOURCE_DIR = 'frames'
NONE_DIR = 'none'
POTENTIAL_DIR = 'unsorted'

def main():
    os.makedirs(NONE_DIR, exist_ok=True)
    os.makedirs(POTENTIAL_DIR, exist_ok=True)
    imgs = os.listdir(SOURCE_DIR)
    imgs.sort(reverse=True)
    last = 0
    current = 0

    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    next_frame(screen, imgs[0])
    while current < len(imgs):
        pygame.time.wait(50)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_p:
                    for i in range(last, current):
                        os.rename(os.path.join(SOURCE_DIR, imgs[i]), os.path.join(NONE_DIR, imgs[i]))
                    last = current
                    current += 6
                if event.key == pygame.K_BACKSPACE:
                    current -= 20
                    for i in range(current, last+1):
                        try:
                            os.rename(os.path.join(NONE_DIR, imgs[i]), os.path.join(SOURCE_DIR, imgs[i]))
                        except:
                            pass
                        try:
                            os.rename(os.path.join(POTENTIAL_DIR, imgs[i]), os.path.join(SOURCE_DIR, imgs[i]))
                        except:
                            pass
                    last = current
                elif event.key == pygame.K_o:
                    current += 6
                    for i in range(last, current):
                        os.rename(os.path.join(SOURCE_DIR, imgs[i]), os.path.join(POTENTIAL_DIR, imgs[i]))
                    last = current
                next_frame(screen, imgs[current])

def next_frame(screen, image):
    img = pygame.image.load(os.path.join(SOURCE_DIR, image))
    img = pygame.transform.scale(img, (640, 480))
    screen.blit(img,(0, 0))
    pygame.display.update()


if __name__ == "__main__":
    main()
