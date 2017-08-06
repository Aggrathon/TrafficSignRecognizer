
import uuid
import os
import sys
import pygame

WINDOW_WIDTH = 960
WINDOW_HEIGHT = 720

def get_rnd_filename():
    return str(hex(uuid.uuid4().time))[2:]+".png"

def save_image(image, folder):
    pygame.image.save(image, os.path.join(folder, get_rnd_filename()))

def crop_image(image, rect):
    nimg = pygame.Surface((rect[2], rect[3]))
    nimg.blit(image, (0, 0), rect)
    return nimg

def save_cropped(image, rect, folder):
    save_image(crop_image(image, rect), folder)

class Window():

    def __init__(self, text, width=WINDOW_WIDTH, height=WINDOW_HEIGHT):
        pygame.init()
        font = pygame.font.SysFont("monospace", 15)
        self.label = font.render(text, 1, (255, 64, 127))
        self.screen = pygame.display.set_mode((int(width), int(height)))
        self.clock = pygame.time.Clock()
        self.last_frame = None

    def show_file(self, image, folder=None):
        """
            Draw the image file to the screen

            image: the path to the file to display

            return: the new frame
        """
        if folder is not None:
            img = pygame.image.load(os.path.join(folder, image))
        else:
            img = pygame.image.load(image)
        img = pygame.transform.scale(img, self.screen.get_size())
        img.blit(self.label, (10, 10))
        self.screen.blit(img, (0, 0))
        pygame.display.update()
        self.last_frame = img
    
    def show_image(self, image):
        width = self.screen.get_width()
        height = image.get_height()*width//image.get_width()
        if height > self.screen.get_height():
            height = self.screen.get_height()
            width = image.get_width()*height//image.get_height()
        image = pygame.transform.scale(image, (width, height))
        image.blit(self.label, (10, 10))
        self.screen.blit(image, (0, 0))
        pygame.display.update()
        self.last_frame = image

    def draw_rects(self, configs):
        self.screen.blit(self.last_frame, (0, 0))
        for c in configs:
            pygame.draw.rect(self.screen, *c)
        pygame.display.update()

    def check_input(self):
        """
            Checks the pygame events
            Quits if necessary
            
            return: A generator for the key releases or mouse actions
                -10 == mouse UP
                -11 == mouse DOWN
                -12 == mouse PRESSSED
        """
        self.clock.tick(20)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYUP:
                yield event.key
            elif event.type == pygame.MOUSEBUTTONUP:
                yield -10
            elif event.type == pygame.MOUSEBUTTONDOWN:
                yield -11
            elif pygame.MOUSEMOTION and pygame.mouse.get_pressed()[0]:
                yield -12

    def iterate(self, images, actions, folder=None):
        index = 0
        last = 0
        self.show_file(images[index], folder)
        while index < len(images):
            for key in self.check_input():
                if key in actions:
                    index, last = actions[key](images, self, index, last)
                    break

    def iterate2(self, generator, actions):
        def handle_image(image, name):
            self.show_image(image)
            while True:
                for key in self.check_input():
                    if key in actions:
                        actions[key](self, image, name)
                        return
        for image, name in generator:
            handle_image(image, name)
