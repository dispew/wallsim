import os
import pygame
import pygame.gfxdraw
import csv
import pickle
import tkinter
from tkinter import filedialog
import Robot

# flags
no_show = False

# simulator
version = 1
intro = False
running = True
paused = False
message = ''
pygame.init()
pygame.display.set_caption('Wallsim')
clock = pygame.time.Clock()
emu_speed = 1
mouse_drag = False
mouse_cell = [-1, -1]

pygame.font.init()
font = pygame.font.SysFont('Tahoma', 18)
fontPause = pygame.font.Font('fnt/prstart.ttf', 40)
fontIntro = pygame.font.Font('fnt/prstart.ttf', 36)
fontLogo = pygame.font.Font('fnt/kid.ttf', 120)

os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (30, 50)
size = width, height = 1920, 1080
size_cell = 80

root = tkinter.Tk()
root.withdraw()

mapa = pygame.Surface(size)
mapa_color = pygame.Surface(size)
mapa_rect = mapa.get_rect()

ratio_x = int(width/size_cell)
ratio_y = int(height/size_cell)
mapa_struct = [[0 for x in range(ratio_x)] for y in range(ratio_y)]
walls_struct = [[0 for x in range(ratio_x * 2 - 1)] for y in range(ratio_y * 2 - 1)]

screen_info = pygame.display.Info()
screen_size = (int(screen_info.current_w * 0.9), int(screen_info.current_h * 0.9))

screen = pygame.display.set_mode(screen_size, pygame.DOUBLEBUF)
scene = pygame.Surface(size)

state = 0
state_names = ['Build', 'Navigate', 'Finish', '']

csvfile = None
writer = None
file_path = None

path_build = []
path_index = 0
wall_offsets = [(size_cell/4, -size_cell/4), (size_cell*3/4, size_cell/4), (size_cell/4, size_cell*3/4), (-size_cell/4, size_cell/4)]

# Robot
robot = Robot.Robot(width/2, height/2, 90.0, size)
# (o, no, n, ne, l, se, s, so)
maxRangeSensor = 100
robot.set_range_sensors([90.0, 45.0, 0.0, -45.0, -90.0, -135.0, -180.0, -225.0], maxRangeSensor)
reads = []

def generate_map():
    mapa.fill((255, 255, 255, 255))
    mapa_color.fill((255, 255, 255, 255))
    # Build
    # Floor
    for y in range(len(mapa_struct)):
        for x in range(len(mapa_struct[0])):
            if mapa_struct[y][x] == 0:
                pygame.gfxdraw.box(mapa, pygame.Rect(x * size_cell, y * size_cell, size_cell, size_cell), (0, 0, 0, 255))
                pygame.gfxdraw.box(mapa_color, pygame.Rect(x * size_cell, y * size_cell, size_cell, size_cell), (0, 0, 0, 255))
            if mapa_struct[y][x] == 1:
                pygame.gfxdraw.box(scene, pygame.Rect(x * size_cell, y * size_cell, size_cell, size_cell), (255, 255, 255, 255))
                pygame.gfxdraw.box(mapa_color, pygame.Rect(x * size_cell, y * size_cell, size_cell, size_cell), (0, 255, 0, 255))
            if mapa_struct[y][x] == 2:
                pygame.gfxdraw.box(scene, pygame.Rect(x * size_cell, y * size_cell, size_cell, size_cell), (255, 255, 255, 255))
                pygame.gfxdraw.box(mapa_color, pygame.Rect(x * size_cell, y * size_cell, size_cell, size_cell), (0, 0, 255, 255))
            # N
            if y - 1 < 0 or mapa_struct[y - 1][x] != mapa_struct[y][x]:
                pygame.gfxdraw.hline(mapa, x * size_cell, x * size_cell + size_cell, y * size_cell, (0, 0, 0, 255))
                pygame.gfxdraw.hline(mapa_color, x * size_cell, x * size_cell + size_cell, y * size_cell, (0, 0, 0, 255))
            # S
            if y + 1 >= ratio_y or mapa_struct[y + 1][x] != mapa_struct[y][x]:
                pygame.gfxdraw.hline(mapa, x * size_cell, x * size_cell + size_cell, y * size_cell + size_cell - 1, (0, 0, 0, 255))
                pygame.gfxdraw.hline(mapa_color, x * size_cell, x * size_cell + size_cell, y * size_cell + size_cell - 1, (0, 0, 0, 255))
            # L
            if x + 1 >= ratio_x or mapa_struct[y][x + 1] != mapa_struct[y][x]:
                pygame.gfxdraw.vline(mapa, x * size_cell + size_cell - 1, y * size_cell, y * size_cell + size_cell, (0, 0, 0, 255))
                pygame.gfxdraw.vline(mapa_color, x * size_cell + size_cell - 1, y * size_cell, y * size_cell + size_cell, (0, 0, 0, 255))
            # O
            if x - 1 < 0 or mapa_struct[y][x - 1] != mapa_struct[y][x]:
                pygame.gfxdraw.vline(mapa, x * size_cell, y * size_cell, y * size_cell + size_cell, (0, 0, 0, 255))
                pygame.gfxdraw.vline(mapa_color, x * size_cell, y * size_cell, y * size_cell + size_cell, (0, 0, 0, 255))

    # Walls
    for y in range(len(walls_struct)):
        for x in range(len(walls_struct[0])):
            # Horizontal
            if x % 2 == 0 and y % 2 == 1:
                # Door
                if walls_struct[y][x] == 1:
                    pygame.gfxdraw.box(mapa, pygame.Rect(x * size_cell/2, y * size_cell/2 + size_cell/2 - 1, size_cell, 2), (0, 0, 0, 255))
                    pygame.gfxdraw.box(mapa, pygame.Rect(x * size_cell/2 + size_cell/4, y * size_cell/2 + size_cell*7/16, size_cell/2, size_cell/8), (255, 255, 255, 255))
                    pygame.gfxdraw.box(mapa_color, pygame.Rect(x * size_cell/2, y * size_cell/2 + size_cell/2 - 1, size_cell, 2), (0, 0, 0, 255))
                    pygame.gfxdraw.box(mapa_color, pygame.Rect(x * size_cell/2 + size_cell/4, y * size_cell/2 + size_cell*7/16, size_cell/2, size_cell/8), (255, 0, 0, 255))
                # Wall
                if walls_struct[y][x] == 2:
                    pygame.gfxdraw.box(mapa, pygame.Rect(x * size_cell/2, y * size_cell/2 + size_cell/2 - 1, size_cell, 2), (0, 0, 0, 255))
                    pygame.gfxdraw.box(mapa_color, pygame.Rect(x * size_cell/2, y * size_cell/2 + size_cell/2 - 1, size_cell, 2), (0, 0, 0, 255))
                # Goal
                if walls_struct[y][x] == 3:
                    pygame.gfxdraw.box(mapa, pygame.Rect(x * size_cell/2 + 1, y * size_cell/2 + size_cell * 7/16, size_cell - 2, size_cell/8 + 1), (255, 201, 14, 128))
                    pygame.gfxdraw.box(mapa_color, pygame.Rect(x * size_cell/2 + 1, y * size_cell/2 + size_cell * 7/16, size_cell - 2, size_cell/8 + 1), (255, 255, 0, 255))
            # Vertical
            if x % 2 == 1 and y % 2 == 0:
                # Door
                if walls_struct[y][x] == 1:
                    pygame.gfxdraw.box(mapa, pygame.Rect(x * size_cell/2 + size_cell/2 - 1, y * size_cell/2, 2, size_cell), (0, 0, 0, 255))
                    pygame.gfxdraw.box(mapa, pygame.Rect(x * size_cell/2 + size_cell*7/16, y * size_cell/2 + size_cell/4, size_cell/8, size_cell/2), (255, 255, 255, 255))
                    pygame.gfxdraw.box(mapa_color, pygame.Rect(x * size_cell/2 + size_cell/2 - 1, y * size_cell/2, 2, size_cell), (0, 0, 0, 255))
                    pygame.gfxdraw.box(mapa_color, pygame.Rect(x * size_cell/2 + size_cell*7/16, y * size_cell/2 + size_cell/4, size_cell/8, size_cell/2), (255, 0, 0, 255))
                # Wall
                if walls_struct[y][x] == 2:
                    pygame.gfxdraw.box(mapa, pygame.Rect(x * size_cell/2 + size_cell/2 - 1, y * size_cell/2, 2, size_cell), (0, 0, 0, 255))
                    pygame.gfxdraw.box(mapa_color, pygame.Rect(x * size_cell/2 + size_cell/2 - 1, y * size_cell/2, 2, size_cell), (0, 0, 0, 255))
                # Goal
                if walls_struct[y][x] == 3:
                    pygame.gfxdraw.box(mapa, pygame.Rect(x * size_cell/2 + size_cell * 7/16, y * size_cell/2 + 1, size_cell/8 + 1, size_cell - 2), (255, 201, 14, 128))
                    pygame.gfxdraw.box(mapa_color, pygame.Rect(x * size_cell/2 + size_cell * 7/16, y * size_cell/2 + 1, size_cell/8 + 1, size_cell - 2), (255, 255, 0, 255))


# Intro
scene.fill((0, 0, 0, 255))
scene.blit(fontIntro.render('Dispew\'s Tech', False, (255, 255, 255)), (width / 2 - width / 8, height / 2 - height / 7))
scene.blit(fontLogo.render('PEW ROBOTICS SIMULATOR', False, (200, 200, 200)), (width / 2 - int(width / 3.5), height / 2))
screen.blit(pygame.transform.smoothscale(scene, screen_size), (0, 0))
pygame.display.flip()
pygame.time.wait(1000)

while running:

    events = pygame.event.get()
    for event in events:
        # GUI
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            paused = not paused
            if paused:
                pygame.gfxdraw.box(scene, pygame.Rect(0, 0, width, height), (0, 0, 0, 50))
                scene.blit(fontPause.render('Paused', False, (0, 0, 0)), (width / 2 - width / 10 + 5, height - height / 10 + 5))
                scene.blit(fontPause.render('Paused', False, (255, 255, 255)), (width / 2 - width / 10, height - height / 10))
                screen.blit(pygame.transform.smoothscale(scene, screen_size), (0, 0))
                pygame.display.flip()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_u:
            if file_path != '':
                filename, file_extension = os.path.splitext(os.path.basename(file_path))
                pygame.image.save(mapa_color, './out/image_' + filename + '.png')
                message = 'Image saved'
            else:
                message = 'No Map Loaded or Saved'
        if event.type == pygame.KEYDOWN and event.key == pygame.K_o:
            file_path = filedialog.asksaveasfilename(defaultextension='.map', filetypes=[('Map File', '.map')], initialdir='./maps/')
            if file_path != '':
                with open(file_path, 'wb') as fp:
                    save_state = [version, mapa_struct, walls_struct, robot.get_position()]
                    pickle.dump(save_state, fp)
                    message = 'Saved'
                    screen = pygame.display.set_mode(screen_size)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_i:
            file_path = filedialog.askopenfilename(defaultextension='.map', filetypes=[('Map File', '.map')], initialdir='./maps/')
            if file_path != '':
                with open(file_path, 'rb') as fp:
                    save_state = pickle.load(fp)
                    if save_state[0] == version:
                        [mapa_struct, walls_struct, rpos] = save_state[1:]
                        robot.set_position(rpos)
                        path_build = []
                        path_index = 0
                        generate_map()
                        message = 'Loaded'
                        screen = pygame.display.set_mode(screen_size)
                    else:
                        message = 'Map File Version Error, build a new Map'

        if event.type == pygame.KEYDOWN and event.key == pygame.K_l:
            path_build = []
            path_index = 0

        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            robot.reset_position()
            path_index = 0

        # Emu Speed
        if event.type == pygame.KEYDOWN and event.key == pygame.K_COMMA:
            emu_speed *= 0.5

        if event.type == pygame.KEYDOWN and event.key == pygame.K_PERIOD:
            emu_speed *= 2

        if event.type == pygame.KEYDOWN and event.key == pygame.K_n:
            no_show = not no_show

        # States
        if event.type == pygame.KEYDOWN and event.key == pygame.K_1:
            state = 0
            path_build = []
            path_index = 0
        if event.type == pygame.KEYDOWN and event.key == pygame.K_2:
            if file_path is not None and file_path != '':
                state = 1
                generate_map()
                filename, file_extension = os.path.splitext(os.path.basename(file_path))
                csvfile = open('./out/output_' + filename + '.csv', 'w')
                writer = csv.writer(csvfile, delimiter=',')
                writer.writerow(['s_o', 's_no', 's_n', 's_ne', 's_l', 's_se', 's_s', 's_so', 's_top', 'x', 'y', 'ori', 'cur', 'class'])
            else:
                message = 'No MAP loaded. Load a MAP file or save the current MAP'

    # Build
    if state == 0:
        for event in events:
            mouse_ratio = (float(width)/float(screen_size[0]))
            if event.type == pygame.MOUSEBUTTONUP:
                message = ''
            if event.type == pygame.MOUSEMOTION:
                if mouse_drag:
                    mx = int((event.pos[0] * mouse_ratio) / size_cell)
                    my = int((event.pos[1] * mouse_ratio) / size_cell)
                    if mouse_cell[0] != mx or mouse_cell[1] != my:
                        if mx < len(mapa_struct[0]) and my < len(mapa_struct):
                            mapa_struct[my][mx] = (mapa_struct[my][mx] + 1) % 3
                            mouse_cell = [mx, my]
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_drag = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mouse_drag = False
                if mouse_cell[0] == -1 and mouse_cell[1] == -1:
                    mx = int((event.pos[0] * mouse_ratio) / size_cell)
                    my = int((event.pos[1] * mouse_ratio) / size_cell)
                    if mx < len(mapa_struct[0]) and my < len(mapa_struct):
                        mapa_struct[my][mx] = (mapa_struct[my][mx] + 1) % 3
                else:
                    mouse_cell = [-1, -1]
            if event.type == pygame.MOUSEBUTTONUP and event.button == 3:
                ix = int(((event.pos[0] * mouse_ratio) / (size_cell / 2.0)) + .5) - 1
                iy = int(((event.pos[1] * mouse_ratio) / (size_cell / 2.0)) + .5) - 1

                if ix < len(walls_struct[0]) and iy < len(walls_struct):
                    if ix % 2 == 0 and iy % 2 == 1 or ix % 2 == 1 and iy % 2 == 0:
                        walls_struct[iy][ix] = (walls_struct[iy][ix] + 1) % 4

            if event.type == pygame.MOUSEBUTTONUP and event.button == 2:
                robot.robot_init = [event.pos[0] * mouse_ratio, event.pos[1] * mouse_ratio, 90.0]
                robot.reset_position()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_z:
                for y in range(len(mapa_struct)):
                    for x in range(len(mapa_struct[0])):
                        mapa_struct[y][x] = 0
                for y in range(len(walls_struct)):
                    for x in range(len(walls_struct[0])):
                        walls_struct[y][x] = 0

            if event.type == pygame.KEYDOWN and event.key == pygame.K_x:
                for y in range(len(mapa_struct)):
                    for x in range(len(mapa_struct[0])):
                        mapa_struct[y][x] = 1
                for y in range(len(walls_struct)):
                    for x in range(len(walls_struct[0])):
                        walls_struct[y][x] = 0

            if event.type == pygame.KEYDOWN and event.key == pygame.K_c:
                for y in range(len(mapa_struct)):
                    for x in range(len(mapa_struct[0])):
                        mapa_struct[y][x] = 2
                for y in range(len(walls_struct)):
                    for x in range(len(walls_struct[0])):
                        walls_struct[y][x] = 0

            if event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
                robot.robot_init[2] += 45.0
                if robot.get_position() == robot.robot_init:
                    robot.reset_position()
                else:
                    robot.theta = robot.robot_init[2]
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
                robot.robot_init[2] -= 45.0
                if robot.get_position() == robot.robot_init:
                    robot.reset_position()
                else:
                    robot.theta = robot.robot_init[2]

    # Paused ?
    if paused:
        continue

    # Movement
    if state == 1:
        # Measures (sl, slf, sf, sfr, sr, sb), st, x, y, ori, loc, class
        reads = robot.sense(mapa, mapa_color)

        velocities = robot.think(reads)
        robot.move(velocities[0], velocities[1], mapa)

        # Goal?
        if robot.at_goal(mapa_color):
            csvfile.close()
            state = 2
            no_show = False

    ###########
    # Drawing #
    ###########

    # Clear
    scene.fill((255, 255, 255, 255))

    # Build
    if state == 0:
        # Floor
        for y in range(len(mapa_struct)):
            for x in range(len(mapa_struct[0])):
                if mapa_struct[y][x] == 0:
                    pygame.gfxdraw.box(scene, pygame.Rect(x * size_cell, y * size_cell, size_cell + 1, size_cell + 1), (225, 225, 225, 255))
                    pygame.gfxdraw.rectangle(scene, pygame.Rect(x * size_cell, y * size_cell, size_cell + 1, size_cell + 1), (50, 50, 50, 255))
                if mapa_struct[y][x] == 1:
                    pygame.gfxdraw.box(scene, pygame.Rect(x * size_cell, y * size_cell, size_cell + 1, size_cell + 1), (176, 224, 230, 255))
                    pygame.gfxdraw.rectangle(scene, pygame.Rect(x * size_cell, y * size_cell, size_cell + 1, size_cell + 1), (50, 50, 50, 255))
                if mapa_struct[y][x] == 2:
                    pygame.gfxdraw.box(scene, pygame.Rect(x * size_cell, y * size_cell, size_cell + 1, size_cell + 1), (230, 230, 250, 255))
                    pygame.gfxdraw.rectangle(scene, pygame.Rect(x * size_cell, y * size_cell, size_cell + 1, size_cell + 1), (50, 50, 50, 255))
        # Walls
        for y in range(len(walls_struct)):
            for x in range(len(walls_struct[0])):
                if x % 2 == 0 and y % 2 == 1:
                    if walls_struct[y][x] == 0:
                        pygame.gfxdraw.rectangle(scene, pygame.Rect(x * size_cell / 2 + size_cell / 4, y * size_cell / 2 + size_cell * 7 / 16, size_cell / 2 + 1, size_cell / 8 + 1), (250, 50, 50, 255))
                    if walls_struct[y][x] == 1:
                        pygame.gfxdraw.box(scene, pygame.Rect(x * size_cell / 2 + size_cell / 4, y * size_cell / 2 + size_cell * 7 / 16, size_cell / 2 + 1, size_cell / 8 + 1), (150, 0, 0, 255))
                        pygame.gfxdraw.rectangle(scene, pygame.Rect(x * size_cell / 2 + size_cell / 4, y * size_cell / 2 + size_cell * 7 / 16, size_cell / 2 + 1, size_cell / 8 + 1), (80, 0, 0, 255))
                    if walls_struct[y][x] == 2:
                        pygame.gfxdraw.box(scene, pygame.Rect(x * size_cell / 2 + size_cell / 4, y * size_cell / 2 + size_cell * 7 / 16, size_cell / 2 + 1, size_cell / 8 + 1), (20, 20, 20, 255))
                    if walls_struct[y][x] == 3:
                        pygame.gfxdraw.box(scene, pygame.Rect(x * size_cell / 2 + 1, y * size_cell / 2 + size_cell * 7 / 16, size_cell - 1, size_cell / 8 + 1), (255, 201, 14, 255))
                if x % 2 == 1 and y % 2 == 0:
                    if walls_struct[y][x] == 0:
                        pygame.gfxdraw.rectangle(scene, pygame.Rect(x * size_cell / 2 + size_cell * 7 / 16, y * size_cell / 2 + size_cell / 4, size_cell / 8 + 1, size_cell / 2 + 1), (250, 50, 50, 255))
                    if walls_struct[y][x] == 1:
                        pygame.gfxdraw.box(scene, pygame.Rect(x * size_cell / 2 + size_cell * 7 / 16, y * size_cell / 2 + size_cell / 4, size_cell / 8 + 1, size_cell / 2 + 1), (150, 0, 0, 255))
                        pygame.gfxdraw.rectangle(scene, pygame.Rect(x * size_cell / 2 + size_cell * 7 / 16, y * size_cell / 2 + size_cell / 4, size_cell / 8 + 1, size_cell / 2 + 1), (80, 0, 0, 255))
                    if walls_struct[y][x] == 2:
                        pygame.gfxdraw.box(scene, pygame.Rect(x * size_cell / 2 + size_cell * 7 / 16, y * size_cell / 2 + size_cell / 4, size_cell / 8 + 1, size_cell / 2 + 1), (20, 20, 20, 255))
                    if walls_struct[y][x] == 3:
                        pygame.gfxdraw.box(scene, pygame.Rect(x * size_cell / 2 + size_cell * 7 / 16, y * size_cell / 2 + 1, size_cell / 8 + 1, size_cell - 1), (255, 201, 14, 255))

    ticks = no_show and pygame.time.get_ticks() % 1000 == 0

    # Navigate Map
    if state == 1 or state == 2:

        # Path
        path_build.append(robot.get_position())
        if not csvfile.closed:
            writer.writerow(reads)

        if (not no_show) or ticks:
            # Map
            scene.blit(mapa, mapa_rect)

            for pt in range(len(path_build) - 1):
                pygame.gfxdraw.pixel(scene, int(path_build[pt][0]), int(path_build[pt][1]), (128, 128, 128, 255))

    clock.tick()
    fps = clock.get_fps()
    scene.blit(font.render('FPS %d | EMUSPD %.3f ' % (fps, emu_speed), False, (0, 0, 0)), (width - 220, height - 30))

    if (not no_show) or ticks:
        # Robot
        robot.draw(scene)

        # Sim GUI
        text = state_names[state]
        if len(message) > 0:
            text += ' | ' + message
        if len(reads) > 0:
            text += ' | ' + 'Dist. Sensor = Esq: %.1f Fre: %.1f Dir: %.1f' % (reads[0], reads[2], reads[4])

        scene.blit(font.render(text, False, (255, 0, 0)), (20, height - 30))

        screen.blit(pygame.transform.smoothscale(scene, screen_size), (0, 0))
        pygame.display.flip()

    if not no_show:
        pygame.time.wait(int(10 * emu_speed))

pygame.display.quit()
