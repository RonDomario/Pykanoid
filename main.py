import pygame
from os.path import join, abspath
from math import sin, pi
import sys


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = abspath(".")
    return join(base_path, relative_path)


class Game:
    pygame.init()
    pygame.mouse.set_visible(False)
    screen_width = 800
    screen_height = 800
    clock = pygame.time.Clock()
    fps = 60
    brick_columns = 10
    brick_rows = 5
    h_spaces = brick_columns + 1
    v_spaces = brick_rows + 1
    space_size = 15
    brick_width = (screen_width - h_spaces * space_size) // brick_columns
    brick_height = (screen_height // 3 - v_spaces * space_size) // brick_rows
    ball_radius = 10
    platform_width = 150
    platform_height = 30
    platform_half = platform_width // 2
    font_score = pygame.font.SysFont('Impact', 30)
    bg_image = pygame.image.load(resource_path('assets/background.png'))
    bg_image = pygame.transform.scale(bg_image, (screen_width, screen_height))
    restart_image = pygame.image.load(resource_path('assets/restart.png'))
    restart_image = pygame.transform.scale(restart_image, (200, 100))

    def __init__(self):
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption('Pykanoid')
        self.game_over = False
        self.restart_button = Button(Game.screen_width // 2, Game.screen_height // 2, Game.restart_image)
        self.score = 0
        self.platform = Platform(Game.screen_width // 2, Game.screen_height - Game.platform_height, "mouse")
        self.ball = Ball(self.platform.rect.centerx, self.platform.rect.top - self.ball_radius * 2)
        self.brick_group = set()
        self.reset()
        self.run = True

    def reset(self):
        self.platform.__init__(Game.screen_width // 2, Game.screen_height - Game.platform_height, "mouse")
        self.ball.__init__(self.platform.rect.centerx, self.platform.rect.top - self.ball_radius * 2)
        self.brick_group.clear()
        x_offset = 0
        y_offset = 50 + Game.space_size
        for _ in range(Game.brick_rows):
            for _ in range(Game.brick_columns):
                x_offset += Game.space_size
                brick = Brick(x_offset, y_offset)
                self.brick_group.add(brick)
                x_offset += Game.brick_width
            x_offset = 0
            y_offset += Game.space_size + Game.brick_height

    def draw_text(self, text, font, text_color, x, y):
        image = font.render(text, True, text_color)
        rect = image.get_rect()
        self.screen.blit(image, (x - rect.width // 2, y - rect.height // 2))

    def mainloop(self):
        while self.run:
            Game.clock.tick(Game.fps)
            self.screen.blit(Game.bg_image, (0, 0))
            if not self.game_over:
                self.platform.control()
                self.score, self.game_over = self.ball.update(self.brick_group, self.platform, self.score,
                                                              self.game_over)
                self.ball.draw(self.screen)
            self.platform.draw(self.screen)
            for brick in self.brick_group:
                brick.draw(self.screen)
            self.draw_text(f'SCORE: {self.score}', Game.font_score, 'black', 60, 20)
            if self.game_over:
                if self.restart_button.draw(self.screen):
                    self.game_over = False
                    self.score = 0
                    self.reset()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False
            pygame.display.update()


class Button:
    def __init__(self, x, y, image_i):
        self.image_i = image_i
        self.image = self.image_i
        self.rect = self.image.get_rect(center=(x, y))
        self.clicked = False

    def draw(self, screen):
        action = False
        pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] and not self.clicked:
                action = True
                self.clicked = True
        if not pygame.mouse.get_pressed()[0]:
            self.clicked = False
        screen.blit(self.image, self.rect)
        return action


class Platform:
    def __init__(self, x, y, control):
        self.image = pygame.image.load(resource_path('assets/platform.png'))
        self.image = pygame.transform.scale(self.image, (Game.platform_width, Game.platform_height))
        self.y = y
        self.rect = self.image.get_rect(center=(x, self.y))
        self.pos = pygame.Vector2(x, self.y)
        self.slow = 4
        self.fast = 8
        self.speed = self.slow
        self.idle_radius = 5
        if control == "mouse":
            self.control = self.mouse
            self.speed = self.slow
        elif control == "keyboard":
            self.control = self.keyboard
            self.speed = self.fast

    def mouse(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        target_pos = pygame.Vector2(mouse_x, self.y)
        direction = target_pos - self.pos
        if direction.length() > self.idle_radius:
            direction = direction.normalize()
            self.pos += direction * self.fast
        self.rect.center = self.pos.x, self.y
        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(Game.screen_width, self.rect.right)

    def keyboard(self):
        key = pygame.key.get_pressed()
        if key[pygame.K_LEFT]:
            self.speed = self.slow
            if key[pygame.K_LSHIFT]:
                self.speed = self.fast
            self.rect.left = max(0, self.rect.left - self.speed)
        if key[pygame.K_RIGHT]:
            self.speed = self.slow
            if key[pygame.K_LSHIFT]:
                self.speed = self.fast
            self.rect.right = min(Game.screen_width, self.rect.right + self.speed)

    def draw(self, screen):
        screen.blit(self.image, self.rect)


class Ball:
    def __init__(self, x, y):
        self.image = pygame.image.load(resource_path('assets/ball.png'))
        self.image = pygame.transform.scale(self.image, (Game.ball_radius * 2, Game.ball_radius * 2))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 6
        self.move_x = self.speed * 0
        self.move_y = self.speed * (-1)
        self.norm_vector_length = 1
        self.angle_min = 30
        self.angle_max = 70
        self.angle_diff = self.angle_max - self.angle_min

    def update(self, brick_group, platform, score, game_over):
        brick_collision = None
        for brick in brick_group:
            if brick.rect.colliderect(self.rect.x + self.move_x,
                                      self.rect.y + self.move_y,
                                      self.rect.width,
                                      self.rect.height):
                brick_collision = brick
                score += 1
                break
        if brick_collision is not None:
            directions = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (-1, -1), (1, -1))
            for (x, y) in directions:
                if brick_collision.rect.colliderect(self.rect.x + abs(self.move_x) * x,
                                                    self.rect.y + abs(self.move_y) * y,
                                                    self.rect.width,
                                                    self.rect.height):
                    if x:
                        self.move_x *= -1
                    if y:
                        self.move_y *= -1
                    brick_group.remove(brick_collision)
                    break
        if self.rect.left <= 0:
            self.rect.left = 0
            self.move_x *= -1
        if self.rect.right >= Game.screen_width:
            self.rect.right = Game.screen_width
            self.move_x *= -1
        if self.rect.top <= 0:
            self.rect.top = 0
            self.move_y *= -1
        if self.rect.bottom >= Game.screen_height:
            game_over = True
        if platform.rect.colliderect(self.rect.x + self.move_x, self.rect.y + self.move_y, self.rect.width,
                                     self.rect.height):
            dist = min(abs(platform.rect.centerx - self.rect.centerx), Game.platform_half)
            ratio = dist / Game.platform_half
            y = self.norm_vector_length * sin((self.angle_min + self.angle_diff * (1 - ratio)) * pi / 180)
            x = (self.norm_vector_length ** 2 - y ** 2) ** 0.5

            self.move_y = - y * self.speed
            if self.rect.centerx >= platform.rect.centerx:
                self.move_x = x * self.speed
            else:
                self.move_x = -x * self.speed
        self.rect.x += self.move_x
        self.rect.y += self.move_y
        return score, game_over

    def draw(self, screen: pygame.Surface):
        screen.blit(self.image, self.rect)


class Brick:
    def __init__(self, x, y):
        self.image = pygame.image.load(resource_path('assets/brick.png'))
        self.image = pygame.transform.scale(self.image, (Game.brick_width, Game.brick_height))
        self.rect = self.image.get_rect()
        self.rect.topleft = x, y

    def draw(self, screen: pygame.Surface):
        screen.blit(self.image, self.rect)


class Menu:
    def __init__(self):
        self.image = pygame.image.load(resource_path('assets/menu.png'))
        self.image = pygame.transform.scale(self.image, (Game.screen_width, Game.screen_height))

    def show_menu(self, screen):
        screen.blit(self.image, (0, 0))


if __name__ == '__main__':
    game = Game()
    game.mainloop()
