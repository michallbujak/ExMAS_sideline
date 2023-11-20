import pandas as pd
import numpy as np
import networkx as nx

df = pd.read_csv('data/rejony.att', skiprows=85, delimiter=";", index_col=0)
df = df[[isinstance(t, str) for t in df["WOJEWODZTWO"]]]
df["REGION_ID"] = list(df.index)
df = df.rename(columns={"NAME": "NEIGHBOURS"})
df["NEIGHBOURS"] = df["NEIGHBOURS"].apply(lambda x: [int(t) for t in x.split(',')])
df["NEIGHBOURS"] = df.apply(lambda x: [t for t in x["NEIGHBOURS"] if t != x["REGION_ID"]], axis=1)
df["CITIZENS"] = df.apply(lambda x: int(x["MR_LUDN"]) if
((not np.isnan(x["MR_LUDN"])) & (x["MR_LUDN"] != 0)) else
int(x["G_LUD_TOTAL"]), axis=1)

adj_graph = nx.Graph()
adj_graph.add_nodes_from([
    (t[1]["REGION_ID"], {"CITIZENS": t[1]["CITIZENS"]})
    for t in df.iterrows()
])

dist_matrix = pd.read_csv('data/DIS2.csv', sep=';', index_col=0)
dist_matrix.columns = [int(t) for t in dist_matrix.columns]


for node, neighbours in df["NEIGHBOURS"].items():
    nodes_ns = []
    for neighbour in neighbours:
        nodes_ns += [neighbour]
        adj_graph.add_edge(node, neighbour, weight=dist_matrix.loc[node, neighbour])

    if len(nodes_ns) == 0:
        print(0)

x = 0
