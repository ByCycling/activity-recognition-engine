import base64
from io import BytesIO

from matplotlib.figure import Figure
import pandas as pd

type_colors = {
    "on_foot": "cyan",
    "walking": "cyan",
    "running": "blue",
    "on_bicycle": "green",
    "still": "black",
    "in_vehicle": "red",
    "unknown": "gray"
}


def show(before_df: pd.DataFrame, after_df: pd.DataFrame):
    fig = Figure()

    axs = fig.subplots(2)

    fig.suptitle('Speeds', fontsize=18)

    for name, group in before_df.groupby('activity.type'):
        axs[0].plot(group['timestamp'], group['coordinates.speed'] * 3.6,
                    color=type_colors[group['activity.type'].iloc[0]],
                    marker='.', linestyle='', markersize=12, label=name)
    axs[0].plot(before_df['timestamp'],
                before_df['coordinates.speed'] * 3.6, 'black')
    axs[0].legend(loc='lower right')
    axs[0].title.set_text('after')
    axs[0].set_ylabel('km/h')
    axs[0].set_xlabel('date & time')
    fig.set_size_inches(17, 5, forward=True)

    for name, group in after_df.groupby('activity.type'):
        axs[1].plot(group['timestamp'], group['coordinates.speed'] * 3.6,
                    color=type_colors[group['activity.type'].iloc[0]],
                    marker='.', linestyle='', markersize=12, label=name)
    axs[1].plot(after_df['timestamp'],
                after_df['coordinates.speed'] * 3.6, 'black')
    axs[1].legend(loc='lower right')
    axs[1].title.set_text('after')
    axs[1].set_ylabel('km/h')
    axs[1].set_xlabel('date & time')
    fig.set_size_inches(17, 5, forward=True)

    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png")
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    # return f"<img src='data:image/png;base64,{data}'/>"
    return data
