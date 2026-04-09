from collections import deque
import heapq
import math


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




def flip(state, i):
    if i < 1 or i >= len(state.stack):
        return None
    new_stack = state.stack[:i + 1][::-1] + state.stack[i + 1:]
    return PancakeState(new_stack), 1


def child_pancake_states(state):

    children = []
    for i in range(1, len(state.stack)):
        result = flip(state, i)
        if result:
            children.append(result)
    return children




def goal_pancake_state(state):
    return state.stack == tuple(sorted(state.stack))


class TreeNode:
    def __init__(self, state, parent=None):
        self.state = state
        self.parent = parent
        self.children = []
        self.cost = 0 

    def add_child(self, child_node, operator_cost=0):
        self.children.append(child_node)
        child_node.cost = self.cost + operator_cost
        child_node.parent = self

    def __lt__(self, other):
        return self.cost < other.cost

def print_solution(node):
    path = []
    while node:
        path.append(node.state)
        node = node.parent
    path.reverse()
    for step in path:
        print(step)


def _invert_permutation(stack):
    n = len(stack)
    inverse = [0] * (n + 1)
    for pos, rank in enumerate(stack):
        inverse[rank] = pos
    return tuple(inverse[1:])


def heuristic_adjacency(node):
    stack = node.state.stack
    return sum(1 for i in range(len(stack) - 1) if abs(stack[i] - stack[i + 1]) != 1)


def heuristic_gap(node):
    stack = node.state.stack
    n = len(stack)
    gaps = sum(1 for i in range(n - 1) if abs(stack[i] - stack[i + 1]) != 1)
    if stack[-1] != n:
        gaps += 1
    return gaps


def _gap_raw(stack):
    n = len(stack)
    gaps = sum(1 for i in range(n - 1) if abs(stack[i] - stack[i + 1]) != 1)
    if stack[-1] != n:
        gaps += 1
    return gaps


def _top_heuristic_raw(stack):
    base = _gap_raw(stack)
    if base == 0:
        return 0
    n = len(stack)
    for i in range(1, n):
        child = stack[:i + 1][::-1] + stack[i + 1:]
        if _gap_raw(child) < base:
            return base
    return base + 1


def heuristic_top_prime(node):
    stack = node.state.stack
    inv = _invert_permutation(stack)
    return max(_top_heuristic_raw(stack), _top_heuristic_raw(inv))


def _top_prime_raw(stack):
    inv = _invert_permutation(stack)
    return max(_top_heuristic_raw(stack), _top_heuristic_raw(inv))


def heuristic_l_top_prime(node):
    """
    L-Top' heuristic (artigo de referência):
    Lookahead de top' — max( lookahead(stack), lookahead(inverso(stack)) ).
    Admissível e domina top'.
    """
    stack = node.state.stack
    inv = _invert_permutation(stack)

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


def getHeuristicByName(heuristic_name):
    if(heuristic_name == "gap"):
        return heuristic_gap
    elif(heuristic_name == "adjancy"):
        return heuristic_adjacency
    elif(heuristic_name == "top_prime"):
        return heuristic_top_prime
    elif(heuristic_name == "l_top_prime"):
        return heuristic_l_top_prime





def breadth_first_search(initial_state, goal_state_func, operators_func):
    """BFS — completa e ótima para custos uniformes."""
    root = TreeNode(initial_state)
    queue = deque([root])
    visited = {initial_state}

    while queue:
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


def depth_first_search(initial_state, goal_state_func, operators_func):

    root = TreeNode(initial_state)
    stack = [root]
    visited = {initial_state}

    while stack:
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


def depth_limited_search(initial_state, goal_state_func, operators_func, depth_limit):

    def dls(node, limit, visited_path):
        if goal_state_func(node.state):
            return node
        if limit == 0:
            return None
        for state, cost in operators_func(node.state):
            if state not in visited_path:
                visited_path.add(state)
                child = TreeNode(state)
                node.add_child(child, cost)
                result = dls(child, limit - 1, visited_path)
                if result is not None:
                    return result
                visited_path.discard(state)
        return None

    root = TreeNode(initial_state)
    return dls(root, depth_limit, {initial_state})


def iterative_deepening_search(initial_state, goal_state_func, operators_func, depth_limit=50):

    for limit in range(depth_limit + 1):
        result = depth_limited_search(initial_state, goal_state_func, operators_func, limit)
        if result is not None:
            return result
    return None


def uniform_cost_search(initial_state, goal_state_func, operators_func):

    root = TreeNode(initial_state)
    heap = [(0, root)]
    best_g = {initial_state: 0}

    while heap:
        g, node = heapq.heappop(heap)
        if best_g.get(node.state, math.inf) < g:
            continue
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



def greedy_search(initial_state, goal_state_func, operators_func, heuristic_func):

    root = TreeNode(initial_state)
    queue = [(root, heuristic_func(root))]
    visited = {initial_state}

    while queue:
        node, _ = queue.pop(0)
        if goal_state_func(node.state):
            return node

        for state, cost in operators_func(node.state):
            if state not in visited:
                visited.add(state)
                child = TreeNode(state)
                node.add_child(child, cost)
                queue.append((child, heuristic_func(child)))

        queue = sorted(queue, key=lambda x: x[1])

    return None


def a_star_search(initial_state, goal_state_func, operators_func, heuristic_func):

    root = TreeNode(initial_state)
    queue = [(root, 0 + heuristic_func(root))]
    visited = {initial_state}

    while queue:
        node, _ = queue.pop(0)
        if goal_state_func(node.state):
            return node

        for state, cost in operators_func(node.state):
            if state not in visited:
                visited.add(state)
                child = TreeNode(state)
                node.add_child(child, cost)
                queue.append((child, child.cost + heuristic_func(child)))

        queue = sorted(queue, key=lambda x: x[1])

    return None


def weighted_a_star_search(initial_state, goal_state_func, operators_func,heuristic_func, weight=1.5):

    root = TreeNode(initial_state)
    queue = [(root, 0 + weight * heuristic_func(root))]
    visited = {initial_state}

    while queue:
        node, _ = queue.pop(0)
        if goal_state_func(node.state):
            return node

        for state, cost in operators_func(node.state):
            if state not in visited:
                visited.add(state)
                child = TreeNode(state)
                node.add_child(child, cost)
                queue.append((child, child.cost + weight * heuristic_func(child)))

        queue = sorted(queue, key=lambda x: x[1])

    return None


def solve(initial_state, method="astar", heuristic_name="gap", weight=1.5, max_depth=50):
    if isinstance(initial_state, tuple):
        initial_state = PancakeState(initial_state)
    heuristic_func = getHeuristicByName(heuristic_name) 

    if method == "bfs":
        return breadth_first_search(initial_state, goal_pancake_state, child_pancake_states)
    elif method == "dfs":
        return depth_first_search(initial_state, goal_pancake_state, child_pancake_states)
    elif method == "dls":
        return depth_limited_search(initial_state, goal_pancake_state, child_pancake_states, max_depth)
    elif method == "ids":
        return iterative_deepening_search(initial_state, goal_pancake_state, child_pancake_states, max_depth)
    elif method == "ucs":
        return uniform_cost_search(initial_state, goal_pancake_state, child_pancake_states)
    elif method == "greedy":
        return greedy_search(initial_state, goal_pancake_state, child_pancake_states, heuristic_func)
    elif method == "astar":
        return a_star_search(initial_state, goal_pancake_state, child_pancake_states, heuristic_func)
    elif method == "wastar":
        return weighted_a_star_search(initial_state, goal_pancake_state, child_pancake_states, heuristic_func, weight)