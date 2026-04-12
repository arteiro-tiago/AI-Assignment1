import pygame
import random
import math
import pancake_brain as pb


# ──────────────────────────────────────────────
#  Constants Screen
# ──────────────────────────────────────────────
WIDTH, HEIGHT = 640, 720
FPS = 60


# ──────────────────────────────────────────────
#  Colors
# ──────────────────────────────────────────────
BACKGROUND_COLOR = (15,  15,  20)
PANEL_COLOR = (25,  25,  35)
ACCENT = (255, 180,  50)   
ACCENT_DIM = (180, 120,  30)
TEXT_COLOR = (230, 230, 230)
TEXT_DIM = (140, 140, 155)
BTN_COLOR = (40,  40,  55)
BTN_HOVER = (60,  60,  80)
BTN_BORDER = (80,  80, 110)
SUCCESS_COLOR = (80, 210, 130)
DANGER_COLOR = (220,  80,  80)
FLIP_HIGHLIGHT = (255, 220, 100, 80)  


# ──────────────────────────────────────────────
# Atribuir cor a cada panqueca
# ──────────────────────────────────────────────

def pancake_color(rank, n_total, selected=False, flipping=False):
    t = (rank - 1) / max(n_total - 1, 1) # Evitar divisão por 0
    r = int(60  + t * 195)
    g = int(100 + t * 80)
    b = int(200 - t * 150)
    if flipping: 
        return (min(r + 80, 255), min(g + 60, 255), min(b + 20, 255)) # não implementado
    if selected:
        return (min(r + 50, 255), min(g + 40, 255), min(b + 10, 255)) # Cursor sobre a panqueca clarifica a sua cor
    return (r, g, b)


# ──────────────────────────────────────────────
#  Geometry helpers
# ──────────────────────────────────────────────
STACK_TOP_Y  = 160
STACK_AREA_H = 430          # vertical space dedicated to pancakes
MIN_PANCAKE_H = 14
MAX_PANCAKE_H = 52

MIN_PANCAKE_W_RATIO = 0.18  # smallest pancake = 18 % of WIDTH
MAX_PANCAKE_W_RATIO = 0.72  # largest pancake  = 72 % of WIDTH


def compute_geometry(n):
    """Return (pancake_h, w_step) for n pancakes."""
    usable = STACK_AREA_H - 10
    h = max(MIN_PANCAKE_H, min(MAX_PANCAKE_H, usable // n))
    w_step = (MAX_PANCAKE_W_RATIO - MIN_PANCAKE_W_RATIO) * WIDTH / max(n - 1, 1)
    return h, w_step


def pancake_rect(rank, n, h, w_step, y):
    min_w = int(MIN_PANCAKE_W_RATIO * WIDTH)
    w = int(min_w + (rank - 1) * w_step)
    x = WIDTH // 2 - w // 2
    return pygame.Rect(x, y, w, h)


# ──────────────────────────────────────────────
#  UI Widgets
# ──────────────────────────────────────────────
class Button:
    def __init__(self, rect, label, accent=False):
        self.rect   = pygame.Rect(rect)
        self.label  = label
        self.accent = accent
        self._hover = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self._hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, surface, font):
        fill = ACCENT if (self.accent and self._hover) else \
               ACCENT_DIM if self.accent else \
               BTN_HOVER if self._hover else BTN_COLOR
        pygame.draw.rect(surface, fill, self.rect, border_radius=10)
        pygame.draw.rect(surface, BTN_BORDER if not self.accent else ACCENT,
                         self.rect, 1, border_radius=10)
        tc = BACKGROUND_COLOR if self.accent else TEXT_COLOR
        txt = font.render(self.label, True, tc)
        surface.blit(txt, txt.get_rect(center=self.rect.center))


class Slider:
    def __init__(self, x, y, w, min_v, max_v, value, label):
        self.x, self.y, self.w = x, y, w
        self.min_v, self.max_v = min_v, max_v
        self.value = value
        self.label = label
        self._dragging = False
        self.track = pygame.Rect(x, y + 10, w, 4)
        self._update_knob()

    def _update_knob(self):
        t = (self.value - self.min_v) / (self.max_v - self.min_v)
        kx = self.x + int(t * self.w)
        self.knob = pygame.Rect(kx - 9, self.y + 1, 18, 22)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.knob.collidepoint(event.pos) or self.track.collidepoint(event.pos):
                self._dragging = True
        if event.type == pygame.MOUSEBUTTONUP:
            self._dragging = False
        if event.type == pygame.MOUSEMOTION and self._dragging:
            t = max(0, min(1, (event.pos[0] - self.x) / self.w))
            self.value = self.min_v + int(round(t * (self.max_v - self.min_v)))
            self._update_knob()

    def draw(self, surface, font_sm):
        pygame.draw.rect(surface, BTN_COLOR, self.track, border_radius=2)
        t = (self.value - self.min_v) / (self.max_v - self.min_v)
        filled = pygame.Rect(self.x, self.y + 10, int(t * self.w), 4)
        pygame.draw.rect(surface, ACCENT, filled, border_radius=2)
        pygame.draw.rect(surface, ACCENT, self.knob, border_radius=5)
        lbl = font_sm.render(f"{self.label}  {self.value}", True, TEXT_DIM)
        surface.blit(lbl, (self.x, self.y - 22))


# ──────────────────────────────────────────────
#  Dropdown (algorithm / heuristic)
# ──────────────────────────────────────────────
class Dropdown:
    def __init__(self, x, y, w, h, options, label):
        self.rect    = pygame.Rect(x, y, w, h)
        self.options = options
        self.label   = label
        self.index   = 0
        self.open    = False

    @property
    def value(self):
        return self.options[self.index]

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.open = not self.open
                return
            if self.open:
                for i, opt in enumerate(self.options):
                    item_rect = pygame.Rect(self.rect.x,
                                            self.rect.bottom + i * self.rect.h,
                                            self.rect.w, self.rect.h)
                    if item_rect.collidepoint(event.pos):
                        self.index = i
                        self.open  = False
                        return
                self.open = False

    def draw(self, surface, font_sm, font_tiny):
        # Header
        pygame.draw.rect(surface, BTN_COLOR, self.rect, border_radius=6)
        pygame.draw.rect(surface, BTN_BORDER, self.rect, 1, border_radius=6)
        lbl = font_tiny.render(self.label, True, TEXT_DIM)
        surface.blit(lbl, (self.rect.x, self.rect.y - 18))
        val = font_sm.render(self.value, True, TEXT_COLOR)
        surface.blit(val, val.get_rect(midleft=(self.rect.x + 10, self.rect.centery)))
        arrow = "▲" if self.open else "▼"
        arr = font_tiny.render(arrow, True, TEXT_DIM)
        surface.blit(arr, arr.get_rect(midright=(self.rect.right - 8, self.rect.centery)))
        if self.open:
            for i, opt in enumerate(self.options):
                ir = pygame.Rect(self.rect.x, self.rect.bottom + i * self.rect.h,
                                 self.rect.w, self.rect.h)
                col = BTN_HOVER if i == self.index else PANEL_COLOR
                pygame.draw.rect(surface, col, ir)
                pygame.draw.rect(surface, BTN_BORDER, ir, 1)
                t = font_sm.render(opt, True, ACCENT if i == self.index else TEXT_COLOR)
                surface.blit(t, t.get_rect(midleft=(ir.x + 10, ir.centery)))


# ──────────────────────────────────────────────
#  Particle system (win screen)
# ──────────────────────────────────────────────
class Particle:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x  = random.randint(0, WIDTH)
        self.y  = random.randint(-20, HEIGHT // 2)
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = random.uniform(1, 4)
        self.r  = random.randint(4, 10)
        self.color = random.choice([ACCENT, SUCCESS_COLOR, (180, 140, 255), (255, 100, 150)])
        self.life = 1.0
        self.decay = random.uniform(0.005, 0.015)

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vy += 0.08
        self.life -= self.decay
        if self.life <= 0 or self.y > HEIGHT + 20:
            self.reset()

    def draw(self, surface):
        alpha = int(self.life * 255)
        s = pygame.Surface((self.r * 2, self.r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (self.r, self.r), self.r)
        surface.blit(s, (int(self.x - self.r), int(self.y - self.r)))


# ──────────────────────────────────────────────
#  Main game class
# ──────────────────────────────────────────────
class PancakeGame:
    # States
    MENU    = "menu"
    PLAYING = "playing"
    WIN     = "win"

    def __init__(self):
        pygame.init()
        self.screen  = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Pancake Sorting")
        self.clock   = pygame.time.Clock()

        # Fonts
        self.font_lg   = pygame.font.SysFont("Georgia",       52, bold=True)
        self.font_md   = pygame.font.SysFont("Georgia",       28, bold=True)
        self.font_sm   = pygame.font.SysFont("Verdana",       16)
        self.font_tiny = pygame.font.SysFont("Verdana",       12)

        self.state = self.MENU
        self._init_menu()

    # ── MENU ──────────────────────────────────
    def _init_menu(self):
        cx = WIDTH // 2
        self.slider_n = Slider(cx - 140, 290, 280, 3, 12, 7, "Pancakes")
        self.dd_algo  = Dropdown(cx - 200, 380, 185, 34,
                                 ["astar", "wastar", "greedy", "bfs", "dfs", "ucs", "ids"],
                                 "Algorithm")
        self.dd_heur  = Dropdown(cx + 15,  380, 185, 34,
                                 ["gap", "l_top_prime", "top_prime", "adjancy"],
                                 "Heuristic")
        self.btn_play  = Button((cx - 110, 460, 220, 48), "Play »", accent=True)
        self.btn_solve = Button((cx - 110, 520, 220, 48), "Auto-Solve »")

    # ── PLAYING ───────────────────────────────
    def _init_playing(self, auto_solve=False):
        n = self.slider_n.value
        self.stack     = list(range(1, n + 1))
        random.shuffle(self.stack)
        self.n         = n
        self.moves     = 0
        self.hover_idx = None          # pancake row under cursor
        self.flip_anim = None          # (idx, progress 0→1)
        self.algo      = self.dd_algo.value
        self.heur      = self.dd_heur.value

        self.ph, self.pw_step = compute_geometry(n)

        cx = WIDTH // 2
        bw, bh = 145, 38
        self.btn_flip    = Button((cx - bw - 4, HEIGHT - 70, bw, bh), "↩ Flip here")
        self.btn_shuffle = Button((cx + 4,       HEIGHT - 70, bw, bh), "⟳ Shuffle")
        self.btn_back    = Button((14,            HEIGHT - 70, 90, bh),  "← Menu")
        self.btn_ai      = Button((WIDTH - 104,   HEIGHT - 70, 90, bh),  "AI Solve", accent=True)

        self.solution_queue = []       # pending states from solver
        self.solving        = False
        self.solve_timer    = 0

        if auto_solve:
            self._start_solve()

    def _start_solve(self):
        initial = tuple(self.stack)
        goal_node, elapsed, memory, states = pb.solve(initial, method=self.algo, heuristic_name=self.heur)
        if not goal_node:
            return
        path, node = [], goal_node
        while node.parent is not None:
            path.append(node.state.stack)
            node = node.parent
        path.reverse()
        self.solution_queue = list(path)
        self.solving        = True
        self.solve_timer    = 0

    def _apply_flip(self, idx):
        self.stack[:idx + 1] = self.stack[:idx + 1][::-1]
        self.moves += 1
        self.hover_idx = None

    def _is_sorted(self):
        return self.stack == sorted(self.stack)

    # ── WIN ───────────────────────────────────
    def _init_win(self):
        self.particles = [Particle() for _ in range(80)]
        cx = WIDTH // 2
        self.btn_menu   = Button((cx - 115, 540, 220, 48), "Main Menu", accent=True)
        self.btn_replay = Button((cx - 115, 600, 220, 48), "Play Again")

    # ══════════════════════════════════════════
    #  EVENT HANDLING
    # ══════════════════════════════════════════
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if self.state == self.MENU:
                self.slider_n.handle_event(event)
                self.dd_algo.handle_event(event)
                self.dd_heur.handle_event(event)
                if self.btn_play.handle_event(event):
                    self._init_playing(auto_solve=False)
                    self.state = self.PLAYING
                if self.btn_solve.handle_event(event):
                    self._init_playing(auto_solve=True)
                    self.state = self.PLAYING

            elif self.state == self.PLAYING:
                self.btn_flip.handle_event(event)
                self.btn_shuffle.handle_event(event)
                if self.btn_back.handle_event(event):
                    self.state = self.MENU
                    self._init_menu()
                if self.btn_ai.handle_event(event) and not self.solving:
                    self._start_solve()

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.btn_flip.rect.collidepoint(event.pos) and self.hover_idx is not None:
                        self._apply_flip(self.hover_idx)
                        if self._is_sorted():
                            self._init_win()
                            self.state = self.WIN
                    elif not any(b.rect.collidepoint(event.pos) for b in
                                 [self.btn_flip, self.btn_shuffle, self.btn_back, self.btn_ai]):
                        # Click on a pancake row
                        idx = self._row_at(event.pos)
                        if idx is not None:
                            self._apply_flip(idx)
                            if self._is_sorted():
                                self._init_win()
                                self.state = self.WIN

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.btn_shuffle.rect.collidepoint(event.pos):
                        random.shuffle(self.stack)
                        self.solution_queue = []
                        self.solving = False
                        self.moves = 0

                if event.type == pygame.MOUSEMOTION:
                    self.hover_idx = self._row_at(event.pos)

            elif self.state == self.WIN:
                if self.btn_menu.handle_event(event):
                    self.state = self.MENU
                    self._init_menu()
                if self.btn_replay.handle_event(event):
                    self._init_playing(auto_solve=False)
                    self.state = self.PLAYING

        return True

    def _row_at(self, pos):
        mx, my = pos
        for i in range(self.n):
            y = STACK_TOP_Y + i * self.ph
            r = pancake_rect(self.stack[i], self.n, self.ph, self.pw_step, y)
            if r.collidepoint(mx, my):
                return i
        return None

    # ══════════════════════════════════════════
    #  UPDATE
    # ══════════════════════════════════════════
    def update(self, dt):
        if self.state == self.PLAYING and self.solving and self.solution_queue:
            self.solve_timer += dt
            if self.solve_timer >= 320:          # ms between steps
                self.solve_timer = 0
                target = self.solution_queue.pop(0)
                # find flip index
                cur = self.stack[:]
                flip_idx = 0
                for i in range(len(cur) - 1, -1, -1):
                    if cur[i] != target[i]:
                        flip_idx = i
                        break
                if flip_idx > 0:
                    self._apply_flip(flip_idx)
                if not self.solution_queue:
                    self.solving = False
                    if self._is_sorted():
                        self._init_win()
                        self.state = self.WIN

        if self.state == self.WIN:
            for p in self.particles:
                p.update()

    # ══════════════════════════════════════════
    #  DRAW
    # ══════════════════════════════════════════
    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)

        if self.state == self.MENU:
            self._draw_menu()
        elif self.state == self.PLAYING:
            self._draw_playing()
        elif self.state == self.WIN:
            self._draw_win()

        pygame.display.flip()

    # ── MENU draw ─────────────────────────────
    def _draw_menu(self):
        # Title
        title = self.font_lg.render("Pancake Sort", True, ACCENT)
        sub   = self.font_sm.render("An AI search puzzle", True, TEXT_DIM)
        self.screen.blit(title, title.get_rect(centerx=WIDTH // 2, y=60))
        self.screen.blit(sub,   sub.get_rect(centerx=WIDTH // 2, y=128))

        # Decorative pancakes preview
        self._draw_preview_stack(WIDTH // 2, 175, 6)

        # Controls
        self.slider_n.draw(self.screen, self.font_tiny)
        self.dd_algo.draw(self.screen, self.font_sm, self.font_tiny)
        self.dd_heur.draw(self.screen, self.font_sm, self.font_tiny)
        self.btn_play.draw(self.screen, self.font_sm)
        self.btn_solve.draw(self.screen, self.font_sm)

        # Footer
        ft = self.font_tiny.render("Click a pancake to flip — or let AI do it", True, TEXT_DIM)
        self.screen.blit(ft, ft.get_rect(centerx=WIDTH // 2, y=HEIGHT - 30))

    def _draw_preview_stack(self, cx, y, n):
        """Small decorative stack shown on the menu."""
        ph = 16
        pw_step = (MAX_PANCAKE_W_RATIO - MIN_PANCAKE_W_RATIO) * WIDTH / max(n - 1, 1)
        ranks = list(range(1, n + 1))
        random.seed(42)
        random.shuffle(ranks)
        for i, rank in enumerate(ranks):
            r = pancake_rect(rank, n, ph, pw_step, y + i * ph)
            col = pancake_color(rank, n)
            pygame.draw.rect(self.screen, col, r, border_radius=4)

    # ── PLAYING draw ──────────────────────────
    def _draw_playing(self):
        # Header bar
        pygame.draw.rect(self.screen, PANEL_COLOR, (0, 0, WIDTH, 50))
        algo_txt = self.font_tiny.render(
            f"algo: {self.algo}  |  heuristic: {self.heur}", True, TEXT_DIM)
        moves_txt = self.font_sm.render(f"Moves: {self.moves}", True, ACCENT)
        self.screen.blit(algo_txt,  (14, 10))
        self.screen.blit(moves_txt, moves_txt.get_rect(right=WIDTH - 14, centery=25))

        # "Solving..." badge
        if self.solving:
            badge = self.font_tiny.render("⟳  AI solving…", True, BACKGROUND_COLOR)
            br = badge.get_rect(centerx=WIDTH // 2, centery=25)
            pygame.draw.rect(self.screen, ACCENT, br.inflate(16, 8), border_radius=6)
            self.screen.blit(badge, br)

        # Stack guide line
        pygame.draw.line(self.screen, (40, 40, 55),
                         (0, STACK_TOP_Y - 12), (WIDTH, STACK_TOP_Y - 12))

        # Pancakes
        for i, rank in enumerate(self.stack):
            y   = STACK_TOP_Y + i * self.ph
            sel = (i == self.hover_idx) and not self.solving
            col = pancake_color(rank, self.n, selected=sel)
            r   = pancake_rect(rank, self.n, self.ph, self.pw_step, y)

            # Flip highlight (above selected row)
            if sel and i > 0:
                hl = pygame.Surface((WIDTH, i * self.ph), pygame.SRCALPHA)
                hl.fill((255, 220, 100, 25))
                self.screen.blit(hl, (0, STACK_TOP_Y))

            # Shadow
            sr = r.copy(); sr.y += 3
            pygame.draw.rect(self.screen, (0, 0, 0, 100), sr, border_radius=6)

            # Pancake body
            pygame.draw.rect(self.screen, col, r, border_radius=6)

            # Border highlight on top edge
            top_r = pygame.Rect(r.x, r.y, r.width, 3)
            pygame.draw.rect(self.screen, tuple(min(c + 60, 255) for c in col),
                             top_r, border_radius=3)

            # Rank label
            if self.ph >= 20:
                lbl = self.font_tiny.render(str(rank), True, (0, 0, 0, 180))
                self.screen.blit(lbl, lbl.get_rect(center=r.center))

        # Separator line
        sep_y = STACK_TOP_Y + self.n * self.ph + 10
        pygame.draw.line(self.screen, (40, 40, 55), (0, sep_y), (WIDTH, sep_y))

        # Instruction
        if self.hover_idx is not None and not self.solving:
            msg = self.font_tiny.render(
                f"Click to flip top {self.hover_idx + 1} pancake{'s' if self.hover_idx else ''}",
                True, TEXT_DIM)
            self.screen.blit(msg, msg.get_rect(centerx=WIDTH // 2, y=sep_y + 8))

        # Buttons
        self.btn_back.draw(self.screen, self.font_tiny)
        self.btn_flip.draw(self.screen, self.font_sm)
        self.btn_shuffle.draw(self.screen, self.font_sm)
        self.btn_ai.draw(self.screen, self.font_sm)

    # ── WIN draw ──────────────────────────────
    def _draw_win(self):
        # Final sorted stack (small)
        n = self.n
        ph_small = max(12, min(28, 260 // n))
        pw_step  = (MAX_PANCAKE_W_RATIO - MIN_PANCAKE_W_RATIO) * WIDTH / max(n - 1, 1)
        start_y  = 220
        for i, rank in enumerate(sorted(self.stack)):
            y = start_y + i * ph_small
            r = pancake_rect(rank, n, ph_small, pw_step, y)
            pygame.draw.rect(self.screen, pancake_color(rank, n), r, border_radius=5)

        # Particles
        for p in self.particles:
            p.draw(self.screen)

        # Overlay text
        win_txt   = self.font_lg.render("Sorted!", True, SUCCESS_COLOR)
        moves_txt = self.font_md.render(f"{self.moves} flip{'s' if self.moves != 1 else ''}",
                                        True, ACCENT)
        self.screen.blit(win_txt,   win_txt.get_rect(centerx=WIDTH // 2, y=120))
        self.screen.blit(moves_txt, moves_txt.get_rect(centerx=WIDTH // 2, y=188))

        self.btn_menu.draw(self.screen, self.font_sm)
        self.btn_replay.draw(self.screen, self.font_sm)

    # ══════════════════════════════════════════
    #  MAIN LOOP
    # ══════════════════════════════════════════
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS)
            running = self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()


if __name__ == "__main__":
    PancakeGame().run()