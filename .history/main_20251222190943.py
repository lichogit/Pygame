
import pygame
import random
import sys
import os

# ---------------------------
# Configuration
# ---------------------------
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
TILE = 20                     # grid cell size in pixels
COLUMNS = SCREEN_WIDTH // TILE
ROWS = SCREEN_HEIGHT // TILE

FPS = 10                      # base speed
GROW_ON_EAT = 1
INITIAL_LENGTH = 4

# Colors
BG_COLOR = (30, 30, 30)
TEXT_COLOR = (240, 240, 240)

# Directions (dx, dy in grid units)
DIR_UP = (0, -1)
DIR_DOWN = (0, 1)
DIR_LEFT = (-1, 0)
DIR_RIGHT = (1, 0)
OPPOSITE = {DIR_UP: DIR_DOWN, DIR_DOWN: DIR_UP, DIR_LEFT: DIR_RIGHT, DIR_RIGHT: DIR_LEFT}
HEAD_FRAME_INDEX = 0

SNAKE_ASSET = "snakeog.png"
FRUIT_ASSET = "pineapple.png"

# If your snake base frame faces right, keep 'right'. If it faces left/up/down change accordingly.
HEAD_BASE_FACING = "right"  # 'right' | 'left' | 'up' | 'down'

# ---------------------------
# Helpers
# ---------------------------
def resource_path(filename):
    """Return absolute path to filename placed next to this script."""
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, filename)

def grid_to_pixel(pos):
    return pos[0] * TILE, pos[1] * TILE

def add_tuples(a, b):
    return a[0] + b[0], a[1] + b[1]

def inside_bounds(pos):
    x, y = pos
    return 0 <= x < COLUMNS and 0 <= y < ROWS

def random_free_cell(occupied):
    all_cells = [(x, y) for x in range(COLUMNS) for y in range(ROWS)]
    free = [c for c in all_cells if c not in occupied]
    return random.choice(free) if free else None

# ---------------------------
# Image loading & sprite helpers
# ---------------------------
def slice_sprite_sheet(surf):
    """
    Slice a sprite sheet that contains square frames arranged either
    horizontally (left->right) or vertically (top->bottom).
    If nothing sensible can be produced, return [surf].
    """
    w, h = surf.get_size()

    frames = []

    # Prefer square frames. Use the smaller dimension as frame size.
    frame_size = min(w, h)
    if frame_size <= 0:
        return [surf]

    # If sheet is wider than tall -> horizontal strip of square frames
    if w >= h:
        # number of frames that fit horizontally
        n = w // frame_size
        for i in range(n):
            rect = pygame.Rect(i * frame_size, 0, frame_size, frame_size)
            if rect.right <= w:
                frames.append(surf.subsurface(rect).copy())

    # If sheet is taller than wide -> vertical strip of square frames
    if h > w:
        n = h // frame_size
        for i in range(n):
            rect = pygame.Rect(0, i * frame_size, frame_size, frame_size)
            if rect.bottom <= h:
                frames.append(surf.subsurface(rect).copy())

    # Fallback: if nothing produced, return the whole surface as single frame
    if not frames:
        return [surf]
    return frames

class SpriteManager:
    """Load and cache scaled & rotated/flipped images for quick rendering."""
    def __init__(self, tile_size):
        self.tile_size = tile_size
        self.cache = {}

    def load_and_prep_snake(self, path):
        surf = pygame.image.load(path).convert_alpha()
        frames = slice_sprite_sheet(surf)
        # pick the first frame as the default head frame
        head = frames[0]
        head = pygame.transform.scale(head, (self.tile_size, self.tile_size))
        # create rotated/flipped versions according to HEAD_BASE_FACING
        oriented = {}
        # map desired direction to rotation angle depending on base facing
        # angles are clockwise degrees used with pygame.transform.rotate
        base = HEAD_BASE_FACING
        # rotation needed to map frame that faces `base` to face requested direction
        rotation_map = {
            'right': { 'right': 0,   'down': 90,  'left': 180, 'up': -90 },
            'left' : { 'left': 0,    'up': 90,    'right': 180,'down': -90 },
            'up'   : { 'up': 0,      'right': 90, 'down': 180, 'left': -90 },
            'down' : { 'down': 0,    'left': 90,  'up': 180,   'right': -90 }
        }
        map_for_base = rotation_map.get(base, rotation_map['right'])
        oriented[DIR_RIGHT] = pygame.transform.rotate(head, map_for_base['right'])
        oriented[DIR_LEFT]  = pygame.transform.rotate(head, map_for_base['left'])
        oriented[DIR_UP]    = pygame.transform.rotate(head, map_for_base['up'])
        oriented[DIR_DOWN]  = pygame.transform.rotate(head, map_for_base['down'])

        # scale rect to tile (rotation can change surface size; re-scale to tile)
        for k in list(oriented.keys()):
            oriented[k] = pygame.transform.smoothscale(oriented[k], (self.tile_size, self.tile_size))

        # prepare a simple body image by taking the head and desaturating slightly or using next frame if sheet exists
        if len(frames) > 1:
            body_base = pygame.transform.scale(frames[1], (self.tile_size, self.tile_size))
        else:
            body_base = head.copy()
        # darken body slightly
        body_surf = body_base.copy()
        body_surf.fill((0, 0, 0, 100), special_flags=pygame.BLEND_RGBA_SUB)
        self.cache['snake_head_oriented'] = oriented
        self.cache['snake_body'] = body_surf

    def load_fruit(self, path):
        surf = pygame.image.load(path).convert_alpha()
        surf = pygame.transform.smoothscale(surf, (self.tile_size, self.tile_size))
        self.cache['fruit'] = surf

    def head_image(self, direction):
        return self.cache['snake_head_oriented'][direction]

    def body_image(self):
        return self.cache['snake_body']

    def fruit_image(self):
        return self.cache['fruit']

# ---------------------------
# Game class (uses sprites)
# ---------------------------
class SnakeGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Retro Snake - WASD (sprites)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 28)

        # sprite manager
        self.spr = SpriteManager(TILE)
        try:
            self.spr.load_and_prep_snake(resource_path(SNAKE_ASSET))
        except Exception as e:
            print("Failed loading snake sprite:", e)
            pygame.quit(); sys.exit(1)
        try:
            self.spr.load_fruit(resource_path(FRUIT_ASSET))
        except Exception as e:
            print("Failed loading fruit sprite:", e)
            pygame.quit(); sys.exit(1)

        self.reset()

    def reset(self):
        mid_x = COLUMNS // 2
        mid_y = ROWS // 2
        self.snake = [(mid_x - i, mid_y) for i in range(INITIAL_LENGTH)]
        self.direction = DIR_RIGHT
        self.next_direction = self.direction
        self.grow_by = 0
        self.score = 0
        self.game_over = False
        occupied = set(self.snake)
        self.fruit = random_free_cell(occupied)

    def handle_input(self):
        keys = pygame.key.get_pressed()
        new_dir = None
        if keys[pygame.K_w]:
            new_dir = DIR_UP
        elif keys[pygame.K_s]:
            new_dir = DIR_DOWN
        elif keys[pygame.K_a]:
            new_dir = DIR_LEFT
        elif keys[pygame.K_d]:
            new_dir = DIR_RIGHT
        if new_dir is not None and new_dir != OPPOSITE.get(self.direction, None):
            self.next_direction = new_dir

    def auto_handle_bounds(self, proposed_head):
        if inside_bounds(proposed_head):
            return self.next_direction
        candidates = []
        for d in (DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT):
            if d == OPPOSITE.get(self.direction):
                continue
            pos = add_tuples(self.snake[0], d)
            if inside_bounds(pos):
                candidates.append(d)
        if not candidates:
            fallback = OPPOSITE.get(self.direction)
            return fallback if fallback else self.direction
        if self.direction in (DIR_LEFT, DIR_RIGHT):
            pref = [d for d in candidates if d in (DIR_UP, DIR_DOWN)]
        else:
            pref = [d for d in candidates if d in (DIR_LEFT, DIR_RIGHT)]
        if pref:
            head_x, head_y = self.snake[0]
            center_x, center_y = COLUMNS // 2, ROWS // 2
            best = None
            best_score = None
            for d in pref:
                nx, ny = head_x + d[0], head_y + d[1]
                score = abs(nx - center_x) + abs(ny - center_y)
                if best is None or score < best_score:
                    best = d
                    best_score = score
            return best
        return random.choice(candidates)

    def spawn_fruit(self):
        occupied = set(self.snake)
        self.fruit = random_free_cell(occupied)

    def update(self):
        if self.game_over:
            return
        self.direction = self.next_direction
        proposed = add_tuples(self.snake[0], self.direction)
        if not inside_bounds(proposed):
            alt_dir = self.auto_handle_bounds(proposed)
            self.direction = alt_dir
            proposed = add_tuples(self.snake[0], self.direction)
        self.snake.insert(0, proposed)
        if proposed in self.snake[1:]:
            self.game_over = True
            return
        if self.fruit is not None and proposed == self.fruit:
            self.score += 1
            self.grow_by += GROW_ON_EAT
            self.spawn_fruit()
        else:
            if self.grow_by > 0:
                self.grow_by -= 1
            else:
                self.snake.pop()

    def render(self):
        self.screen.fill(BG_COLOR)
        # draw fruit
        if self.fruit:
            fx, fy = grid_to_pixel(self.fruit)
            self.screen.blit(self.spr.fruit_image(), (fx, fy))
        # draw body segments (draw body first then head on top)
        body_img = self.spr.body_image()
        for seg in self.snake[1:]:
            px, py = grid_to_pixel(seg)
            self.screen.blit(body_img, (px, py))
        # head
        head_img = self.spr.head_image(self.direction)
        hx, hy = grid_to_pixel(self.snake[0])
        self.screen.blit(head_img, (hx, hy))

        # HUD
        score_surf = self.font.render(f"Score: {self.score}", True, TEXT_COLOR)
        self.screen.blit(score_surf, (8, 8))

        if self.game_over:
            go_surf = self.font.render("GAME OVER - Press R to restart or Esc to quit", True, TEXT_COLOR)
            self.screen.blit(go_surf, (SCREEN_WIDTH//2 - go_surf.get_width()//2, SCREEN_HEIGHT//2 - 12))

        pygame.display.flip()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()
                    if event.key == pygame.K_r and self.game_over:
                        self.reset()
            self.handle_input()
            if not self.game_over:
                self.update()
            self.render()
            self.clock.tick(FPS)

if __name__ == "__main__":
    random.seed()
    game = SnakeGame()
    game.run()
