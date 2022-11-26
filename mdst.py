import igraph as ig
from disjoint_set import DisjointSet


def get_mdst(graph: ig.Graph) -> ig.Graph:
    '''
    Функция для нахождения остовного дерева минимальной степени
    '''
    # получаем произвольное остовное дерево
    tree = graph.spanning_tree(return_tree=True)
    # отдельно будем поддерживать лес хороших вершин
    forest = tree.copy()

    # флаг того, что прошлись по всем ребрам и нашли ребро,
    # которое соединяет разные поддеревья в лесу
    was_change = True
    while (was_change):
        max_deg = tree.maxdegree()
        # md - max degree, pmd - pred max degree (max_degree - 1)
        # вершины, которые есть в текущем остовном дереве, но их нет в лесу
        md_vertexes = set(forest.vs.select(_degree=max_deg).indices)
        pmd_vertexes = set(forest.vs.select(_degree=max_deg - 1).indices)

        # превращаем наше дерево в начальный лес
        # удалим только ребра, но оставим сами вершины для удобства реализации
        for v in md_vertexes:
            forest.delete_edges(forest.incident(v))
        for v in pmd_vertexes:
            forest.delete_edges(forest.incident(v))

        components = tree.connected_components()
        set_components = DisjointSet()

        # добавляем в disjoint_set только вершины леса
        for component in components:
            if len(component) == 1:
                if not (component[0] in md_vertexes or component[0] in pmd_vertexes):
                    set_components.find(component[0])
            else:
                for i in range(len(component) - 1):
                    set_components.union(component[i], component[i + 1])

        # будем для каждой вершины степени md - 1 добавленной в лес
        # хранить ребро из улучшающего цикла
        useful_edges = {}
        was_change = False
        for e in graph.es():
            # надо запускать новую итерацию алгоритма,
            # так как максимальная степень дерева уменьшилась
            if len(md_vertexes) == 0:
                break

            u, v = e.tuple

            # проверка на то, что вершины u, v из леса и лежат в разных поддеревьях
            if (u in md_vertexes) or (u in pmd_vertexes):
                continue
            if (v in md_vertexes) or (v in pmd_vertexes):
                continue
            if set_components.connected(u, v):
                continue

            path = tree.get_shortest_paths(u, to=v)
            path_md = max(tree.degree(path))
            if path_md == max_deg - 1:
                # случай когда в пути нет вершины максимальной степени
                for i in range(len(path) - 1):
                    set_components.union(path[i], path[i + 1])
                    forest.add_edges([(path[i], path[i + 1])])
                    if (tree.degree(path[i]) == max_deg - 1):
                        useful_edges[path[i]] = (u, v)
                        pmd_vertexes.remove(path[i])
            else:
                # случай, когда в пути есть вершина максимальной степени

                # если концы текущего взятого ребра блокируют вершину, которую хотим улучшить,
                # то их самих нужно улучшить
                # заметим, что нужно одновременно модифицировать и лес, и остовное дерево
                if (tree.degree(u) == max_deg - 1):
                    paths = forest.get_shortest_paths(u, useful_edges[u])
                    # следим за тем, чтобы не удалить ребро из полученного пути
                    # а то будем грустно, и придется искать новый путь
                    if (paths[0][0] != path[0]):
                        forest.delete_edges([paths[0][0], ])
                        tree.delete_edges([paths[0][0], ])
                    else:
                        forest.delete_edges([paths[1][0], ])
                        tree.delete_edges([paths[1][0], ])

                    forest.add_edges([useful_edges[u], ])
                    tree.add_edges([useful_edges[u], ])

                # почти копипаста ифа выше, кроме одного индекса
                # TODO: вынести в отдельную функцию, если я смогу придумать норм название
                if (tree.degree(v) == max_deg - 1):
                    paths = forest.get_shortest_paths(v, useful_edges[v])
                    if (paths[0][0] != path[-1]):
                        forest.delete_edges([paths[0][0], ])
                        tree.delete_edges([paths[0][0], ])
                    else:
                        forest.delete_edges([paths[1][0], ])
                        tree.delete_edges([paths[1][0], ])

                    forest.add_edges([useful_edges[v], ])
                    tree.add_edges([useful_edges[v], ])

                # ищем вершину максимальной степени,
                # и произвольную соседнюю в пути
                ind = tree.degree(path).index(max_deg)
                n_big_v, big_v = path[[ind - 1, ind]]

                # модифицируем дерево
                tree.delete_edges(tree.get_eid(n_big_v, big_v))
                tree.add_edges([(u, v), ])

                # модифицируем лес
                # заметим, что ребро (n_big_v, big_v) удалять не надо,
                # оно и так не лежит в лесу
                forest.add_edges([(u, v), ])
                set_components.union(u, v)

                # корректно обрабатываем множества вершин, не лежащих в лесу
                md_vertexes.remove(big_v)
                pmd_vertexes.add(big_v)

                if (tree.degree(n_big_v) == max_deg - 1):
                    md_vertexes.remove(n_big_v)
                    pmd_vertexes.add(n_big_v)
                if (tree.degree(n_big_v) == max_deg - 2):
                    pmd_vertexes.remove(n_big_v)
                    # n_big_v теперь маленькой степени, нужно её добавить в лес
                    for v in tree.neighbors(n_big_v):
                        if not (v in md_vertexes or v in pmd_vertexes):
                            forest.add_edges([(n_big_v, v), ])
                            set_components.union(n_big_v, v)
                    # если из n_big_v нет ребер в текущий лес,
                    # то она образует новую компоненту связности
                    # следующая строчка добавить новое множество в disjoint_set
                    set_components.find(n_big_v)

                # уменьшили количество вершин с максимальной степенью
                was_change = True

    return tree
