import pygame; pygame.init()
screen = pygame.display.set_mode((400, 300))
running=True
x=0
while running:
clock = pygame.time.Clock()

delta_time =0.1
x+=50*delta_time

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running=False

pygame.display.flip()
            clock.tick(60)
pygame.quit()