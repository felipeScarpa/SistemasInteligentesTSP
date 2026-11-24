"""
Entrada : CSV com uma linha por nó e as coordenadas "x,y". A primeira linha é
          o ponto inicial e final. Cabeçalho opcional é ignorado.
Saída   : CSV com colunas geracao, melhor_fitness, fitness_medio, caminho.
          O caminho é o do melhor indivíduo da geração.

Representação: com n nós, o indivíduo é uma permutação dos genes 0..n-2, onde
o gene g representa o nó g+1. O nó 0 é fixo no início e no fim. Os genes
começam em 0 porque cxOrdered e cxPartialyMatched da DEAP usam os valores dos
genes como índices.

Fitness: distância total do percurso fechado (minimização, weights=(-1.0,)).
"""
import time
import argparse
import csv
import math
import random
from deap import algorithms, base, creator, tools


PARAMETROS = {
    # --- arquivos ---
    "entrada": "datasets/u159.csv",
    "saida": "resultado_ga_u159.csv",

    # --- população e evolução ---
    "tam_populacao": 30,
    "geracoes": 10000000,
    "elite": 2,

    # --- seleção ---
    "tam_torneio": 3,

    # --- crossover ---
    "crossover": "ordered",           # "ordered" (OX) ou "pmx" (partially matched)
    "prob_crossover": 0.9,

    # --- mutação ---
    "mutacao": "inversao",               # "troca", "inversao" ou "mista" (sorteia uma das duas)
    "prob_mutacao": 0.2,
    "prob_gene_troca": None,          # na troca: chance por gene; None = automático (2 / nº de genes)

    # --- execução ---
    "semente": 42,
    "salvar_a_cada": 100,               # grava uma linha no CSV a cada N gerações
    "log_a_cada": 100,                 # imprime o progresso a cada N gerações (0 = só o final)
}

# Valores aceitos nos parâmetros de texto
OPCOES = {
    "crossover": ["ordered", "pmx"],
    "mutacao": ["troca", "inversao", "mista"],
}

# Parâmetros cujo padrão é None precisam de um tipo explícito na linha de comando
TIPOS_OPCIONAIS = {"semente": int, "prob_gene_troca": float}


creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individuo", list, fitness=creator.FitnessMin)


# ----------------------------------------------------------------------
# Parâmetros: linha de comando e validação
# ----------------------------------------------------------------------
def ler_parametros():
    """Começa dos valores de PARAMETROS e aplica o que vier na linha de comando."""
    ap = argparse.ArgumentParser(
        description="Algoritmo genético (DEAP) para o TSP métrico. "
                    "Os padrões vêm do dicionário PARAMETROS no topo do arquivo.")
    for nome, padrao in PARAMETROS.items():
        tipo = TIPOS_OPCIONAIS.get(nome, type(padrao))
        ap.add_argument(f"--{nome}", type=tipo, default=padrao,
                        choices=OPCOES.get(nome))
    args = ap.parse_args()
    p = vars(args)

    return p


# ----------------------------------------------------------------------
# Entrada e distâncias
# ----------------------------------------------------------------------
def ler_instancia(caminho_csv):
    with open(caminho_csv, newline="") as f:
        linhas = [l.strip() for l in f if l.strip()]

    primeira = linhas[0]
    if "\t" in primeira:
        sep = "\t"
    else:
        sep = ","

    pontos = []
    for i, linha in enumerate(linhas):
        campos = [c.strip() for c in linha.split(sep)]

        pontos.append((float(campos[0]), float(campos[1])))
    return pontos


def matriz_distancias(pontos):
    n = len(pontos)
    d = [[0.0] * n for _ in range(n)]
    for i in range(n):
        xi, yi = pontos[i]
        for j in range(i + 1, n):
            d[i][j] = d[j][i] = math.hypot(xi - pontos[j][0], yi - pontos[j][1])
    return d


# ----------------------------------------------------------------------
# Fitness e operadores
# ----------------------------------------------------------------------
def caminho_completo(ind):
    """Converte os genes em nós e fecha o percurso: 0 -> ... -> 0."""
    return [0] + [g + 1 for g in ind] + [0]


def avaliar(ind, dist):
    """Fitness: distância total do percurso. A DEAP exige uma tupla."""
    c = caminho_completo(ind)
    return (sum(dist[a][b] for a, b in zip(c, c[1:])),)


def montar_mutacao(tipo, indpb_troca, num_genes):
    """Devolve a função de mutação escolhida (cada uma retorna uma tupla, como a DEAP exige)."""
    indpb = indpb_troca if indpb_troca is not None else min(1.0, 2.0 / num_genes)

    def troca(ind):
        return tools.mutShuffleIndexes(ind, indpb=indpb)

    def inversao(ind):
        i, j = sorted(random.sample(range(len(ind)), 2))
        ind[i:j + 1] = ind[i:j + 1][::-1]
        return (ind,)

    def mista(ind):
        return troca(ind) if random.random() < 0.5 else inversao(ind)

    return {"troca": troca, "inversao": inversao, "mista": mista}[tipo]


def montar_toolbox(dist, p):
    m = len(dist) - 1  # número de genes (todos os nós, menos o inicial)
    nome_crossover = {"ordered": "cxOrdered", "pmx": "cxPartialyMatched"}[p["crossover"]]

    tb = base.Toolbox()
    tb.register("genes", random.sample, range(m), m)
    tb.register("individuo", tools.initIterate, creator.Individuo, tb.genes)
    tb.register("populacao", tools.initRepeat, list, tb.individuo)
    tb.register("evaluate", avaliar, dist=dist)
    tb.register("mate", getattr(tools, nome_crossover))
    tb.register("mutate", montar_mutacao(p["mutacao"], p["prob_gene_troca"], m))
    tb.register("select", tools.selTournament, tournsize=p["tam_torneio"])
    return tb


def avaliar_invalidos(tb, pop):
    """Calcula o fitness só dos indivíduos que foram alterados."""
    invalidos = [ind for ind in pop if not ind.fitness.valid]
    for ind, fit in zip(invalidos, map(tb.evaluate, invalidos)):
        ind.fitness.values = fit


# ----------------------------------------------------------------------
# Algoritmo genético
# ----------------------------------------------------------------------
def algoritmo_genetico(tb, p, registrar):
    """
    Evolui a população. A cada geração chama registrar(g, melhor_ind, estat),
    onde estat = {"min": ..., "avg": ...} (g = 0 é a população inicial).
    Devolve o melhor indivíduo encontrado (HallOfFame).
    """
    stats = tools.Statistics(lambda ind: ind.fitness.values[0])
    stats.register("min", min)
    stats.register("avg", lambda xs: sum(xs) / len(xs))
    hof = tools.HallOfFame(p["elite"])

    pop = tb.populacao(n=p["tam_populacao"])
    avaliar_invalidos(tb, pop)
    hof.update(pop)
    registrar(0, tools.selBest(pop, 1)[0], stats.compile(pop))

    for g in range(1, p["geracoes"] + 1):
        elite_inds = [tb.clone(ind) for ind in hof]                  # elitismo
        filhos = tb.select(pop, p["tam_populacao"] - len(elite_inds))  # seleção
        filhos = algorithms.varAnd(filhos, tb, cxpb=p["prob_crossover"],
                                   mutpb=p["prob_mutacao"])          # crossover + mutação
        avaliar_invalidos(tb, filhos)
        pop = filhos + elite_inds
        hof.update(pop)
        registrar(g, tools.selBest(pop, 1)[0], stats.compile(pop))

    return hof[0]


# ----------------------------------------------------------------------
# Execução
# ----------------------------------------------------------------------
def main():
    start_time = time.time()

    p = ler_parametros()

    if p["semente"] is not None:
        random.seed(p["semente"])

    pontos = ler_instancia(p["entrada"])
    dist = matriz_distancias(pontos)
    n = len(pontos)
    print(f"Instância: {n} nós (nó 0 = ponto inicial e final)")
    print("Parâmetros:", ", ".join(f"{k}={v}" for k, v in p.items()))

    with open(p["saida"], "w", newline="") as f:
        escritor = csv.writer(f)
        escritor.writerow(["geracao", "melhor_fitness", "fitness_medio", "caminho"])

        def registrar(g, ind, estat):
            fit = ind.fitness.values[0]
            ultima = g == p["geracoes"]
            if g % p["salvar_a_cada"] == 0 or ultima:
                escritor.writerow([g, f"{fit:.6f}", f"{estat['avg']:.6f}",
                                   " ".join(map(str, caminho_completo(ind)))])
                f.flush()  # mantém o CSV íntegro mesmo se a execução for interrompida
            if (p["log_a_cada"] > 0 and g % p["log_a_cada"] == 0) or ultima:
                print(f"geração {g:>5} | melhor = {fit:.4f} | média = {estat['avg']:.4f}")

        tb = montar_toolbox(dist, p)
        algoritmo_genetico(tb, p, registrar)

    print(f"Historico salvo em: {p['saida']}")
    print(f"Tempo de execucao: {time.time() - start_time}")


if __name__ == "__main__":
    main()
