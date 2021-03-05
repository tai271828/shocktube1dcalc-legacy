#!/usr/bin/env python
import collections
import matplotlib.animation as animation
import matplotlib.pyplot as plt

from shocktube1dcalc import (
    solver_analytic,
    cese,
    helper,
)
from shocktube1dcalc.helper import (
    get_deviation_values,
    convert_format1_to_format2,
)

TIME_STEP_SIZE = 0.01
TIME_TOTAL_ELAPSE = 0.4


def get_analytic_solutions(moment, mesh):
    shocktube = solver_analytic.ShockTube()

    return shocktube.get_analytic_solution(mesh, t=moment)


def get_cese_solutions(moment):
    cese_grid_size_t = 0.004
    # multiply 2 for half grids, so total iteration number should be double
    iteration_number = round(moment / 0.004 * 2)
    shocktube = cese.ShockTube(iteration=iteration_number, grid_size_t=cese_grid_size_t)
    shocktube.run_cese_iteration()
    return shocktube.data.solution


def plot_solution_single_artist_overlapping(
    artist,
    titles_ordered,
    time_moment,
    type_name,
    ax_type,
    values_base,
    values_target,
    color_base,
    color_target,
    marker_base,
    marker_target,
):
    key_idx = 0
    for key in titles_ordered:
        ax = ax_type[key_idx]

        values_x = values_base["x"] + values_target["x"]
        values_y = values_base[key] + values_target[key]
        colors = [color_base]*len(values_base["x"]) + [color_target]*len(values_target["x"])
        markers = [marker_base]*len(values_base["x"]) + [marker_target]*len(values_target["x"])

        subplot = ax.scatter(
            values_x, values_y, s=10, c=colors, marker=marker_base
        )

        if type_name == "deviation":
            ax.set(xlim=[-1, 1], ylim=[-0.01, 0.01])
        else:
            ax.set(xlim=[-1, 1], ylim=[0, 1.1])

        ax.set_title(titles_ordered[key] + f" ({type_name})")
        text_time = plt.text(
            0.1, 0.08, f"Time: {time_moment:.2f}", transform=ax.transAxes
        )

        artist.append(subplot)
        artist.append(text_time)
        key_idx = key_idx + 1

    return artist


def plot_solution_single_artist(
    artist, titles_ordered, time_moment, type_name, ax_type, values_type, color, marker
):
    key_idx = 0
    for key in titles_ordered:
        ax = ax_type[key_idx]
        subplot = ax.scatter(
            values_type["x"], values_type[key], s=10, c=color, marker=marker
        )

        if type_name == "deviation":
            ax.set(xlim=[-1, 1], ylim=[-0.01, 0.01])
        else:
            ax.set(xlim=[-1, 1], ylim=[0, 1.1])

        ax.set_title(titles_ordered[key] + f" ({type_name})")
        text_time = plt.text(
            0.1, 0.08, f"Time: {time_moment:.2f}", transform=ax.transAxes
        )

        artist.append(subplot)
        artist.append(text_time)
        key_idx = key_idx + 1

    return artist


def plot_solution_single_frame(
    values_base, values_target, ax_overlapping, ax_deviation, moment
):
    artist = []

    title_items = [
        ("p", "Pressure"),
        ("rho", "Density"),
        ("u", "Velocity"),
    ]
    titles_ordered = collections.OrderedDict(title_items)

    helper.DEVIATION_PRECISION = 2
    values_deviation = get_deviation_values(values_base, values_target, titles_ordered)

    plot_solution_single_artist_overlapping(
        artist, titles_ordered, moment, "target", ax_overlapping, values_base, values_target, "g", "b", "8", "s"
    )
    plot_solution_single_artist(
        artist,
        titles_ordered,
        moment,
        "deviation",
        ax_deviation,
        values_deviation,
        "r",
        "o",
    )

    return artist


def plot_solution_video_frames(
    time_step, time_total_elapse, ax_overlapping, ax_deviation
):
    artist_frames = []
    time_total_steps = int(time_total_elapse / time_step)
    for idx_step in range(0, time_total_steps):
        moment = TIME_STEP_SIZE * idx_step

        # generate the CESE solutions
        sodtube_cese = get_cese_solutions(moment)
        mesh_cese = helper.get_cese_mesh(sodtube_cese)
        # generate the analytic result from shocktube1d package
        sodtube_analytic = get_analytic_solutions(moment, mesh_cese)

        solution_cese = convert_format1_to_format2(sodtube_cese)[2]
        solution_analytic = convert_format1_to_format2(sodtube_analytic)[2]

        artist_frames.append(
            plot_solution_single_frame(
                solution_analytic,
                solution_cese,
                ax_overlapping,
                ax_deviation,
                moment,
            )
        )

    return artist_frames


# Output video
#
# Set up formatting for the movie files
subplot_row = 2
subplot_column = 3
Writer = animation.writers["ffmpeg"]
writer = Writer(fps=15, metadata=dict(artist="Me"), bitrate=1800)
my_dpi = 96
fig4video, (axis_overlapping, axis_deviation) = plt.subplots(
    subplot_row, subplot_column, figsize=(1600 / my_dpi, 1000 / my_dpi), dpi=my_dpi
)
fig4video.subplots_adjust(hspace=0.4, wspace=0.4)
frame_seq = plot_solution_video_frames(
    TIME_STEP_SIZE, TIME_TOTAL_ELAPSE, axis_overlapping, axis_deviation
)

ani = animation.ArtistAnimation(
    fig4video, frame_seq, interval=25, repeat_delay=300, blit=True
)
ani.save("/tmp/1d-sod-tube-cese-analytic.mp4", writer=writer)
