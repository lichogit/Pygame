import pygame
import random
import sys

# ---------------------------
# Configuration
# ---------------------------
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
TILE = 20                     # grid cell size in pixels
COLUMNS = SCREEN_WIDTH // TILE
ROWS = SCREEN_HEIGHT // TILE

FPS = 10                      # base speed (frames per second)
GROW_ON_EAT = 1               # how many segments to grow when eating
INITIAL_LENGTH = 4

# Colors
BG_COLOR = (30, 30, 30)
SNAKE_COLOR = (0, 200, 0)
SNAKE_HEAD_COLOR = (0, 255, 100)
FRUIT_COLOR = (200, 40, 40)
TEXT_COLOR = (240, 240, 240)

# ---------------------------
# Directions (dx, dy in grid units)
# ---------------------------
DIR_UP = (0, -1)
DIR_DOWN = (0, 1)
DIR_LEFT = (-1, 0)
DIR_RIGHT = (1, 0)
OPPOSITE = {DIR_UP: DIR_DOWN, DIR_DOWN: DIR_UP, DIR_LEFT: DIR_RIGHT, DIR_RIGHT: DIR_LEFT}

# ---------------------------
# Utility helpers
# ---------------------------
def grid_to_pixel(pos):
    """Convert grid (col,row) to pixel coordinates (x,y)."""
    return pos[0] * TILE, pos[1] * TILE

def random_free_cell(occupied):
    """Return a random (col,row) not in occupied set."""
    all_cells = [(x, y) for x in range(COLUMNS) for y in range(ROWS)]
    free = [c for c in all_cells if c not in occupied]
    if not free:
        return None
    return random.choice(free)

def add_tuples(a, b):
    return a[0] + b[0], a[1] + b[1]

def inside_bounds(pos):
    x, y = pos
    return 0 <= x < COLUMNS and 0 <= y < ROWS

# ---------------------------
# Game class
# ---------------------------
class SnakeGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Retro Snake - WASD controls")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 28)

        self.reset()

    def reset(self):
        # Start snake in the center moving to the right
        mid_x = COLUMNS // 2
        mid_y = ROWS // 2
        self.snake = [(mid_x - i, mid_y) for i in range(INITIAL_LENGTH)]
        self.direction = DIR_RIGHT
        self.next_direction = self.direction
        self.grow_by = 0
        self.score = 0
        self.game_over = False

        occupied = set(self.snake)
        fruit_cell = random_free_cell(occupied)
        self.fruit = fruit_cell

    def handle_input(self):
        # Map keys to directions. Prevent immediate reversal.
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
            # set next_direction (will apply on the next tick)
            self.next_direction = new_dir

    def auto_handle_bounds(self, proposed_head):
        """
        If the proposed head would be out of bounds, pick an alternate valid direction.
        Strategy:
        - Collect candidate directions that keep the head inside and are not the immediate reverse.
        - Prefer continuing axis if possible; otherwise pick a random candidate.
        """
        if inside_bounds(proposed_head):
            return self.next_direction  # still valid

        # find all valid candidate directions
        candidates = []
        for d in (DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT):
            if d == OPPOSITE.get(self.direction):
                continue  # disallow immediate reversal
            pos = add_tuples(self.snake[0], d)
            if inside_bounds(pos):
                candidates.append(d)

        if not candidates:
            # no valid moves (shouldn't happen on this board size), allow reverse as fallback
            fallback = OPPOSITE.get(self.direction)
            return fallback if fallback else self.direction

        # Heuristics: prefer perpendicular directions that move away from the edge.
        # Example: if we tried to move right and hit edge, prefer up/down.
        # We'll implement a simple preference then random choice among remaining.
        if self.direction in (DIR_LEFT, DIR_RIGHT):
            pref = [d for d in candidates if d in (DIR_UP, DIR_DOWN)]
        else:
            pref = [d for d in candidates if d in (DIR_LEFT, DIR_RIGHT)]

        chosen = None
        if pref:
            # pick the one that moves toward the board center if possible
            head_x, head_y = self.snake[0]
            center_x, center_y = COLUMNS // 2, ROWS // 2
            # score candidates by closeness to center after moving
            best = None
            best_score = None
            for d in pref:
                nx, ny = head_x + d[0], head_y + d[1]
                score = abs(nx - center_x) + abs(ny - center_y)
                if best is None or score < best_score:
                    best = d
                    best_score = score
            chosen = best
        else:
            chosen = random.choice(candidates)

        return chosen

    def spawn_fruit(self):
        occupied = set(self.snake)
        pos = random_free_cell(occupied)
        self.fruit = pos

    def update(self):
        if self.game_over:
            return

        # apply queued direction change (if any)
        self.direction = self.next_direction

        # compute proposed head
        proposed = add_tuples(self.snake[0], self.direction)

        # if proposed is out of bounds, choose an automatic valid direction
        if not inside_bounds(proposed):
            # get a new direction that keeps us inside
            alt_dir = self.auto_handle_bounds(proposed)
            self.direction = alt_dir
            # recompute proposed head
            proposed = add_tuples(self.snake[0], self.direction)

        # move snake: insert new head
        self.snake.insert(0, proposed)

        # check self-collision
        if proposed in self.snake[1:]:
            self.game_over = True
            return

        # handle fruit collision
        if self.fruit is not None and proposed == self.fruit:
            self.score += 1
            self.grow_by += GROW_ON_EAT
            self.spawn_fruit()
        else:
            if self.grow_by > 0:
                self.grow_by -= 1  # keep tail to grow
            else:
                self.snake.pop()  # remove tail segment

    def draw_grid(self):
        # optional: draw light grid lines for retro feel (comment out if not desired)
        for x in range(0, SCREEN_WIDTH, TILE):
            pygame.draw.line(self.screen, (40, 40, 40), (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, TILE):
            pygame.draw.line(self.screen, (40, 40, 40), (0, y), (SCREEN_WIDTH, y))

    def render(self):
        self.screen.fill(BG_COLOR)

        # draw fruit
        if self.fruit:
            fx, fy = grid_to_pixel(self.fruit)
            rect = pygame.Rect(fx, fy, TILE, TILE)
            pygame.draw.ellipse(self.screen, FRUIT_COLOR, rect)

        # draw snake segments
        for i, seg in enumerate(self.snake):
            px, py = grid_to_pixel(seg)
            rect = pygame.Rect(px, py, TILE, TILE)
            color = SNAKE_HEAD_COLOR if i == 0 else SNAKE_COLOR
            pygame.draw.rect(self.screen, color, rect.inflate(-2, -2))  # slight padding for visual

        # HUD
        score_surf = self.font.render(f"Score: {self.score}", True, TEXT_COLOR)
        self.screen.blit(score_surf, (8, 8))

        if self.game_over:
            go_surf = self.font.render("GAME OVER - Press R to restart or Esc to quit", True, TEXT_COLOR)
            self.screen.blit(go_surf, (SCREEN_WIDTH//2 - go_surf.get_width()//2, SCREEN_HEIGHT//2 - 12))

        pygame.display.flip()

    def run(self):
        while True:
            # event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if event.key == pygame.K_r and self.game_over:
                        self.reset()

            # keyboard continuous input (WASD)
            self.handle_input()

            # update and render
            if not self.game_over:
                self.update()

            self.render()
            # maintain consistent speed; you can change FPS to make snake faster/slower
            self.clock.tick(FPS)

# ---------------------------
# Entry point
# ---------------------------
if __name__ == "__main__":
    random.seed()  # system random
    game = SnakeGame()
    game.run()
