import pygame
from pygame.locals import *
import os

# taken from https://www.youtube.com/watch?v=d06aVDzOfV8
# github: https://github.com/russs123/Explosion

pygame.init()

clock = pygame.time.Clock()
fps = 60

screen_width = 600
screen_height = 800

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Explosion Demo')

#define colours
bg = (50, 50, 50)

def draw_bg():
	screen.fill(bg)

explosion_image_list = []
for num in range(1, 6):
	img = pygame.image.load(os.path.join('Assets', f'exp{num}.png'))
	img = pygame.transform.scale(img, (100, 100))
	explosion_image_list.append(img)

#create Explosion class
class Explosion(pygame.sprite.Sprite):
	def __init__(self, x, y):
		global explosion_image_list
		pygame.sprite.Sprite.__init__(self)
		self.index = 0
		self.image = explosion_image_list[self.index]
		self.rect = self.image.get_rect()
		self.rect.center = [x, y]
		self.counter = 0

	def update(self):
		explosion_speed = 4
		#update explosion animation
		self.counter += 1

		if self.counter >= explosion_speed and self.index < len(explosion_image_list ) - 1:
			self.counter = 0
			self.index += 1
			self.image = explosion_image_list [self.index]

		#if the animation is complete, reset animation index
		if self.index >= len(explosion_image_list) - 1 and self.counter >= explosion_speed:
			self.kill()


explosion_group = pygame.sprite.Group()


run = True
while run:

	clock.tick(fps)

	#draw background
	draw_bg()

	explosion_group.draw(screen)
	explosion_group.update()


	#event handler
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			run = False
		if event.type == pygame.MOUSEBUTTONDOWN:
			pos = pygame.mouse.get_pos()
			explosion = Explosion(pos[0], pos[1])
			explosion_group.add(explosion)


	pygame.display.update()

pygame.quit()	