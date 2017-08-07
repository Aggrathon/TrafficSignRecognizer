
import uuid
import os
import sys
import pygame

WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480

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
        font1 = pygame.font.SysFont("monospace", 15)
        font2 = pygame.font.SysFont("monospace", height//4)
        self.label = font1.render(text, 1, (255, 64, 127))
        self.screen = pygame.display.set_mode((int(width), int(height)))
        self.wait_screen = pygame.Surface(self.screen.get_size())
        self.wait_screen.fill((0, 0, 0))
        self.wait_screen.blit(font2.render("WAIT", 1, (255, 255, 255)), (100, height//4))
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
        img = pygame.transform.smoothscale(img, self.screen.get_size())
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
        image = pygame.transform.smoothscale(image, (width, height))
        image.blit(self.label, (10, 10))
        self.screen.blit(image, (0, 0))
        pygame.display.update()
        self.last_frame = image

    def draw_rects(self, configs):
        self.screen.blit(self.last_frame, (0, 0))
        for c in configs:
            pygame.draw.rect(self.screen, *c)
        pygame.display.update()
    
    def show_wait(self):
        self.screen.blit(self.wait_screen, (0, 0))
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
        self.show_wait()
        def handle_image(image, name):
            if image is None:
                self.show_file(name)
            else:
                self.show_image(image)
            while True:
                for key in self.check_input():
                    if key in actions:
                        actions[key](self, image, name)
                        self.show_wait()
                        return
        for image, name in generator:
            handle_image(image, name)
