import pygame; pygame.init()
screen = pygame.display.set_mode((600, 600))
running=True
x=0
clock = pygame.time.Clock()
delta_time = 0.1

while running:
    # update delta_time in seconds and clamp
    delta_time = clock.tick(60) / 1000.0
    delta_time = max(0.001, min(0.1, delta_time))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running=False

    # update logic
    x += 50 * delta_time

    # render
    screen.fill((0, 0, 0))
    pygame.draw.circle(screen, (255, 0, 0), (int(x) % 600, 300), 20)
    pygame.display.flip()

pygame.quit()