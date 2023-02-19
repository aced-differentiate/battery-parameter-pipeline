import matplotlib.pyplot as plt
import numpy as np
import pybamm


def open_circuit(parameter_values):
    fig, ax = plt.subplots()

    # Load/define parameters
    x_100 = parameter_values["Maximum stoichiometry in negative electrode"]
    x_0 = parameter_values["Minimum stoichiometry in negative electrode"]
    y_100 = parameter_values["Minimum stoichiometry in positive electrode"]
    y_0 = parameter_values["Maximum stoichiometry in positive electrode"]

    def U_n(x):
        if not isinstance(x, float):
            x = pybamm.Vector(x)
        return parameter_values["Negative electrode OCP [V]"](x).evaluate()

    def U_p(y):
        if not isinstance(y, float):
            y = pybamm.Vector(y)
        return parameter_values["Positive electrode OCP [V]"](y).evaluate()

    # Create axes
    ax_x = ax
    ax_y = ax.twiny()
    ax_soc = ax.twiny()
    _make_second_bottom_axis(ax_soc)

    # Plot
    x = np.linspace(0, 1, 100)
    ax_x.plot(x, U_n(x), color="tab:blue", label=r"$U_\mathrm{n}$")
    for x_ in [x_0, x_100]:
        _annotate(ax_x, x_, U_n(x_), color="tab:blue", pad=(0.01, 0.05))

    y = np.linspace(1, 0, 100)
    ax_y.plot(y, U_p(y), color="tab:red", label=r"$U_\mathrm{p}$")
    for y_ in [y_0, y_100]:
        _annotate(ax_y, y_, U_p(y_), color="tab:red", pad=(-0.01, 0.05))
    soc = np.linspace(0, 1, 100)
    x = x_0 + soc * (x_100 - x_0)
    y = y_0 - soc * (y_0 - y_100)

    ax_soc.plot(soc, U_p(y) - U_n(x), color="k", label=r"$U_\mathrm{p}-U_\mathrm{n}$")
    ax_soc.axvline(0, color="0.5", linestyle="--")
    ax_soc.axvline(1, color="0.5", linestyle="--")

    # Adjust limits so that whole x and y stoich range is visible
    # and axes are aligned
    xlim = np.array([-0.02, 1.02])
    ylim = np.array([-0.02, 1.02])
    soclim_from_x = (xlim - x_0) / (x_100 - x_0)
    soclim_from_y = -(ylim - y_0) / (y_0 - y_100)

    soclim = np.array(
        [
            min(soclim_from_x[0], soclim_from_y[1]),
            max(soclim_from_x[1], soclim_from_y[0]),
        ]
    )
    xlim = x_0 + (x_100 - x_0) * soclim
    ylim = y_0 - (y_0 - y_100) * soclim

    ax_x.set_xlim(xlim)
    ax_y.set_xlim(ylim)
    ax_soc.set_xlim(soclim)

    # Labeling
    tick_locations = np.linspace(0, 1, 6)
    for ax_ in [ax_x, ax_y, ax_soc]:
        ax_.set_xticks(tick_locations)

    ax_x.set_xlabel("Negative electrode stoichiometry")
    ax_y.set_xlabel("Positive electrode stoichiometry")
    ax_soc.set_xlabel("Full cell SOC")
    ax_x.set_ylabel("Potential [V]")

    fig.legend(loc="center right", bbox_to_anchor=(0.98, 0.6))

    fig.tight_layout()

    return fig, ax


def _annotate(ax, x, y, color=None, pad=(0, 0)):
    ax.plot(x, y, "x", color=color)
    ax.text(x + pad[0], y + pad[1], f"{x:.2g}", color=color, ha="left", va="bottom")


def _make_second_bottom_axis(ax):
    # Move twinned axis ticks and label from top to bottom
    ax.xaxis.set_ticks_position("bottom")
    ax.xaxis.set_label_position("bottom")

    # Offset the twin axis below the host
    ax.spines["bottom"].set_position(("axes", -0.2))

    # Turn on the frame for the twin axis, but then hide all
    # but the bottom spine
    ax.set_frame_on(True)
    ax.patch.set_visible(False)

    # as @ali14 pointed out, for python3, use this
    # for sp in ax.spines.values():
    # and for python2, use this
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.spines["bottom"].set_visible(True)
