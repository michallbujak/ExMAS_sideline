import os
import sys
import numpy as np
import pickle

sys.path.append(os.path.abspath(os.getcwd()))
sys.path.append(os.path.abspath(os.path.dirname(os.getcwd())))

import Utils.utils_topology as utils
import NYC_tools.NYC_data_prep_functions as nyc_tools
from ExMAS.probabilistic_exmas import main as exmas_algo

if __name__ == "__main__":
    # """ Load all the topological parameters """
    config = utils.get_parameters(
        r"C:\Users\szmat\Documents\GitHub\ExMAS_sideline\Miscellaneous_scripts\configs\test_config.json"
    )

    """ Set up varying parameters (optional) """
    config.variable = 'shared_discount'
    config.values = [0.30] # np.arange(0, 0.51, 0.01)

    """ Run parameters """
    config.replications = 1
    config.no_batches = 1

    """ Prepare folder """
    utils.create_results_directory(config)

    """ Prepare data """
    # dotmaps_list, exmas_params = nyc_tools.prepare_batches(config.no_batches,
    #                                                  filter_function=lambda x: (len(x.requests) < 150) &
    #                                                                            (len(x.requests) > 140),
    #                                                  config=config.initial_parameters)
    # with open("data/exemplary_demand.obj", "wb") as file:
    #     pickle.dump(dotmaps_list, file)
    # with open("data/params_in_process.obj", "wb") as file:
    #     pickle.dump(exmas_params, file)

    with open("data/exemplary_demand.obj", "rb") as file:
        dotmaps_list = pickle.load(file)
    with open("data/params_in_process.obj", "rb") as file:
        params = pickle.load(file)

    """ Run ExMAS """
    params = utils.update_probabilistic(config, params)
    config.replications = 1
    s = 1
    params.sampling_function = utils.mixed_discrete_norm_distribution_with_index((0.29, 0.57, 0.81, 1),
                                                                                 ((16.98 / 3600, 1.22),
                                                                                  (s * 1.68 / 3600, s * 0.122)),
                                                                                 ((14.02 / 3600, 1.135),
                                                                                  (s * 1.402 / 3600, s * 0.1135)),
                                                                                 ((26.25 / 3600, 1.049),
                                                                                  (s * 2.625 / 3600, s * 0.105)),
                                                                                 ((7.78 / 3600, 1.18),
                                                                                  (s * 0.778 / 3600, s * 0.118)))
    # utils.display_text(exmas_params, is_dotmap=True)

    dotmaps_list_results, settings_list = nyc_tools.testing_exmas_basic(exmas_algorithm=exmas_algo,
                                                                        params=params,
                                                                        indatas=dotmaps_list,
                                                                        topo_params=config,
                                                                        replications=config.replications,
                                                                        logger_level='INFO',
                                                                        sampling_function_with_index=True)

    # final_results = zip([x.exmas for x in dotmaps_list_results], settings_list)
    # utils.save_with_pickle(dotmaps_list_results, 'dotmap_list', config)
    # utils.save_with_pickle(settings_list, 'config', config)
    print(dotmaps_list_results[0]['exmas']['res'])
