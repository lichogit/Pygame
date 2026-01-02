import pygame
import random
import os
import sys

# -----------------------------
# CONFIG
# -----------------------------
WIDTH, HEIGHT = 600, 600
CELL_SIZE = 32
FPS = 10

SNAKE_SPRITE_PATH = "snakeog.png"
FRUIT_SPRITE_PATH = "pineapple.png"

# Index of the frame in the sprite sheet that is the HEAD
HEAD_FRAME_INDEX = 0

# Direction constants
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# -----------------------------
# INITIALIZE
# -----------------------------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Retro Snake")
clock = pygame.time.Clock()

# -----------------------------
# SPRITE LOADING
# -----------------------------
def slice_sprite_sheet(surface):
    """Slice square frames from a vertical or horizontal sprite sheet."""
    w, h = surface.get_size()
    frame_size = min(w, h)
    frames = []

    if h > w:  # vertical sheet
        for y in range(0, h, frame_size):
            if y + frame_size <= h:
                frames.append(surface.subsurface((0, y, frame_size, frame_size)).copy())
    else:  # horizontal sheet
        for x in range(0, w, frame_size):
            if x + frame_size <= w:
                frames.append(surface.subsurface((x, 0, frame_size, frame_size)).copy())

    return frames if frames else [surface]

# Load snake sprites
snake_sheet = pygame.image.load(SNAKE_SPRITE_PATH).convert_alpha()
snake_frames = slice_sprite_sheet(snake_sheet)

snake_head_base = pygame.transform.scale(
    snake_frames[HEAD_FRAME_INDEX], (CELL_SIZE, CELL_SIZE)
)

snake_head_images = {
    UP: snake_head_base,
    RIGHT: pygame.transform.rotate(snake_head_base, -90),
    DOWN: pygame.transform.rotate(snake_head_base, 180),
    LEFT: pygame.transform.rotate(snake_head_base, 90),
}

snake_body_image = snake_head_images[UP]

# Load fruit
fruit_image = pygame.image.load(FRUIT_SPRITE_PATH).convert_alpha()
fruit_image = pygame.transform.scale(fruit_image, (CELL_SIZE, CELL_SIZE))

# -----------------------------
# GAME STATE
# -----------------------------
snake = [(WIDTH // 2, HEIGHT // 2)]
direction = RIGHT
pending_direction = RIGHT

def random_grid_position():
    x = random.randrange(0, WIDTH, CELL_SIZE)
    y = random.randrange(0, HEIGHT, CELL_SIZE)
    return (x, y)

fruit_pos = random_grid_position()

# -----------------------------
# GAME LOOP
# -----------------------------
running = True
while running:
    clock.tick(FPS)

    # -------------------------
    # INPUT
    # -------------------------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w and direction != DOWN:
                pending_direction = UP
            elif event.key == pygame.K_s and direction != UP:
                pending_direction = DOWN
            elif event.key == pygame.K_a and direction != RIGHT:
                pending_direction = LEFT
            elif event.key == pygame.K_d and direction != LEFT:
                pending_direction = RIGHT

    direction = pending_direction

    # -------------------------
    # MOVE SNAKE
    # -------------------------
    head_x, head_y = snake[0]
    dx, dy = direction
    new_head = (head_x + dx * CELL_SIZE, head_y + dy * CELL_SIZE)

    # Auto-redirect if hitting bounds
    if new_head[0] < 0:
        direction = RIGHT
    elif new_head[0] >= WIDTH:
        direction = LEFT
    elif new_head[1] < 0:
        direction = DOWN
    elif new_head[1] >= HEIGHT:
        direction = UP

    dx, dy = direction
    new_head = (head_x + dx * CELL_SIZE, head_y + dy * CELL_SIZE)

    snake.insert(0, new_head)

    # -------------------------
    # FRUIT COLLISION
    # -------------------------
    if new_head == fruit_pos:
        fruit_pos = random_grid_position()
    else:
        snake.pop()

    # -------------------------
    # DRAW
    # -------------------------
    screen.fill((20, 20, 20))

    # Draw fruit
    screen.blit(fruit_image, fruit_pos)

    # Draw snake
    for i, segment in enumerate(snake):
        if i == 0:
            screen.blit(snake_head_images[direction], segment)
        else:
            screen.blit(snake_body_image, segment)

    pygame.display.flip()

pygame.quit()
sys.exit()
