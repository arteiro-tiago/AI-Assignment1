# AI-Assignment1

# Pancake Sorting Problem

Implementação do Pancake Sorting Problem com interface gráfica em pygame e vários algoritmos de pesquisa em IA.



## Requisitos

- Python 3.10+
- pip


---

## Instalação

```bash
# 1. criar ambiente virtual
python3 -m venv .venv

# 2. ativar o ambiente virtual
source .venv/bin/activate

# 3. instalar dependências
pip install -r requirements.txt
```

---

## Como correr

```bash
python3 __main__.py
```

---

## Modos de jogo

### Manual
O utilizador resolve o puzzle sozinho. Basta passar o rato por cima da pancake até onde se quer fazer o flip e clicar. Todas as pancakes acima do ponto de clique são invertidas.

Existe também um botão **Hint** que usa o A* internamente para sugerir o próximo flip ótimo a pancake sugerida fica destacada a branco.

--- 

### AI Solver
O algoritmo escolhido resolve o puzzle automaticamente e a solução é animada passo a passo no ecrã. No ecrã de setup é possível escolher:

**Algoritmo:**
| Nome | Descrição |
|------|-----------|
| `bfs` | Breadth-First Search |
| `dfs` | Depth-First Search |
| `ids` | Iterative Deepening Search |
| `ucs` | Uniform Cost Search |
| `greedy` | Greedy Search |
| `astar` | A* Search |
| `wastar` | Weighted A* Search |

**Heurística** (usada pelo greedy, astar e wastar):
| Nome | Descrição |
|------|-----------|
| `gap` | conta pares adjacentes não consecutivos |
| `adjancy` | semelhante ao gap mas sem verificar o fundo |
| `top_prime` | versão melhorada do gap com lookahead |
| `l_top_prime` | versão ainda mais forte do top_prime |

---

## Ficheiros de input/output

### Carregar um puzzle de ficheiro
No ecrã de setup existe o botão **Load from file** que lê o ficheiro `input.txt` na pasta do projeto.

O formato do ficheiro é:
```
4
3 1 4 2
```
- Primeira linha: número de pancakes
- Segunda linha: ordem inicial separada por espaços

### Resultado guardado automaticamente
No fim de cada jogo (manual ou AI) o resultado é guardado automaticamente em `output.txt` na pasta do projeto.

Exemplo de output:
```
Initial State: (3, 1, 4, 2)
Steps (3 moves):
(3, 1, 4, 2)
(4, 1, 3, 2)
(1, 4, 3, 2)
(1, 2, 3, 4)

Calculation time: 0.00041 s
Used memory: 24576 bytes
Explored states: 12
```

---

## Estrutura do projeto

```
.
├── __main__.py       # ponto de entrada, interface gráfica
├── pancake_brain.py  # algoritmos de pesquisa e heurísticas
├── file_io.py        # leitura e escrita de ficheiros
├── input.txt         # puzzle a carregar (opcional)
├── output.txt        # resultado gerado automaticamente
└── requirements.txt  # dependências
```