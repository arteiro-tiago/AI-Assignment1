import pygame
import random

WIDTH, HEIGHT = 600, 700

class Piece:
    def __init__(self, rank):
        self.rank = rank
        self.color = (100,100,100)
        self.height = 40
        self.width = 100 + (rank * 35)

    def draw(self, screen, x, y, width):
        rect = pygame.Rect(x - width // 2, y, width, self.height)
        pygame.draw.rect(screen, self.color, rect)
        return rect

class Stack:
    def __init__(self, num_pancakes=7):
        self.items = [Piece(i) for i in range(1, num_pancakes + 1)]
        random.shuffle(self.items)
        self.moves = 0

    def flip(self, index):
        portion = self.items[:index + 1]
        self.items[:index + 1] = reversed(portion)

    def draw(self, screen):
        start_y = 150
        for i, piece in enumerate(self.items):
            p_y = start_y + i * piece.height
            piece.draw(screen, WIDTH // 2, p_y, piece.width)

class PancakePuzzle:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.stack = Stack(num_pancakes=8)

    def move(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                start_y = 150
                for i in range(len(self.stack.items)):
                    y_top = start_y + i * 45
                    if y_top <= my <= y_top + 40:
                        self.stack.flip(i)
                        break

    def draw(self):
        self.screen.fill((25,25,25))        
        self.stack.draw(self.screen)
        pygame.display.flip()

    def run(self):
        while True:
            self.move()
            self.draw()

if __name__ == "__main__":
    PancakePuzzle().run()