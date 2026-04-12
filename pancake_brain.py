from collections import deque
import heapq
import math
import time
import tracemalloc

# variável global para contar o nº de estados explorados as pesquisas
explored_states = 0



# representa um estado da pilha de como um tuplo imutável e hashável
class PancakeState:
    def __init__(self, stack):
        self.stack = tuple(stack)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.stack == other.stack
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.stack)

    def __str__(self):
        return str(self.stack)




# inverte os primeiros i+1 elementos da pilha e devolve o novo estado com custo 1
def flip(state, i):
    if i < 1 or i >= len(state.stack):
        return None
    new_stack = state.stack[:i + 1][::-1] + state.stack[i + 1:]
    return PancakeState(new_stack), 1


# gera todos os estados filhos possíveis a partir do estado atual (um flip por posição)
def child_pancake_states(state):

    children = []
    for i in range(1, len(state.stack)):
        result = flip(state, i)
        if result:
            children.append(result)
    return children




# verifica se a pilha está ordenada
def goal_pancake_state(state):
    return state.stack == tuple(sorted(state.stack))


# nó da árvore de pesquisa: guarda o estado, o pai, os filhos e o custo acumulado
class TreeNode:
    def __init__(self, state, parent=None):
        self.state = state
        self.parent = parent
        self.children = []
        self.cost = 0 

    # adiciona um child node, e atualiza o custo acumulado e o pointer para o pai
    def add_child(self, child_node, operator_cost=0):
        self.children.append(child_node)
        child_node.cost = self.cost + operator_cost
        child_node.parent = self

    def __lt__(self, other):
        return self.cost < other.cost


# calcula a permutação inversa da pilha: inverse[rank] = posição do rank na pilha
def invert_permutation(stack):
    n = len(stack)
    inverse = [0] * (n + 1)
    for pos, rank in enumerate(stack):
        inverse[rank] = pos
    return tuple(inverse[1:])


# heuristica de adjacência: conta pares consecutivos cujos ranks não são adjacentes
def heuristic_adjacency(node):
    stack = node.state.stack
    return sum(1 for i in range(len(stack) - 1) if abs(stack[i] - stack[i + 1]) != 1)


# heuristica gap: conta quebras de adjacência + penalidade se o maior pancake não está na base
def heuristic_gap(node):
    stack = node.state.stack
    n = len(stack)
    gaps = sum(1 for i in range(n - 1) if abs(stack[i] - stack[i + 1]) != 1)
    if stack[-1] != n:
        gaps += 1                  # penalidade extra porque o maior pancake não está na base
    return gaps


# versão interna do gap sem wrapper de nó, para usar nas heuristicas compostas
def gap_raw(stack):
    n = len(stack)
    gaps = sum(1 for i in range(n - 1) if abs(stack[i] - stack[i + 1]) != 1)
    if stack[-1] != n:
        gaps += 1
    return gaps


# heuristica top': se nenhum flip reduz o gap, adiciona 1 ao valor base (força lower bound mais apertado)
def top_heuristic_raw(stack):
    base = gap_raw(stack)
    if base == 0:
        return 0
    n = len(stack)
    for i in range(1, n):
        child = stack[:i + 1][::-1] + stack[i + 1:]
        if gap_raw(child) < base:
            return base            # existe um flip que melhora então devolve o valor base sem penalidade
    return base + 1                # nenhum flip melhora então adiciona penalidade de +1


# heurística top': aplica top_heuristic_raw à pilha e à sua permutação inversa, retorna o máximo
def heuristic_top_prime(node):
    stack = node.state.stack
    inv = invert_permutation(stack)
    return max(top_heuristic_raw(stack), top_heuristic_raw(inv))


# versão interna do top' sem wrapper de nó, usada no l_top_prime
def _top_prime_raw(stack):
    inv = invert_permutation(stack)
    return max(top_heuristic_raw(stack), top_heuristic_raw(inv))


# heurística L-Top': lookahead de top'
def heuristic_l_top_prime(node):
    stack = node.state.stack
    inv = invert_permutation(stack)

    # para cada estado, considera o melhor filho possível e garante que h >= h_filho + 1
    def lookahead(s):
        base = _top_prime_raw(s)
        if base == 0:
            return 0
        n = len(s)
        min_child = min(
            _top_prime_raw(s[:i + 1][::-1] + s[i + 1:])
            for i in range(1, n)
        )
        return max(base, min_child + 1)

    return max(lookahead(stack), lookahead(inv))


# devolve a função de heuristíca correspondente ao nome fornecido
def getHeuristicByName(heuristic_name):
    if(heuristic_name == "gap"):
        return heuristic_gap
    elif(heuristic_name == "adjancy"):
        return heuristic_adjacency
    elif(heuristic_name == "top_prime"):
        return heuristic_top_prime
    elif(heuristic_name == "l_top_prime"):
        return heuristic_l_top_prime




# pesquisa em largura: écompleta e ótima; expande nós por ordem de profundidade crescente
def breadth_first_search(initial_state, goal_state_func, operators_func):
    global explored_states
    root = TreeNode(initial_state)
    queue = deque([root])
    visited = {initial_state}

    while queue:
        explored_states += 1
        node = queue.popleft()
        if goal_state_func(node.state):
            return node

        for state, cost in operators_func(node.state):
            if state not in visited:
                visited.add(state)
                child = TreeNode(state)
                node.add_child(child, cost)
                queue.append(child)

    return None


# pesquisa em profundidade: não garante solução ótima; usa pilha LIFO
def depth_first_search(initial_state, goal_state_func, operators_func):
    global explored_states
    root = TreeNode(initial_state)
    stack = [root]
    visited = {initial_state}

    while stack:
        explored_states += 1
        node = stack.pop()
        if goal_state_func(node.state):
            return node

        for state, cost in operators_func(node.state):
            if state not in visited:
                visited.add(state)
                child = TreeNode(state)
                node.add_child(child, cost)
                stack.append(child)

    return None


# pesquisa em profundidade com limite máximo; devolve None se não encontrar uma solução dentro do limite
def depth_limited_search(initial_state, goal_state_func, operators_func, depth_limit):

    def dls(node, limit, visited_path):
        global explored_states
        explored_states += 1
        if goal_state_func(node.state):
            return node
        if limit == 0:
            return None                        # limite atingido: não expande mais
        for state, cost in operators_func(node.state):
            if state not in visited_path:
                visited_path.add(state)
                child = TreeNode(state)
                node.add_child(child, cost)
                result = dls(child, limit - 1, visited_path)
                if result is not None:
                    return result
                visited_path.discard(state)    # backtrack: remove do caminho atual ao recuar
        return None

    root = TreeNode(initial_state)
    return dls(root, depth_limit, {initial_state})


# pesquisa por aprofundamento iterativo: repete DLS com limite crescente até encontrar solução
def iterative_deepening_search(initial_state, goal_state_func, operators_func, depth_limit=50):

    for limit in range(depth_limit + 1):
        result = depth_limited_search(initial_state, goal_state_func, operators_func, limit)
        if result is not None:
            return result
    return None


# pesquisa de custo uniforme: expande sempre o nó de menor custo acumulado (g)
def uniform_cost_search(initial_state, goal_state_func, operators_func):
    global explored_states
    root = TreeNode(initial_state)
    heap = [(0, root)]
    best_g = {initial_state: 0}

    while heap:
        explored_states += 1
        g, node = heapq.heappop(heap)
        if best_g.get(node.state, math.inf) < g:
            continue                           # ignora entradas obsoletas na heap
        if goal_state_func(node.state):
            return node

        for state, cost in operators_func(node.state):
            new_g = g + cost
            if new_g < best_g.get(state, math.inf):
                best_g[state] = new_g
                child = TreeNode(state)
                node.add_child(child, cost)
                heapq.heappush(heap, (new_g, child))

    return None



# pesquisa greedy: expande sempre o nó com menor valor heurístico h, sem considerar o custo g
def greedy_search(initial_state, goal_state_func, operators_func, heuristic_func):
    global explored_states
    root = TreeNode(initial_state)
    queue = [(root, heuristic_func(root))]
    visited = {initial_state}

    while queue:
        explored_states += 1
        node, _ = queue.pop(0)
        if goal_state_func(node.state):
            return node

        for state, cost in operators_func(node.state):
            if state not in visited:
                visited.add(state)
                child = TreeNode(state)
                node.add_child(child, cost)
                queue.append((child, heuristic_func(child)))

        queue = sorted(queue, key=lambda x: x[1])   # reordena pela heurística após cada expansão

    return None


# pesquisa A*: expande pelo menor f = g + h; ótima se a heuristica for admissível
def a_star_search(initial_state, goal_state_func, operators_func, heuristic_func):
    global explored_states
    root = TreeNode(initial_state)
    queue = [(root, 0 + heuristic_func(root))]
    visited = {initial_state}

    while queue:
        explored_states += 1
        node, _ = queue.pop(0)
        if goal_state_func(node.state):
            return node

        for state, cost in operators_func(node.state):
            if state not in visited:
                visited.add(state)
                child = TreeNode(state)
                node.add_child(child, cost)
                queue.append((child, child.cost + heuristic_func(child)))

        queue = sorted(queue, key=lambda x: x[1])   # reordena por f = g + h

    return None


# Weighted A* : multiplica h por weight para explorar menos nós à custa de optimalidade
def weighted_a_star_search(initial_state, goal_state_func, operators_func,heuristic_func, weight=1.5):
    global explored_states
    root = TreeNode(initial_state)
    queue = [(root, 0 + weight * heuristic_func(root))]
    visited = {initial_state}

    while queue:
        explored_states += 1
        node, _ = queue.pop(0)
        if goal_state_func(node.state):
            return node

        for state, cost in operators_func(node.state):
            if state not in visited:
                visited.add(state)
                child = TreeNode(state)
                node.add_child(child, cost)
                queue.append((child, child.cost + weight * heuristic_func(child)))

        queue = sorted(queue, key=lambda x: x[1])   # reordena por f = g + weight*h

    return None


# reconstrói o caminho desde a raiz até ao nó goal, devolvendo lista de tuplos de ranks
def get_path(node):
    path = []
    curr = node
    while curr:
        path.append(curr.state.stack)
        curr = curr.parent
    path.reverse()
    return path

# ponto de entrada do solver: escolhe o algoritmo, mede tempo e memória, devolve (goal, tempo, mem, estados)
def solve(initial_state, method="astar", heuristic_name="gap", weight=1.5, max_depth=50):
    global explored_states
    explored_states = 0
    
    if isinstance(initial_state, tuple):
        initial_state = PancakeState(initial_state)
    heuristic_func = getHeuristicByName(heuristic_name) 

    tracemalloc.start()
    start_time = time.time()

    if method == "bfs":
        goal = breadth_first_search(initial_state, goal_pancake_state, child_pancake_states)
    elif method == "dfs":
        goal = depth_first_search(initial_state, goal_pancake_state, child_pancake_states)
    elif method == "dls":
        goal = depth_limited_search(initial_state, goal_pancake_state, child_pancake_states, max_depth)
    elif method == "ids":
        goal = iterative_deepening_search(initial_state, goal_pancake_state, child_pancake_states, max_depth)
    elif method == "ucs":
        goal = uniform_cost_search(initial_state, goal_pancake_state, child_pancake_states)
    elif method == "greedy":
        goal = greedy_search(initial_state, goal_pancake_state, child_pancake_states, heuristic_func)
    elif method == "astar":
        goal = a_star_search(initial_state, goal_pancake_state, child_pancake_states, heuristic_func)
    elif method == "wastar":
        goal = weighted_a_star_search(initial_state, goal_pancake_state, child_pancake_states, heuristic_func, weight)

    end_time = time.time()
    _, peak_memory = tracemalloc.get_traced_memory()   # pico de memória em bytes durante a pesquisa
    tracemalloc.stop()
    
    elapsed_time = end_time - start_time
    
    return goal, elapsed_time, peak_memory, explored_states

# usa A* + gap para sugerir o próximo flip ótimo; devolve o índice do flip ou None se já resolvido
def get_hint(initial_state):
    goal, time_taken, memory, states = solve(initial_state, "astar", "gap")
    if not goal: return None
    path = get_path(goal)
    if len(path) > 1:
        next_state = path[1]
        # descobre qual o indice de flip que transforma o estado atual no próximo estado ótimo
        for i in range(1, len(initial_state)):
            if initial_state[:i + 1][::-1] + initial_state[i + 1:] == next_state:
                return i
    return None