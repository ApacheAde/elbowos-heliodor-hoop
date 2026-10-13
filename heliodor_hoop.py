#!/usr/bin/env python3
"""Heliodor Hoop — neon gravity basketball arcade for ElbowOS. Python 3 + pygame."""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/HELIODOR_HOOP_ElbowOS.mp4")
TITLE, HANDLE = "HELIODOR HOOP", "x.com/ElbowOS"
VOID, INK, GOLD, AMBER = (12, 6, 28), (22, 12, 48), (255, 200, 40), (255, 140, 30)
CYAN, MAG, WHITE, LIME, ROSE = (40, 220, 255), (255, 60, 180), (240, 245, 255), (100, 255, 120), (255, 80, 100)
NAVY = (18, 10, 40)

class Game:
    def __init__(self):
        pygame.init(); pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.quit(); pygame.display.init()
            self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(TITLE)
        self.font_lg = pygame.font.SysFont("DejaVu Sans", 64, bold=True)
        self.font = pygame.font.SysFont("DejaVu Sans", 40, bold=True)
        self.font_sm = pygame.font.SysFont("DejaVu Sans", 28)
        self.clock = pygame.time.Clock()
        self.score = self.combo = self.t = self.flash = 0
        self.launcher_x = W // 2
        self.aim = 0.0
        self.balls = []
        self.hoops = []
        self.platforms = []
        self.sparks = []
        self.pop, self.pop_t = "", 0
        self.shoot_cd = 0
        for i in range(3):
            self.hoops.append({
                "x": random.randint(200, W-200),
                "y": 480 + i * 280,
                "w": 160 + random.randint(-20, 40),
                "vx": random.choice([-2.2, -1.6, 1.6, 2.2]),
                "scored": False
            })
        for y in (900, 1300, 1600):
            self.platforms.append([random.randint(100, W-300), y, random.randint(180, 320), 18])

    def burst(self, x, y, col, n=12):
        for _ in range(n):
            a = random.uniform(0, 6.2832)
            sp = random.uniform(2, 9)
            self.sparks.append([x, y, math.cos(a)*sp, math.sin(a)*sp, 18, col])

    def shoot(self, power=14.0, tilt=0.0):
        vx = tilt * 3.2 + random.uniform(-0.4, 0.4)
        vy = -power
        self.balls.append([self.launcher_x, H-180, vx, vy, True])
        self.shoot_cd = 12

    def autoplay(self):
        target = min(self.hoops, key=lambda h: abs(h["x"] - self.launcher_x) + (200 if h.get("scored") else 0))
        want = target["x"]
        self.launcher_x += max(-6, min(6, (want - self.launcher_x) * 0.18))
        self.aim = max(-1.2, min(1.2, (target["x"] - self.launcher_x) * 0.012))
        if self.shoot_cd <= 0 and random.random() < 0.35:
            self.shoot(power=random.uniform(13.5, 16.5), tilt=self.aim)
        self.shoot_cd = max(0, self.shoot_cd - 1)

    def tick(self):
        self.t += 1
        self.flash = max(0, self.flash - 1)
        self.pop_t = max(0, self.pop_t - 1)
        for h in self.hoops:
            h["x"] += h["vx"]
            if h["x"] < 120 or h["x"] > W - 120 - h["w"]:
                h["vx"] *= -1
            h["scored"] = False
        for b in self.balls:
            if not b[4]: continue
            b[3] += 0.38
            b[0] += b[2]; b[1] += b[3]
            if b[0] < 30: b[0], b[2] = 30, abs(b[2]) * 0.7
            if b[0] > W-30: b[0], b[2] = W-30, -abs(b[2]) * 0.7
            for px, py, pw, ph in self.platforms:
                if py < b[1] < py + ph + 8 and px < b[0] < px + pw and b[3] > 0:
                    b[1] = py - 2
                    b[3] = -abs(b[3]) * 0.72
                    b[2] *= 0.92
            for h in self.hoops:
                if abs(b[1] - h["y"]) < 22 and h["x"] < b[0] < h["x"] + h["w"] and b[3] > 1.5 and not h["scored"]:
                    self.score += 100 + self.combo * 20
                    self.combo += 1
                    self.flash = 8
                    self.pop, self.pop_t = "SWISH!", 14
                    self.burst(b[0], b[1], GOLD, 16)
                    h["scored"] = True
                    b[4] = False
            if b[1] > H + 40:
                b[4] = False
                self.combo = 0
        self.balls = [b for b in self.balls if b[4]]
        for s in self.sparks:
            s[0] += s[2]; s[1] += s[3]; s[3] += 0.15; s[4] -= 1
        self.sparks = [s for s in self.sparks if s[4] > 0]
        self.launcher_x = max(80, min(W-80, self.launcher_x))

    def draw(self, surf):
        surf.fill(VOID)
        for i in range(12):
            c = (18 + i*2, 8 + i, 42 + i*3)
            pygame.draw.rect(surf, c, (0, i*160, W, 160))
        for px, py, pw, ph in self.platforms:
            pygame.draw.rect(surf, NAVY, (px, py, pw, ph))
            pygame.draw.rect(surf, CYAN, (px, py, pw, 4))
        for h in self.hoops:
            hx, hy, hw = int(h["x"]), int(h["y"]), int(h["w"])
            pygame.draw.rect(surf, MAG, (hx, hy-6, hw, 12), 3)
            pygame.draw.line(surf, CYAN, (hx, hy), (hx, hy+40), 3)
            pygame.draw.line(surf, CYAN, (hx+hw, hy), (hx+hw, hy+40), 3)
            pygame.draw.arc(surf, AMBER, (hx+20, hy-30, hw-40, 50), 0.2, 2.9, 4)
        for b in self.balls:
            pygame.draw.circle(surf, GOLD, (int(b[0]), int(b[1])), 22)
            pygame.draw.circle(surf, AMBER, (int(b[0])-5, int(b[1])-6), 8)
        for s in self.sparks:
            pygame.draw.circle(surf, s[5], (int(s[0]), int(s[1])), max(2, s[4]//4))
        lx = int(self.launcher_x)
        pygame.draw.rect(surf, INK, (lx-40, H-160, 80, 50))
        pygame.draw.polygon(surf, GOLD, [(lx-18, H-160), (lx+18, H-160), (lx, H-200)])
        pygame.draw.circle(surf, WHITE, (lx, H-130), 12)
        if self.flash:
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((255, 200, 40, 32)); surf.blit(ov, (0, 0))
        if self.pop_t:
            lab = self.font_lg.render(self.pop, True, LIME)
            surf.blit(lab, lab.get_rect(center=(W//2, 360)))
        title = self.font_lg.render(TITLE, True, GOLD)
        surf.blit(title, title.get_rect(center=(W//2, 80)))
        sub = self.font_sm.render(HANDLE, True, MAG)
        surf.blit(sub, sub.get_rect(center=(W//2, 140)))
        sc = self.font.render(f"SCORE  {self.score}", True, WHITE)
        cb = self.font_sm.render(f"COMBO  x{self.combo}", True, CYAN)
        hint = self.font_sm.render("A/D move   SPACE shoot", True, AMBER)
        surf.blit(sc, sc.get_rect(center=(W//2, H-120)))
        surf.blit(cb, cb.get_rect(center=(W//2, H-70)))
        surf.blit(hint, hint.get_rect(center=(W//2, H-30)))

    def play_interactive(self):
        running = True
        while running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_SPACE and self.shoot_cd <= 0:
                    self.shoot(power=15.0, tilt=self.aim)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]: self.launcher_x -= 7
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.launcher_x += 7
            self.shoot_cd = max(0, self.shoot_cd - 1)
            self.tick()
            self.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

    def record(self):
        frames = FPS * SECS
        cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
               "-crf", "20", "-preset", "fast", "-movflags", "+faststart", OUT]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        canvas = pygame.Surface((W, H))
        try:
            for i in range(frames):
                self.autoplay()
                self.tick()
                self.draw(canvas)
                proc.stdin.write(pygame.image.tostring(canvas, "RGB"))
                if i % 30 == 0:
                    print(f"frame {i}/{frames}", flush=True)
        finally:
            proc.stdin.close()
            err = proc.stderr.read().decode("utf-8", "ignore")
            rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1500:]}")
        print("wrote", OUT)
        pygame.quit()

def main():
    g = Game()
    if PLAY and not RECORD:
        g.play_interactive()
    else:
        g.record()

if __name__ == "__main__":
    main()
