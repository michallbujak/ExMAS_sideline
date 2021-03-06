import numpy as np
import pickle
import os

import pandas as pd
import seaborn

from ExMAS.main_prob import main as exmas_algo
from NYC_tools import NYC_data_prep_functions as nyc_func
import Topology.utils_topology as utils
import matplotlib.pyplot as plt
import networkx as nx
from networkx.algorithms import bipartite
import datetime

num_list = [1] + list(range(100, 1000, 100))

topological_config = utils.get_parameters('data/configs/topology_settings.json')
utils.create_results_directory(topological_config)

os.chdir(r'C:\Users\szmat\Documents\GitHub\ExMAS_sideline\Topology\data\results\06-06-22')

with open('all_graphs_list_06-06-22.obj', 'rb') as file:
    e = pickle.load(file)




