import pygame
import random
import sys
import os
import pancake_brain as pb
import file_io

WIDTH, HEIGHT = 620, 720

BG = (18,  18,  22)
ACCENT = (255, 195,  50)
ACCENT2 = (80,  180, 240)
TEXT = (230, 230, 230)
TEXT_DIM = (120, 120, 130)
BTN_BG = (38, 38, 48)
BTN_HOV = (55, 55, 70)
SUCCESS = (80, 200, 120)
QUIT = (220, 80, 80)


# renderiza texto numa superficie do pygame, com alinhamento configurável
def draw_text(surf, text, font, color, cx, cy, anchor="center"):
    img = font.render(text, True, color)
    r = img.get_rect()
    if anchor == "center":    r.center   = (cx, cy)
    elif anchor == "midleft": r.midleft  = (cx, cy)
    surf.blit(img, r)
    return r


# desenha um botão retangular com borda colorida e texto centrado
def draw_button(surf, font, text, rect, hovered, color=None):
    bg = BTN_HOV if hovered else BTN_BG                                      # cor de fundo muda ao passar o rato
    pygame.draw.rect(surf, bg, rect, border_radius=8)
    border_col = color if color else (ACCENT if hovered else (60, 60, 75))   # borda destaca quando fazemos hover
    pygame.draw.rect(surf, border_col, rect, 2, border_radius=8)
    draw_text(surf, text, font, TEXT, rect.centerx, rect.centery)

# calcula as dimensões (altura, espaço, largura min/max) das peças em função do nº de pancakes
def piece_dims(total):
    available_h = HEIGHT - 360
    slot = max(10, available_h // total)
    h = max(8, slot - 2)
    gap = slot - h
    max_w = WIDTH - 120
    min_w = max(20, max_w // 4)
    step = max(1, (max_w - min_w) // max(total - 1, 1))  # aumento da largura por rank
    return h, gap, min_w, step


class Piece:
    # Inicializa uma peça com o rank e dimensões de acordo com o total de pancakes
    def __init__(self, rank, total):
        self.rank = rank
        self.total = total
        h, gap, min_w, step = piece_dims(total)
        self.height = h
        self.gap = gap
        self.width = min_w + (rank - 1) * step   # quanto maior a peça, mais larga

    # Devolve uma cor interpolada entre vermelho e laranja
    def color(self):
        t = (self.rank - 1) / max(self.total - 1, 1)   # t=0 é a menor peça, t=1 é a maior peça
        return (225, 20 + int(200 * (1 - t)), 25)


    # Desenha a peça centrada horizontalmente em cx, na posição vertical y
    def draw(self, surf, cx, y, highlight=False):
        w = self.width
        rect = pygame.Rect(cx - w // 2, y, w, self.height)
        col = self.color()
        if highlight:
            col = (255, 255, 255)                              # branco para indicar hint
        pygame.draw.rect(surf, col, rect, border_radius=6)
        pygame.draw.rect(surf, (0, 0, 0), rect, 1, border_radius=6)
        return rect


class Stack:
    # Inicializa a pilha: a partir de uma lista de ranks ou gerada aleatoriamente
    def __init__(self, items=None, num_pancakes=7):
        
        if items is not None:
            total = max(items)
            self.items = [Piece(r, total) for r in items]
        else:
            n = num_pancakes
            ranks = list(range(1, n + 1))
            random.shuffle(ranks)                              # ordem inicial aleatória
            self.items = [Piece(r, n) for r in ranks]
        self.moves = 0
        self.initial_state = self.as_tuple()
        self.path = [self.as_tuple()]                          # regista todos os estados para guardar no ficheiro de output

    # Inverte a sub-pilha do topo até ao indice indicado (única operação do nosso jogo)
    def flip(self, index):
        portion = self.items[:index + 1]
        self.items[:index + 1] = list(reversed(portion))
        self.moves += 1
        self.path.append(self.as_tuple())

    # Verifica se a pilha está ordenada 
    def is_solved(self):
        return self.as_tuple() == tuple(sorted(self.as_tuple()))
    
    # Devolve o estado atual da pilha como tuplo de ranks
    def as_tuple(self):
        return tuple(p.rank for p in self.items)

    # Desenha todas as peças da pilha, e destaca as que estão acima do índice de hint
    def draw(self, surf, cx, start_y, highlight_idx=None):
        rects = []
        y = start_y
        for i, p in enumerate(self.items):
            hl = (highlight_idx is not None and i <= highlight_idx)   # destaca peças acima do flip sugerido
            r = p.draw(surf, cx, y, highlight=hl)
            rects.append(r)
            y += p.height + p.gap
        return rects


class App:
    # estados possíveis da aplicação
    MENU = "menu"
    SETUP = "setup"
    PLAYING = "playing"
    AI_SOLVE = "ai_solve"
    WIN = "win"

    # inicia o pygame, a janela e todas as variáveis de estado da aplicação
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Pancake Puzzle")
        self.clock  = pygame.time.Clock()

        self.font_title = pygame.font.SysFont("Georgia", 44, bold=True)
        self.font_h2 = pygame.font.SysFont("Georgia", 26, bold=True)
        self.font_body = pygame.font.SysFont("Courier New", 19)
        self.font_sm = pygame.font.SysFont("Courier New", 15)

        self.state = self.MENU
        self.stack = None
        self.mode = None          # "manual" ou "ai"
        self.num_pan = 7
        self.ai_method = "astar"
        self.ai_heur = "gap"
        self.hint_idx = None      # índice do flip sugerido pelo hint
        self.setup_mode = None    # "manual" ou "ai", definido no menu

        self.win_moves = 0
        self.win_time = 0.0
        self.win_mem = 0
        self.win_states = 0

        self.ai_queue = []        # sequência de estados para mostrar ao usuário durante a resolução
        self.ai_delay = 350       # milissegundos entre cada passo da animação
        self.ai_last = 0          # timestamp do último passo animado
        self.ai_stats = {}        # estatísticas do solver


    # ciclo principal: processa eventos e delega o desenho ao handler do estado atual
    def run(self):
        while True:
            self.clock.tick(60)
            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

            if self.state == self.MENU:
                self.handle_menu(events)
            elif self.state == self.SETUP:
                self.handle_setup(events)
            elif self.state == self.PLAYING:
                self.handle_playing(events)
            elif self.state == self.AI_SOLVE:
                self.handle_ai(events)
            elif self.state == self.WIN:
                self.handle_win(events)

            pygame.display.flip()

    def handle_menu(self, events):
        surf = self.screen
        surf.fill(BG)

        draw_text(surf, "PANCAKE", self.font_title, ACCENT, WIDTH//2, 130)
        draw_text(surf, "PUZZLE", self.font_title, TEXT, WIDTH//2, 180)

        mx, my = pygame.mouse.get_pos()

        btns = {
            "play": pygame.Rect(WIDTH//2-130, 300, 260, 52),
            "ai": pygame.Rect(WIDTH//2-130, 370, 260, 52),
            "quit": pygame.Rect(WIDTH//2-130, 460, 260, 52),
        }
        labels = {"play": "Play Manually", "ai": "AI Solver", "quit": "Quit"}
        colors = {"play": ACCENT, "ai": ACCENT2, "quit": QUIT}

        clicked = None
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for k, r in btns.items():
                    if r.collidepoint(mx, my): clicked = k

        for k, r in btns.items():
            draw_button(surf, self.font_body, labels[k], r, r.collidepoint(mx, my), colors[k])

        if clicked == "play":
            self.setup_mode = "manual"
            self.state = self.SETUP
        elif clicked == "ai":
            self.setup_mode = "ai"
            self.state = self.SETUP
        elif clicked == "quit":
            pygame.quit()
            sys.exit()

    def handle_setup(self, events):
        surf = self.screen
        surf.fill(BG)
        mx, my = pygame.mouse.get_pos()

        title = "Manual Setup" if self.setup_mode == "manual" else "AI Solver Setup"
        draw_text(surf, title, self.font_h2, ACCENT, WIDTH//2, 55)

        # seletor do número de pancakes
        draw_text(surf, "Number of Pancakes", self.font_body, TEXT_DIM, WIDTH//2, 115)
        minus_r = pygame.Rect(WIDTH//2-75, 138, 44, 36)
        plus_r = pygame.Rect(WIDTH//2+31, 138, 44, 36)
        draw_button(surf, self.font_h2, "-", minus_r, minus_r.collidepoint(mx, my))
        draw_button(surf, self.font_h2, "+", plus_r, plus_r.collidepoint(mx, my))
        draw_text(surf, str(self.num_pan), self.font_h2, ACCENT, WIDTH//2, 156)

        y = 210
        algo_rects = {}
        heur_rects = {}

        if self.setup_mode == "ai":
            # seleção do algoritmo
            draw_text(surf, "Algorithm", self.font_body, TEXT_DIM, WIDTH//2, y); y += 32
            methods = ["bfs","dfs","ids","ucs","greedy","astar","wastar"]
            col_w = 82
            total_w = len(methods) * col_w
            ax0 = WIDTH//2 - total_w//2
            for i, m in enumerate(methods):
                r = pygame.Rect(ax0 + i*col_w, y, col_w-4, 34)
                algo_rects[m] = r
                sel = self.ai_method == m
                pygame.draw.rect(surf, ACCENT if sel else BTN_BG, r, border_radius=6)
                pygame.draw.rect(surf, ACCENT if sel else (60,60,75), r, 2, border_radius=6)
                draw_text(surf, m.upper(), self.font_sm, BG if sel else TEXT, r.centerx, r.centery)
            y += 46

            # seleção da heurística 
            draw_text(surf, "Heuristic", self.font_body, TEXT_DIM, WIDTH//2, y); y += 32
            heurs = ["gap","adjancy","top_prime","l_top_prime"]
            col_w2 = 130
            total_w2 = len(heurs) * col_w2
            hx0 = WIDTH//2 - total_w2//2
            for i, h in enumerate(heurs):
                r = pygame.Rect(hx0 + i*col_w2, y, col_w2-4, 34)
                heur_rects[h] = r
                sel = self.ai_heur == h
                pygame.draw.rect(surf, ACCENT2 if sel else BTN_BG, r, border_radius=6)
                pygame.draw.rect(surf, ACCENT2 if sel else (60,60,75), r, 2, border_radius=6)
                draw_text(surf, h, self.font_sm, BG if sel else TEXT, r.centerx, r.centery)
            y += 50

        start_r = pygame.Rect(WIDTH//2-110, HEIGHT-205, 220, 48)
        load_r = pygame.Rect(WIDTH//2-110, HEIGHT-147, 220, 40)
        back_r = pygame.Rect(WIDTH//2-80,  HEIGHT-90,  160, 36)
        draw_button(surf, self.font_body, "Start", start_r, start_r.collidepoint(mx, my), ACCENT)
        draw_button(surf, self.font_sm, "Load from file", load_r, load_r.collidepoint(mx, my), ACCENT2)
        draw_button(surf, self.font_sm, "<- Back", back_r, back_r.collidepoint(mx, my))

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if minus_r.collidepoint(mx, my): self.num_pan = max(3, self.num_pan-1)
                if plus_r.collidepoint(mx, my):  self.num_pan = min(50, self.num_pan+1)

                for m, r in algo_rects.items():
                    if r.collidepoint(mx, my): self.ai_method = m
                for h, r in heur_rects.items():
                    if r.collidepoint(mx, my): self.ai_heur = h

                if start_r.collidepoint(mx, my):
                    self.stack = Stack(num_pancakes=self.num_pan)
                    if self.setup_mode == "manual":
                        self.mode = "manual"
                        self.state = self.PLAYING
                    else:
                        self.mode = "ai"
                        self.start_ai()
                        self.state = self.AI_SOLVE

                if load_r.collidepoint(mx, my):
                    #usa como input o ficheiro "input.txt"
                    self.try_load_file('input.txt')

                if back_r.collidepoint(mx, my):
                    self.state = self.MENU

    def try_load_file(self, fname):
        try:
            items = file_io.read_board(os.path.join(os.getcwd(), fname))
            self.num_pan = len(items)
            self.stack = Stack(items=items)
            if self.setup_mode == "ai":
                self.mode = "ai"
                self.start_ai()
                self.state = self.AI_SOLVE
            else:
                self.mode = "manual"
                self.state = self.PLAYING
        except Exception as ex:
            print(f"Could not load {fname}: {ex}")

    def handle_playing(self, events):
        # ecrã do jogo manual: mostra a pilha, deteta hover do rato e processa flips
        surf = self.screen
        surf.fill(BG)
        mx, my = pygame.mouse.get_pos()

        hint_r = pygame.Rect(20, 20, 120, 38)
        restart_r = pygame.Rect(WIDTH-250, 20, 120, 38)
        menu_r = pygame.Rect(WIDTH-120, 20, 100, 38)

        draw_button(surf, self.font_sm, "Hint", hint_r, hint_r.collidepoint(mx, my), ACCENT)
        draw_button(surf, self.font_sm, "Restart", restart_r, restart_r.collidepoint(mx, my))
        draw_button(surf, self.font_sm, "<- Menu", menu_r, menu_r.collidepoint(mx, my))
        draw_text(surf, f"Moves: {self.stack.moves}", self.font_sm, TEXT_DIM, WIDTH//2, 30)

        n = len(self.stack.items)
        p0 = self.stack.items[0]
        slot = p0.height + p0.gap                    # altura total ocupada por uma peça
        stack_h = n * slot
        start_y = (HEIGHT - stack_h) // 2 + 20
        cx = WIDTH // 2

        # deteta qual a peça sob o cursor do rato
        hover_idx = None
        for i in range(n):
            yy = start_y + i * slot
            if yy <= my <= yy + p0.height:
                hover_idx = i; break

        # destaca a peça do hint se estiver ativo
        hl = self.hint_idx

        self.stack.draw(surf, cx, start_y, highlight_idx=hl)

        if hover_idx is not None:
            # desenha uma linha horizontal a indicar onde o flip vai acontecer
            line_y = start_y + (hover_idx + 1) * slot - 2
            pygame.draw.line(surf, ACCENT, (cx-310, line_y), (cx+310, line_y), 2)

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if hint_r.collidepoint(mx, my):
                    self.request_hint()
                elif restart_r.collidepoint(mx, my):
                    self.stack = Stack(num_pancakes=self.num_pan)
                    self.hint_idx = None
                elif menu_r.collidepoint(mx, my):
                    self.state = self.MENU
                elif hover_idx is not None:
                    self.stack.flip(hover_idx)     # executa o flip na peça clicada
                    self.hint_idx = None

        if self.stack.is_solved():
            self.win_moves = self.stack.moves
            self.win_time = 0.0
            self.win_mem = 0
            self.win_states = 0
            self.save_result()
            self.state = self.WIN

    def request_hint(self):
        # pede ao solver (com o A* + gap) o próximo flip ótimo e ativa o highlight
        idx = pb.get_hint(self.stack.as_tuple())
        if idx is not None:
            self.hint_idx = idx

    def start_ai(self):
        self.ai_queue = []
        self.ai_stats = {}
        self.ai_last = pygame.time.get_ticks()

        initial = self.stack.as_tuple()
        goal, t, mem, states = pb.solve(
            initial, method=self.ai_method, heuristic_name=self.ai_heur)
        path = pb.get_path(goal)                            # lista de estados desde inicial até solução
        self.ai_queue = path
        self.ai_stats = {"time": t, "mem": mem, "states": states, "moves": len(path)-1, "path": path}

    def handle_ai(self, events):
        surf = self.screen
        surf.fill(BG)
        mx, my = pygame.mouse.get_pos()

        menu_r = pygame.Rect(WIDTH-120, 20, 100, 38)
        draw_button(surf, self.font_sm, "<- Menu", menu_r, menu_r.collidepoint(mx, my))

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if menu_r.collidepoint(mx, my): self.state = self.MENU

        n = len(self.stack.items)
        p0 = self.stack.items[0]
        slot = p0.height + p0.gap
        stack_h = n * slot
        start_y = (HEIGHT - stack_h) // 2 + 20
        self.stack.draw(surf, WIDTH // 2, start_y)

        # avança um passo da animação a cada ai_delay 
        now = pygame.time.get_ticks()
        if len(self.ai_queue) > 1 and now - self.ai_last > self.ai_delay:
            next_ranks = self.ai_queue[1]
            curr = self.stack.as_tuple()
            # descobre qual o indice de flip que transforma o estado atual no próximo
            for i in range(1, len(curr)):
                if curr[:i+1][::-1] + curr[i+1:] == next_ranks:
                    self.stack.flip(i); break
            self.ai_queue.pop(0)       # remove o estado já executado da fila
            self.ai_last = now

        s = self.ai_stats
        draw_text(surf, f"{self.ai_method.upper()} / {self.ai_heur}", self.font_sm, TEXT_DIM, WIDTH//2, 30)
        steps_left = max(0, len(self.ai_queue)-1)
        draw_text(surf, f"Steps left: {steps_left}", self.font_sm, ACCENT, WIDTH//2, 50)

        if len(self.ai_queue) == 1 and self.stack.is_solved():
            self.win_moves = s.get("moves", self.stack.moves)
            self.win_time = s.get("time",  0)
            self.win_mem = s.get("mem",   0)
            self.win_states = s.get("states", 0)
            self.save_result()
            self.state = self.WIN

    def handle_win(self, events):
        surf = self.screen
        surf.fill(BG)
        mx, my = pygame.mouse.get_pos()

        draw_text(surf, "Solved!", self.font_title, SUCCESS, WIDTH//2, 75)

        rows = [("Moves", str(self.win_moves))]
        if self.mode == "ai":
            rows += [
                ("Time", f"{self.win_time:.4f} s"),
                ("Memory", f"{self.win_mem:,} bytes"),
                ("States", f"{self.win_states:,}"),
                ("Method", f"{self.ai_method.upper()}"),
                ("Heuristic", self.ai_heur),
            ]

        y = 145
        for label, val in rows:
            draw_text(surf, label, self.font_body, TEXT_DIM, 110, y, "midleft")
            draw_text(surf, val, self.font_body, TEXT, 300, y, "midleft")
            pygame.draw.line(surf, (50, 50, 62), (90, y+22), (WIDTH-90, y+22), 1)   # linha separadora
            y += 44

        draw_text(surf, "Results saved to  output.txt", self.font_sm, SUCCESS, WIDTH//2, y+18)

        menu_r = pygame.Rect(WIDTH//2-135, HEIGHT-130, 120, 48)
        again_r = pygame.Rect(WIDTH//2+15,  HEIGHT-130, 120, 48)
        draw_button(surf, self.font_body, "<- Menu", menu_r, menu_r.collidepoint(mx, my))
        draw_button(surf, self.font_body, "Again", again_r, again_r.collidepoint(mx, my), ACCENT)

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if menu_r.collidepoint(mx, my):
                    self.state = self.MENU
                if again_r.collidepoint(mx, my):
                    self.stack = Stack(num_pancakes=self.num_pan)
                    if self.mode == "manual":
                        self.state = self.PLAYING
                    else:
                        self.start_ai()
                        self.state = self.AI_SOLVE

    # guarda o resultado da sessão (caminho, movimentos, tempo, memória) no "output.txt"
    def save_result(self):
        if not self.stack: return
        if self.mode == "ai":
            sol_path = self.ai_stats.get("path", [])
            initial = sol_path[0] if sol_path else self.stack.as_tuple()
        else:
            sol_path = self.stack.path
            initial = self.stack.initial_state
        file_io.write_result("output.txt", initial, sol_path, self.win_moves, self.win_time, self.win_mem, self.win_states)


if __name__ == "__main__":
    App().run()