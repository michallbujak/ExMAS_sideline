import pickle
import os
import argparse

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import matplotlib.pylab as pylab
from matplotlib.markers import MarkerStyle
from matplotlib.ticker import PercentFormatter

from pricing_functions import _expected_flat_measures
from pricing_functions import *
from matching import matching_function
from auxiliary_functions import extract_selected_discounts, extract_selected_profitability, bracket

parser = argparse.ArgumentParser()
parser.add_argument("--no-requests", type=int, required=True)
parser.add_argument("--sample-size", type=int, required=True)
parser.add_argument("--profitability", action="store_false")
parser.add_argument("--min-accept", type=float, default=0.1)
parser.add_argument("--operating-cost", type=float, default=0.5)
parser.add_argument("--analysis-parts", nargs='+', type=int, default=[1] * 7)
parser.add_argument("--discounts", nargs='+', type=int, default=[0.2])
parser.add_argument("--avg-speed", type=float, default=6)
parser.add_argument("--price", type=float, default=1.5)
parser.add_argument("--guaranteed-discount", type=float, default=0.05)
parser.add_argument("--separate", action='store_false')
parser.add_argument("--dpi", type=int, default=300)
parser.add_argument("--pic-format", type=str, default='png')
args = parser.parse_args()
print(args)

_num = args.no_requests
_sample = args.sample_size

if os.getcwd()[-len("Individual_pricing"):] == "Individual_pricing":
    path = os.getcwd()
else:
    path = path_joiner(os.getcwd(), "Individual_pricing")
path = path_joiner(path, 'data')
path = path_joiner(path, str(_num) + '_' + str(_sample))


if args.profitability:
    path = path_joiner(path, 'results_[' + str(_num) + ', ' + str(_num) + ']_' + str(_sample))
else:
    res_name = 'results_[' + str(_num) + ', ' + str(_num) + ']_' + str(_sample)
    res_name += "_" + str(args.operating_cost) + "_" + str(args.min_accept)
    path = path_joiner(path, res_name)

try:
    with open(path + '_amended.pickle', "rb") as file:
        data = pd.read_pickle(file)
except FileNotFoundError:
    with open(path + '.pickle', "rb") as file:
        data = pd.read_pickle(file)[0]

os.chdir(os.path.join(os.getcwd(), "results"))
res_path = os.path.join(os.getcwd(), str(_num) + "_" + str(_sample))

try:
    os.chdir(res_path)
except FileNotFoundError:
    os.mkdir(res_path)
    os.chdir(res_path)

if not args.profitability:
    res_path = os.path.join(res_path,
                            str(args.operating_cost) + "_" + str(args.min_accept))
    try:
        os.chdir(res_path)
    except FileNotFoundError:
        os.mkdir(res_path)
        os.chdir(res_path)

rr = data["exmas"]["recalibrated_rides"]
schedule_profit = data['exmas']['schedules']['profitability']
schedule_profit_sh = schedule_profit.loc[[len(t) > 1 for t in schedule_profit['indexes']]]

avg_discount = np.mean(
    [a for b in schedule_profit_sh['best_profit'].apply(lambda x: list(x[1])) for a in b]
)
avg_discount = round(avg_discount, 2)

discounts = [avg_discount] + args.discounts
discounts_names = ['0' + str(int(100 * disc)) for disc in discounts]
discounts_labels = ['Personalised'] + ['Flat discount ' + str(d) for d in discounts]

# Conduct analysis for flat discount if not conducted yet
if data.get('flat_analysis') == discounts:
    pass
else:
    for name, disc in zip(discounts_names, discounts):
        rr[name + '_accepted'] = rr.apply(lambda x: all([calculate_delta_utility(
            discount=disc,
            price=1.5 / 1000,
            ns_trip_dist=x['individual_distances'][j],
            vot=0.0046,
            wts=1.14756,
            travel_time_ns=x['individual_distances'][j] / args.avg_speed,
            travel_time_s=x['individual_times'][j]
        ) > 0 for j in range(len(x['indexes']))]),
                                          axis=1)

        rr["prod_prob_" + name] = rr.apply(check_prob_if_accepted, axis=1, discount=disc)
        rr["probs_" + name] = rr.apply(check_prob_if_accepted, axis=1, discount=disc, total=False)

        rr['rev_cost'] = rr.apply(
            lambda x: _expected_flat_measures(
                vector_probs=x["probs_" + name],
                shared_dist=x['u_veh'] * args.avg_speed,
                ind_dists=x['individual_distances'],
                price=args.price,
                sharing_disc=disc,
                guaranteed_disc=args.guaranteed_discount
            ),
            axis=1
        )

        rr[name + '_profitability'] = rr.apply(
            lambda row: len(row['indexes']) * row['rev_cost'][0] / row['rev_cost'][1]
            if row['rev_cost'][1] != 0 else 0,
            axis=1
        )

        for oc in discounts:
            rr[name + '_profit_' + str(int(100 * oc))] = rr['rev_cost'].apply(
                lambda el: el[0] - oc * el[1]
            ).copy()
            data = matching_function(
                databank=data,
                objectives=[name + '_profit_' + str(int(100 * oc))],
                min_max='max',
                filter_rides=False,  # name + '_accepted',
                opt_flag=""
            )

        data = matching_function(
            databank=data,
            objectives=[name + '_profitability'],
            min_max='max',
            filter_rides=False,  # name + '_accepted',
            opt_flag=""
        )
    data['flat_analysis'] = discounts

    with open(path + '_amended.pickle', "wb") as file:
        pickle.dump({
            'exmas': data['exmas'],
            'flat_analysis': data['flat_analysis']
        }, file)

    raise Warning("Please, rerun the project to ensure the data integrity")

# Now analysis
singles = rr.loc[[len(t) == 1 for t in rr['indexes']]].copy()
shared = rr.loc[[len(t) > 1 for t in rr['indexes']]].copy()

shared["prob"] = shared["best_profit"].apply(lambda x: np.prod(x[3]))
rr["prob"] = rr["best_profit"].apply(lambda x: np.prod(x[3]))

params = {'legend.fontsize': 'x-large',
          'figure.figsize': (8, 5),
          'axes.labelsize': 'x-large',
          'axes.titlesize': 'x-large',
          'xtick.labelsize': 'x-large',
          'ytick.labelsize': 'x-large'}
pylab.rcParams.update(params)

if args.analysis_parts[0]:
    for obj in data['exmas']['objectives']:
        obj_no_int = obj.replace('_int', '')
        print(f"RIDE-HAILING: {obj}:\n {sum(singles[obj_no_int])} ")
        print(f"RIDE-POOLING: {obj}:\n {sum(data['exmas']['schedules'][obj][obj_no_int])} \n")

if args.analysis_parts[1]:
    objectives_to_plot = ['profitability'] + [t + "_profitability" for t in discounts_names]
    _d = {}
    for obj in data['exmas']['schedules'].keys():
        _d[obj] = [len(t) for t in data['exmas']['schedules'][obj]["indexes"]]

    max_deg = max(max(j for j in tt) for tt in _d.values())

    _df = {}
    for k, v in _d.items():
        c = Counter(v)
        _df[k] = [c[j] for j in range(1, max(v) + 1)]

    _df = {k: v for k, v in _df.items() if
           k in objectives_to_plot}
    _df2 = {j: [] for j in range(1, max_deg + 1)}
    for k, v in _df.items():
        for j in range(1, max_deg + 1):
            _df2[j].append(v[j - 1] if j <= len(v) else 0)

    x = np.arange(len(_df.keys()))
    width = 0.2  # the width of the bars
    multiplier = 0
    fig, ax = plt.subplots()

    for attribute, measurement in _df2.items():
        offset = width * multiplier
        rects = ax.bar(x + offset, measurement, width, label=attribute)
        ax.bar_label(rects, padding=0)
        multiplier += 1

    ax.set_ylabel('Number of rides')
    ax.set_xticks(x + width, discounts_labels)
    lgd = ax.legend(title='Degree', bbox_to_anchor=(1.02, 1), borderaxespad=0, ncols=2, loc='upper left')
    ax.set_ylim(0, max(max(t) for t in _df.values()) + 5)
    plt.savefig('degrees_' + str(_sample) + '.' + args.pic_format, dpi=args.dpi,
                bbox_extra_artists=(lgd,), bbox_inches='tight')
    plt.close()

    penguins = sns.load_dataset("penguins")
    _df3 = pd.DataFrame(_df2)
    _df3['kind'] = discounts_labels
    for num in [2, 3, 4]:
        _df3[num] = _df3[num].apply(lambda x: num*x)
    _df4 = pd.DataFrame(columns=['degree', 'kind'])
    for out_lab, (lab, row) in enumerate(_df3.iterrows()):
        cur_kind = discounts_labels[out_lab]
        for deg in range(1, 5):
            for en in range(row[deg]):
                _df4 = pd.concat([_df4, pd.DataFrame({'degree': [str(deg)], 'kind': [cur_kind]})])
    _df4 = _df4.reset_index(drop=True)
    fig, ax = plt.subplots()
    sns.histplot(x='kind', data=_df4, hue='degree', multiple='stack', shrink=0.9,
                 hue_order=[str(t) for t in range(3, 0, -1)])
    lgd = ax.legend(title='Degree', labels=range(1, 4), title_fontsize='x-large',
                    bbox_to_anchor=(1.15, 1), borderaxespad=0, loc='upper right')
    plt.xlabel(None)
    plt.ylabel(None)
    plt.yticks(np.arange(0, 180, 30))
    # plt.tight_layout()
    plt.savefig('degrees_stacked_' + str(_sample) + '.' + args.pic_format, dpi=args.dpi,
                bbox_extra_artists=(lgd,), bbox_inches='tight')
    plt.close()
    raise Exception('aa')

if args.analysis_parts[2]:
    obj_discounts = {'all': [a for b in shared["best_profit"].apply(lambda x: x[1]) for a in b],
                     'selected': [a for b in
                                  shared.loc[shared['selected_profitability'] == 1,
                                  'best_profit'].apply(lambda x: x[1])
                                  for a in b]
                     }
    fig, ax = plt.subplots()
    plt.hist(list(obj_discounts.values()), stacked=False, density=True, label=['All', 'Selected'],
             weights=[[1 / max(t)] * len(t) for t in list(obj_discounts.values())])
    ax.legend()
    ax.set_xlim(0.05, 0.55)
    plt.yticks([])
    plt.tight_layout()
    plt.savefig('discounts_density_' + str(_sample) + '.' + args.pic_format, dpi=args.dpi)
    plt.close()

    fig, ax = plt.subplots()
    sns.kdeplot(list(obj_discounts.values())[0], label='All')
    sns.kdeplot(list(obj_discounts.values())[1], label='Selected')
    ax.legend()
    ax.set_xlim(0.05, 0.55)
    plt.yticks([])
    plt.tight_layout()
    plt.savefig('discounts_density_kde_' + str(_sample) + '.' + args.pic_format, dpi=args.dpi)
    plt.close()

if args.analysis_parts[3] + args.analysis_parts[4] >= 1:
    selected_objectives = ['selected_profitability']
    selected_objectives += ['selected_' + t + '_profitability' for t in discounts_names]
    selected = {
        objective: (shared.loc[rr[objective] == 1], name)
        for objective, name in zip(selected_objectives, discounts_labels)
    }

if args.analysis_parts[3]:
    col_labels = ["prob"] + ["prod_prob_" + t for t in discounts_names]
    dat = []
    labels = []
    for num, (sel, name) in enumerate(selected.values()):
        dat += [list(sel[col_labels[num]])]
        labels += [name]

    fig, ax = plt.subplots()
    plt.hist(dat, label=labels)
    ax.legend(loc='upper left')
    plt.xlabel(None)
    plt.tight_layout()
    plt.savefig("probability_shared_" + str(_sample) + "_sel." + args.pic_format, dpi=args.dpi)
    plt.close()

    fig, ax = plt.subplots()
    for _d, _l in zip(dat, labels):
        sns.kdeplot(_d, label=None, bw_method=0.2)
    plt.ylabel(None)
    ax.set_yticks([])
    plt.yticks(None)
    plt.tight_layout()
    plt.savefig("probability_shared_" + str(_sample) + "_sel_kde." + args.pic_format, dpi=args.dpi)
    plt.close()

    dat = []
    labels = []
    for obj, label in zip(col_labels, discounts_labels):
        r_s = rr.loc[[len(t) != 1 for t in rr["indexes"]]]
        dat += [list(r_s[obj])]
        labels += [label]

    fig, ax = plt.subplots()
    plt.hist(dat, label=labels)
    # ax.legend(loc='upper right')
    # ax.get_legend().remove()
    plt.xlabel(None)
    plt.tight_layout()
    plt.savefig("probability_shared_" + str(_sample) + "_all." + args.pic_format, dpi=args.dpi)
    plt.close()

    fig, ax = plt.subplots()
    for _d, _l in zip(dat, labels):
        sns.kdeplot(_d, label=_l, bw_method=0.2)
    ax.legend(loc='upper right')
    plt.ylabel(None)
    plt.yticks(None)
    ax.set_yticks([])
    plt.tight_layout()
    plt.savefig("probability_shared_" + str(_sample) + "_all_kde." + args.pic_format, dpi=args.dpi)
    plt.close()

if args.analysis_parts[4]:
    temp_data = rr.loc[rr['selected_profitability'] == 1]
    results = {
        'profitability': [np.mean(temp_data['profitability'])],
        'e_dist': [sum(temp_data['best_profit'].apply(lambda x: x[4]))]
    }
    for flat_disc in discounts_names:
        temp_data = rr.loc[rr['selected_' + flat_disc + '_profitability'] == 1]
        results['profitability'] += [np.mean(temp_data[flat_disc + '_profitability'])]
        results['e_dist'] += [sum(temp_data.apply(
            lambda x: (x['veh_dist'] * x["prod_prob_" + flat_disc] +
                       sum(x['individual_distances']) * (1 - x["prod_prob_" + flat_disc])) / 1000,
            axis=1
        ))]
    results['profitability'] += [1.5]
    results['e_dist'] += [sum(singles['veh_dist']) / 1000]

    results = pd.DataFrame(results)
    results.index = discounts_labels + ['Private only']
    results = results.round(2)
    print(results.to_latex())

if args.analysis_parts[5]:
    results, results_list = extract_selected_discounts(rr, discounts_names)

    fig, ax = plt.subplots()

    for k, v in results.items():
        sns.kdeplot(v, label=k, bw_adjust=1)

    ax.legend(loc='upper left')
    plt.xlabel(None)
    plt.ylabel(None)
    plt.tight_layout()
    plt.savefig("profitability_" + str(_sample) + "_sel." + args.pic_format, dpi=args.dpi)
    plt.close()

    fig, ax = plt.subplots()
    plt.hist(results_list, label=['Personalised'] + discounts_names,
             stacked=False, density=True,
             weights=[[1 / max(t)] * len(t) for t in results_list])
    ax.legend(loc='upper right')
    plt.xlabel(None)
    plt.ylabel(None)
    plt.tight_layout()
    plt.savefig("profitability_" + str(_sample) + "_sel_hist." + args.pic_format, dpi=args.dpi)
    plt.close()

if args.analysis_parts[6]:
    profitability_scatter = [(x, num) for num, x in enumerate(list(shared['profitability']))]
    profitability_scatter.sort(reverse=False)
    profitability_scatter, permutation = zip(*profitability_scatter)
    profitability_scatter = [list(profitability_scatter)]
    for disc_name in discounts_names:
        dat = list(shared[disc_name + '_profitability'])
        dat = [dat[t] for t in permutation]
        profitability_scatter += [dat]
    degrees = [len(t) for t in shared['indexes']]
    degrees = list(Counter(degrees).values())
    degrees_positions = list(np.cumsum(degrees))
    degrees_positions = [int(t1 + t2 / 2)
                         for t1, t2 in zip([0] + degrees_positions[:-1], degrees)]

    fig, ax = plt.subplots()
    for num, cur_label in enumerate(discounts_labels):
        dat = profitability_scatter[num]
        if num == 0:
            size = 2
        else:
            size = 1
        plt.scatter(x=range(len(dat)), y=dat, label=discounts_labels[num], s=2,
                    edgecolors='none')

    for num, (deg_len, deg_post) in enumerate(zip(degrees, [0] + list(np.cumsum(degrees)))):
        bracket(ax, text=str(num + 2), pos=[deg_post, -0.01], scalex=deg_len,
                linekw={'color': "black", 'lw': 1}, textkw={'size': 12})

    # ax.set_xticks(degrees_positions, [t + 2 for t in range(len(degrees_positions))])
    ax.set_xticks([])
    lgnd = plt.legend(loc='upper left', fontsize=10)
    for handle in lgnd.legend_handles:
        handle.set_sizes([30])
    plt.savefig("scatter_all_profitability_balanced_" + str(_sample) + "." + args.pic_format, dpi=args.dpi)
    plt.close()

    shared['profitability_unbalanced'] = shared.apply(
        lambda row: row['profitability'] / len(row['indexes']),
        axis=1
    )
    for disc_name in discounts_names:
        shared[disc_name + '_profitability_unbalanced'] = shared.apply(
            lambda row: row[disc_name + '_profitability'] / len(row['indexes']),
            axis=1
        )

    shared_reordered = shared.copy()
    shared_reordered = shared_reordered.reset_index(drop=True)
    unbalanced = [shared_reordered.apply(
        lambda row: (row.name, 'Personalised', len(row['indexes']), row['profitability_unbalanced']),
        axis=1
    ).to_list()]
    unbalanced[0].sort(key=lambda it: (it[2], it[3]))
    new_order = [t[0] for t in unbalanced[0]]
    shared_reordered = shared_reordered.reindex(new_order)

    for disc_name, label in zip(discounts_names, discounts_labels[1:]):
        unbalanced += [shared_reordered.apply(
            lambda row: (row.name, label, len(row['indexes']), row[disc_name + '_profitability_unbalanced']),
            axis=1
        ).to_list()]

    if args.separate:
        _range = range(2, 5)
    else:
        _range = [0]

    for _deg in _range:
        if args.separate:
            temp_data = [[ins for ins in outs if ins[2] == _deg] for outs in unbalanced]
        else:
            temp_data = unbalanced
        fig, ax = plt.subplots()
        for num, cur_label in enumerate(discounts_labels):
            if num == 0:
                size = 2
            else:
                size = 1
            plt.scatter(x=range(len(temp_data[num])), y=[t[3] for t in temp_data[num]], label=cur_label, s=size,
                        edgecolors='none')

        if not args.separate:
            for num, (deg_len, deg_post) in enumerate(zip(degrees, [0] + list(np.cumsum(degrees)))):
                bracket(ax, text=str(num + 2), pos=[deg_post, -0.01], scalex=deg_len,
                        linekw={'color': "black", 'lw': 1}, textkw={'size': 12})

        ax.set_xticks([])
        plt.ylim(1.1, 2.3)
        if _deg != list(_range)[0]:
            plt.yticks([])
        else:
            plt.yticks(fontsize=20)
        if _deg == list(_range)[-1]:
            lgnd = plt.legend(loc='upper left', fontsize=20)
            for handle in lgnd.legend_handles:
                handle.set_sizes([100])
        plt.tight_layout()
        if args.separate:
            plt.savefig("scatter_all_profitability_unbalanced_" + str(_deg) + "_"
                        + str(_sample) + "." + args.pic_format, dpi=args.dpi)
        else:
            plt.savefig("scatter_all_profitability_unbalanced_" + str(_sample) + "." + args.pic_format, dpi=args.dpi)
        plt.close()

    shared_reordered['dist_prop'] = shared_reordered.apply(
        lambda row: 1 - row['u_veh'] * args.avg_speed / sum(row['individual_distances']),
        axis=1
    )

    output_list = shared_reordered.apply(
        lambda row: [row['dist_prop'], row['profitability_unbalanced']] +
                    [row[t + '_profitability_unbalanced'] for t in discounts_names],
        axis=1
    ).to_list()

    output_list.sort(key=lambda it: it[0])

    fig, ax = plt.subplots()
    for _num in range(len(output_list[0]) - 1):
        _size = 1 if _num != 0 else 2
        _lab = discounts_labels[_num]
        plt.scatter(x=[t[0] for t in output_list], y=[t[1 + _num] for t in output_list],
                    s=_size, label=_lab)
    lgnd = plt.legend(loc='upper left', fontsize=10)
    for handle in lgnd.legend_handles:
        handle.set_sizes([30])
    ax.xaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
    plt.tight_layout()
    plt.savefig('scatter_all_distance_saved_profitability_' + str(_sample) + "." + args.pic_format, dpi=args.dpi)
    plt.close()

    from numpy.polynomial.polynomial import Polynomial
    x, y = [t[0] for t in output_list], [t[1] for t in output_list]
    _Poly = Polynomial.fit(x, y, 5)
    x_plot, y_plot = _Poly.linspace(n=1000, domain=[min(x), max(x)])

    fig, ax = plt.subplots()
    plt.scatter(x=x, y=y, s=1, label='Expected profitability')
    plt.plot(x_plot, y_plot, lw=1.5, color='red', label='Polynomial fit')
    plt.legend(loc='upper left', fontsize=10, markerscale=3)
    plt.tight_layout()
    plt.savefig('scatter_distance_saved_profitability_' + str(_sample) + "." + args.pic_format, dpi=args.dpi)

