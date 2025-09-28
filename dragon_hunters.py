# This is one of my first Pygame games, so sorry if it isn't coded that well
# Written in Python 3.13.1 / 1.13.3

# To build this, you need to use cx_freeze. Run 'pip install cx_freeze' and run build.bat to build.
# Certain modules are required to run and build this. Run setup.bat to install them.

'''
---FOR THE MODDERS---
To add a new object, make sure each object has a tick() function. For rendering the object, use a render() function.
'''

# Always gotta import modules first!!!
import pygame
import random
import math
import time
import pickle
import json
import os
from os import system
from psutil import Process
from sys import exit
from font_manager import FontManager

font_manager = FontManager()

# Code values
tile_size = 32 # Determines the resolution of the tileset on screen, really important
screen_width = 640
screen_height = 480
draw_width = 21 # This and draw_height contain the allowance of tiles on the screen, could save on performance or can be adjusted for lower tile resolutions
draw_height = 20
camera_smoothness = 15

pygame.font.init()
pygame.mixer.init()

font = FontManager().get_font("font.ttf",32)
smaller_font = font_manager.get_font("font.ttf",16)
debug_font = pygame.font.Font('assets/fonts/debug.TTF',16)
working_text = font.render('Working...',False,'white')

# Loading other stuff
dialog_box = pygame.image.load("assets/boxes/original/dialog.png")

hints_file = open("data/text/loading_hints.json")
loading_hints = json.load(hints_file)
hints_file.close()

version_file = open("version.txt")
version = version_file.read()
version_file.close()

# Settings
options_file = open("save_data/options.json")
options = json.load(options_file)
options_file.close()

tile_addresses = { # Add your tiles here
    # Tiles are located in assets/tiles, please only use up to 32x because higher resolutions will be downscaled
    # Keys can be strings or integers, but its easier and faster to work with integers
    0:"grass.png",
    1:"snow.png",
    2:"water.png",
    3:"brick.png",
    4:"tree.png",
    5:"wood.png",
    6:"error.png",
    7:"house_bottom_left.png",
    8:"house_bottom_middle.png",
    9:"house_bottom_right.png",
    10:"house_top_left.png",
    11:"house_top_middle.png",
    12:"house_top_right.png",
    13:"transparent.png",
    14:"sand.png"
}

collision_table = { # 0 = no collision, 1 = collision
    0:0,
    1:0,
    2:1,
    3:1,
    4:1,
    5:0,
    6:1,
    7:1,
    8:0,
    9:1,
    10:1,
    11:1,
    12:1,
    13:1,
    14:0
}

try:
    controls_file = open("save_data/controls.json")
    controls = json.load(controls_file)
    controls_file.close()
except:
    print("Either an error occured loading controls or no file exists")
    controls = {
        "keyboard":{
            "up":"up",
            "down":"down",
            "left":"left",
            "right":"right",
            "a":"x",
            "b":"z",
            "y":"a",
            "x":"s",
            "start":"return",
            "fullscreen":"f11"
        } # I'm planning on adding controller input soon
    }

tilemap = [] # Currently loaded tilemap
# Width (480) = 20
# Height (360) = 15

# Memory stuff, no editing
level = []
tiles = {}
objects = {}
teleports = {}
images = {}
audio = {}
single_keys = {}
level_values = {}
active_keys = {}
old_keys = {}
fonts = {}
player_data = None
show_dialog = False
controls_enabled = True
music = None
in_controls = False

# Classes

class player_class():
    def __init__(self, x=16, y=16,spritelist=['player/front.png','player/back.png','player/left.png','player/right.png','player/front_walk1.png','player/front_walk2.png','player/back_walk1.png','player/back_walk2.png','player/left_walk1.png','player/left_walk2.png','player/right_walk1.png','player/right_walk2.png'],animations={"front_walk":4,"back_walk":6,"left_walk":8,"right_walk":10},sizex=28,sizey=28):
        self.x = x
        self.y = y
        self.sprite = 0
        self.sizex = sizex
        self.sizey = sizey
        self.left = False
        self.direction = 'down'
        self.spritelist = spritelist
        self.animations = animations
        self.class_type = 'player'
        self.animation_frame = 0
        self.animation_speed = 0.05
        self.moved = False
        self.rect = pygame.rect.Rect(x,y,sizex,sizey)
    def load_assets(self):
        load_object_images(self.spritelist)
    def move(self, by):
        by_x = by[0]
        by_y = by[1]
        if by_x > 0:
            self.direction = 0
        elif by_x < 0:
            self.direction = 1
        elif by_y > 0:
            self.direction = 3
        elif by_y < 0:
            self.direction = 2
        old_pos = (self.x,self.y)
        self.x += by_x
        self.y += by_y
        if (check_collision((self.x,self.y)) or check_collision((self.x + 28,self.y)) or check_collision((self.x,self.y + 28)) or check_collision((self.x + 28,self.y + 28))) and not noclip:
            self.x = old_pos[0]
            self.y = old_pos[1]
    def tick(self):
        global camera_x, camera_y, player_data
        if controls_enabled:
            if active_keys["b"]:
                player_speed = 4
            else:
                player_speed = 2
            self.moved = False
            if active_keys["right"]:
                self.move((player_speed,0))
                self.moved = True
            elif active_keys["left"]:      
                self.move((0 - player_speed,0))
                self.moved = True
            if active_keys["up"]:
                self.move((0,0 - player_speed))
                self.moved = True
            elif active_keys["down"]:
                self.move((0,player_speed))
                self.moved = True
            if self.moved:
                self.animation_frame += player_speed * self.animation_speed
            else:
                self.animation_frame = 0
            target_camera_x = (self.x - (((screen_width - 640) / 640) + 1) * 306) - camera_x # 306
            target_camera_y = (self.y - (((screen_height - 480) / 640) + 1) * 226) - camera_y
            camera_x += (target_camera_x / camera_smoothness)
            camera_y += (target_camera_y / camera_smoothness)
            static_level = level_values.get("static")
            if static_level:
                if bool(static_level):
                    camera_x = 0
                    camera_y = 0
        self.rect = pygame.rect.Rect(self.x,self.y,self.sizex,self.sizey)
    def render(self):
        flipped = False
        animation_frame = math.floor(self.animation_frame)
        animation_id = 0
        if animation_frame >= 2:
            animation_frame = 0
            self.animation_frame = 0
        if self.direction == 2:
            animation_id = self.animations["back_walk"]
            sprite = 1
        elif self.direction == 0:
            animation_id = self.animations["right_walk"]
            sprite = 3
        elif self.direction == 1:
            sprite = 2
            animation_id = self.animations["left_walk"]
        else:
            animation_id = self.animations["front_walk"]
            sprite = 0
        if self.moved == True:
            sprite = animation_id + animation_frame
        sprite_to_render = pygame.transform.scale(images[self.spritelist[sprite]],(self.sizex,self.sizey))
        if flipped:
            sprite_to_render = pygame.transform.flip(sprite_to_render,True,False)
        screen.blit(sprite_to_render,(self.x - camera_x,self.y - camera_y))

class npc():
    def __init__(self,x,y,spritelist,sprite,sizex,sizey,behaviour={"type":"idle"}):
        self.x = x
        self.y = y
        self.sprite = sprite
        self.sizex = sizex
        self.sizey = sizey
        self.spritelist = spritelist
        self.behaviour = behaviour
        self.class_type = 'npc'
        self.load_assets()
    def load_assets(self):
        self.a_released = True
        load_object_images(self.spritelist)
        if self.behaviour.get("dialog_audio"):
            load_audio([f'dialog/{self.behaviour["dialog_audio"]}'])
    def tick(self):
        global dialog, show_dialog, controls_enabled
        if self.behaviour.get("dialog"):
            collide_with_player = False
            for obj in objects:
                if obj.class_type == 'player':
                    if obj.rect.collidepoint(self.x,self.y) or obj.rect.collidepoint(self.x + self.sizex, self.y) or obj.rect.collidepoint(self.x, self.y + self.sizey) or obj.rect.collidepoint(self.x + self.sizex, self.y + self.sizey):
                        collide_with_player = True
            if show_dialog and collide_with_player:
                controls_enabled = False
            if single_keys["a"] and show_dialog:
                show_dialog = False
                controls_enabled = True
            elif single_keys["a"] and not show_dialog and collide_with_player:
                dialog_file = open(f"data/dialog/{self.behaviour["dialog"]}","r")
                dialog = json.load(dialog_file)
                dialog_file.close()
                if self.behaviour.get("dialog_audio") and options["dialog_audio_enabled"]:
                    audio[f'dialog/{self.behaviour.get("dialog_audio")}'].play()
                show_dialog = True
    def render(self):
        sprite_to_render = pygame.transform.scale(images[self.spritelist[self.sprite]],(self.sizex,self.sizey))
        screen.blit(sprite_to_render,(self.x - camera_x,self.y - camera_y))

# Game functions

def handle_events():
    global screen, fullscreen, z, events, screen_width, screen_height
    for key in controls["keyboard"]:
        single_keys[key] = False
    pressed_keys = pygame.key.get_pressed()
    for key in controls["keyboard"]:
        pressed = False
        if pressed_keys[pygame.key.key_code(controls["keyboard"].get(key))]:
            pressed = True
        active_keys[key] = pressed
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    toggle_fullscreen = False
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        if event.type == pygame.KEYDOWN:
            key_name = pygame.key.name(event.key)
            if controls["keyboard"].get("fullscreen") == key_name and not in_controls:
                toggle_fullscreen = True
            for key in controls["keyboard"]:
                if controls["keyboard"].get(key) == key_name:
                    single_keys[key] = True
                else:
                    single_keys[key] = False
    if toggle_fullscreen:
        fullscreen = not fullscreen
        if fullscreen:
            screen = pygame.display.set_mode((screen_width,screen_height),pygame.FULLSCREEN)
        else:
            screen = pygame.display.set_mode((screen_width,screen_height))
        time.sleep(1)

def render_text(text_data,font:pygame.font.Font,pos,line_space):
    i = 0
    for text in text_data:
        screen.blit(font.render(text,False,'black'),(pos[0],pos[1] + i * line_space))
        i += 1

def load_object_images(images_to_load):
    global images
    for image in images_to_load:
        images[image] = pygame.image.load(f"assets/objects/{image}")
        print(f"Loaded {image}")

def load_audio(audio_to_load):
    global audio
    for audio_file in audio_to_load:
        audio[audio_file] = pygame.mixer.Sound(f"assets/audio/{audio_file}")
        print(f"Loaded {audio_file}")

def check_collision(coords):
    global player_x, player_y
    global teleports
    coords = convert_to_tile_coords(coords)
    tile = get_tile(coords)
    teleport = teleports.get(f'{coords[0]},{coords[1]}')
    if teleport:
        print(teleport)
        target_map = teleport["target_map"]
        starting_pos = str.split(teleport["starting_pos"],",")
        print(starting_pos)
        loading_screen = None
        if teleport.get('loading_screen'):
            loading_screen = teleport["loading_screen"]
        render_loading_screen(loading_screen,None)
        load_level(target_map,teleport['starting_pos'])
        if starting_pos != ['']:
            for obj in objects:
                if obj.class_type == "player":
                    obj.x = int(starting_pos[0])
                    obj.y = int(starting_pos[1])
    return dict.get(collision_table,tile) == 1

def load_tile(tile):
    tile = pygame.image.load(f'assets/tiles/{tile}')
    return tile

# Loading tiles is now performed by load_group_of_assets().

def get_tile(coords): # Gets the tile at the X and Y coordinates, starting from 0,0
    if coords[0] < 0 or coords[1] < 0:
        return(6)
    try:
        row = tilemap[coords[1]]
        return row[coords[0]]
    except:
        return(6)

def set_tile(coords,tile): # Replaces tile at the coordinates with the tile specified. It's so much easier, trust me.
    try:
        row = tilemap[coords[1]]
        row[coords[0]] = tile
    except:
        print(f"Error: Index out of range. Tried to set tile at {coords}")

def convert_to_tile_coords(coords): # basically converts normal coordinates to tile coordinates
    return math.floor(coords[0] / tile_size), math.floor(coords[1] / tile_size)

def generate_random_level(width,height): # Randomly generates a mess of random tiles, can be fun to mess on with
    global tilemap
    tilemap = []
    row = 0
    column = 0
    while column != height:
        data = []
        while row != width:
            row += 1
            data.append(random.choice(list(tiles.keys())))
        row = 0
        tilemap.append(data)
        column += 1

def create_level(width,height):
    global tilemap
    tilemap = []
    row = 0
    column = 0
    while column != height:
        data = []
        while row != width:
            row += 1
            data.append(0)
        row = 0
        tilemap.append(data)
        column += 1

def save_level(use_json=False):
    save_to = input('Enter level name to write to: ').lower()
    save_file = open(f'data/levels/{save_to}','wb')
    print("Saving...")
    save_data = {"tilemap":tilemap,"teleports":teleports,"objects":objects,"values":level_values}
    if use_json:
        json.dump(save_data,save_file)
    else:
        pickle.dump(save_data,save_file)
    save_file.close()
    print("Save complete.")

def load_level(name,starting_pos="16,16"):
    global tilemap, teleports, objects, images, level_values, music, bg_color
    if music:
        music.stop()
    images = {}
    save_file = open(f'data/levels/{name}','rb')
    saved_data = pickle.load(save_file)
    tilemap = saved_data["tilemap"]
    teleports = saved_data["teleports"]
    should_load_objects = True
    if debug:
        should_load_objects = bool("Y" in input("Load objects?").upper())
        print(should_load_objects)
    if should_load_objects:
        objects = saved_data["objects"]
    else:
        objects = [player_class()]
    level_values = saved_data["values"]
    bg_color = level_values.get("bg_color")
    if not bg_color:
        bg_color = "green"
    starting_pos = str.split(starting_pos,',')
    save_file.close()
    for obj in objects:
        obj.load_assets()
        '''if obj.class_type == "player":
            obj.x = starting_pos[0]
            obj.y = starting_pos[1]'''
    music = level_values.get("music")
    if music:
        if music != "":
            music = pygame.mixer.Sound(f'assets/audio/music/{music}')
            music.play(-1)

def refresh_tiles(): # Call this when resizing or something
    global draw_width, draw_height
    draw_width = math.ceil((screen_width / tile_size) + 1)
    draw_height = math.ceil((screen_height / tile_size) + 1)

def render():
    # Tile rendering
    # refresh_tiles()

    screen.fill(bg_color)

    draw_x = camera_x
    draw_y = camera_y
    starting_tile_x = math.floor(draw_x / tile_size)
    starting_tile_y = math.floor(draw_y / tile_size)

    draw_width = math.ceil((screen_width / tile_size) + 1)
    draw_height = math.ceil((screen_height / tile_size) + 1)

    tiles_on_screen = []

    for a in range(starting_tile_y,starting_tile_y + draw_height):
        for b in range(starting_tile_x,starting_tile_x + draw_width):
            tiles_on_screen.append({
                'type':get_tile((b,a)),
                'position':[(b*tile_size) - draw_x,(a*tile_size) - draw_y]
                })

    '''for row in tilemap:
        for tile in row:
            screen.blit(dict.get(tiles,tile),(draw_x,draw_y))
            draw_x += tile_size
        draw_y += tile_size
        draw_x = 0 - camera_x'''
    
    for tile in tiles_on_screen:
        try:
            screen.blit(pygame.transform.scale(dict.get(tiles,tile['type']),(tile_size,tile_size)),tile['position'])
        except:
            screen.blit(dict.get(tiles,6),tile['position'])
    
    # Draw ALL THE OBJECTS!!!!
    for obj in objects:
        obj.render()

    if show_dialog:
        half_width = screen_width / 2
        # having to constantly edit and test the game just for this was not fun =D
        screen.blit(pygame.transform.scale(dialog_box,(400,160)),(half_width - 200,screen_height - 160))
        render_text(dialog,smaller_font,(half_width - 184,screen_height - 144),16)

def load_obj(name,sprites): # Make sure 'sprites' is in the same order you want the ids to be in, ok?
    # To avoid confusion, an object is similar to a Scratch sprite. A sprite is the name of the photo used, similar to a Scratch costume.
    global objects
    objects[name] = {}
    loaded_sprites = []
    for sprite in sprites:
        loaded_sprites.append(pygame.image.load(f'assets/objects/{name}/{sprite}'))
    objects[name] = loaded_sprites

def draw_obj(name,sprite_num,position,offset=(0,0),flipped_x=False,flipped_y=False,scale=None,zoom=False): # Zoom decides whether the object will be drawn with the map scaling in mind, useless atm
    sprite_to_draw = objects.get(name)[sprite_num]
    if flipped_x:
        sprite_to_draw = pygame.transform.flip(sprite_to_draw,True,False)
    if flipped_y:
        sprite_to_draw = pygame.transform.flip(sprite_to_draw,False,True)
    if scale:
        sprite_to_draw = pygame.transform.scale(sprite_to_draw,(scale[0],scale[1]))
    else:
        scale = sprite_to_draw.get_size()
    screen.blit(sprite_to_draw,(((position[0] - offset[0]) - camera_x),((position[1] - offset[1]) - camera_y)))

def move_player(by):
    global player_x
    global player_y
    x = by[0]
    y = by[1]
    old_pos = (player_x,player_y)
    player_x += x
    player_y += y
    if check_collision((player_x,player_y)) or check_collision((player_x + 28,player_y)) or check_collision((player_x,player_y + 28)) or check_collision((player_x + 28,player_y + 28)):
        player_x = old_pos[0]
        player_y = old_pos[1]

def render_loading_screen(loading_photo,hint,progress=None,length=None,text_color="white"):
    screen.fill("black")
    if loading_photo:
        screen.blit(loading_photo,(0,0))
    loading_text = font.render('Loading...',False,text_color)
    loading_text_size = loading_text.get_size()
    if progress and length:
        progress = smaller_font.render(f"Progress: {math.ceil(progress / length * 100)}%",False,text_color)
    screen.blit(loading_text,(screen_width - loading_text_size[0],screen_height - loading_text_size[1]))
    hint = smaller_font.render(hint,False,text_color)
    screen.blit(hint,(0,0))
    if progress and length:
        screen.blit(progress,(0,480 - progress.get_size()[1]))
    handle_events()
    pygame.display.flip()

def get_loading_photo(name):
    loading_photo = pygame.image.load(f'assets/loading_screens/{name}')
    return pygame.transform.scale(loading_photo,(screen_width,screen_height))

def load_group_of_assets(table,loading_photo=None,text_color="white"):
    hint = random.choice(loading_hints)
    length = len(table["tiles"]) + len(table["data"])
    loaded = 0
    for tile in table["tiles"]:
        tiles[tile] = load_tile(dict.get(tile_addresses,tile))
        loaded += 1
        render_loading_screen(loading_photo,hint,loaded,length,text_color)
    for asset in table["data"]:
        if asset["type"] == "obj":
            load_obj(asset["id"],asset["sprites"])
        loaded += 1
        render_loading_screen(loading_photo,hint,loaded,length,text_color)

def begin_battle(battle_file):
    encounter_sound = pygame.mixer.Sound("assets/audio/other/encounter.wav")
    encounter_sound.play()
    i = 0
    black_screen.set_alpha(0)
    while i != 25:
        handle_events()
        i += 1
        render()
        black_screen.set_alpha(black_screen.get_alpha() + 10)
        screen.blit(black_screen,(0,0))
        pygame.display.flip()
        clock.tick(60)
    battle_file = open(f"data/battles/{battle_file}")
    battle_data = json.load(battle_file)
    battle_file.close()

def title_screen():
    global logo
    logo = pygame.image.load("assets/other/logo.png")
    in_title_screen = True
    title_image = pygame.image.load("assets/other/title.png")
    screen.fill("black")
    screen.blit(pygame.transform.scale(title_image,(screen_width,screen_height)),(0,0))
    screen.blit(logo,(440,320))
    while in_title_screen:
        handle_events()
        if single_keys["start"]:
            in_title_screen = False
        pygame.display.flip()
        clock.tick(60)

pygame.init()

debug = False

pg_logo = pygame.image.load("assets/other/pygame_powered.png")

clock = pygame.time.Clock()
screen = pygame.display.set_mode((screen_width,screen_height)) # Resolution: 480p 4:3
fullscreen = False
pygame.display.set_caption("Dragon Hunters")
pygame.display.set_icon(pygame.image.load('assets/objects/player/front.png'))

display_logo = True

# Powered by Pygame logo
if display_logo:
    screen.fill("white")
    print(640 - screen_width,480 - screen_height)
    screen.blit(pg_logo,((screen_width - 640) / 2,(screen_height - 480) / 2))
    frame = 0
    while frame != 120:
        handle_events()
        pressed_keys = pygame.key.get_pressed()
        if pressed_keys[pygame.K_q] and pressed_keys[pygame.K_e]:
            debug = True
        pygame.display.flip()
        clock.tick(60)
        frame += 1

running = True

bg_color = 'black'

camera_x = 0
camera_y = 0

player_x = 0
player_y = 0

selected_tile = 0

# Inital loading
load_group_of_assets({
    "tiles":tile_addresses.keys(),
    "data":[]
},get_loading_photo("dragon_hunters_artwork.png"),text_color="dark blue")

title_screen()

objects = [player_class()]
create_level(1000,1000) # Need a level to be in memory or else the game isn't... there?
load_level("a","100,100")

player_speed = 2

player_direction = 'front'

noclip = False

while running: # Main loop
    handle_events()

    black_screen = pygame.surface.Surface((screen_width,screen_height))
    black_screen.fill("black")

    level_width = len(tilemap)
    level_height = len(tilemap[0])

    # Actual game code
    pressed_keys = pygame.key.get_pressed()
    for obj in objects:
        obj.tick()
    if camera_x < 0:
        camera_x = 0
    if camera_y < 0:
        camera_y = 0
    if camera_x > (level_width * tile_size) - screen_width:
        camera_x = (level_width * tile_size) - screen_width
    if camera_y > (level_height * tile_size) - screen_height:
        camera_y = (level_height * tile_size) - screen_height
    if single_keys["start"]:
        music.stop()
        i = 0
        black_screen.set_alpha(0)
        while i != 20:
            handle_events()
            i += 1
            render()
            black_screen.set_alpha(black_screen.get_alpha() + 10)
            screen.blit(black_screen,(0,0))
            pygame.display.flip()
            clock.tick(60)
        pause_music = pygame.mixer.Sound("assets/audio/music/pause.wav")
        pause_music.play(-1)
        paused_text = font.render("PAUSED",False,"white")
        pause_options = ["Resume","Controls","Toggle debug","Widescreen (experimental)","4:3 (original)","README.txt","itch.io page","Discord server","Quit game"]
        selected_option = 0
        exit_pause = False
        frame_number = 0
        hint = random.choice(loading_hints)
        while not exit_pause:
            frame_number += 1
            if frame_number == 300:
                frame_number = 0
                hint = random.choice(loading_hints)
            handle_events()
            render()
            if single_keys["up"]:
                selected_option -= 1
                if selected_option == -1:
                    selected_option = len(pause_options) - 1
            elif single_keys["down"]:
                selected_option += 1
                if selected_option == len(pause_options):
                    selected_option = 0
            if single_keys["a"]:
                option_selected = pause_options[selected_option]
                if option_selected == "Resume":
                    exit_pause = True
                if option_selected == "README.txt":
                    readme_file = open("README.txt")
                    readme = readme_file.readlines()
                    readme_file.close()
                    scroll_x = 0
                    scroll_y = 0
                    while single_keys["b"] == False:
                        handle_events()
                        render()
                        screen.blit(black_screen,(0,0))
                        draw_y = 0
                        if active_keys["right"]:
                            scroll_x += 3
                        elif active_keys["left"]:
                            scroll_x -= 3
                            if scroll_x <= 0:
                                scroll_x = 0
                        if active_keys["down"]:
                            scroll_y += 3
                            text_height = (len(readme) * 16) - screen_height
                            if scroll_y >= text_height:
                                scroll_y = text_height
                        elif active_keys["up"]:
                            scroll_y -= 3
                            if scroll_y <= 0:
                                scroll_y = 0
                        for line in readme:
                            screen.blit(smaller_font.render(line,False,"white"),(0 - scroll_x,draw_y - scroll_y))
                            draw_y += 16
                        pygame.display.flip()
                        clock.tick(60)
                if option_selected == "itch.io page":
                    os.startfile("https://damon-m1.itch.io/dragon-hunters")
                if option_selected == "Discord server":
                    os.startfile("https://discord.gg/mCU5JjEMGv")
                if option_selected == "Quit game":
                    exit()
                if option_selected == "Toggle debug":
                    debug = not debug
                if option_selected == "Widescreen (experimental)":
                    if screen_width == 640:
                        screen_width = 640
                        while screen_width != 854:
                            pygame.display.set_caption("Woah! Check out this AMAZING window effect!!!")
                            screen_width += 1
                            pygame.display.set_mode((screen_width,480))
                            handle_events()
                            pygame.display.flip()
                            time.sleep(0.01)
                        pygame.display.set_caption("Dragon Hunters (widescreen)")
                if option_selected == "4:3 (original)":
                    if screen_width == 854:
                        screen_width = 854
                        while screen_width != 640:
                            pygame.display.set_caption("goodbye widescreen :(")
                            screen_width -= 1
                            pygame.display.set_mode((screen_width,480))
                            handle_events()
                            pygame.display.flip()
                            time.sleep(0.01)
                        pygame.display.set_caption("Dragon Hunters")
                if option_selected == "Controls":
                    in_controls = True
                    exit_controls = False
                    listening_key = None
                    skip_frame = 0
                    while not exit_controls:
                        for event in events:
                            if event.type == pygame.KEYDOWN:
                                if pygame.key.name(event.key) == "escape":
                                    exit_controls = True
                        render()
                        screen.blit(black_screen,(0,0))
                        screen.blit(font.render("Press any key to change",False,"white"),(0,0))
                        screen.blit(font.render("Press ESC to go back",False,"white"),(0,30))
                        draw_y = 90
                        i = 0
                        handle_events()
                        if skip_frame > 0:
                            skip_frame -= 1
                        if skip_frame == 0:
                            for control in controls["keyboard"]:
                                key_name = controls['keyboard'].get(control)
                                text_color = "white"
                                if single_keys[control]:
                                    listening_key = control
                                if listening_key == control:
                                    text_color = "yellow"
                                    keys = []
                                    for event in events:
                                        if event.type == pygame.KEYDOWN:
                                            keys.append(pygame.key.name(event.key))
                                            controls["keyboard"][control] = pygame.key.name(event.key)
                                            listening_key = None
                                            skip_frame = 2
                                screen.blit(font.render(f"{control}: {key_name}",False,text_color),(0,draw_y))
                                draw_y += 30
                            i += 1                           
                        pygame.display.flip()
                        clock.tick(60)
                    controls_file = open("save_data/controls.json","w")
                    json.dump(controls,controls_file)
                    controls_file.close()
                    in_controls = False
            screen.blit(pygame.transform.scale(black_screen,(screen_width,screen_height)),(0,0))
            screen.blit(paused_text,(0,0))
            logo_size = logo.get_size()
            screen.blit(logo,(screen_width - logo_size[0],(screen_height - 20) - logo_size[1]))
            hint_image = smaller_font.render(hint,False,"white")
            hint_size = hint_image.get_size()
            screen.blit(hint_image,(0,screen_height - hint_size[1]))
            ver_text = smaller_font.render(f"Version: {version}",False,"white")
            ver_text_size = ver_text.get_size()
            screen.blit(ver_text,(screen_width - ver_text_size[0],0))
            draw_y = 60
            i = 0
            for option in pause_options:
                if i == selected_option:
                    text_color = "yellow"
                else:
                    text_color = "white"
                screen.blit(font.render(option,False,text_color),(0,draw_y))
                draw_y += 30
                i += 1
            pygame.display.flip()
            clock.tick(60)
        pause_music.stop()
        music.play(-1)
    # Commands and stuff
    if debug:
        command = ""
        if pressed_keys[pygame.K_c]:
            try:
                command = input("Command: ").upper()
            except:
                command = ""
                screen.fill("black")
                screen.blit(font_manager.get_font("debug.ttf",12).render("Error occured while using command",False,"white"),(0,0))
                screen.blit(font_manager.get_font("debug.ttf",12).render("This may be due to no terminal existing",False,"white"),(0,12))
                frame = 0
                while frame != 120:
                    handle_events()
                    frame += 1
                    pygame.display.flip()
                    clock.tick(60)
        # Q and E keys change selected tile
        if pressed_keys[pygame.K_q]:
            if not selected_tile == 0:
                selected_tile -= 1
                print(f'{selected_tile}: {tile_addresses[selected_tile]}')
                time.sleep(0.25)
            else:
                print('Out of range!')
        elif pressed_keys[pygame.K_e]:
            if not selected_tile == len(tile_addresses) - 1:
                selected_tile += 1
                print(f'{selected_tile}: {tile_addresses[selected_tile]}')
                time.sleep(0.25)
            else:
                print('Out of range!')
        # For creating levels with custom dimensions
        if command == "NEW":
            level_width = int(input('Enter level width: '))
            level_height = int(input('Enter level height: '))
            create_level(level_width,level_height)
        # Teleport commands for editor
        if command == "NEW TP":
            coords = input("Enter the coords where the teleport should be: ")
            target_map = input("Enter the name of the map it should teleport you to: ")
            starting_pos = input("Enter the starting coords for after the teleport: ")
            teleports[coords] = {
                "target_map":target_map,
                "starting_pos":starting_pos
            }
        if command == "DELETE TP":
            teleports = {}
            print("Deleted teleports.")
        if command == "NOCLIP":
            noclip = not noclip
            print(f"Noclip set to {noclip}")
        if command == "NEW NPC":
            coords = input("Enter the coords where the NPC should be seperated by ,: ")
            coords = coords.split(",")
            x = int(coords[0])
            y = int(coords[1])
            dialog_name = None
            audio_name = None
            sprite = input("Sprite: ")
            if "Y" in input("Should this have dialog?").upper():
                dialog_name = input("Enter dialog name: ")
                objects.append(npc(x,y,[sprite],0,28,28,behaviour={"type":"idle","dialog":dialog_name}))
            else:
                objects.append(npc(x,y,[sprite],0,28,28))
        if command == "SET VALUE":
            value_to_set = input("Value name: ").lower()
            value_set_to = input("Set to: ")
            level_values[value_to_set] = value_set_to
        if command == "SAVE":
            screen.blit(working_text,(0,0))
            pygame.display.flip()
            if len(str(tilemap)) > 10000000:
                level_size_warning_answer = input('Warning: This level is HUGE! Are you sure you want to save? (Y/N)').upper()
                if level_size_warning_answer == 'Y':
                    print('Okay, but don\'t go blaming me when you have a 8GB level on your computer.')
                    save_level()
                elif level_size_warning_answer == 'N':
                    print('Better to not be risky.')
            else:
                save_level()
        if command == "LOAD":
            screen.blit(working_text,(0,0))
            pygame.display.flip()
            load_level(input('Enter level name to load from: ').lower())
        if command == "REMOVE OBJECTS":
            objects = []
            objects.append(player_class())
        if command == "CHANGE RESOLUTION":
            resolution_input = input("Enter the resolution to change to (format: 'x,y'): ")
            split_resolution = resolution_input.split(",")
            pygame.display.set_mode((int(split_resolution[0]),int(split_resolution[1])))
        # Mouse controls
        mouse_position = pygame.mouse.get_pos()
        mouse_position = list(mouse_position)
        mouse_position[0] += camera_x
        mouse_position[1] += camera_y
        mouse_position = tuple(mouse_position)
        tile_mouse_pos = convert_to_tile_coords(mouse_position)
        if debug:
            if pygame.mouse.get_pressed()[0]:
                # print(f'Tile {mouse_position} clicked')
                set_tile(tile_mouse_pos,selected_tile)
    # Rendering
    render()
    if debug:
        screen.blit(font.render(f'Camera Pos: {camera_x},{camera_y}',False,'white'),(0,0))
        screen.blit(font.render(f'Mouse Pos: {mouse_position[0]},{mouse_position[1]} ({tile_mouse_pos})',False,'white'),(0,30))
        screen.blit(font.render(f'Memory usage: {math.floor(Process().memory_info().rss / 1024 / 1024)}MB',False,'white'),(0,60))
    pygame.display.flip()
    clock.tick(60)