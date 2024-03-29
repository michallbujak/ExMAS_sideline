import pickle
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns
from collections import Counter
import matplotlib.pylab as pylab

from pricing_functions import *

_cr = 0.3
_num = 150
_sample = 25

performance = False
plot_degrees = False
plot_discounts = False
prob_distribution = False
res_analysis = True


with open("results_" + str(_num) + "_" + str(_sample) + "_v4.pickle", "rb") as _file:
    data = pickle.load(_file)

rr = data["exmas"]["recalibrated_rides"]
singles = rr.loc[[len(t) == 1 for t in rr['indexes']]].copy()
shared = rr.loc[[len(t) > 1 for t in rr['indexes']]].copy()

if performance:
    for obj in data['exmas']['objectives']:
        obj_no_int = obj.replace('_int', '')
        print(f"RIDE-HAILING: {obj}:\n {sum(singles[obj_no_int])} ")
        print(f"RIDE-POOLING: {obj}:\n {sum(data['exmas']['schedules'][obj][obj_no_int])} \n")

if plot_degrees:
    _d = {}
    for obj in data['exmas']['objectives']:
        _d[obj] = [len(t) for t in data['exmas']['schedules'][obj]["indexes"]]

    _df = {}
    for k, v in _d.items():
        c = Counter(v)
        _df[k] = [c[j] for j in range(1, 4)]

    _df = {k: v for k, v in _df.items() if
           k in ['expected_revenue',
                 'expected_profit_int_20',
                 'expected_profit_int_40',
                 'expected_profit_int_60']}
    _df2 = {j: [] for j in range(1, 4)}
    for k, v in _df.items():
        for j in range(1, 4):
            _df2[j].append(v[j - 1])

    x = np.arange(len(_df.keys()))
    width = 0.25  # the width of the bars
    multiplier = 0
    fig, ax = plt.subplots()

    for attribute, measurement in _df2.items():
        offset = width * multiplier
        rects = ax.bar(x + offset, measurement, width, label=attribute)
        ax.bar_label(rects, padding=0)
        multiplier += 1

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Number of rides')
    # ax.set_title('Penguin attributes by species')
    ax.set_xticks(x + width, ['0 (Revenue)', '0.2', '0.4', '0.6'])
    ax.legend(title='Degree', loc='upper left', ncols=3)
    ax.set_ylim(0, 80)
    ax.set_xlabel("Expected profit with operating cost of")

    plt.savefig('degrees_' + str(_sample) + '.png', dpi=200)

if plot_discounts:
    discounts = shared["best_profit"].apply(lambda x: x[1])
    discounts = [a for b in discounts for a in b]
    discounts_revenue = shared.loc[shared['selected_expected_revenue'] == 1, "best_profit"].apply(lambda x: x[1])
    discounts_revenue = [a for b in discounts_revenue for a in b]
    discounts_profit20 = shared.loc[shared['selected_expected_profit_int_20'] == 1, "best_profit"].apply(lambda x: x[1])
    discounts_profit20 = [a for b in discounts_profit20 for a in b]
    discounts_profit40 = shared.loc[shared['selected_expected_profit_int_40'] == 1, "best_profit"].apply(lambda x: x[1])
    discounts_profit40 = [a for b in discounts_profit40 for a in b]
    discounts_profit60 = shared.loc[shared['selected_expected_profit_int_60'] == 1, "best_profit"].apply(lambda x: x[1])
    discounts_profit60 = [a for b in discounts_profit60 for a in b]
    discounts_no_select = shared.loc[(shared['selected_expected_revenue'] == 0)
                                 & (shared['selected_expected_profit_int_20'] == 0)
                                 & (shared['selected_expected_profit_int_40'] == 0)
                                 & (shared['selected_expected_profit_int_60'] == 0), "best_profit"].apply(lambda x: x[1])
    discounts_no_select = [a for b in discounts_no_select for a in b]

    fig, ax = plt.subplots()
    sns.kdeplot(discounts, color='green', ax=ax, label="All rides")
    sns.kdeplot(discounts_revenue, color='lightcoral', ax=ax, label="Revenue")
    sns.kdeplot(discounts_profit20, color='indianred', ax=ax, label="Profit OC 0.2")
    sns.kdeplot(discounts_profit40, color='brown', ax=ax, label="Profit OC 0.4")
    sns.kdeplot(discounts_profit60, color='darkred', ax=ax, label="Profit OC 0.6")
    sns.kdeplot(discounts_no_select, color='blue', ax=ax, label="Not selected")


    def upper_rugplot(data, height=.02, _ax=None, **kwargs):
        from matplotlib.collections import LineCollection
        _ax = _ax or plt.gca()
        kwargs.setdefault("linewidth", 0.1)
        kwargs.setdefault("color", "green")
        segs = np.stack((np.c_[data, data],
                         np.c_[np.ones_like(data), np.ones_like(data) - height]),
                        axis=-1)
        lc = LineCollection(segs, transform=_ax.get_xaxis_transform(), **kwargs)
        _ax.add_collection(lc)

    upper_rugplot(discounts, _ax=ax)
    sns.rugplot(discounts_revenue, color='lightcoral')
    # sns.kdeplot(discounts_no_select, color='blue', ax=ax, label="Not selected")

    ax.legend(bbox_to_anchor=(1.02, 1.02), loc='upper left')
    plt.tight_layout()
    plt.savefig('discount_density_' + str(_sample) + '_rug.png', dpi=200)

    d_list = [discounts, discounts_revenue, discounts_profit20, discounts_profit40, discounts_profit60]

    print(pd.DataFrame({'mean': [np.mean(t) for t in d_list]},
                       index=["discount", "discounts_revenue", "discounts_profit20", "discounts_profit40", "discounts_profit60"]))


if prob_distribution or res_analysis:
    shared["prob"] = shared["best_profit"].apply(lambda x: x[3])
    rr = data["exmas"]["recalibrated_rides"]
    rr["prob"] = rr["best_profit"].apply(lambda x: x[3])
    # data["d_avg_prob"] = data.apply(check_prob_if_accepted, axis=1, discount=0.203369)
    objectives = ["selected_02_revenue",
                  "selected_03_revenue",
                  "selected_expected_revenue",
                  "selected_expected_profit_int_20",
                  "selected_expected_profit_int_40",
                  "selected_expected_profit_int_60"]
    names = ["Flat disc. 0.2 Revenue",
             "Flat disc. 0.3 Revenue",
             "Pers. Revenue",
             "Pers. Profit OC 0.2",
             "Pers. Profit OC 0.4",
             "Pers. Profit OC 0.6"]
    selected = {
        objective: (shared.loc[rr[objective] == 1], name) for objective, name in zip(objectives, names)
    }

if prob_distribution:
    params = {'legend.fontsize': 'x-large',
              'figure.figsize': (8, 5),
              'axes.labelsize': 'x-large',
              'axes.titlesize': 'x-large',
              'xtick.labelsize': 'x-large',
              'ytick.labelsize': 'x-large'}
    pylab.rcParams.update(params)

    fig, ax = plt.subplots()

    for num, (sel, name) in enumerate(selected.values()):
        if num == 0:
            dat = sel["02_accepted"]
        elif num == 1:
            dat = sel["03_accepted"]
        else:
            dat = sel["prob"]
        # sns.histplot(dat, color=list(mcolors.BASE_COLORS.keys())[num],
        #              cumulative=False, label=name, kde=False, alpha=0.1,
        #              stat="frequency", element="step")
                     # log_scale=True, element="step", fill=False,
                     # cumulative=True, stat="density", label=name)
        # sns.ecdfplot(dat, color=list(mcolors.BASE_COLORS.keys())[num], label=name)
        sns.kdeplot(dat, color=list(mcolors.BASE_COLORS.keys())[num], label=name, bw_adjust=1)
    # ax.legend(bbox_to_anchor=(1.02, 1.02), loc='upper left')
    ax.legend(loc='upper left')
    ax.set_xlim(0, 1)
    # plt.xlabel("Acceptance probability")
    plt.xlabel(None)
    plt.tight_layout()
    # plt.savefig("probability_shared_" + str(_sample) + ".png", dpi=200)
    plt.savefig("probability_shared_" + str(_sample) + "_sel.png", dpi=200)

    fig, ax = plt.subplots()

    for obj, lab in [("02_accepted", "Flat discount 0.2"),
                     ("03_accepted", "Flat discount 0.3"),
                     ("prob", "Personalised")]:
        r_s = rr.loc[[len(t) != 1 for t in rr["indexes"]]]
        # sns.histplot(data[obj], cumulative=False, label=lab, kde=False, alpha=0.1,
        #              stat="frequency", element="step")
        sns.kdeplot(r_s[obj], label=lab, bw_adjust=1)
    # ax.legend(bbox_to_anchor=(1.02, 1.02), loc='upper left')
    ax.legend(loc='upper left')
    # plt.ylabel("Density", fontsize=13)
    ax.set_xlim(0, 1)
    plt.xlabel(None)
    # plt.xlabel("Acceptance probability")
    plt.tight_layout()
    plt.savefig("probability_shared_" + str(_sample) + "_all.png", dpi=200)


if res_analysis:
    schedules = data['exmas']['schedules']

    for name, schedule in schedules.items():
        if name[:2] == "ex":
            schedule["prob"] = schedule["best_profit"].apply(lambda x: x[3])
        else:
            col = name[:2] + "_accepted"
            schedule["prob"] = schedule[col]

        schedule["dist_saved"] = schedule['ttrav_ns'] - schedule['ttrav']
        schedule["e_dist_saved"] = schedule.apply(lambda x: x["prob"]*x["dist_saved"], axis=1)

    # measures = ['u_veh', 'revenue', 'expected_revenue', 'expected_profit_20',
    #             'expected_profit_30', 'expected_profit_40', 'expected_profit_50',
    #             'expected_profit_60', 'dist_saved', 'e_dist_saved']
    measures = ['expected_revenue', 'expected_profit_20',
                'expected_profit_30', 'expected_profit_40', 'expected_profit_50',
                'expected_profit_60', 'e_dist_saved']

    results = {}
    for meas in measures:
        results[meas] = [sum(t[meas]) for t in schedules.values()]

    # results["dist_saved"] = [6*sum(t['ttrav_ns'] - t['ttrav']) for t in schedules.values()]
    # results["dist_veh"] = [6*t for t in results["u_veh"]]
    # del results["u_veh"]
    results = pd.DataFrame(results)
    results.index = schedules.keys()
    results = results.round()
    results = results.drop(columns=["expected_profit_30", "expected_profit_50"])
    results = results.drop(labels=["expected_profit_int_30", "expected_profit_int_50"])
    print(results.to_latex())
