import pygame; pygame.init()
screen = pygame.display.set_mode((600, 600))
snake_img =pygame.image.load('snakev1.png').convert()




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
    screen.fill((255, 255, 255))
    screen.blit(snake_img,(x,30))
    pygame.display.flip()

pygame.quit()