# Render Rush: 3D Endless Escape

A **3D OpenGL endless runner** built with **Python + PyOpenGL (GLU / GLUT)**. You're a futuristic runner sprinting down a three-lane skyway — dodging barriers, grabbing coins and magnets, riding a hoverboard, and outrunning a robot guard that hunts you down the moment you slip up.

---
## Team Members

| Name | Student ID |
|---|---|
| **Md. Tanvirul Islam Rifat** | **22101311** |
| Fahim Rahman |  22101240  |
| Istiak Al Imran | 22301040 |

---

## Gameplay

https://github.com/user-attachments/assets/6175d02c-a7b0-46b6-bf6c-f455e7a25461


You start in the middle lane as the road speeds up beneath you. Obstacles, coins, and magnets spawn ahead in real time — switch lanes, jump, or slide to survive and collect. Hit a barrier and you lose a life *and* trigger a robot chaser that hunts you down the lane, jumping and sliding over its own obstacles just like you do. Lose all 3 lives and it's game over.

---

## Features

| Feature | Description |
|---|---|
| **Endless Procedural World** | The road, lane markers, street lights, obstacles, coins, and magnets are all generated and scrolled on the fly — nothing is a fixed, finite level |
| **Composite Character Rigs** | The player and the chaser are built from connected primitives (spheres, cylinders, cuboids) with arms and legs that swing through running, jumping, and sliding poses |
| **Look-Ahead Enemy AI** | The chaser doesn't blindly copy the player — it scans its own lane for the next obstacle and independently decides to jump or slide over it |
| **Dual Camera System** | Switch between a pannable third-person view and a first-person view with subtle procedural camera shake while running |
| **Hoverboard Mode** | Mount a hovering board that changes movement height, animation speed, and unlocks a speed-boost toggle |
| **Magnet Power-Up** | Picking up a magnet temporarily pulls every nearby coin toward the player for a few seconds |
| **Timed Combo System** | Chain Jump → Switch Lane → Slide within a few seconds to trigger a temporary 5x score multiplier |
| **Live HUD** | Real-time score, lives, distance, coins collected, magnet count, camera mode, and combo status, all rendered on screen |
| **Game Over & Restart** | A dedicated game-over screen with team credits appears on defeat; pressing `R` resets every system back to its initial state |

---

## Controls

| Input | Action |
|---|---|
| `A` / `D` | Switch one lane left / right |
| `SPACE` | Jump over obstacles (toggles speed boost instead while on the hoverboard) |
| `S` | Slide under obstacles (also usable on the hoverboard) |
| `F` | Toggle first-person / third-person camera |
| `C` | Mount / dismount the hoverboard |
| `↑` / `↓` | Pan the third-person camera vertically |
| `←` / `→` | Pan the third-person camera horizontally |
| `R` | Restart the game |

**Scoring Combo:** Press **Jump → Switch Lane → Slide** in sequence, each within a few seconds of the last, to activate a temporary **5x score multiplier**.

---

## How It Works

### Perspective Projection & Dual Camera System

Both camera modes rebuild their projection and view matrices every frame. Third-person is a fixed, arrow-key-pannable `gluLookAt`; first-person recomputes the eye and target points from the player's own position and layers a small sinusoidal offset on top to simulate footfall:

```python
def init_camera_view():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(cam_fov if not first_person_active else 90, 1.25, 0.1, 4000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if first_person_active:
        t_now = t_lib.time()
        if not jumping_state and not sliding_state and not board_active:
            camera_shake_offset = m_lib.sin(t_now * 8) * 3
        ...
        gluLookAt(view_x, view_y, view_z, tgt_x, tgt_y, tgt_z, 0, 0, 1)
    else:
        cam_x, cam_y, cam_z = cam_position
        gluLookAt(cam_x, cam_y, cam_z, 0, 0, hero_stats["z"], 0, 0, 1)
```

### Composite Character Animation

The player and chaser share the same rig structure — cylinders for limbs, spheres for joints, and a quad-built torso — with arm and leg swing angles driven by a sine wave against elapsed time, so the animation stays smooth regardless of frame rate:

```python
sw_angle = m_lib.sin(t_curr * 6) * 60   # arm swing
lg_angle = m_lib.sin(t_curr * 6 + m_lib.pi) * 40   # leg swing (opposite phase)
```

Sliding, jumping, and hoverboarding each override these angles and the character's base height, so the same rig reads correctly in every movement state.

### Look-Ahead Enemy AI

Rather than teleporting or scripted dodging, the chaser scans its own lane for the nearest upcoming obstacle and only then rolls a decision to jump or slide, exactly like a second player would:

```python
def detect_blocker_ahead(x_pos, y_pos, look_dist=400):
    for b in blockers:
        if abs(b["x"] - x_pos) < 80:
            if b["y"] > y_pos and b["y"] - y_pos < look_dist:
                return b
    return None

def chaser_ai_decision(obs_ref, dist_val):
    if dist_val < 200:
        ai_choice = r_lib.choice(['jump', 'slide'])
        ...
```

### Timed Combo System

The combo tracks progress through Jump → Switch Lane → Slide using a step counter and a timestamp; any wrong key or a timeout resets it to step 0, while completing all three steps in time unlocks a temporary score multiplier:

```python
if input_combo_step == 2 and combo_init_time != 0.0:
    if curr_t - combo_init_time <= COMBO_TIME_LIMIT:
        multiplier_active = True
        multiplier_start = t_lib.time()
```

### Magnet Attraction Physics

While a magnet's effect is active, every coin within range each frame is pulled along the normalized vector toward the player, rather than snapping to them instantly:

```python
if dist_c < RANGE_ATTRACT:
    n_x = d_x / (dist_c + 1e-6)
    n_y = d_y / (dist_c + 1e-6)
    c["x"] += n_x * cur_vel * 2 * delta_t
    c["y"] += n_y * cur_vel * 2 * delta_t
```

### Collision Detection

Obstacles, coins, and magnets each use axis-aligned XY hitboxes combined with a per-object Z-range check, so the same obstacle can be jumped over, ducked under, or missed entirely depending on the player's current pose (standing, sliding, or hoverboarding):

```python
if (abs(b["y"] - hero_stats["y"]) < Y_HITBOX and abs(b["x"] - hero_stats["x"]) < X_HITBOX):
    if (hero_top_z > b_bot) and (hero_bot_z < b_top):
        # collision confirmed
```

---

## How to Run

### Requirements

```bash
pip install PyOpenGL PyOpenGL_accelerate
```

> On macOS you may also need: `brew install freeglut`
> On Linux: `sudo apt-get install freeglut3-dev`

### Run

1. Download the **render_rush.py** file
2. Make sure PyOpenGL is installed in your environment
3. Run it from a terminal

```bash
python3 render_rush.py
```

---

## Project Structure

```
render-rush-3d-endless-runner/
├── render_rush.py           # Full game — rendering, physics, AI, input, and the GLUT loop
├── screenshots/
│   ├── gameplay.png         # Static screenshot of running game
│   └── gameplay.gif         # (add your screen recording here)
└── README.md
```

---

## Technical Architecture

- **Language:** Python 3.x
- **Graphics API:** OpenGL via PyOpenGL + GLU/GLUT (freeglut)
- **Projection:** Perspective projection (`gluPerspective`) with two switchable `gluLookAt` camera configurations
- **Rendering Primitives:** GLU quadrics (`gluSphere`, `gluCylinder`) and GLUT solids (`glutSolidCube`), plus hand-built `GL_QUADS`/`GL_TRIANGLES` geometry for the road, coins, and torsos
- **Coordinate System:** 3D world space scrolling toward a fixed-lane player, with hierarchical modelview transformations (`glPushMatrix` / `glPopMatrix`) for every composite object
- **Animation:** `glutIdleFunc` main loop driving delta-time physics, procedural limb-swing animation, enemy AI, and timed power-ups/combos

## Core Engineering Practices Demonstrated

- **Delta-Time Physics:** Gravity, jump/slide timers, hoverboard bobbing, and world scroll speed are all scaled by frame delta time, keeping movement consistent across hardware
- **State-Driven Composite Rigs:** A single character-drawing function branches its pose (running, sliding, hoverboarding, jumping) while reusing the same primitive hierarchy for both the player and the chaser
- **Autonomous Look-Ahead AI:** The enemy queries the same obstacle list the player collides with and makes its own jump/slide decisions based on distance, rather than following scripted or guaranteed-safe behavior
- **Procedural, Endless World Generation:** Road segments, lane dividers, street lights, and spawns are generated relative to the camera/player position on a rolling basis, so the world never runs out
- **Dual Camera Engineering:** One third-person free camera and one first-person camera with procedural shake share a single projection setup, branching only on `first_person_active`
- **Timed Input Sequencing:** The combo system implements a small step-based state machine gated by timestamps, rejecting any input that breaks the required order or arrives too late
- **Layered Collision Detection:** XY bounding-box checks are combined with per-pose Z-range checks so hitboxes correctly shrink or shift when sliding or hoverboarding
- **Clean Separation of Concerns:** Input handling, physics/collision updates, AI decision-making, and rendering are each isolated into dedicated functions driven by a single idle loop

## Author

**Md. Tanvirul Islam Rifat**

* **GitHub:** [@tanvirul-islam-rifat](https://github.com/tanvirul-islam-rifat)
* **LinkedIn:** [Tanvirul Islam Rifat](https://www.linkedin.com/in/tanvirul-islam-rifat)

