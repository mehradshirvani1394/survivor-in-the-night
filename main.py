import pygame, sys, random
from pygame.math import Vector2

# تنظیمات
WIDTH, HEIGHT = 800, 600
FPS = 60
PLAYER_SPEED = 300
BULLET_SPEED = 500
ROCKET_SPEED = 300
ZOMBIE_SPEED = 100
PLAYER_MAX_HP = 5
WAVE_SIZE = 5

# کلاس‌ها
class Explosion(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.frames = []
        self.max_radius = 50
        for r in range(5, self.max_radius+1, 5):
            surface = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(surface, (255,150,0, 255 - r*4), (r,r), r)
            self.frames.append(surface)
        self.index = 0
        self.image = self.frames[self.index]
        self.rect = self.image.get_rect(center=pos)
        self.frame_time = 30  # ms
        self.last_update = pygame.time.get_ticks()

    def update(self, dt):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_time:
            self.index += 1
            if self.index >= len(self.frames):
                self.kill()
            else:
                self.image = self.frames[self.index]
                self.rect = self.image.get_rect(center=self.rect.center)
                self.last_update = now

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, vel, rocket=False):
        super().__init__()
        size = 16 if rocket else 8
        self.image = pygame.Surface((size, size))
        self.image.fill((255,0,255) if rocket else (255,255,0))
        self.rect = self.image.get_rect(center=(x, y))
        self.vel = vel
        self.rocket = rocket

    def update(self, dt, zombies, kill_count, explosions_group):
        self.rect.x += self.vel.x * dt / 1000
        self.rect.y += self.vel.y * dt / 1000

        if self.rect.bottom < 0 or self.rect.top > HEIGHT or self.rect.right < 0 or self.rect.left > WIDTH:
            self.kill()

        hits = pygame.sprite.spritecollide(self, zombies, False)
        for z in hits:
            if self.rocket:
                # انفجار موشک: آسیب به زامبی‌های نزدیک
                explosions_group.add(Explosion(self.rect.center))
                for z2 in zombies:
                    if Vector2(self.rect.center).distance_to(z2.rect.center) < 50:
                        z2.hp -= 2
                        if z2.hp <= 0:
                            z2.kill()
                            kill_count[0] += 1
            else:
                z.hp -= 1
                if z.hp <= 0:
                    z.kill()
                    kill_count[0] += 1
            self.kill()

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((32,32))
        self.image.fill((0,255,0))
        self.rect = self.image.get_rect(center=(x, y))
        self.vel = Vector2(0,0)
        self.hp = PLAYER_MAX_HP
        self.shoot_cooldown = 300
        self.last_shot = 0
        self.invincible_timer = 0
        self.shoot_mode = 1  # 1 تیر، 2 تیر، 3 تیر، موشک

    def update(self, dt, keys, bullets, explosions_group):
        self.vel = Vector2(0,0)
        if keys[pygame.K_w]: self.vel.y=-PLAYER_SPEED*dt/1000
        if keys[pygame.K_s]: self.vel.y=PLAYER_SPEED*dt/1000
        if keys[pygame.K_a]: self.vel.x=-PLAYER_SPEED*dt/1000
        if keys[pygame.K_d]: self.vel.x=PLAYER_SPEED*dt/1000
        self.rect.center += self.vel

        # تغییر مود شلیک با Q
        if keys[pygame.K_q]:
            self.shoot_mode += 1
            if self.shoot_mode > 4:
                self.shoot_mode = 1
            pygame.time.wait(150)

        # شلیک
        if keys[pygame.K_SPACE]:
            now = pygame.time.get_ticks()
            if now - self.last_shot > self.shoot_cooldown:
                self.shoot(bullets)
                self.last_shot = now

        if self.invincible_timer > 0:
            self.invincible_timer -= dt

    def shoot(self, bullets):
        if self.shoot_mode == 1:
            bullets.add(Bullet(self.rect.centerx, self.rect.centery, Vector2(0,-BULLET_SPEED)))
        elif self.shoot_mode == 2:
            bullets.add(Bullet(self.rect.centerx-10, self.rect.centery, Vector2(-100,-BULLET_SPEED).normalize()*BULLET_SPEED))
            bullets.add(Bullet(self.rect.centerx+10, self.rect.centery, Vector2(100,-BULLET_SPEED).normalize()*BULLET_SPEED))
        elif self.shoot_mode == 3:
            bullets.add(Bullet(self.rect.centerx, self.rect.centery, Vector2(0,-BULLET_SPEED)))
            bullets.add(Bullet(self.rect.centerx-10, self.rect.centery, Vector2(-150,-BULLET_SPEED).normalize()*BULLET_SPEED))
            bullets.add(Bullet(self.rect.centerx+10, self.rect.centery, Vector2(150,-BULLET_SPEED).normalize()*BULLET_SPEED))
        elif self.shoot_mode == 4:
            bullets.add(Bullet(self.rect.centerx, self.rect.centery, Vector2(0,-ROCKET_SPEED), rocket=True))

class Zombie(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((32,32))
        self.image.fill((255,0,0))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = ZOMBIE_SPEED
        self.hp = 3

    def update(self, dt, player):
        direction = Vector2(player.rect.centerx - self.rect.centerx, player.rect.centery - self.rect.centery)
        if direction.length() > 0:
            direction = direction.normalize()
            self.rect.centerx += direction.x * self.speed * dt / 1000
            self.rect.centery += direction.y * self.speed * dt / 1000

def spawn_wave(zombies, num):
    for _ in range(num):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT//2)
        zombies.add(Zombie(x, y))

def game_over_screen(screen, kill_count, wave_number):
    font = pygame.font.SysFont(None, 48)
    small_font = pygame.font.SysFont(None, 36)
    screen.fill((50,0,0))
    txt1 = font.render("YOU DIED!", True, (255,255,255))
    txt2 = small_font.render(f"Kills: {kill_count}", True, (255,255,255))
    txt3 = small_font.render(f"Wave reached: {wave_number}", True, (255,255,255))
    txt4 = small_font.render("Press ESC to exit", True, (255,255,255))
    screen.blit(txt1, (WIDTH//2 - txt1.get_width()//2, HEIGHT//2 - 100))
    screen.blit(txt2, (WIDTH//2 - txt2.get_width()//2, HEIGHT//2 - 40))
    screen.blit(txt3, (WIDTH//2 - txt3.get_width()//2, HEIGHT//2))
    screen.blit(txt4, (WIDTH//2 - txt4.get_width()//2, HEIGHT//2 + 60))
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    waiting = False

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Shooter Simple")
    clock = pygame.time.Clock()

    player = Player(WIDTH//2, HEIGHT-50)
    player_group = pygame.sprite.Group(player)
    bullets = pygame.sprite.Group()
    zombies = pygame.sprite.Group()
    explosions = pygame.sprite.Group()

    kill_count = [0]
    wave_number = 1

    spawn_wave(zombies, WAVE_SIZE)

    running = True
    while running:
        dt = clock.tick(FPS)
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        player.update(dt, keys, bullets, explosions)
        bullets.update(dt, zombies, kill_count, explosions)
        explosions.update(dt)
        for z in zombies:
            z.update(dt, player)

        hits = pygame.sprite.spritecollide(player, zombies, False)
        if hits and player.invincible_timer <= 0:
            player.hp -= 1
            player.invincible_timer = 1000
            if player.hp <= 0:
                running = False

        if len(zombies) == 0:
            wave_number += 1
            spawn_wave(zombies, WAVE_SIZE + wave_number)

        screen.fill((20,20,30))
        player_group.draw(screen)
        bullets.draw(screen)
        zombies.draw(screen)
        explosions.draw(screen)

        # نوار سلامتی
        bar_width = 200
        bar_height = 20
        fill = (player.hp / PLAYER_MAX_HP) * bar_width
        pygame.draw.rect(screen, (255,0,0), (10,10,bar_width,bar_height))
        pygame.draw.rect(screen, (0,255,0), (10,10,fill,bar_height))
        pygame.draw.rect(screen, (255,255,255), (10,10,bar_width,bar_height), 2)

        font = pygame.font.SysFont(None,28)
        txt_kills = font.render(f'Kills: {kill_count[0]}', True, (255,255,255))
        txt_wave = font.render(f'Wave: {wave_number}', True, (255,255,255))
        txt_mode = font.render(f'Mode: {player.shoot_mode}', True, (255,255,255))
        screen.blit(txt_kills,(10,40))
        screen.blit(txt_wave,(10,70))
        screen.blit(txt_mode,(10,100))

        pygame.display.flip()

    # صفحه پایان بازی
    game_over_screen(screen, kill_count[0], wave_number)
    pygame.quit()
    sys.exit()

if __name__=="__main__":
    main()
