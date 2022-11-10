import pygame
import os
from datetime import datetime
import threading
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import tkinter as tk
import math
from math import atan2 # degrees
import pandas as pd
import numpy as np
# from pygame.constants import USEREVENT
# from pygame.display import toggle_fullscreen

root = tk.Tk()

# screen variables
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
WIDTH, HEIGHT = screen_width, screen_height

# ship variables
ship_list = []
team_1_ship_list = []
team_1_ship_waiting_list = []
team_2_ship_list = []
team_2_ship_waiting_list = []
SPACESHIP_WIDTH, SPACESHIP_HEIGHT = 70, 70

# player stats
PLAYER_CREDITS: float
PLAYER_MAX_BULLETS: float
PLAYER_LASER_RECHARGE_TIME: float
PLAYER_HEALTH: float
PLAYER_FUEL: float
PLAYER_MAX_TORPEDOES: int

def initialize_player_stats():
    """
    Resets the player stats to default. 
    This function runs once at the beginning, and then
    again each time the player loses and returns to round 1.
    """
    global PLAYER_CREDITS, PLAYER_MAX_BULLETS, PLAYER_LASER_RECHARGE_TIME
    global PLAYER_HEALTH, PLAYER_FUEL, PLAYER_MAX_TORPEDOES
    PLAYER_CREDITS = 1000
    PLAYER_MAX_BULLETS = 3
    PLAYER_LASER_RECHARGE_TIME = 1
    PLAYER_HEALTH = 5
    PLAYER_FUEL = 1500
    PLAYER_MAX_TORPEDOES = 0

initialize_player_stats()

# game variables
FPS = 60
TIME_TO_BUY_UPGRADES = False
keys_pressed = []
ROUND_COUNT = 1
round_is_ongoing = False
run = True
version = 2.14
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Game")
BORDER = pygame.Rect(WIDTH//2 - 5, 0, 10, HEIGHT)
event_ID = 1
explosion_group = pygame.sprite.Group()
projectile_list = []
show_targets = False
ship_id = 0 # used for generating a name for the ship
UPGRADE_BUTTON_LIST = []
UPGRADE_WINDOW: object
NUMBER_OF_CHANNELS = 10
current_channel = 1


pygame.font.init()
pygame.mixer.init()
pygame.mixer.set_num_channels(NUMBER_OF_CHANNELS)

# colors
GREY = (100, 100, 100)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
UPGRADE_WINDOW_BACKGROUND = (56, 54, 84)
SELECTED = (47, 85, 151)
ACTIVE =  (143, 170, 220)
INACTIVE = (214, 220, 229)
INACTIVE_TEXT = (127, 127, 127)
GREEN = (56, 87, 35)

# sound effects taken from https://mixkit.co/free-sound-effects/
# also https://pixabay.com/sound-effects
BULLET_HIT_SOUND = pygame.mixer.Sound(os.path.join('Assets', 'war_field_explosion.wav'))
BULLET_HIT_SOUND_PLAYER = pygame.mixer.Sound(os.path.join('Assets', 'explosion_in_battle.wav'))
BULLET_FIRE_SOUND = pygame.mixer.Sound(os.path.join('Assets', 'laser.wav'))
BULLET_FIRE_SOUND_PLAYER = pygame.mixer.Sound(os.path.join('Assets', 'laser_2.mp3'))
BULLET_FIRE_SOUND_ALLY = pygame.mixer.Sound(os.path.join('Assets', 'laser_4.mp3'))
SEISMIC_CHARGE_SOUND= pygame.mixer.Sound(os.path.join('Assets', 'seismic_charge.wav'))
TORPEDO_LAUNCH_SOUND= pygame.mixer.Sound(os.path.join('Assets', 'torpedo_launch.wav'))

EXPLOSION_AND_SCREAMING_SOUND = pygame.mixer.Sound(os.path.join('Assets', 'ship_explodes.wav'))
VICTORY_SOUND = pygame.mixer.Sound(os.path.join('Assets', 'drums.wav'))
ENGINE_SOUND = pygame.mixer.Sound(os.path.join('Assets', 'fuel_burn.wav'))
OUT_OF_FUEL_SOUND = pygame.mixer.Sound(os.path.join('Assets', 'emf_shutdown.mp3'))
EXPLOSION_SOUND = pygame.mixer.Sound(os.path.join('Assets', 'car_explosion_debris.wav'))

SUCCESS_SOUND = pygame.mixer.Sound(os.path.join('Assets', 'success.wav'))
DENIED_SOUND = pygame.mixer.Sound(os.path.join('Assets', 'denied.wav'))
NEXT_ROUND_SOUND = pygame.mixer.Sound(os.path.join('Assets', 'next_round.wav'))


HEALTH_FONT = pygame.font.Font(os.path.join('Assets', 'Roboto-Light.ttf'), 40)
WEAPON_FONT = pygame.font.Font(os.path.join('Assets', 'Roboto-Light.ttf'), 20)
BANNER_FONT = pygame.font.Font(os.path.join('Assets', 'Roboto-Medium.ttf'), 60)
DIAGNOSTICS_FONT = pygame.font.Font(os.path.join('Assets', 'Roboto-Light.ttf'), 15)
UPGRADE_BUTTON_FONT = pygame.font.Font(os.path.join('Assets', 'Roboto-Light.ttf'), 20)

# images
X_WING_IMAGE = pygame.image.load(os.path.join('Assets', 'xwing.png')).convert_alpha()
X_WING_IMAGE = pygame.transform.scale(X_WING_IMAGE, (SPACESHIP_WIDTH, SPACESHIP_HEIGHT))
X_WING_IMAGE = pygame.transform.rotate(X_WING_IMAGE, 270)

OLD_REPUBLIC_FIGHTER = pygame.image.load(os.path.join('Assets', 'old_republic_fighter.png')).convert_alpha()
OLD_REPUBLIC_FIGHTER = pygame.transform.scale(OLD_REPUBLIC_FIGHTER, (SPACESHIP_WIDTH, SPACESHIP_HEIGHT))
OLD_REPUBLIC_FIGHTER = pygame.transform.rotate(OLD_REPUBLIC_FIGHTER, 270)

TIE_FIGHTER_IMAGE = pygame.image.load(os.path.join('Assets', 'tiefighter.png')).convert_alpha()
TIE_FIGHTER_IMAGE = pygame.transform.scale(TIE_FIGHTER_IMAGE, (SPACESHIP_WIDTH, SPACESHIP_HEIGHT))
TIE_FIGHTER_IMAGE = pygame.transform.rotate(TIE_FIGHTER_IMAGE, 90)

BLUE_ORB_IMAGE = pygame.image.load(os.path.join('Assets', 'blue_orb.png')).convert_alpha()
BLUE_ORB_IMAGE = pygame.transform.scale(BLUE_ORB_IMAGE, (15, 15))

BLUE_ORB_IMAGE_DISABLED = pygame.image.load(os.path.join('Assets', 'blue_orb_disabled.png')).convert_alpha()
BLUE_ORB_IMAGE_DISABLED = pygame.transform.scale(BLUE_ORB_IMAGE_DISABLED, (15, 15))

RED_LASER_IMAGE = pygame.image.load(os.path.join('Assets', 'red_laser.png')).convert_alpha()
RED_LASER_IMAGE = pygame.transform.scale(RED_LASER_IMAGE, (15, 15))
RED_LASER_IMAGE = pygame.transform.rotate(RED_LASER_IMAGE, 90)

BLUE_LASER_IMAGE = pygame.image.load(os.path.join('Assets', 'blue_laser.png')).convert_alpha()
BLUE_LASER_IMAGE = pygame.transform.scale(BLUE_LASER_IMAGE, (15, 15))
BLUE_LASER_IMAGE = pygame.transform.rotate(BLUE_LASER_IMAGE, 90)

GREEN_LASER_IMAGE = pygame.image.load(os.path.join('Assets', 'green_laser.png')).convert_alpha()
GREEN_LASER_IMAGE = pygame.transform.scale(GREEN_LASER_IMAGE, (15, 15))
GREEN_LASER_IMAGE = pygame.transform.rotate(GREEN_LASER_IMAGE, 90)

GREEN_LASER_IMAGE_DISABLED = pygame.image.load(os.path.join('Assets', 'green_laser_disabled.png')).convert_alpha()
GREEN_LASER_IMAGE_DISABLED = pygame.transform.scale(GREEN_LASER_IMAGE_DISABLED, (15, 15))
GREEN_LASER_IMAGE_DISABLED = pygame.transform.rotate(GREEN_LASER_IMAGE_DISABLED, 90)

RED_ARROW_WIDTH, RED_ARROW_HEIGHT  = 100, 100
RED_ARROW_IMAGE = pygame.image.load(os.path.join('Assets', 'red_arrow.png')).convert_alpha()
RED_ARROW_IMAGE = pygame.transform.scale(RED_ARROW_IMAGE, (RED_ARROW_WIDTH, RED_ARROW_HEIGHT))
RED_ARROW_IMAGE = pygame.transform.rotate(RED_ARROW_IMAGE, 180)
RED_ARROW_IMAGE_DOWN = pygame.transform.rotate(RED_ARROW_IMAGE, 90)
RED_ARROW_IMAGE_UP = pygame.transform.rotate(RED_ARROW_IMAGE, 270)
RED_ARROW_IMAGE_UP_LEFT = pygame.transform.rotate(RED_ARROW_IMAGE, 315)
RED_ARROW_IMAGE_DOWN_LEFT = pygame.transform.rotate(RED_ARROW_IMAGE, 45)
RED_ARROW = pygame.Rect(WIDTH//4, HEIGHT//2, RED_ARROW_WIDTH, RED_ARROW_HEIGHT) 

TARGET_IMAGE = pygame.image.load(os.path.join('Assets', 'red_target_2.png')).convert_alpha()
TARGET_IMAGE = pygame.transform.scale(TARGET_IMAGE, (200, 200))

SPACE = pygame.image.load(os.path.join('Assets', 'space.png')).convert_alpha()
SPACE = pygame.transform.scale(SPACE, (WIDTH, HEIGHT))

pygame.display.set_icon(X_WING_IMAGE)

# read the game controller from the csv
game_controller = pd.read_csv("game_controller.csv")
print(game_controller)

# events
bullet_sound_event = pygame.USEREVENT + 1
bullet_hit_sound_event = pygame.USEREVENT + 2
engine_sound_event = pygame.USEREVENT + 3
screaming_sound_event = pygame.USEREVENT + 4
toggle_target_event = pygame.USEREVENT + 5

# quadrants
quadrant_6 = ((0, WIDTH//2), (0, HEIGHT))
quadrant_7 = ((WIDTH//2, WIDTH), (0, HEIGHT))
quadrant_14 = ((-1 * WIDTH//2, 0), (-1 * HEIGHT//2, 1.5 * HEIGHT))
quadrant_15 = ((WIDTH, 1.5 * WIDTH), (-1 * HEIGHT//2, 1.5 * HEIGHT))
# entire_playable_area_quadrant = ((.1 * WIDTH, .9 * WIDTH), (.1 * HEIGHT, .9 * HEIGHT)) # smaller playable area for testing
entire_playable_area_quadrant = ((-1 * WIDTH, 2 * WIDTH), (-1 * HEIGHT, 2 * HEIGHT))

# sprites
explosion_image_list = []
for num in range(1, 6):
	img = pygame.image.load(os.path.join('Assets', f'exp{num}.png'))
	img = pygame.transform.scale(img, (100, 100))
	explosion_image_list.append(img)

green_explosion_image_list = []
for num in range(1, 6):
	img = pygame.image.load(os.path.join('Assets', f'exp{num}_green.png'))
	img = pygame.transform.scale(img, (100, 100))
	green_explosion_image_list.append(img)

# general functions
def get_angle(p1, p2):
  """
  Determines the angle of a straight line drawn between point one and two. 
  In radians.
  REFERENCE: WikiCode, http://wikicode.wikidot.com/get-angle-of-line-between-two-points
  """
  xDiff = p2[0] - p1[0]
  yDiff = p2[1] - p1[1]

  radians = atan2(yDiff, xDiff)

  return radians

def get_distance(p1, p2):
    """calculates the distance between two points"""
    xDiff = p2[0] - p1[0]
    yDiff = p2[1] - p1[1]

    distance = math.sqrt(xDiff ** 2 + yDiff **2)
    return distance


def simplify_angle(angle):
    """
    takes and angle and returns simplied angle in radians.
    no negatives or angles greater than 6.28319 radians.
    for example: 
        -5 degrees -> 355 degress
        400 degress -> 340 degress

    """
    full_rotation = 6.28319 # 360 degrees in radians
    while angle > full_rotation:
        angle -= full_rotation
    if angle < 0:
        angle += full_rotation
    return angle

def play_sound_and_increment_channel(sound):
    """
    chooses the next channel and then plays the sound on that channel
    prevents sounds from overlapping and causing conflicts
    """
    global current_channel

    if current_channel == NUMBER_OF_CHANNELS:
        current_channel = 1
    else:
        current_channel += 1

    pygame.mixer.Channel(current_channel).play(sound)

class upgrade_button:
    def __init__(self):
        """
        type: Laser Capacity, Laser Recharge Time, Health, Fuel, Next Round
        """
        global UPGRADE_WINDOW
        button_width = 400
        button_height = 50
        button_padding = 5

        if len(UPGRADE_BUTTON_LIST) == 0:
            self.blit_coord = (WIDTH/2 - button_width/2, HEIGHT/2 - 200)
        else:
            previous_x = UPGRADE_BUTTON_LIST[-1].blit_coord[0]
            previous_y = UPGRADE_BUTTON_LIST[-1].blit_coord[1]
            previous_height = UPGRADE_BUTTON_LIST[-1].button_rect.height
            self.blit_coord = (previous_x, previous_y + previous_height + button_padding)
        
        self.button_rect = pygame.Rect(self.blit_coord[0], self.blit_coord[1], button_width, button_height)
        self.status = "active"
        self.color = GREY
        self.text_color = WHITE
        
        UPGRADE_BUTTON_LIST.append(self)

        # re-define UPGRADE_WINDOW
        blit_x = WIDTH / 2 - button_width / 2 - button_padding
        blit_y = UPGRADE_BUTTON_LIST[0].button_rect.y - button_padding # HEIGHT / 2 - 400
        width = button_width + (2 * button_padding)
        height = len(UPGRADE_BUTTON_LIST) * (button_height + button_padding) + button_padding
        UPGRADE_WINDOW = pygame.Rect(blit_x, blit_y, width, height)

    def check_status(self):
        """
        checks the status of the upgrade buttons and updates their color accordingly
        """
        if self.status not in ["selected", "active", "inactive"]:
            return

        if self.status == "selected":
            self.color = SELECTED
            self.text_color = WHITE
        elif PLAYER_CREDITS >= self.cost:
            self.status = "active"
            self.color = ACTIVE
            self.text_color = WHITE
        elif PLAYER_CREDITS < self.cost:
            self.status = "inactive"
            self.color = INACTIVE
            self.text_color = INACTIVE_TEXT
        
    def is_pressed(self):
        """
        defines what happens when upgrade button is clicked
        """
        global player_ship, PLAYER_MAX_BULLETS, PLAYER_CREDITS, TIME_TO_BUY_UPGRADES
        global PLAYER_LASER_RECHARGE_TIME
        if self.status == "active":
            self.status = "selected"
            PLAYER_CREDITS -= self.cost
            self.price_text = "Purchased"
            self.perform_action()
        elif self.status == "next button":
            self.perform_action()
        else:
            DENIED_SOUND.play()
            print("insufficient funds")

    def blit(self):
        pygame.draw.rect(WIN, self.color, self.button_rect)
        text_buffer = 10
        self.text_rendered = UPGRADE_BUTTON_FONT.render(self.text, 1, self.text_color)
        self.price_text_rendered = UPGRADE_BUTTON_FONT.render(self.price_text, 1, self.text_color)
        self.text_blit_x = self.button_rect.x + text_buffer
        self.text_blit_y = self.button_rect.y + self.button_rect.height / 2 - self.text_rendered.get_height() / 2
        self.price_text_blit_x = self.button_rect.x + self.button_rect.width - self.price_text_rendered.get_width() - text_buffer
        self.price_text_blit_y = self.text_blit_y
        WIN.blit(self.text_rendered, (self.text_blit_x, self.text_blit_y))
        WIN.blit(self.price_text_rendered, (self.price_text_blit_x, self.price_text_blit_y))

class upgrade_button_laser_capacity(upgrade_button):
    def __init__(self):
        upgrade_button.__init__(self)
        self.cost = 3000
        self.text = f"Laser Capacity +1"
        self.price_text = f"{self.cost} Credits"
        
    def perform_action(self):
        global PLAYER_MAX_BULLETS
        PLAYER_MAX_BULLETS += 1
        player_ship.available_bullets = PLAYER_MAX_BULLETS # this is to ensure display is instantly updated 
        print("upgrading laser capacity")
        SUCCESS_SOUND.play()

class upgrade_button_laser_time(upgrade_button):
    def __init__(self):
        upgrade_button.__init__(self)
        self.cost = 4000
        self.text = "Laser Recharge Time -10%"
        self.price_text = f"{self.cost} Credits"

    def perform_action(self):
        global PLAYER_LASER_RECHARGE_TIME
        previous_time = PLAYER_LASER_RECHARGE_TIME
        PLAYER_LASER_RECHARGE_TIME *= .9
        print(f"upgrading laser recharge time from {previous_time} to {PLAYER_LASER_RECHARGE_TIME}")
        SUCCESS_SOUND.play()

class upgrade_button_health(upgrade_button):
    def __init__(self):
        upgrade_button.__init__(self)
        self.cost = 4000
        self.text = "Health +1"
        self.price_text = f"{self.cost} Credits"

    def perform_action(self):
        global PLAYER_HEALTH
        PLAYER_HEALTH += 1
        player_ship.health = PLAYER_HEALTH # this is to ensure display is instantly updated
        SUCCESS_SOUND.play()

class upgrade_button_fuel(upgrade_button):
    def __init__(self):
        upgrade_button.__init__(self)
        self.cost = 2500
        self.text = "Fuel +500"
        self.price_text = f"{self.cost} Credits"

    def perform_action(self):
        global PLAYER_FUEL
        PLAYER_FUEL += 500
        player_ship.fuel = PLAYER_FUEL # this is to ensure display is instantly updated
        SUCCESS_SOUND.play()

class upgrade_torpedo(upgrade_button):
    def __init__(self):
        upgrade_button.__init__(self)
        self.cost = 5000
        self.text = "Proton Torpedo"
        self.price_text = f"{self.cost} Credits"

    def perform_action(self):
        global PLAYER_MAX_TORPEDOES
        PLAYER_MAX_TORPEDOES += 1
        player_ship.maximum_torpedoes = PLAYER_MAX_TORPEDOES # this is to ensure display is instantly updated
        player_ship.available_torpedoes = PLAYER_MAX_TORPEDOES
        SUCCESS_SOUND.play()

class next_round_button(upgrade_button):
    def __init__(self):
        upgrade_button.__init__(self)
        self.status = "next button" # this prevents the check_status function from altering this button
        self.cost = 0
        self.text = "Next Round"
        self.price_text = ""
        self.color = GREEN

    def blit(self):
        pygame.draw.rect(WIN, self.color, self.button_rect)
        self.text_rendered = UPGRADE_BUTTON_FONT.render(self.text, 1, self.text_color)
        self.text_blit_x = self.button_rect.x + self.button_rect.width / 2 - self.text_rendered.get_width() / 2
        self.text_blit_y = self.button_rect.y + self.button_rect.height / 2 - self.text_rendered.get_height() / 2
        WIN.blit(self.text_rendered, (self.text_blit_x, self.text_blit_y))

    def perform_action(self):
        global TIME_TO_BUY_UPGRADES
        TIME_TO_BUY_UPGRADES = False
        NEXT_ROUND_SOUND.play()
        main()
                
class ship_1:
    def __init__(self, image, team, is_ai = True, 
                    health=5, fuel=2000, maximum_torpedoes=0,
                    maximum_bullets=3, bullet_recharge_time=1,
                    acceleration=.5, accuracy=50):
        global event_ID, ship_id
        
        # image
        self.image = image
        self.width = 70
        self.height = 70
                
        # general characteristics
        self.ship_id = ship_id
        ship_id += 1
        self.team = team
        self.is_ai = is_ai
        self.acceleration = acceleration
        self.health = health
        self.fuel = fuel
        self.out_of_fuel = False
        self.max_speed = 3.5
        self.vel_x = 0
        self.vel_y = 0
        self.selected_weapon = 'Laser'
        self.maximum_bullets = maximum_bullets
        self.available_bullets = maximum_bullets
        self.maximum_torpedoes = maximum_torpedoes
        self.available_torpedoes = self.maximum_torpedoes
        self.bullet_recharge_time = bullet_recharge_time # in seconds
        self.hit_event = pygame.USEREVENT + 5 + event_ID
        event_ID += 1
        self.is_off_screen = False
        self.quadrant = ''
        self.accuracy = accuracy

        # sounds
        if self.team == 1 and self.is_ai == False:
            self.laser_sound = BULLET_FIRE_SOUND_PLAYER
        elif self.team == 1 and self.is_ai:
            self.laser_sound = BULLET_FIRE_SOUND_ALLY
        elif self.team == 2:
            self.laser_sound = BULLET_FIRE_SOUND

        # controls
        self.up = False
        self.down = False
        self.left = False
        self.right = False
        self.fire = False
        self.engine_on = False
        self.change_target = False

        # movement
        self.x_vel = 0
        self.y_vel = 0
        self.target_point_x, self.target_point_y = self.select_starting_position()
        self.rectangle = pygame.Rect(self.target_point_x, self.target_point_y, self.width, self.height)
        self.target_rectangle = pygame.Rect(-100, -100, 70, 70)
        self.target_ship = self

        # team 1 bots start in random movement mode
        # team 2 bots start in pursue target mode
        if self.team == 1:
            self.ai_mode = 0
        elif self.team == 2:
            self.ai_mode = 1

        if self.team == 2: # if enemy, rotate the image to face the left side of the screen
            self.image = pygame.transform.rotate(self.image, 180)

    def check_fuel(self):
        """
        checks if ship is out of fuel
        when fuel reaches 0, a sound plays, 10 seconds passes, and then the ship's health is set to zero
        """
        def thread():
            global FPS
            if self.out_of_fuel == False and self.fuel <= 0:
                OUT_OF_FUEL_SOUND.play()
                self.out_of_fuel = True

                clock = pygame.time.Clock()
                frame = 0
                while run and round_is_ongoing and self in ship_list:
                    clock.tick(FPS)
                    frame += 1
                    if frame > 10 * FPS: 
                        self.health = 0
                        break
        threading.Thread(target=thread).start()

    def select_starting_position(self):
        """
        selects a random starting position for the beginning of the round.
        """
        global player_ship
        buffer = .75 * self.width # some buffer so that ships don't get placed on the edge of the screen.
        if self.team == 2:
            target_point_x = np.random.randint(quadrant_15[0][0] + buffer , quadrant_15[0][1] - buffer)
            target_point_y = np.random.randint(quadrant_15[1][0] + buffer , quadrant_15[1][1] - buffer)
        elif self. team == 1 and self.is_ai == False:
            target_point_x = np.random.randint(quadrant_6[0][0] + buffer , quadrant_6[0][1] - buffer)
            target_point_y = np.random.randint(quadrant_6[1][0] + buffer , quadrant_6[1][1] - buffer)
        elif self.team == 1:
            target_point_x = np.random.randint(quadrant_14[0][0] + buffer , quadrant_14[0][1] - buffer)
            target_point_y = np.random.randint(quadrant_14[1][0] + buffer , quadrant_14[1][1] - buffer)
        return target_point_x, target_point_y

    def select_random_position(self):
        """
        selects a random position within its own quadrant
        used by the ai for randomly moving around during the round. 
        """
        buffer = .75 * self.width # some buffer so that ships don't get placed on the edge of the screen.
        if self.team == 2:
            target_point_x = np.random.randint(quadrant_7[0][0] + buffer , quadrant_7[0][1] - buffer)
            target_point_y = np.random.randint(quadrant_7[1][0] + buffer , quadrant_7[1][1] - buffer)
        elif self.team == 1:
            target_point_x = np.random.randint(quadrant_6[0][0] + buffer , quadrant_6[0][1] - buffer)
            target_point_y = np.random.randint(quadrant_6[1][0] + buffer , quadrant_6[1][1] - buffer)

        self.define_target_rectangle()

        return target_point_x, target_point_y

    def check_controls(self, events):
        """
        checks the buttons the user is pressing.
        only for the human player.
        ai equivalent is ai_move_to_target()
        """
        global keys_pressed, team_2_ship_list
        if self.is_ai == False:
            self.up = keys_pressed[pygame.K_w]
            self.down = keys_pressed[pygame.K_s]
            self.left = keys_pressed[pygame.K_a]
            self.right = keys_pressed[pygame.K_d]

            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.fire = True
                    else:
                        self.fire = False
                    
                increment = 0 
                # changing target_ship
                if event.type == pygame.KEYDOWN: # and self.change_target == False:
                    if event.key == pygame.K_UP:
                        team_2_ship_list.sort(key=lambda ship: ship.rectangle.y)
                        increment = -1
                    if event.key == pygame.K_DOWN:
                        team_2_ship_list.sort(key=lambda ship: ship.rectangle.y)
                        increment = 1                        
                    if event.key == pygame.K_LEFT:
                        team_2_ship_list.sort(key=lambda ship: ship.rectangle.x)
                        increment = -1
                    if event.key == pygame.K_RIGHT:
                        team_2_ship_list.sort(key=lambda ship: ship.rectangle.x)
                        increment = 1

                    if increment != 0:
                        if self.target_ship == self:
                                self.target_ship = team_2_ship_list[0]
                        else:
                            index = team_2_ship_list.index(self.target_ship)
                            try:
                                self.target_ship = team_2_ship_list[index + increment]
                            except:
                                self.target_ship = team_2_ship_list[0]
                    
                    # changing weapon
                    if event.key == pygame.K_1:
                        self.selected_weapon = "Laser"
                    if event.key == pygame.K_2 and self.available_torpedoes > 0: 
                        self.selected_weapon = "Torpedo"
                        
        else:
            pass

        if self.available_torpedoes <= 0:
            self.selected_weapon = "Laser"

    def run_ai(self):
        def thread():
            global run, round_is_ongoing, player_ship, ship_list, PLAYER_CREDITS
            self.ai_move_to_target()
            self.manage_firing()
            if self.ai_mode == 0:
                self.random_movement()
                self.select_target_ship()
            elif self.ai_mode == 1:
                self.pursue_target()
            self.randomize_ai_mode()
            clock = pygame.time.Clock()
            while run and round_is_ongoing and self in ship_list and self.health > 0:
                clock.tick(FPS)
                # when the ship's target ship dies, choose a new target
                # do not select any dead ships or ai ships that are off screen
                target_is_off_screen, _ = self.target_ship.determine_off_screen()
                if self.target_ship not in ship_list or (target_is_off_screen and self.target_ship != player_ship): 
                    self.select_target_ship()
                    
                # seek vengeance on attacker, unless self is low on health
                for laser in projectile_list:
                    if self.rectangle.colliderect(laser.rectangle) and laser.team != self.team:
                        random_chance = np.random.randint(100)
                        if random_chance > 50 and self.health > 2: # randomly choose whether to retaliate against attacker
                            self.pursue_target(laser.parent)
                        else: 
                            self.random_movement()
                # don't pursue target ship off screen unless it is the player ship
                is_off_screen, _ = self.target_ship.determine_off_screen()
                if is_off_screen and self.target_ship != player_ship: 
                    self.random_movement()
                    # pause the run_ai function to give the ship time to re-enter the screen. 
                    # otherwise it will calculate a bunch of new random positions unnecessarily 
                    time.sleep(3)  

                # if the bot's target is the player and the player is offscreen, change bot's ai_mode to pursue target
                # this is to ensure the player can't hide offscreen from bots
                if self.target_ship.is_ai == False and self.target_ship.determine_off_screen()[0] and self.ai_mode != 1:
                    self.pursue_target(provided_target=self.target_ship)

        threading.Thread(target=thread).start()

    def randomize_ai_mode(self):
        """
        runs a looping thread that waits a random number of seconds and then
        randomly selects a new ai mode
        """
        def thread():
            global run, round_is_ongoing, ship_list

            fps = 10
            clock = pygame.time.Clock()
            while run and round_is_ongoing and self in ship_list and self.health > 0:
                clock.tick(fps)

                random_wait_time = np.random.randint(20, 60) # random wait time in seconds
                fps = 10
                clock = pygame.time.Clock()
                n = 0
                while run and round_is_ongoing and self in ship_list and self.health > 0 and n < random_wait_time * fps:
                    clock.tick(fps)
                    n += 1

                original_ai_mode = self.ai_mode
                self.ai_mode = np.random.randint(2)

                if self.ai_mode == 0:
                    self.random_movement()
                elif self.ai_mode == 1:
                    self.pursue_target()  
        threading.Thread(target=thread).start()

    def select_target_ship(self):
        global team_1_ship_list, team_2_ship_list
        """randomly selects a new target ship"""
        if self.team == 1 and len(team_2_ship_list) != 0:
            index = np.random.randint(len(team_2_ship_list))
            self.target_ship = team_2_ship_list[index]
        elif self.team == 2 and len(team_1_ship_list) != 0:
            index = np.random.randint(len(team_1_ship_list))
            self.target_ship = team_1_ship_list[index]
        else:
            self.target_ship = self
        return self.target_ship

    def define_target_rectangle(self):
        """
        when the target coordinates change, 
        use this function to update the target rectangle's position
        """
        plot_point_x = self.target_point_x - self.target_rectangle.width//2
        plot_point_y = self.target_point_y - self.target_rectangle.height//2

        self.target_rectangle = pygame.Rect(plot_point_x, plot_point_y, 70, 70)

    def random_movement(self):
        """"mode 0"""
        def thread():
            global run, round_is_ongoing

            # generate a new target rectangle
            self.ai_mode = 0
            self.target_point_x, self.target_point_y = self.select_random_position()
            self.define_target_rectangle()

            clock = pygame.time.Clock()
            while run and round_is_ongoing and self.ai_mode == 0:
                clock.tick(10)
                if self.rectangle.colliderect(self.target_rectangle):
                    # when it reaches its target rectangle, select a  new target rectangle
                    self.target_point_x, self.target_point_y = self.select_random_position()
                    self.define_target_rectangle()
        threading.Thread(target=thread).start()

    def pursue_target(self, provided_target=""):
        """
        mode 1
        if there is no provided_target, one will be chosen randomly
        """
        self.ai_mode = 1
        if provided_target == "":
            self.select_target_ship()
        else:
            self.target_ship = provided_target
        self.target_point_x, _ = self.select_random_position()
        def thread():
            clock = pygame.time.Clock()
            while run and round_is_ongoing and self.ai_mode == 1:
                clock.tick(10)

                # time it will take bullet to reach x coordinate of target
                bullet_time = abs((self.rectangle.x - self.target_ship.rectangle.x) / 20) # 20 is the speed of bullets

                # distance the enemy will travel in bullet_time
                enemy_distance = self.target_ship.y_vel * bullet_time

                # the distance that the ship should trail behind its target_ship on the y axis
                # don't trail at all if the target_ship is moving slowly
                if abs(self.target_ship.y_vel) < 2:
                    self.target_point_y = self.target_ship.rectangle.center[1]
                if abs(self.target_ship.y_vel) > 2:
                    trailing_distance = enemy_distance
                    self.target_point_y = self.target_ship.rectangle.center[1] - trailing_distance
                
                self.define_target_rectangle()

                if self.rectangle.colliderect(self.target_rectangle):
                    self.target_point_x, _ = self.select_random_position()
                    self.target_point_y = self.target_ship.rectangle.center[1]
                    self.define_target_rectangle()

        threading.Thread(target=thread).start()  

    def hold_position(self):
        """
        mode 2
        move to a randomly selected position and hold it
        """
        # generate a new target rectangle
        self.ai_mode = 2
        self.target_point_x, self.target_point_y = self.select_random_position()
        self.define_target_rectangle()

 
    def ai_move_to_target(self):
        """
        meant to run perpetuately during each round, regardless of the ship's current ai_mode
        cause the ship to direct itself to its current target
        """                
        # manage directional keys (new way)
        # not as fuel efficient as the old way
        if self.ship_id % 2 == 0:
            p1 = self.rectangle.center
            p2 = self.target_rectangle.center
            angle = get_angle(p1, p2)
            angle = simplify_angle(angle)

            goal_vel_x = math.cos(angle) * self.max_speed
            goal_vel_y = math.sin(angle) * self.max_speed

            if self.vel_x < goal_vel_x:
                self.right = True
            else:
                self.right = False

            if self.vel_x > goal_vel_x:
                self.left = True
            else: 
                self.left = False

            if self.vel_y < goal_vel_y: 
                self.down = True
            else:
                self.down = False

            if self.vel_y > goal_vel_y: 
                self.up = True
            else:
                self.up = False

        else:

        # manage directional keys (old way)
        # more fuel efficient than the new way
            buffer = self.target_rectangle.width//2
            my_x, my_y = self.rectangle.center

            if my_x < self.target_point_x - buffer: 
                self.right = True
            else:
                self.right = False

            if my_x > self.target_point_x + buffer: 
                self.left = True
            else: 
                self.left = False

            if my_y < self.target_point_y - buffer: 
                self.down = True
            else:
                self.down = False

            if my_y > self.target_point_y + buffer: 
                self.up = True
            else:
                self.up = False

        # threading.Thread(target=thread).start()

    def manage_firing(self):
        """
        initiates a thread that continously loops to determine when the ship should fire
        """
        def caculate_miss_margin():
            """
            in between each shot fired, this function calculates 
            the margin by which the next shot will miss its target
            this is determined by self.accuracy
            """
            rand_chance = np.random.randint(0, 100)
            if  rand_chance > self.accuracy:
                miss_above = np.random.randint(0, 2)
                miss_margin = np.random.randint(70, 180)
                if miss_above:
                    pass
                else:
                    miss_margin = miss_margin * -1 
            else:
                miss_margin = 0
            return miss_margin

        def thread():
            global ship_list
            miss_margin = caculate_miss_margin()
            clock = pygame.time.Clock()
            target_still_count = 0 
            while run and round_is_ongoing and self in ship_list and self.health > 0:
                clock.tick(60)

                # if the target comes to a stop, calculate a new miss margin
                
                if -1 < self.target_ship.y_vel < 1:
                    target_still_count += 1
                if target_still_count > 200:
                    # print('target is staying still. setting miss margin to 0')
                    miss_margin = 0
                    target_still_count = 0

                if self.ai_mode == 0 or self.ai_mode == 1:
                    buffer = 10
                    # calculate the distance_between_ships_x, given the point where the bullet is fired and 
                    # where it will impact on the target
                    # this value is calculated differently based on team, because each team faces opposite directions
                    if self.team == 1:
                        point_of_bullet_fire_x = self.rectangle.x + self.rectangle.width
                        point_of_bullet_impact_x = self.target_ship.rectangle.x
                    elif self.team == 2:
                        point_of_bullet_fire_x = self.rectangle.x
                        point_of_bullet_impact_x = self.target_ship.rectangle.x + self.target_ship.rectangle.width

                    distance_between_ships_x = abs(point_of_bullet_fire_x - point_of_bullet_impact_x)

                    # calculate bullet velocity based on team
                    if self.team == 1:
                        bullet_velocity = 20
                    elif self.team == 2:
                        bullet_velocity = -20

                    # time it will take bullet to reach x coordinate of the leading edge of the target
                    # this may not be a perfect way of calcuating the time, but it seems very close, the ai's shooting seems to be 100% accurate
                    bullet_time = (distance_between_ships_x) / abs(self.target_ship.x_vel - bullet_velocity) 

                    # distance the enemy will travel in bullet_time
                    enemy_distance_y = self.target_ship.y_vel * bullet_time

                    if self.rectangle.center[1] - buffer < self.target_ship.rectangle.center[1] + enemy_distance_y + miss_margin < self.rectangle.center[1] + buffer:
                        bullets_to_fire = np.random.randint(1, 6)
                        fire_speed = np.random.randint(5, 50) / 100 # random firing speed between .05 and .5 seconds
                        for _ in range(bullets_to_fire):                
                            self.fire = True
                            time.sleep(fire_speed)
                            self.fire = False
                            thread() # start the thread over so that a new miss_margin can be randomly calculated
                            break # break out of the loop so the current thread ends
        threading.Thread(target=thread).start()


    def handle_movement(self):
        global keys_pressed, entire_playable_area_quadrant
        global team_1_ship_list, team_2_ship_list
        # SHIP MOVEMENT
        team_1_center_boundary = BORDER.x - 5
        team_2_center_boundary = BORDER.x + BORDER.width + 5
        if self.team == 1 and self.rectangle.x + self.width >= team_1_center_boundary:
            self.x_vel = 0
            self.rectangle.x = team_1_center_boundary - self.width - 1
        elif self.team ==2 and self.rectangle.x <= team_2_center_boundary:
            self.x_vel = 0
            self.rectangle.x = team_2_center_boundary + 1
        else:
            pass

        self.rectangle.x += self.x_vel
        self.rectangle.y += self.y_vel

        # ENGINES
        if self.fuel > 0:
            if self.left and self.x_vel > (-1 * self.max_speed):
                self.x_vel -= self.acceleration
                self.try_engine_fire()
                if self.fuel > 0:
                    self.fuel -= 1
                else:
                    self.fuel = 0 
            if self.right and self.x_vel < self.max_speed:
                self.x_vel += self.acceleration
                self.try_engine_fire()
                if self.fuel > 0:
                    self.fuel -= 1
                else:
                    self.fuel = 0
            if self.up and self.y_vel > (-1 * self.max_speed):
                self.y_vel -= self.acceleration
                self.try_engine_fire()
                if self.fuel > 0:
                    self.fuel -= 1
                else:
                    self.fuel = 0
            if self.down and self.y_vel < self.max_speed:
                self.y_vel += self.acceleration
                self.try_engine_fire()
                if self.fuel > 0:
                    self.fuel -= 1
                else:
                    self.fuel = 0

        else:
            pass

        # enforcement of boundaries
        if self.rectangle.x <= entire_playable_area_quadrant[0][0]:
            self.x_vel = 0
            self.rectangle.x = entire_playable_area_quadrant[0][0] + 1

        if self.rectangle.x >= entire_playable_area_quadrant[0][1]:
            self.x_vel = 0
            self.rectangle.x = entire_playable_area_quadrant[0][1] -1

        if self.rectangle.y <= entire_playable_area_quadrant[1][0]:
            self.y_vel = 0
            self.rectangle.y = entire_playable_area_quadrant[1][0] + 1

        if self.rectangle.y >= entire_playable_area_quadrant[1][1]:
            self.y_vel = 0
            self.rectangle.y = entire_playable_area_quadrant[1][1] - 1

        # turn of the engine if none of the directional keys are pressed
        if self.left == False and \
            self.right == False and \
            self.up == False and \
            self.down == False:
            self.engine_on = False 
        else:
            pass
            
        # assign a new target_ship if the current target_ship dies
        if self.team == 1:
            enemy_list = team_2_ship_list
        elif self.team == 2:
            enemy_list = team_1_ship_list

        if self.target_ship not in enemy_list and len(enemy_list) > 0:
            self.target_ship = enemy_list[0]
       
    def detect_collisions(self):
        global player_ship, ship_list, explosion_group, projectile_list, team_1_ship_list, team_2_ship_list, PLAYER_CREDITS
        for proj in projectile_list:
            if self.rectangle.colliderect(proj.rectangle) and proj.parent != self:
                if proj.team != self.team:
                    original_health = self.health
                    self.health -= proj.damage
                    if self.health < 0:
                        self.health = 0
                    damage_infliced = original_health - self.health
                    if proj.parent == player_ship:
                        PLAYER_CREDITS += 100 * damage_infliced
                projectile_list.remove(proj)
                if self == player_ship:
                    proj.impact_sound.play()
                else:
                    proj.impact_sound.play()
                                    
                x, y = self.rectangle.center
                explosion = Explosion(x, y)
                explosion_group.add(explosion)
                del proj # delete the instance of the projectile object
        if self.health <= 0:
            for _ in range(10):
                random_x = np.random.randint(100) + self.rectangle.x
                random_y = np.random.randint(100) + self.rectangle.y
                explosion = Explosion(random_x, random_y)
                explosion_group.add(explosion)

            if self == player_ship:
                EXPLOSION_AND_SCREAMING_SOUND.play()
            else:
                EXPLOSION_SOUND.play()
            ship_list.remove(self)
            if self.team == 1:
                team_1_ship_list.remove(self)
            elif self.team == 2:
                team_2_ship_list.remove(self)
            del self # delete the instance of the ship object


    def fire_weapons(self):
        global bullet_sound_event
        if self.fire:
            if self.team == 1:
                laser_start_x = self.rectangle.x + self.rectangle.width
            if self.team == 2:
                laser_start_x = self.rectangle.x
            laser_start_y = self.rectangle.center[1]
            
            if self.selected_weapon == "Laser" and self.available_bullets > 0: 
                laser_beam(laser_start_x, laser_start_y, team=self.team, parent=self)
                self.available_bullets -= 1

                # if self.determine_off_screen()[0]:
                #     center_of_the_map = ((WIDTH / 2), (HEIGHT / 2))
                #     distance = get_distance(self.rectangle.center, center_of_the_map)
                #     distance_percentage = 1 - (distance / WIDTH)
                #     print(distance_percentage)
                #     self.laser_sound.set_volume(distance_percentage)
                # else:
                #     self.laser_sound.set_volume(1)

                self.laser_sound.play()

            
            elif self.selected_weapon == "Torpedo" and self.available_torpedoes > 0:
                torpedo(laser_start_x, laser_start_y, team=self.team, parent=self)
                self.available_torpedoes -= 1

                # if self.determine_off_screen()[0]:
                #     TORPEDO_LAUNCH_SOUND.set_volume(.1)
                # else:
                #     TORPEDO_LAUNCH_SOUND.set_volume(1)

                TORPEDO_LAUNCH_SOUND.play()
            self.fire = False

    def replenish_bullets(self):
        def thread():
            global run, round_is_ongoing, ship_list
            clock = pygame.time.Clock()
            while run and round_is_ongoing and self in ship_list and self.health > 0:
                clock.tick(10)
                if self.available_bullets < self.maximum_bullets:
                    time.sleep(self.bullet_recharge_time)
                    self.available_bullets += 1
        threading.Thread(target=thread).start()
    
    def try_engine_fire(self):
        """
        If the engine is off, this function will turn it on and play the engine firing sound.
        this function is just to handle the playing of the engine sound. It does not affect movement
        """
        def thread():
            if self.engine_on: # checks to see if the engine is already on. Won't play the sound again if the engine is already on 
                pass
            else:
                self.engine_on = True # turns on the engine
                # ENGINE_SOUND.set_volume(.4)
                # ENGINE_SOUND.play()
                # pygame.event.post(pygame.event.Event(engine_sound_event))

        threading.Thread(target=thread).start() 

    def determine_off_screen(self):
        """determines if the ship is off screen and what quadrant it is in
        RETURNS
        self.is_off_screen: Bool
        self.quadrant: str
        quadrants: left, top, bottom, upper left, bottom left, on screen
        """
        if (self.rectangle.x + self.rectangle.width) < 0 and self.rectangle.y > 0 and self.rectangle.y < HEIGHT:
            self.is_off_screen = True
            self.quadrant = 'left'
        elif (self.rectangle.y + self.rectangle.height) < 0 and self.rectangle.x > 0:
            self.is_off_screen = True
            self.quadrant = 'top'
        elif self.rectangle.y > HEIGHT and self.rectangle.x > 0:
            self.is_off_screen = True
            self.quadrant = 'bottom'
        elif self.rectangle.x < 0 and self.rectangle.y < 0:
            self.is_off_screen = True
            self.quadrant = 'upper left'
        elif self.rectangle.x < 0 and self.rectangle.y > HEIGHT:
            self.is_off_screen = True
            self.quadrant = 'bottom left'
        elif self.rectangle.x > WIDTH and self.rectangle.y > 0 and self.rectangle.y < HEIGHT:
            self.is_off_screen = True
            self.quadrant = 'right'
        else:
            self.is_off_screen = False
            self.quadrant = 'on screen'

        if self.fuel <= 0 and self.is_off_screen:
            self.health = 0
        return self.is_off_screen, self.quadrant

    def draw_off_screen_arrow(self):
        if self.quadrant == "left":
            WIN.blit(RED_ARROW_IMAGE, (0, self.rectangle.y))
        elif self.quadrant == "top":
            WIN.blit(RED_ARROW_IMAGE_UP, (self.rectangle.x, 0))
        elif self.quadrant == "bottom":
            WIN.blit(RED_ARROW_IMAGE_DOWN, (self.rectangle.x, HEIGHT - RED_ARROW_HEIGHT))
        elif self.quadrant == "upper left":
            WIN.blit(RED_ARROW_IMAGE_UP_LEFT, (0, 0))
        elif self.quadrant == "bottom left":
            WIN.blit(RED_ARROW_IMAGE_DOWN_LEFT, (0, HEIGHT - RED_ARROW_HEIGHT - 40))
        else:
            pass

       
class laser_beam:
    def __init__(self, x, y, team, parent):
        global projectile_list
        self.team = team
        self.parent = parent
        self.width = 10
        self.height = 10
        self.rectangle = pygame.Rect(x - self.width//2, y - self.height//2, self.width, self.height)
        self.damage = 1
        if self.parent == player_ship:
            self.image = GREEN_LASER_IMAGE
            self.vel_x = 20
            self.launch_sound = BULLET_FIRE_SOUND_PLAYER
            self.impact_sound = BULLET_HIT_SOUND
        elif self.team == 1:
            self.image = BLUE_LASER_IMAGE
            self.vel_x = 20
            self.launch_sound = BULLET_FIRE_SOUND_ALLY
            self.impact_sound = BULLET_HIT_SOUND
        elif self.team == 2:
            self.image = RED_LASER_IMAGE
            self.vel_x = -20
            self.launch_sound = BULLET_FIRE_SOUND
            self.impact_sound = BULLET_HIT_SOUND
        self.vel_y = 0

        projectile_list.append(self)

class torpedo: # needs to more work, needs to be implemented
    def __init__(self, x, y, team, parent):
        global projectile_list
        self.team = team
        self.parent = parent
        self.width = 10
        self.height = 10
        self.angle = 0
        self.vel_x = 0
        self.vel_y = 0
        self.rectangle = pygame.Rect(x - self.width//2, y - self.height//2, self.width, self.height)
        self.damage = 5
        self.fuel = 400
        self.impact_sound = SEISMIC_CHARGE_SOUND
        self.launch_sound = TORPEDO_LAUNCH_SOUND
        if self.team == 1:
            self.image = BLUE_ORB_IMAGE
            self.vel = 16
            self.target_list = team_2_ship_list
        if self.team == 2:
            self.image = RED_LASER_IMAGE
            self.vel = -16
            self.target_list = team_1_ship_list
            
        projectile_list.append(self)        

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

def handle_projectiles():
    for proj in projectile_list:
        if type(proj).__name__ == "torpedo":
            if proj.fuel > 0:
                full_rotation = 6.28319 # 360 degrees in radians
                p1 = proj.rectangle.center
                p2 = proj.parent.target_ship.rectangle.center
                new_angle = get_angle(p1, p2)
                new_angle = simplify_angle(new_angle)
                proj.angle = simplify_angle(proj.angle)

                # complex path finding
                # allows the projectile to keep looping back until fuel runs out
                # works well, but not perfect
                if new_angle > proj.angle:
                    left_angle = abs(new_angle - proj.angle)
                    right_angle = abs(full_rotation - left_angle)
                else:
                    left_angle = abs(full_rotation - proj.angle + new_angle)
                    right_angle = abs(full_rotation - left_angle)

                if left_angle < right_angle:
                    proj.angle += .025
                else:
                    proj.angle -= .025

                proj.vel_x = math.cos(proj.angle) * proj.vel
                proj.vel_y = math.sin(proj.angle) * proj.vel
                proj.fuel -= 1
         
        proj.rectangle.x += proj.vel_x
        proj.rectangle.y += proj.vel_y

        # remove the projectile if it goes too far off screen
        if proj.rectangle.center[0] > 2 * WIDTH or proj.rectangle.center[0] < -1 * WIDTH:
            projectile_list.remove(proj)
            del proj

def write_to_leaderboard():
    global version, ROUND_COUNT, player_ship
    """
    see  https://www.analyticsvidhya.com/blog/2020/07/read-and-update-google-spreadsheets-with-python/ for more info
    """
    pass

def draw_window():
    global RED_ARROW, RED_ARROW_IMAGE, ship_list, explosion_group, WIDTH, HEIGHT, team_2_ship_list, projectile_list, player_ship
    global TIME_TO_BUY_UPGRADES, PLAYER_CREDITS
    WIN.blit(SPACE, (0, 0))
    pygame.draw.rect(WIN, BLACK, BORDER)

    # enemy stats
    total_enemy_health = 0
    total_enemy_fuel = 0
    for ship in team_2_ship_list:
        if ship.health > 0:
            total_enemy_health += ship.health
            total_enemy_fuel += ship.fuel

    total_enemy_health_text = HEALTH_FONT.render("Health: " + str(total_enemy_health), 1, WHITE)
    total_enemy_fuel_text = HEALTH_FONT.render("Fuel: " + str(total_enemy_fuel), 1, WHITE)
    
    WIN.blit(total_enemy_health_text, (WIDTH - total_enemy_health_text.get_width() - 10, 10))
    WIN.blit(total_enemy_fuel_text, (WIDTH - total_enemy_fuel_text.get_width() - 10, 80))
 
    # player stats  
    player_health_text = HEALTH_FONT.render("Health: " + str(player_ship.health), 1, WHITE)
    player_fuel_text = HEALTH_FONT.render("Fuel: " + str(player_ship.fuel), 1, WHITE)
    player_credit_text = HEALTH_FONT.render("Credits: " + str(PLAYER_CREDITS), 1, WHITE)

    if TIME_TO_BUY_UPGRADES:
        weapon_1_text = WEAPON_FONT.render("1. Laser", 1, WHITE)
        weapon_2_text = WEAPON_FONT.render("2. Torpedo", 1, WHITE)
        laser_icon = GREEN_LASER_IMAGE
        torpedo_icon = BLUE_ORB_IMAGE
    elif player_ship.selected_weapon == "Laser":
        weapon_1_text = WEAPON_FONT.render("1. Laser", 1, WHITE)
        weapon_2_text = WEAPON_FONT.render("2. Torpedo", 1, GREY)
        laser_icon = GREEN_LASER_IMAGE
        torpedo_icon = BLUE_ORB_IMAGE_DISABLED
    elif player_ship.selected_weapon == "Torpedo":
        weapon_1_text = WEAPON_FONT.render("1. Laser", 1, GREY)
        weapon_2_text = WEAPON_FONT.render("2. Torpedo", 1, WHITE)
        laser_icon = GREEN_LASER_IMAGE_DISABLED
        torpedo_icon = BLUE_ORB_IMAGE 

    if player_ship.health > 0:
        WIN.blit(player_health_text, (10, 10))
        WIN.blit(player_fuel_text, (10, 80))
        WIN.blit(player_credit_text, (10, 150))


        WIN.blit(weapon_1_text, (10, 220))
        n=0
        for _ in range(player_ship.available_bullets):
            WIN.blit(laser_icon, (125 - laser_icon.get_width() / 2 + n, 225))
            n += 25

        if PLAYER_MAX_TORPEDOES > 0: # only blit the torpedo information if the player has torpedoes
            WIN.blit(weapon_2_text, (10, 260))
            n=0
            for _ in range(player_ship.available_torpedoes):
                WIN.blit(torpedo_icon, (125 - torpedo_icon.get_width() / 2 + n, 265))
                n += 25
   

    round_count_text = HEALTH_FONT.render(f'Round {ROUND_COUNT}', 1, WHITE)

    for laser in projectile_list:
        WIN.blit(laser.image, (laser.rectangle.x, laser.rectangle.y))
    
    if show_targets:
        for ship in ship_list:
            if ship.team == 1:
                color = YELLOW
            else:
                color = RED
            if ship.is_ai:
                pygame.draw.rect(WIN, color, ship.target_rectangle)
                text = DIAGNOSTICS_FONT.render(f'Ship {ship.ship_id}', 1, color)
                WIN.blit(text, (ship.rectangle.x,  ship.rectangle.y - text.get_height()))
            if ship.is_ai and ship.ai_mode == 0:
                pygame.draw.rect(WIN, color, ship.target_rectangle)
                pygame.draw.line(WIN, color=color, start_pos=ship.rectangle.center, end_pos=(ship.target_point_x, ship.target_point_y)) # from the ship to the target rectangle
            if ship.is_ai and ship.ai_mode == 1:
                pygame.draw.line(WIN, color=color, start_pos=ship.rectangle.center, end_pos=ship.target_ship.rectangle.center) # from the ship to the target ship

        def define_ship_diagnostics_text():
            ship_diagnostics_text = DIAGNOSTICS_FONT.render(f"Velocity: ({np.round(ship.x_vel)}, {np.round(ship.y_vel)}) | " +
                                                             f"Position: ({np.round(ship.rectangle.x)}, {np.round(ship.rectangle.y)}) | " +
                                                             f"Ship ID: {ship.ship_id} | " +
                                                             f"Target: {ship.target_ship.ship_id} | " +
                                                             f"Mode: {ship.ai_mode} | " +
                                                             f"Health: {str(ship.health)} | " +
                                                             f"Fuel: {str(ship.fuel)} | " + 
                                                             f"Bullets: {str(ship.available_bullets)} | " +
                                                             f"Accuracy: {str(ship.accuracy)} | ", 1, WHITE)
            return ship_diagnostics_text

        n = 0
        for ship in team_2_ship_list:
            try:
                ship_diagnostics_text = define_ship_diagnostics_text()
                WIN.blit(ship_diagnostics_text, (WIDTH - ship_diagnostics_text.get_width() -10,  HEIGHT - 20 -n))
                n += 20
            except:
                pass

        n = 0
        for ship in team_1_ship_list:
            try:
                ship_diagnostics_text = define_ship_diagnostics_text()
                WIN.blit(ship_diagnostics_text, (WIDTH - ship_diagnostics_text.get_width() - 10 - WIDTH//2,  HEIGHT - 20 -n))
                n += 20
            except:
                pass

    for ship in ship_list:
        WIN.blit(ship.image, (ship.rectangle.x, ship.rectangle.y))
        ship.determine_off_screen()
        if ship.is_ai == False:
            ship.draw_off_screen_arrow()
        else:
            pass
    WIN.blit(round_count_text, (10, HEIGHT - 60))

    if player_ship.target_ship != player_ship and player_ship.selected_weapon == "Torpedo":
        x = player_ship.target_ship.rectangle.center[0] - TARGET_IMAGE.get_width()/2
        y = player_ship.target_ship.rectangle.center[1] - TARGET_IMAGE.get_height()/2
        WIN.blit(TARGET_IMAGE, (x, y))

    explosion_group.draw(WIN)
    explosion_group.update()

    if TIME_TO_BUY_UPGRADES:
        draw_upgrade_screen()

    pygame.display.update()

def draw_winner(winner, text):
    global ROUND_COUNT
    draw_text = BANNER_FONT.render(text, 1, WHITE)
    draw_window()
    WIN.blit(draw_text, (WIDTH//2 - draw_text.get_width()/2, HEIGHT//2 - draw_text.get_height()//2))
    pygame.display.update()
    if winner == 'red':
        pygame.time.delay(4500)
        try:
            write_to_leaderboard()
        except:
            pass
        end_round(progress_to_next_round = False)
    else:
        end_round(progress_to_next_round = True)
        pygame.time.delay(600)
        VICTORY_SOUND.play()
        pygame.time.delay(4000)

def end_round(progress_to_next_round = True):
    global ROUND_COUNT, player_ship, PLAYER_CREDITS
    if progress_to_next_round:
        ROUND_COUNT += 1
    else:
        ROUND_COUNT = 1
        initialize_player_stats()

def main():
    global run, ROUND_COUNT, game_controller
    global ship_id, enemy_ship, ship_list, team_1_ship_list, team_2_ship_list
    global team_1_ship_waiting_list, team_2_ship_waiting_list
    global round_is_ongoing, ship_list, player_ship, projectile_list, show_targets, keys_pressed
    global OLD_REPUBLIC_FIGHTER, X_WING_IMAGE, TIE_FIGHTER_IMAGE
    # global player stats
    global PLAYER_CREDITS, PLAYER_MAX_BULLETS, PLAYER_LASER_RECHARGE_TIME
    global PLAYER_HEALTH, PLAYER_FUEL

    projectile_list = []
    team_1_ship_list = []
    team_2_ship_list = []
    ship_list = []
  

    number_of_rounds_in_game_controller = game_controller.iloc[:,0].to_list()[-1]

    if ROUND_COUNT > number_of_rounds_in_game_controller:
        this_rounds_ships = game_controller.loc[game_controller['ROUND_COUNT'] == number_of_rounds_in_game_controller].reset_index()
    else:
        this_rounds_ships = game_controller.loc[game_controller['ROUND_COUNT'] == ROUND_COUNT].reset_index()

    # set up player_ship
    player_ship = ship_1(
                X_WING_IMAGE, team=1, is_ai = False, health=PLAYER_HEALTH, maximum_torpedoes=PLAYER_MAX_TORPEDOES,
                fuel=PLAYER_FUEL, maximum_bullets=PLAYER_MAX_BULLETS, bullet_recharge_time=PLAYER_LASER_RECHARGE_TIME)
    ship_list.append(player_ship)
    team_1_ship_list.append(player_ship)
    player_ship.replenish_bullets()

    ship_id = 0 # this is used when instantiating a ship
    for i in range(this_rounds_ships.shape[0]):
        is_ai = this_rounds_ships.loc[i, 'is_ai']
        if is_ai == 'ai':
          is_ai = 1
        else:
          is_ai = 0

        image = this_rounds_ships.loc[i, 'image']
        if image == 'OLD_REPUBLIC_FIGHTER':
          image = OLD_REPUBLIC_FIGHTER
        elif image == 'TIE_FIGHTER_IMAGE':
          image = TIE_FIGHTER_IMAGE
        elif image == 'X_WING_IMAGE':
          image = X_WING_IMAGE

        team = int(this_rounds_ships.loc[i, 'team'])
        health = int(this_rounds_ships.loc[i, 'health'])
        fuel = int(this_rounds_ships.loc[i, 'fuel'])
        # available_bullets = int(this_rounds_ships.loc[i, 'available_bullets'])
        maximum_bullets = int(this_rounds_ships.loc[i, 'maximum_bullets'])
        bullet_recharge_time = float(this_rounds_ships.loc[i, 'bullet_recharge_time'])
        accuracy = float(this_rounds_ships.loc[i, 'accuracy'])

        
        new_ship = ship_1(image=image, team=team, is_ai=is_ai, 
            health=health, fuel=fuel, 
            maximum_bullets=maximum_bullets, 
            bullet_recharge_time=bullet_recharge_time, accuracy=accuracy) 

        new_ship.replenish_bullets()

        if new_ship.is_ai:    
            new_ship.run_ai()

        if is_ai == False:
            team_1_ship_list.append(player_ship)
            ship_list.append(player_ship)      
        elif team == 1 and is_ai:
            if len(team_1_ship_list) < 5:
                team_1_ship_list.append(new_ship)
                ship_list.append(new_ship) 
            else:
                team_1_ship_waiting_list.append(new_ship)
        elif team == 2: 
            if len(team_2_ship_list) < 5:
                team_2_ship_list.append(new_ship)
                ship_list.append(new_ship) 
            else:
                team_2_ship_waiting_list.append(new_ship)
        
    # should this be moved into the __init__ function of ship_1?
    round_is_ongoing = True
    for ship in ship_list:
        ship.replenish_bullets()
        if ship.is_ai:
            ship.run_ai()

    clock = pygame.time.Clock()
    while run:
        clock.tick(FPS)

        # add reinforcements
        # when the total number of ships for the whole team drops below 5, spawn another from the waiting list
        if len(team_1_ship_list) < 5 and len(team_1_ship_waiting_list) > 0:
            team_1_ship_list.append(team_1_ship_waiting_list[0])
            ship_list.append(team_1_ship_waiting_list[0])
            team_1_ship_waiting_list[0].replenish_bullets()
            team_1_ship_waiting_list[0].run_ai()
            team_1_ship_waiting_list.remove(team_1_ship_waiting_list[0])

        if len(team_2_ship_list) < 5 and len(team_2_ship_waiting_list) > 0:
            team_2_ship_list.append(team_2_ship_waiting_list[0])
            ship_list.append(team_2_ship_waiting_list[0])
            team_2_ship_waiting_list[0].replenish_bullets()
            team_2_ship_waiting_list[0].run_ai()
            team_2_ship_waiting_list.remove(team_2_ship_waiting_list[0])

        keys_pressed = pygame.key.get_pressed()

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p and show_targets:
                    show_targets = False
                elif event.key == pygame.K_p and show_targets != True:
                    show_targets = True    
                    
            # sound events
            if event.type == bullet_sound_event:
                BULLET_FIRE_SOUND.play()
            
            if event.type == bullet_hit_sound_event:
                BULLET_FIRE_SOUND.play()

            if event.type == engine_sound_event:
                ENGINE_SOUND.set_volume(.4)
                ENGINE_SOUND.play()

            # allow the user to pause and quit using the escape key
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:               
                text = "Quit the game? (Y/N)"
                draw_text = BANNER_FONT.render(text, 1, WHITE)
                WIN.blit(draw_text, (WIDTH//2 - draw_text.get_width()/2, HEIGHT//2 - draw_text.get_height()//2))
                pygame.display.update()
                paused = True

                clock = pygame.time.Clock()
                while paused and run:
                    clock.tick(FPS)
                    events = pygame.event.get()
                    for event in events:
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_y:
                                run = False
                                round_is_ongoing = False
                                EXPLOSION_AND_SCREAMING_SOUND.play()
                                time.sleep(7)
                                if ROUND_COUNT > 1:
                                    write_to_leaderboard()
                                else:
                                    pass
                                pygame.quit()
                                break
                            if event.key == pygame.K_ESCAPE or event.key == pygame.K_n:
                                paused = False
                                break
        
        #this breaks out of the main loop if the user quits the game
        if run == False: 
            break

        for ship in ship_list:
            ship.check_controls(events)
            ship.handle_movement()
            ship.fire_weapons()
            ship.detect_collisions()
            ship.check_fuel()
            if ship.is_ai:
                ship.ai_move_to_target()

        handle_projectiles()
        draw_window()

        winner = ""

        sum_of_team_2_health = 0
        for ship in team_2_ship_list:
            sum_of_team_2_health += ship.health
        if sum_of_team_2_health <= 0:
            winner = 'yellow'
            text = "Round cleared!"

        sum_of_team_1_health = 0
        for ship in team_1_ship_list:
            sum_of_team_1_health += ship.health
        if sum_of_team_1_health <= 0:
            winner = 'red'
            text = "Round failed!"
            
        if winner == "":
            n = 0
        if winner != "":
            n += 1
            if n >= 40: # wait a little bit so that the explosion has time to complete, then draw the winner
                round_is_ongoing = False # stops all threads that should be stopped at the end of the round
                draw_window()
                draw_winner(winner, text)
                break
    
    if ROUND_COUNT > 1 and run:
        buy_upgrades()
    elif run:
        main()

def draw_upgrade_screen():
    global player_ship, UPGRADE_WINDOW
    
    pygame.draw.rect(WIN, BLACK, UPGRADE_WINDOW)

    for button in UPGRADE_BUTTON_LIST:
        button.blit()

    purchase_upgrades_text = HEALTH_FONT.render("Purchase Upgrades", 1, WHITE)

    buffer = 10
    text_x = UPGRADE_WINDOW.x + UPGRADE_WINDOW.width / 2 - purchase_upgrades_text.get_width() / 2
    text_y = UPGRADE_WINDOW.y - purchase_upgrades_text.get_height() - buffer
    WIN.blit(purchase_upgrades_text, (text_x, text_y))

def buy_upgrades():
    global player_ship, TIME_TO_BUY_UPGRADES, UPGRADE_WINDOW, UPGRADE_BUTTON_LIST
    
    UPGRADE_BUTTON_LIST = []
    upgrade_button_laser_capacity()
    upgrade_button_laser_time()
    upgrade_button_health()
    upgrade_button_fuel()
    upgrade_torpedo()
    next_round_button()

    # replenish some stats so that the user can see their full stats while buying upgrades
    player_ship.health = PLAYER_HEALTH
    player_ship.fuel = PLAYER_FUEL
    player_ship.available_bullets = PLAYER_MAX_BULLETS
    player_ship.available_torpedoes = PLAYER_MAX_TORPEDOES
    player_ship.maximum_torpedoes = PLAYER_MAX_TORPEDOES

    TIME_TO_BUY_UPGRADES = True
    clock = pygame.time.Clock()
    while TIME_TO_BUY_UPGRADES:
        clock.tick(FPS)
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                TIME_TO_BUY_UPGRADES = False
                pygame.quit()
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                pos = pygame.mouse.get_pos()
                for button in UPGRADE_BUTTON_LIST:
                    if button.button_rect.collidepoint(pos):
                        button.is_pressed()

        for button in UPGRADE_BUTTON_LIST:
            button.check_status()

        draw_window()

if __name__ == "__main__":
    main()