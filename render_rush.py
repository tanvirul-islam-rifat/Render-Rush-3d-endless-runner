# ============================================================
#  Render Rush: 3D Endless Escape
#  A 3D OpenGL endless-runner demonstrating perspective
#  projection, dual camera systems (third-person / first-person
#  with camera shake), procedural world generation, composite
#  character rigs with running/jumping/sliding animation, a
#  look-ahead enemy AI, and a timed input-combo scoring system.
#
#  Course  : CSE423 — Computer Graphics, Section 24, Group 8
#  Authors : Md. Tanvirul Islam Rifat
#            Fahimur Rahman
#            Istiak Al Imran
#  BRAC University
# ============================================================
#
#  Controls:
#    A / D          — switch one lane left / right
#    SPACE          — jump over obstacles (toggles speed boost
#                      instead, while riding the hoverboard)
#    S              — slide under obstacles (also usable on
#                      the hoverboard)
#    F              — toggle first-person / third-person camera
#    C              — mount / dismount the hoverboard
#    LEFT / RIGHT   — pan the third-person camera horizontally
#    UP / DOWN      — pan the third-person camera vertically
#    R              — restart the game
#
#  Scoring Combo:
#    Press JUMP -> SWITCH LANE -> SLIDE within a few seconds of
#    each other to trigger a temporary 5x score multiplier.
# ============================================================

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import time as t_lib
import random as r_lib
import math as m_lib

# GLOBAL VARIABLES & GAME STATE
# ==========================================
is_game_over = False 
first_person_active = False
camera_shake_offset = 0.0
cam_fov = 115.0
highway_offset = 0.0

# Lane X-coordinates.
X_POS_LANES = [-320.0, 0.0, 320.0]
TOTAL_LANES = len(X_POS_LANES)

# ENTITY DICTIONARIES (PLAYER & ENEMY)
hero_stats = {
    "lane": 1,           
    "x": X_POS_LANES[1],
    "y": 2000.0,          
    "z": 40.0,         
    "width": 50.0,
    "height": 50.0
}

bot_jumping = False
bot_jump_vel = 0.0
bot_sliding = False
bot_slide_timer = 0.0
bot_decision_cooldown = 0.0
bot_is_active = False
bot_active_timer = 0.0
BOT_MAX_DURATION = 10.0

chaser_ai = {
    "x": 0.0,
    "y": 0.0,
    "z": 40.0
}

# The camera position tracks behind the player
cam_position = (0, hero_stats["y"] + 400, 500)
blockers = []

# Mechanics variables
run_speed = 450.0    
total_dist = 0.0
current_score = 0
player_lives = 3

# Spawning variables
item_spawn_rate = 0.8 
previous_spawn_time = 0.0
previous_frame_time = t_lib.time()

# Physics variables for Jumping
jumping_state = False
vel_jump = 0.0
WORLD_GRAVITY = -1050.0   
JUMP_POWER = 520.0  
BASE_Z_LEVEL = 40.0     

# Physics variables for Sliding
sliding_state = False
slide_max_time = 0.55   
current_slide_time = 0.0
HEIGHT_SLIDE = 25.0    
HEIGHT_NORMAL = 50.0
Z_SLIDE_LEVEL = -25.0      

# Hoverboard variables
board_active = False
board_elevation = 80.0  
board_tilt_angle = 0.0     
board_bob_anim = 0.0      
BOARD_BOB_RATE = 4.0
BOARD_TILT_RATE = 3.0
board_speed_boost = False  

# Spawning ranges
Y_SPAWN_DIST = hero_stats["y"] - 1800   
Y_DESPAWN_DIST = hero_stats["y"] + 1000  

# Collision bounding boxes
Y_HITBOX = 30.0
X_HITBOX = 40.0

# Combo variables
input_combo_step = 0
combo_init_time = 0.0 
COMBO_TIME_LIMIT = 3

multiplier_active = False
multiplier_start = 0.0
MULTIPLIER_LASTS = 10.0
score_multi_value = 5


# UI RENDERING FUNCTION
# ==========================================
def display_string(x_coord, y_coord, text_str, font_style=GLUT_BITMAP_9_BY_15):
    glRasterPos2f(x_coord, y_coord)
    for char in text_str:
        glutBitmapCharacter(font_style, ord(char))

# OBSTACLE RENDERING
# ==========================================
def render_blocker(obs_data):
    glPushMatrix()
    glTranslatef(obs_data["x"], obs_data["y"], obs_data["z"])
    glColor3f(1.0, 0.3, 0.0) 

    height_pillar = 120
    thick_pillar = 12

    width_lane = X_POS_LANES[1] - X_POS_LANES[0]
    width_gap = width_lane * 0.8   

    # Left pillar
    glPushMatrix()
    glTranslatef(-width_gap * 0.5, 0, height_pillar * 0.5)
    glScalef(thick_pillar, thick_pillar, height_pillar)
    glutSolidCube(1)
    glPopMatrix()

    # Right pillar
    glPushMatrix()
    glTranslatef(width_gap * 0.5, 0, height_pillar * 0.5)
    glScalef(thick_pillar, thick_pillar, height_pillar)
    glutSolidCube(1)
    glPopMatrix()

    # Top beam
    glPushMatrix()
    glTranslatef(0, 0, height_pillar)
    glScalef(width_gap + thick_pillar, thick_pillar, thick_pillar)
    glutSolidCube(1)
    glPopMatrix()

    glPopMatrix()

# ROAD MARKER RENDERING
# ==========================================
def render_lane_markers(x_val, y_begin, y_finish, line_w=4, dash_len=150, empty_gap=120, rgb=(1,1,1), is_vert=True, scroll_off=0):
    glColor3f(*rgb)
    full_pattern = dash_len + empty_gap
    offset_phase = scroll_off % full_pattern
    current_pos = y_begin - (y_begin % full_pattern) - full_pattern

    while current_pos < y_finish + full_pattern:
        glBegin(GL_QUADS)
        if is_vert:
            glVertex3f(x_val - line_w, current_pos + offset_phase, 2)
            glVertex3f(x_val + line_w, current_pos + offset_phase, 2)
            glVertex3f(x_val + line_w, current_pos + offset_phase + dash_len, 2)
            glVertex3f(x_val - line_w, current_pos + offset_phase + dash_len, 2)
        else:
            glVertex3f(current_pos + offset_phase, x_val - line_w, 2)
            glVertex3f(current_pos + offset_phase + dash_len, x_val - line_w, 2)
            glVertex3f(current_pos + offset_phase + dash_len, x_val + line_w, 2)
            glVertex3f(current_pos + offset_phase, x_val + line_w, 2)
        glEnd()
        current_pos += full_pattern

# ENVIRONMENT RENDERING (ROAD)
# ==========================================
def render_highway():
    single_lane_w = 320
    full_road_w = single_lane_w * 3
    block_length = 20000

    dist_behind = 3000
    dist_ahead = 4500

    cam_y_pos = cam_position[1]  
    start_y = cam_y_pos - dist_behind  
    end_y   = cam_y_pos + dist_ahead  

    scroll_shift = -(highway_offset % block_length)
    y_render = start_y + scroll_shift
    
    glColor3f(0.05, 0.0, 0.15)  
    while y_render < end_y:
        glBegin(GL_QUADS)
        glVertex3f(-full_road_w * 0.5, y_render, 1)
        glVertex3f(full_road_w * 0.5, y_render, 1)
        glVertex3f(full_road_w * 0.5, y_render + block_length, 1)
        glVertex3f(-full_road_w * 0.5, y_render + block_length, 1)
        glEnd()
        y_render += block_length

    lane_divs = [-single_lane_w * 0.5, single_lane_w * 0.5]
    for div_x in lane_divs:
        render_lane_markers(div_x, start_y, end_y, line_w=4, dash_len=150, empty_gap=120, rgb=(0.0, 1.0, 0.8), scroll_off=highway_offset)

    road_edges = [-full_road_w * 0.5, full_road_w * 0.5]
    for edge in road_edges:
        render_lane_markers(edge, start_y, end_y, line_w=3, dash_len=150, empty_gap=120, rgb=(1,1,1), scroll_off=highway_offset)

token_spin = 0.0

# COIN RENDERING
# ==========================================
def render_token(coin_obj):
    global token_spin

    x_c, y_c, z_c = coin_obj["x"], coin_obj["y"], coin_obj["z"]
    rad = coin_obj["size"] * 0.5
    thick = coin_obj["size"] * 0.2  
    poly_sides = 32  

    glPushMatrix()
    glTranslatef(x_c, y_c, z_c + thick + 10)
    glRotatef(90, 1, 0, 0)  
    glRotatef(token_spin, 0, 1, 0)  

    glColor3f(0.9, 0.9, 1.0)  

    # Edge of the coin
    glBegin(GL_QUADS)
    for i in range(poly_sides):
        angle1 = (2 * m_lib.pi * i) / poly_sides
        angle2 = (2 * m_lib.pi * (i + 1)) / poly_sides
        x1, y1 = rad * m_lib.cos(angle1), rad * m_lib.sin(angle1)
        x2, y2 = rad * m_lib.cos(angle2), rad * m_lib.sin(angle2)
        glVertex3f(x1, y1, -thick * 0.5)
        glVertex3f(x2, y2, -thick * 0.5)
        glVertex3f(x2, y2, thick * 0.5)
        glVertex3f(x1, y1, thick * 0.5)
    glEnd()

    # Front face
    for i in range(poly_sides):
        angle1 = (2 * m_lib.pi * i) / poly_sides
        angle2 = (2 * m_lib.pi * (i + 1)) / poly_sides
        x1, y1 = rad * m_lib.cos(angle1), rad * m_lib.sin(angle1)
        x2, y2 = rad * m_lib.cos(angle2), rad * m_lib.sin(angle2)
        glBegin(GL_TRIANGLES)
        glVertex3f(0, 0, thick * 0.5)  
        glVertex3f(x1, y1, thick * 0.5)
        glVertex3f(x2, y2, thick * 0.5)
        glEnd()

    # Back face
    for i in range(poly_sides):
        angle1 = (2 * m_lib.pi * i) / poly_sides
        angle2 = (2 * m_lib.pi * (i + 1)) / poly_sides
        x1, y1 = rad * m_lib.cos(angle1), rad * m_lib.sin(angle1)
        x2, y2 = rad * m_lib.cos(angle2), rad * m_lib.sin(angle2)
        glBegin(GL_TRIANGLES)
        glVertex3f(0, 0, -thick * 0.5)  
        glVertex3f(x2, y2, -thick * 0.5)
        glVertex3f(x1, y1, -thick * 0.5)
        glEnd()

    glPopMatrix()


# SPAWNING LOGIC (OBSTACLES, COINS, MAGNETS)
# ==========================================
def generate_blocker():
    chosen_lane = r_lib.randint(0, TOTAL_LANES-1)
    new_obs = {
        "lane": chosen_lane,
        "x": X_POS_LANES[chosen_lane],
        "y": Y_SPAWN_DIST - r_lib.uniform(0.0, 300.0),
        "z": 1.0,   
        "size": 1.0 
    }
    blockers.append(new_obs)

tokens = []   
total_tokens_collected = 0  
SIZE_TOKEN = 70.0

def generate_token():
    chosen_lane = r_lib.randint(0, TOTAL_LANES - 1)
    new_coin = {
        "lane": chosen_lane,
        "x": X_POS_LANES[chosen_lane],
        "y": Y_SPAWN_DIST - r_lib.uniform(0.0, 300.0),
        "z": 20.0,   
        "size": SIZE_TOKEN
    }
    tokens.append(new_coin)

attractors = []   
SIZE_ATTRACTOR = 80.0
total_attractors = 0
attractor_angle = 0.0

# Magnet power-up state: once picked up, "attractor_on" stays True for
# DURATION_ATTRACT seconds. While active, every coin within RANGE_ATTRACT
# units of the player is pulled toward them each frame (see process_game_state).
attractor_on = False
attractor_timer = 0.0
DURATION_ATTRACT = 5.0   
RANGE_ATTRACT = 800.0    

def generate_attractor():
    chosen_lane = r_lib.randint(0, TOTAL_LANES - 1)
    loc_y = Y_SPAWN_DIST - r_lib.uniform(0.0, 300.0)
    
    valid_spawn = True
    for c in tokens:
        if c["lane"] == chosen_lane and abs(c["y"] - loc_y) < 150:  
            valid_spawn = False 
            break
    
    if valid_spawn:
        new_mag = {
            "lane": chosen_lane,
            "x": X_POS_LANES[chosen_lane],
            "y": loc_y,
            "z": 50,
            "collision_z": -15.0,
            "size": SIZE_ATTRACTOR
        }
        attractors.append(new_mag)

# MAGNET RENDERING
# ==========================================
def render_attractor(mag_obj):
    global attractor_angle
    mx, my, mz, msize = mag_obj["x"], mag_obj["y"], mag_obj["z"], mag_obj["size"]
    
    glPushMatrix()
    glTranslatef(mx, my, mz + msize * 0.5)

    height_arm = msize
    glTranslatef(0, 0, -height_arm * 0.5)
    glRotatef(-30, 0, 1, 0) 
    glRotatef(attractor_angle, 1, 0, 1)
    
    width_arm = msize * 0.25
    space_gap = msize * 0.5

    glColor3f(1.0, 0.0, 1.0)  

    glPushMatrix()
    glTranslatef(-space_gap * 0.5, 0, 0)
    glScalef(width_arm, 20, height_arm)
    glutSolidCube(1)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(space_gap * 0.5, 0, 0)
    glScalef(width_arm, 20, height_arm)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.8, 0.8, 0.8)
    glPushMatrix()
    glTranslatef(0, 0, -height_arm * 0.5)
    glScalef(space_gap + width_arm, 20, width_arm)
    glutSolidCube(1)
    glPopMatrix()

    for side in [-1, 1]:
        glPushMatrix()
        glTranslatef(side * space_gap * 0.5, 0, -height_arm * 0.5 + 5)
        glScalef(width_arm, 20, width_arm)
        glutSolidCube(1)
        glPopMatrix()

    glPopMatrix()


# USER INPUT HANDLING
# ==========================================
# Combo system overview:
#   input_combo_step tracks progress through the JUMP -> SWITCH LANE -> SLIDE
#   sequence (steps 0 -> 1 -> 2). Each step must occur within COMBO_TIME_LIMIT
#   seconds of the previous one (checked against combo_init_time), otherwise
#   the sequence resets to step 0. Completing all three steps in time sets
#   multiplier_active = True, giving a temporary score_multi_value (5x) boost
#   to the score for MULTIPLIER_LASTS seconds.
def key_handler(key, x, y):
    global hero_stats, blockers, total_dist, current_score, player_lives, run_speed, highway_offset, cam_position, total_tokens_collected
    global jumping_state, vel_jump, sliding_state, current_slide_time, slide_max_time
    global first_person_active, board_active, board_elevation, board_speed_boost, bot_is_active
    global bot_active_timer, bot_jumping, bot_jump_vel, bot_sliding, bot_slide_timer, bot_decision_cooldown, chaser_ai
    global attractor_angle, total_attractors, attractor_on, attractor_timer
    global board_tilt_angle, board_bob_anim, previous_spawn_time, is_game_over
    global input_combo_step, combo_init_time, multiplier_active, multiplier_start, COMBO_TIME_LIMIT, MULTIPLIER_LASTS

    # Reset combo if wrong key pressed
    if key in [b'a', b'A', b'd', b'D']:
        if input_combo_step != 1:
            input_combo_step = 0
            combo_init_time = 0.0
    elif key in [b's', b'S']:
        if input_combo_step != 2:
            input_combo_step = 0
            combo_init_time = 0.0
    else:
        input_combo_step = 0
        combo_init_time = 0.0

    if key in [b'a', b'A']:
        curr_t = t_lib.time()
        if hero_stats["lane"] < TOTAL_LANES - 1:
            hero_stats["lane"] += 1
            hero_stats["x"] = X_POS_LANES[hero_stats["lane"]]

            if input_combo_step == 1 and combo_init_time != 0.0 and (curr_t - combo_init_time) <= COMBO_TIME_LIMIT:
                input_combo_step = 2
            else:
                input_combo_step = 0
                combo_init_time = 0.0

    elif key in [b'd', b'D']:
        curr_t = t_lib.time()
        if hero_stats["lane"] > 0:
            hero_stats["lane"] -= 1
            hero_stats["x"] = X_POS_LANES[hero_stats["lane"]]

            if (input_combo_step == 1) and (combo_init_time != 0.0) and ((curr_t - combo_init_time) <= COMBO_TIME_LIMIT):
                input_combo_step = 2
            else:
                input_combo_step = 0
                combo_init_time = 0.0

    elif key in [b' ', b'SPACE']:
        if board_active:
            board_speed_boost = not board_speed_boost
            combo_init_time = t_lib.time()
            input_combo_step = 1    
        elif not jumping_state:
            jumping_state = True
            vel_jump = JUMP_POWER
            combo_init_time = t_lib.time()
            input_combo_step = 1    
    
    elif key in [b's', b'S']:
        curr_t = t_lib.time()
        if board_active:
            if not sliding_state:
                sliding_state = True
                current_slide_time = slide_max_time
                hero_stats["height"] = HEIGHT_SLIDE
                hero_stats["z"] = Z_SLIDE_LEVEL
                if input_combo_step == 2 and combo_init_time != 0.0:
                    if curr_t - combo_init_time <= COMBO_TIME_LIMIT:
                        multiplier_active = True
                        multiplier_start = t_lib.time()
                        input_combo_step = 0
                        combo_init_time = 0.0
                    else:
                        input_combo_step = 0
                        combo_init_time = 0.0
        elif not sliding_state and not jumping_state:
            sliding_state = True
            current_slide_time = slide_max_time
            hero_stats["height"] = HEIGHT_SLIDE
            hero_stats["z"] = Z_SLIDE_LEVEL

            if input_combo_step == 2 and combo_init_time != 0.0:
                if curr_t - combo_init_time <= COMBO_TIME_LIMIT:
                    multiplier_active = True
                    multiplier_start = t_lib.time()
                    input_combo_step = 0
                    combo_init_time = 0.0
                else:
                    input_combo_step = 0
                    combo_init_time = 0.0    
    
    elif key in [b'f', b'F']:
        first_person_active = not first_person_active
    
    elif key in [b'c', b'C']:
        board_active = not board_active
        if board_active:
            jumping_state = False
            sliding_state = False
            vel_jump = 0.0
            current_slide_time = 0.0
            hero_stats["z"] = BASE_Z_LEVEL + board_elevation
            hero_stats["height"] = HEIGHT_NORMAL
        else:
            hero_stats["z"] = BASE_Z_LEVEL

    elif key in [b'r', b'R']:
        # Reset everything to initial state
        blockers.clear()
        tokens.clear()
        attractors.clear()
        
        total_dist = 0.0
        current_score = 0
        player_lives = 3
        run_speed = 410.0
        highway_offset = 0.0
        is_game_over = False
        
        hero_stats["lane"] = 1
        hero_stats["x"] = X_POS_LANES[1]
        hero_stats["y"] = 2000.0
        hero_stats["z"] = BASE_Z_LEVEL
        hero_stats["height"] = HEIGHT_NORMAL
        
        jumping_state = False
        vel_jump = 0.0
        sliding_state = False
        current_slide_time = 0.0
        
        first_person_active = False
        board_active = False
        board_speed_boost = False
        board_tilt_angle = 0.0
        board_bob_anim = 0.0
        
        total_tokens_collected = 0
        total_attractors = 0
        
        attractor_on = False
        attractor_timer = 0.0
        attractor_angle = 0.0
        
        bot_is_active = False
        bot_active_timer = 0.0
        bot_jumping = False
        bot_sliding = False
        bot_jump_vel = 0.0
        bot_slide_timer = 0.0
        bot_decision_cooldown = 0.0
        chaser_ai["x"] = 0.0
        chaser_ai["y"] = 0.0
        chaser_ai["z"] = 40.0
        
        cam_position = (0, hero_stats["y"] + 400, 500)
        previous_spawn_time = t_lib.time() - 1.0  

def special_key_handler(key, x, y):
    global cam_position
    cx, cy, cz = cam_position
    if key == GLUT_KEY_LEFT:
        cx -= 10.0
    elif key == GLUT_KEY_RIGHT:
        cx += 10.0
    elif key == GLUT_KEY_UP:
        cy += 10.0
    elif key == GLUT_KEY_DOWN:
        cy -= 10.0
    cam_position = (cx, cy, cz)

def mouse_handler(button, state, x, y):
    pass

# CAMERA SETUP
# ==========================================
# Third-person mode uses a fixed, arrow-key-pannable gluLookAt anchored in
# world space. First-person mode instead rebuilds the eye/target points from
# the player's own position every frame, and layers a small sinusoidal
# "camera_shake_offset" on top to simulate footfall while running (a
# gentler shake while hoverboarding, and no shake mid-air or mid-slide).
def init_camera_view():
    global camera_shake_offset
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(cam_fov if not first_person_active else 90, 1.25, 0.1, 4000)  
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if first_person_active:
        t_now = t_lib.time()
        if not jumping_state and not sliding_state and not board_active:
            camera_shake_offset = m_lib.sin(t_now * 8) * 3  
        elif board_active:
            camera_shake_offset = m_lib.sin(t_now * 4) * 2  
        else:
            camera_shake_offset = 0
        
        cam_height = 70  
        if sliding_state:
            cam_height = 20  
        elif board_active:
            cam_height = 80  
        
        view_x = hero_stats["x"]
        view_y = hero_stats["y"] + 30 
        view_z = hero_stats["z"] + 32 + cam_height + camera_shake_offset
        
        tgt_x = hero_stats["x"]
        tgt_y = hero_stats["y"] - 100  
        tgt_z = hero_stats["z"] + cam_height
        
        gluLookAt(view_x, view_y, view_z, tgt_x, tgt_y, tgt_z, 0, 0, 1)                         
    else:
        cam_x, cam_y, cam_z = cam_position
        gluLookAt(cam_x, cam_y, cam_z, 0, 0, hero_stats["z"], 0, 0, 1)


# GAME LOOP
# ==========================================
def game_loop_idle():
    global previous_frame_time
    now = t_lib.time()
    time_diff = now - previous_frame_time
    if time_diff > 0.1:
        time_diff = 0.1

    process_game_state(time_diff)
    previous_frame_time = now
    glutPostRedisplay()


# ENVIRONMENT DRESSING (LAMP POSTS)
# ==========================================
def render_light_bulb():
    glColor3f(0.0, 1.0, 1.0)   
    gluSphere(gluNewQuadric(), 12, 16, 16)
    glTranslatef(0, 0, 10)
    glColor3f(1.0, 1.0, 1.0)   
    gluSphere(gluNewQuadric(), 8, 16, 16)
    glTranslatef(0, 0, 10)
    glColor3f(0.0, 0.5, 0.5)   
    gluCylinder(gluNewQuadric(), 5, 0, 15, 10, 10)

def render_street_lights():
    h_pole = 250
    spacing = 400
    rear_dist = 3000
    fwd_dist = 5000

    cam_y = cam_position[1]
    y_start = cam_y - rear_dist
    y_finish = cam_y + fwd_dist
    
    offset_y = highway_offset % spacing
    draw_y_start = y_start - (y_start % spacing) - spacing 
    curr_y = draw_y_start

    while curr_y < y_finish:
        real_y = curr_y + offset_y
        
        # Left pole
        glPushMatrix()
        glTranslatef(-470, real_y, 0)
        glColor3f(0.3, 0.3, 0.3) 
        gluCylinder(gluNewQuadric(), 5, 5, h_pole, 10, 10)
        glTranslatef(0, 0, h_pole)
        render_light_bulb()
        glPopMatrix()

        # Right pole
        glPushMatrix()
        glTranslatef(470, real_y, 0)
        glColor3f(0.3, 0.3, 0.3) 
        gluCylinder(gluNewQuadric(), 5, 5, h_pole, 10, 10)
        glTranslatef(0, 0, h_pole)
        render_light_bulb()
        glPopMatrix()

        curr_y += spacing


# HOVERBOARD RENDERING
# ==========================================
def render_glide_board():
    global board_tilt_angle, board_bob_anim, run_speed, board_speed_boost
    glPushMatrix()
    
    len_board = 120
    wid_board = 40
    thick_board = 8
    
    ang_tilt = m_lib.sin(board_tilt_angle * m_lib.pi / 180) * 5  
    glRotatef(ang_tilt, 0, 0, 1)  
    
    glColor3f(0.1, 0.1, 0.2)  
    glPushMatrix()
    glScalef(len_board, wid_board, thick_board)  
    glutSolidCube(1)
    glPopMatrix()
    
    if board_speed_boost:
        glColor3f(1.0, 0.0, 0.5)  
        glPushMatrix()
        glScalef(len_board + 8, wid_board + 8, thick_board + 4)
        glPopMatrix()
    else:
        glColor3f(0.0, 1.0, 0.8) 
        glPushMatrix()
        glScalef(len_board + 4, wid_board + 4, thick_board + 2)
        glPopMatrix()
    
    w_rad = 8
    w_wid = 5
    w_pos = [
        (-wid_board*0.5 - 15, -len_board*0.5 + 20),  
        (-wid_board*0.5 - 15, len_board*0.5 - 20),   
        (wid_board*0.5 + 15, -len_board*0.5 + 20),   
        (wid_board*0.5 + 15, len_board*0.5 - 20)     
    ]
    
    for i, (wx, wy) in enumerate(w_pos):
        glPushMatrix()
        glTranslatef(wx, wy, -thick_board*0.5 - w_rad)
        glColor3f(0.1, 0.1, 0.1)  
        glRotatef(90, 0, 1, 0)  
        gluCylinder(gluNewQuadric(), w_rad, w_rad, w_wid, 12, 2)
        
        glColor3f(0.0, 1.0, 0.8)  
        glPushMatrix()
        glTranslatef(-1, 0, 0)
        gluCylinder(gluNewQuadric(), w_rad + 1, w_rad + 1, 2, 12, 2)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(w_wid, 0, 0)
        gluCylinder(gluNewQuadric(), w_rad + 1, w_rad + 1, 2, 12, 2)
        glPopMatrix()
        glPopMatrix()
    glPopMatrix()

# CHARACTER & ENEMY RENDERING
# ==========================================
def render_main_char():
    global vel_jump, jumping_state, sliding_state, board_active

    h_rad = 15
    n_height = 10
    t_height = 60
    t_width = 30
    t_depth = 15
    a_len = 60
    l_len = 80

    t_curr = t_lib.time()
    
    sw_angle = m_lib.sin(t_curr * 6) * 60  
    lg_angle = m_lib.sin(t_curr * 6 + m_lib.pi) * 40  
    
    if sliding_state and board_active:
        sw_angle = m_lib.sin(t_curr * 6) * 15  
        lg_angle = m_lib.sin(t_curr * 6 + m_lib.pi) * 10  
    elif sliding_state:
        sw_angle = 0
        lg_angle = 0
    elif board_active:
        if board_speed_boost:
            sw_angle = m_lib.sin(t_curr * 12) * 60  
            lg_angle = m_lib.sin(t_curr * 12 + m_lib.pi) * 40  
        else:
            sw_angle = m_lib.sin(t_curr * 4) * 20  
            lg_angle = m_lib.sin(t_curr * 4 + m_lib.pi) * 15  

    if jumping_state:
        sw_angle = 60 * m_lib.sin(t_curr * 10)  
        lg_angle = 45 * m_lib.sin(t_curr * 10)    

    z_offset = 0
    if sliding_state and board_active:
        hero_z_val = hero_stats["z"] + z_offset + 30 
    elif sliding_state:
        hero_z_val = 5.0  
    else:
        hero_z_val = hero_stats["z"] + z_offset

    glPushMatrix()
    glTranslatef(hero_stats["x"], hero_stats["y"], hero_z_val)
    
    if board_active:
        glPushMatrix()
        render_glide_board()
        glPopMatrix()

    if sliding_state:
        # Sliding pose rendering
        for lx in [-10, 10]:
            glPushMatrix()
            glTranslatef(lx, 0, 5 if not board_active else 32)  
            glRotatef(90, 1, 0, 0)  
            glColor3f(0.2, 0.2, 0.2) 
            gluCylinder(gluNewQuadric(), 8, 6, l_len, 8, 2)
            glTranslatef(0, 0, l_len if not board_active else l_len + 32)
            glColor3f(0.0, 1.0, 1.0) 
            gluSphere(gluNewQuadric(), 12, 10, 10)
            glPopMatrix()

        glPushMatrix()
        glTranslatef(0, 0, 10 if not board_active else 30)  
        glRotatef(90, 1, 0, 0)  
        
  
        glColor3f(0.0, 0.8, 1.0)  
        glBegin(GL_QUADS)
        r_height = 20  
        glVertex3f(-t_width*0.5, -t_depth*0.5, 0)
        glVertex3f(t_width*0.5, -t_depth*0.5, 0)
        glVertex3f(t_width*0.5*0.8, -t_depth*0.5, r_height)
        glVertex3f(-t_width*0.5*0.8, -t_depth*0.5, r_height)
        glVertex3f(-t_width*0.5, t_depth*0.5, 0)
        glVertex3f(t_width*0.5, t_depth*0.5, 0)
        glVertex3f(t_width*0.5*0.8, t_depth*0.5, r_height)
        glVertex3f(-t_width*0.5*0.8, t_depth*0.5, r_height)
        glEnd()
        glPopMatrix()

        for side in [-1, 1]:
            glPushMatrix()
            glTranslatef(side * (t_width*0.5 + 5), 0, 8 if not board_active else 10)
            glRotatef(90, 1, 0, 0)  
            glColor3f(0.8, 0.8, 0.8) 
            gluCylinder(gluNewQuadric(), 5, 4, a_len, 8, 2)
            glTranslatef(0, 0, a_len)
            gluSphere(gluNewQuadric(), 8, 10, 10)
            glPopMatrix()

        glPushMatrix()
        glTranslatef(0, t_height*0.5 + 10, 15 if not board_active else 65)  
        glColor3f(0.8, 0.8, 0.8)  
        gluSphere(gluNewQuadric(), h_rad, 12, 12)
        glPopMatrix()
    else:
        # Normal running pose
        for sgn, lg in [(-1, lg_angle), (1, -lg_angle)]:
            glPushMatrix()
            glTranslatef(sgn * 10, 0, l_len)
            glRotatef(180, 1, 0, 0)
            glRotatef(lg, 1, 0, 0)
            glColor3f(0.2, 0.2, 0.2)  
            gluCylinder(gluNewQuadric(), 8, 6, l_len, 8, 2)
            glTranslatef(0, 0, l_len)
            glColor3f(0.0, 1.0, 1.0)  
            gluSphere(gluNewQuadric(), 12, 10, 10)
            glPopMatrix()

        glPushMatrix()
        glTranslatef(0, 0, l_len)
        glColor3f(0.0, 0.8, 1.0) 
        glBegin(GL_QUADS)
        glVertex3f(-t_width*0.5, -t_depth*0.5, 0)
        glVertex3f(t_width*0.5, -t_depth*0.5, 0)
        glVertex3f(t_width*0.5*0.8, -t_depth*0.5, t_height)
        glVertex3f(-t_width*0.5*0.8, -t_depth*0.5, t_height)
        
        glVertex3f(-t_width*0.5, t_depth*0.5, 0)
        glVertex3f(t_width*0.5, t_depth*0.5, 0)
        glVertex3f(t_width*0.5*0.8, t_depth*0.5, t_height)
        glVertex3f(-t_width*0.5*0.8, t_depth*0.5, t_height)
        
        glVertex3f(-t_width*0.5, -t_depth*0.5, 0)
        glVertex3f(-t_width*0.5, t_depth*0.5, 0)
        glVertex3f(-t_width*0.5*0.8, t_depth*0.5, t_height)
        glVertex3f(-t_width*0.5*0.8, -t_depth*0.5, t_height)
        
        glVertex3f(t_width*0.5, -t_depth*0.5, 0)
        glVertex3f(t_width*0.5, t_depth*0.5, 0)
        glVertex3f(t_width*0.5*0.8, t_depth*0.5, t_height)
        glVertex3f(t_width*0.5*0.8, -t_depth*0.5, t_height)
        glEnd()
        glPopMatrix()

        for side, ang in [(-1, sw_angle), (1, -sw_angle)]:
            glPushMatrix()
            glTranslatef(side * (t_width*0.5 + 5), 0, l_len + t_height - 10)
            glRotatef(90, 1, 0, 0)
            glRotatef(ang, 1, 0, 0)
            glColor3f(0.8, 0.8, 0.8)  
            gluCylinder(gluNewQuadric(), 5, 4, a_len, 8, 2)
            glTranslatef(0, 0, a_len)
            gluSphere(gluNewQuadric(), 8, 10, 10)  
            glPopMatrix()

        glPushMatrix()
        glTranslatef(0, 0, l_len + t_height)
        glColor3f(0.8, 0.8, 0.8)  
        gluCylinder(gluNewQuadric(), 5, 5, n_height, 8, 2)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(0, 0, l_len + t_height + n_height + h_rad)
        glColor3f(0.8, 0.8, 0.8)  
        gluSphere(gluNewQuadric(), h_rad, 12, 12)
        glPopMatrix()

    glPopMatrix()  

def render_chaser():
    global bot_jumping, bot_sliding
    h_rad = 15
    n_height = 10
    t_height = 60
    t_width = 30
    t_depth = 15
    a_len = 60
    l_len = 80
    t_curr = t_lib.time()
    
    sw_angle = m_lib.sin(t_curr * 6) * 60  
    lg_angle = m_lib.sin(t_curr * 6 + m_lib.pi) * 40  
    
    if bot_sliding:
        sw_angle = 0
        lg_angle = 0
    elif bot_jumping:
        sw_angle = 60 * m_lib.sin(t_curr * 10)  
        lg_angle = 45 * m_lib.sin(t_curr * 10)

    bot_z_val = 5.0 if bot_sliding else chaser_ai["z"]

    glPushMatrix()
    glTranslatef(chaser_ai["x"], chaser_ai["y"], bot_z_val)

    if bot_sliding:
        for lx in [-10, 10]:
            glPushMatrix()
            glTranslatef(lx, 0, 5)  
            glRotatef(90, 1, 0, 0)  
            glColor3f(0.1, 0.1, 0.1)  
            gluCylinder(gluNewQuadric(), 8, 6, l_len, 8, 2)
            glTranslatef(0, 0, l_len)
            glColor3f(0.0, 0.0, 0.0)  
            gluSphere(gluNewQuadric(), 12, 10, 10)
            glPopMatrix()

        glPushMatrix()
        glTranslatef(0, 0, 10)  
        glRotatef(90, 1, 0, 0)  
        glColor3f(0.8, 0.0, 0.2) 
        glBegin(GL_QUADS)
        r_height = 20  
        glVertex3f(-t_width*0.5, -t_depth*0.5, 0)
        glVertex3f(t_width*0.5, -t_depth*0.5, 0)
        glVertex3f(t_width*0.5*0.8, -t_depth*0.5, r_height)
        glVertex3f(-t_width*0.5*0.8, -t_depth*0.5, r_height)
        glVertex3f(-t_width*0.5, t_depth*0.5, 0)
        glVertex3f(t_width*0.5, t_depth*0.5, 0)
        glVertex3f(t_width*0.5*0.8, t_depth*0.5, r_height)
        glVertex3f(-t_width*0.5*0.8, t_depth*0.5, r_height)
        glEnd()
        glPopMatrix()

        for side in [-1, 1]:
            glPushMatrix()
            glTranslatef(side * (t_width*0.5 + 5), 0, 8)
            glRotatef(90, 1, 0, 0)  
            glColor3f(0.4, 0.4, 0.4)  
            gluCylinder(gluNewQuadric(), 5, 4, a_len, 8, 2)
            glTranslatef(0, 0, a_len)
            gluSphere(gluNewQuadric(), 8, 10, 10)
            glPopMatrix()

        glPushMatrix()
        glTranslatef(0, t_height*0.5 + 10, 15)  
        glColor3f(0.2, 0.2, 0.2)  
        gluSphere(gluNewQuadric(), h_rad, 12, 12)
        glPopMatrix()
    else:
        for sgn, lg in [(-1, lg_angle), (1, -lg_angle)]:
            glPushMatrix()
            glTranslatef(sgn * 10, 0, l_len)
            glRotatef(180, 1, 0, 0)
            glRotatef(lg, 1, 0, 0)
            glColor3f(0.1, 0.1, 0.1)  
            gluCylinder(gluNewQuadric(), 8, 6, l_len, 8, 2)
            glTranslatef(0, 0, l_len)
            glColor3f(0.0, 0.0, 0.0)  
            gluSphere(gluNewQuadric(), 12, 10, 10)
            glPopMatrix()

        glPushMatrix()
        glTranslatef(0, 0, l_len)
        glColor3f(0.8, 0.0, 0.2) 
        glBegin(GL_QUADS)
        glVertex3f(-t_width*0.5, -t_depth*0.5, 0)
        glVertex3f(t_width*0.5, -t_depth*0.5, 0)
        glVertex3f(t_width*0.5*0.8, -t_depth*0.5, t_height)
        glVertex3f(-t_width*0.5*0.8, -t_depth*0.5, t_height)
        glVertex3f(-t_width*0.5, t_depth*0.5, 0)
        glVertex3f(t_width*0.5, t_depth*0.5, 0)
        glVertex3f(t_width*0.5*0.8, t_depth*0.5, t_height)
        glVertex3f(-t_width*0.5*0.8, t_depth*0.5, t_height)
        glVertex3f(-t_width*0.5, -t_depth*0.5, 0)
        glVertex3f(-t_width*0.5, t_depth*0.5, 0)
        glVertex3f(-t_width*0.5*0.8, t_depth*0.5, t_height)
        glVertex3f(-t_width*0.5*0.8, -t_depth*0.5, t_height)
        glVertex3f(t_width*0.5, -t_depth*0.5, 0)
        glVertex3f(t_width*0.5, t_depth*0.5, 0)
        glVertex3f(t_width*0.5*0.8, t_depth*0.5, t_height)
        glVertex3f(t_width*0.5*0.8, -t_depth*0.5, t_height)
        glEnd()
        glPopMatrix()

        for side, ang in [(-1, sw_angle), (1, -sw_angle)]:
            glPushMatrix()
            glTranslatef(side * (t_width*0.5 + 5), 0, l_len + t_height - 10)
            glRotatef(90, 1, 0, 0)
            glRotatef(ang*0.5, 1, 0, 0)
            glColor3f(0.4, 0.4, 0.4)  
            gluCylinder(gluNewQuadric(), 5, 4, a_len, 8, 2)
            glTranslatef(0, 0, a_len)
            gluSphere(gluNewQuadric(), 8, 10, 10)  
            glPopMatrix()

        glPushMatrix()
        glTranslatef(0, 0, l_len + t_height)
        glColor3f(0.4, 0.4, 0.4)  
        gluCylinder(gluNewQuadric(), 5, 5, n_height, 8, 2)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(0, 0, l_len + t_height + n_height + h_rad)
        glColor3f(0.2, 0.2, 0.2)  
        gluSphere(gluNewQuadric(), h_rad, 12, 12)
        glPopMatrix()

    glPopMatrix()

# AI LOGIC FOR ENEMY (LOOK-AHEAD)
# ==========================================
# The chaser does not simply mirror the player — it scans its own lane for
# obstacles and reacts independently. detect_blocker_ahead() searches for the
# nearest obstacle in the chaser's current lane within look_dist units ahead;
# chaser_ai_decision() then randomly commits to a jump or a slide once that
# obstacle is close enough, giving the enemy the same jump/slide options the
# player has instead of scripted, guaranteed avoidance.
def detect_blocker_ahead(x_pos, y_pos, look_dist=400):
    for b in blockers:
        if abs(b["x"] - x_pos) < 80:  
            if b["y"] > y_pos and b["y"] - y_pos < look_dist:
                return b
    return None

def chaser_ai_decision(obs_ref, dist_val):
    global bot_jumping, bot_jump_vel, bot_sliding, bot_slide_timer
    if bot_jumping or bot_sliding:
        return False
    if dist_val < 200:  
        ai_choice = r_lib.choice(['jump', 'slide'])
        if ai_choice == 'jump':
            bot_jumping = True
            bot_jump_vel = JUMP_POWER
        else:
            bot_sliding = True
            bot_slide_timer = slide_max_time
        return True
    return False


# CORE GAME UPDATE LOGIC (PHYSICS & COLLISIONS)
# ==========================================
# Called once per idle tick with the frame's delta time. In order, this
# function: advances run speed and scrolls the world toward the player,
# moves and collision-checks obstacles/coins/magnets against the player's
# current hitbox (which changes with sliding/hoverboarding), despawns
# anything the player has passed, updates distance-based score (applying
# the combo multiplier if active), steps jump/slide/hoverboard physics,
# spawns new obstacles/coins/magnets on a timer, and drives the chaser
# enemy's pursuit + look-ahead obstacle avoidance while it is active.
def process_game_state(delta_t):
    global previous_spawn_time, total_dist, current_score, player_lives, highway_offset
    global jumping_state, vel_jump, sliding_state, tokens, total_tokens_collected, current_slide_time
    global attractor_angle, total_attractors, attractor_on, attractor_timer
    global bot_is_active, bot_active_timer, bot_decision_cooldown
    global bot_jumping, bot_jump_vel, bot_sliding, bot_slide_timer
    global board_active, board_tilt_angle, board_bob_anim, board_speed_boost
    global run_speed, is_game_over, score_multi_value, multiplier_start, multiplier_active, MULTIPLIER_LASTS

    accel = 5.0  
    run_speed += accel * delta_t

    dead_obs = []
    dead_mags = []
    
    H_OBSTACLE = 180 if board_active else 120
    despawn_line = cam_position[1] + 1000

    if sliding_state:
        hero_bot_z = Z_SLIDE_LEVEL
        hero_top_z = Z_SLIDE_LEVEL + HEIGHT_SLIDE
    elif board_active:
        if board_speed_boost:
            b_speed = BOARD_BOB_RATE * 2.5  
            t_speed = BOARD_TILT_RATE * 2.5  
        else:
            b_speed = BOARD_BOB_RATE
            t_speed = BOARD_TILT_RATE
            
        board_bob_anim += b_speed * delta_t
        board_tilt_angle += t_speed * delta_t
        if board_tilt_angle >= 360:
            board_tilt_angle -= 360
        
        bob_val = m_lib.sin(board_bob_anim) * 8.0  
        hero_stats["z"] = BASE_Z_LEVEL + board_elevation + bob_val
        
        if sliding_state:
            hero_bot_z = hero_stats["z"]
            hero_top_z = hero_stats["z"] + hero_stats["height"]
        else:
            hero_bot_z = 0  
            hero_top_z = hero_stats["z"] + hero_stats["height"]  
    else:
        hero_bot_z = hero_stats["z"]
        hero_top_z = hero_stats["z"] + hero_stats["height"]

    # Obstacle Collisions
    for b in blockers:
        cur_vel = run_speed * (2.0 if board_speed_boost else 1.0)
        b["y"] += cur_vel * delta_t
        if (abs(b["y"] - hero_stats["y"]) < Y_HITBOX and abs(b["x"] - hero_stats["x"]) < X_HITBOX):
            b_bot = 0.0
            b_top = H_OBSTACLE
            if (hero_top_z > b_bot) and (hero_bot_z < b_top):
                dead_obs.append(b)
                player_lives -= 1
                
                # Spawn Enemy AI
                bot_is_active = True
                bot_active_timer = BOT_MAX_DURATION
                chaser_ai["x"] = hero_stats["x"]
                chaser_ai["y"] = hero_stats["y"] + 190  
                chaser_ai["z"] = hero_stats["z"]   
                if player_lives < 0:
                    player_lives = 0
                    is_game_over = True

    # Coin Collisions and Magnet logic
    dead_coins = []
    for c in tokens:
        cur_vel = run_speed * (2.0 if board_speed_boost else 1.0)
        c["y"] += cur_vel * delta_t
        c_bot = c["z"] - c["size"] * 0.5
        c_top = c["z"] + c["size"] * 0.5

        if attractor_on:
            d_x = hero_stats["x"] - c["x"]
            d_y = hero_stats["y"] - c["y"]
            dist_c = m_lib.sqrt(d_x*d_x + d_y*d_y)

            if dist_c < RANGE_ATTRACT:
                n_x = d_x / (dist_c + 1e-6)
                n_y = d_y / (dist_c + 1e-6)
                c["x"] += n_x * cur_vel * 2 * delta_t
                c["y"] += n_y * cur_vel * 2 * delta_t

        if (abs(c["y"] - hero_stats["y"]) < Y_HITBOX and abs(c["x"] - hero_stats["x"]) < X_HITBOX):
            if (hero_top_z > c_bot) and (hero_bot_z < c_top):
                dead_coins.append(c)
                total_tokens_collected += 1

    # Magnet Collisions
    for mag in attractors:
        cur_vel = run_speed * (2.0 if board_speed_boost else 1.0)
        mag["y"] += (cur_vel*2) * delta_t
        
        if sliding_state:
            mag_bot = mag["collision_z"] - mag["size"] * 0.5
            mag_top = mag["collision_z"] + mag["size"] * 0.5
        else:
            mag_bot = mag["z"] - mag["size"] * 0.5
            mag_top = mag["z"] + mag["size"] * 0.5
        
        if (abs(mag["y"] - hero_stats["y"]) < Y_HITBOX and abs(mag["x"] - hero_stats["x"]) < X_HITBOX):
            if sliding_state and board_active:
                hero_bot_z = hero_stats["z"]
                hero_top_z = hero_stats["z"] + hero_stats["height"]
            elif sliding_state:
                hero_bot_z = Z_SLIDE_LEVEL
                hero_top_z = Z_SLIDE_LEVEL + HEIGHT_SLIDE
            elif board_active:
                hero_bot_z = 0  
                hero_top_z = hero_stats["z"] + hero_stats["height"]  
            else:
                hero_bot_z = hero_stats["z"]
                hero_top_z = hero_stats["z"] + hero_stats["height"]
            
            if (hero_top_z > mag_bot) and (hero_bot_z < mag_top):
                dead_mags.append(mag)
                total_attractors += 1
                attractor_on = True
                attractor_timer = DURATION_ATTRACT

    for b in list(blockers):
        if b in dead_obs or b["y"] > despawn_line:
            blockers.remove(b)
    for c in list(tokens):
        if c in dead_coins or c["y"] > despawn_line:
            tokens.remove(c)
    for mag in list(attractors):
        if mag in dead_mags or mag["y"] > despawn_line:
            attractors.remove(mag)

    cur_vel = run_speed * (2.0 if board_speed_boost else 1.0)
    total_dist += cur_vel * delta_t
    
    base_calc = int(total_dist // 10)
    if multiplier_start != 0.0:
        current_score = base_calc * score_multi_value
    else:
        current_score = base_calc

    highway_offset += cur_vel * delta_t

    if jumping_state:
        hero_stats["z"] += vel_jump * delta_t
        vel_jump += WORLD_GRAVITY * delta_t
        if hero_stats["z"] <= BASE_Z_LEVEL:
            hero_stats["z"] = BASE_Z_LEVEL
            jumping_state = False
            vel_jump = 0.0

    global token_spin
    token_spin += 180 * delta_t
    if token_spin >= 360:
        token_spin -= 360

    attractor_angle += 180 * delta_t
    if attractor_angle >= 360:
        attractor_angle -= 360

    if sliding_state:
        current_slide_time -= delta_t
        if current_slide_time <= 0:
            sliding_state = False
            hero_stats["height"] = HEIGHT_NORMAL
            hero_stats["z"] = BASE_Z_LEVEL

    curr_t = t_lib.time()
    if curr_t - previous_spawn_time > item_spawn_rate:
        spawn_amount = 1 if r_lib.random() < 0.8 else 2
        for _ in range(spawn_amount):
            generate_blocker()
            if r_lib.random() < 0.75:
                generate_token()
            if r_lib.random() < 0.15:
                generate_attractor()
        previous_spawn_time = curr_t
    
    if attractor_on:
        attractor_timer -= delta_t
        if attractor_timer <= 0:
            attractor_on = False

    # Process AI Bot
    if bot_is_active:
        bot_active_timer -= delta_t
        if bot_active_timer <= 0:
            bot_is_active = False
            bot_jumping = False
            bot_sliding = False
            bot_jump_vel = 0.0
            bot_slide_timer = 0.0
        
        if bot_decision_cooldown > 0:
            bot_decision_cooldown -= delta_t
        
        target_lane = X_POS_LANES[hero_stats["lane"]]
        if abs(chaser_ai["x"] - target_lane) > 50:
            move_s = 800.0
            if chaser_ai["x"] < target_lane:
                chaser_ai["x"] += move_s * delta_t
                if chaser_ai["x"] > target_lane:
                    chaser_ai["x"] = target_lane
            else:
                chaser_ai["x"] -= move_s * delta_t
                if chaser_ai["x"] < target_lane:
                    chaser_ai["x"] = target_lane
        
        bot_tgt_y = hero_stats["y"] + 180
        chaser_ai["y"] += (bot_tgt_y - chaser_ai["y"]) * 2.0 * delta_t
        
        obs_ai_check = detect_blocker_ahead(chaser_ai["x"], chaser_ai["y"], look_dist=600)
        
        if bot_jumping or bot_sliding:
            if not obs_ai_check:
                bot_jumping = False
                bot_sliding = False
                bot_jump_vel = 0.0
                bot_slide_timer = 0.0
                chaser_ai["z"] = BASE_Z_LEVEL
        else:
            if obs_ai_check and bot_decision_cooldown <= 0:
                dist_ai_obs = obs_ai_check["y"] - chaser_ai["y"]
                if chaser_ai_decision(obs_ai_check, dist_ai_obs):
                    bot_decision_cooldown = 0.3
        
        if bot_jumping:
            chaser_ai["z"] += bot_jump_vel * delta_t
            bot_jump_vel += WORLD_GRAVITY * delta_t
            if chaser_ai["z"] <= BASE_Z_LEVEL:
                chaser_ai["z"] = BASE_Z_LEVEL
                bot_jumping = False
                bot_jump_vel = 0.0
        
        if bot_sliding:
            bot_slide_timer -= delta_t
            chaser_ai["z"] = Z_SLIDE_LEVEL  
            if bot_slide_timer <= 0:
                bot_sliding = False
                chaser_ai["z"] = BASE_Z_LEVEL  
        
        if not bot_jumping and not bot_sliding:
            chaser_ai["z"] = BASE_Z_LEVEL

    if multiplier_active and multiplier_start != 0.0:
        if t_lib.time() - multiplier_start > MULTIPLIER_LASTS:
            multiplier_active = False
            multiplier_start = 0.0                

# MAIN RENDER FUNCTION
# ==========================================
# Renders in three passes per frame: (1) an orthographic full-screen quad
# for the sky gradient, (2) the perspective 3D scene — road, lights, coins,
# magnets, obstacles, and the player/chaser models, and (3) a second
# orthographic pass for the HUD text overlay. Game-over state short-circuits
# straight to an orthographic "GAME OVER" / credits screen instead.
def display_frame():
    global is_game_over

    if is_game_over:
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, 1000, 0, 800)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glColor3f(1.0, 0.0, 0.0)
        display_string(400, 420, "GAME OVER!", GLUT_BITMAP_9_BY_15)

        glColor3f(1.0, 1.0, 1.0)
        display_string(400, 370, "Press 'R' to restart", GLUT_BITMAP_9_BY_15)
        
        glColor3f(0.0, 1.0, 1.0)
        display_string(400, 250, "Team:", GLUT_BITMAP_9_BY_15)
        display_string(400, 220, "Md. Tanvirul Islam Rifat", GLUT_BITMAP_9_BY_15)
        display_string(400, 190, "Fahimur Rahman", GLUT_BITMAP_9_BY_15)
        display_string(400, 160, "Istiak Al Imran", GLUT_BITMAP_9_BY_15)

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        glutSwapBuffers()
        return

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)

    # Blue Sky Implementation
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glBegin(GL_QUADS)
    glColor3f(0.53, 0.81, 0.98)
    glVertex2f(0, 0)
    glVertex2f(1000, 0)
    glColor3f(0.0, 0.3, 0.7) 
    glVertex2f(1000, 800)
    glVertex2f(0, 800)
    glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

    init_camera_view()

    render_highway()
    render_street_lights()
    
    for c in tokens:
        render_token(c)

    for mag in attractors:
        render_attractor(mag)

    for b in blockers:
        render_blocker(b)

    if not first_person_active:
        render_main_char()
        if bot_is_active:
            render_chaser()

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # UI Rendering
    glColor3f(1, 1, 1)
    display_string(10, 770, "Score: ")
    glColor3f(0, 1, 1)
    display_string(80, 770, f"{current_score}")

    glColor3f(1, 1, 1)
    display_string(10, 740, "Lives: ")
    glColor3f(0, 1, 1)
    display_string(80, 740, f"{player_lives}")

    mode_text = "FPP" if first_person_active else "TPP"
    glColor3f(1, 1, 1)
    display_string(10, 710, "Camera: ")
    glColor3f(0, 1, 1)
    display_string(90, 710, f"{mode_text} (Press F)")

    board_mode_txt = "HOVERBOARD" if board_active else "NORMAL"
    glColor3f(1, 1, 1)
    display_string(10, 680, "Mode: ")
    glColor3f(0, 1, 1)
    display_string(80, 680, f"{board_mode_txt} (Press C)")

    glColor3f(1, 1, 1)
    display_string(590, 770, "Distance: ")
    glColor3f(0, 1, 1)
    display_string(670, 770, f"{int(total_dist)} Meters")

    glColor3f(1, 1, 1)
    display_string(590, 740, "Coins: ")
    glColor3f(0, 1, 1)
    display_string(670, 740, f"{int(total_tokens_collected)}")

    glColor3f(1, 1, 1)
    display_string(590, 710, "Magnets: ")
    glColor3f(0, 1, 1)
    display_string(670, 710, f"{total_attractors}")

    glColor3f(1, 1, 1)
    display_string(10, 650, "Press 'R' to restart")

    if multiplier_start != 0:
        glColor3f(1.0, 0.0, 1.0)   
        display_string(590, 680, "5x COMBO ACTIVE!", GLUT_BITMAP_9_BY_15)

    if board_speed_boost:
        glColor3f(1, 1, 1)
        display_string(10, 620, "FAST MODE: ON")

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

    glutSwapBuffers()

# MAIN ENTRY POINT
# ==========================================
def main():
    global previous_frame_time, previous_spawn_time
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    
    win_handler = glutCreateWindow(b"Render Rush: 3D Endless Escape")

    glutDisplayFunc(display_frame)
    glutKeyboardFunc(key_handler)
    glutSpecialFunc(special_key_handler)
    glutMouseFunc(mouse_handler)
    glutIdleFunc(game_loop_idle)

    previous_frame_time = t_lib.time()
    previous_spawn_time = t_lib.time() - 1.0  

    glutMainLoop()

if __name__ == "__main__":
    main()