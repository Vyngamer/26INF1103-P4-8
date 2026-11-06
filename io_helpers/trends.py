'''
Assessment trends graph
'''

# graph is actually shown (saves ~0.8s at program start-up)
from data_manager import get_user_records, get_user_int_records
from io_helpers.console import Console

OUTPUT_FILE = "graph.png"

# (data key, grid row, grid columns, y-label, title, y-max, colour)
CHARTS = [
    ("sleep_duration",             0, slice(0, 2), 'Hours (H)',                     'Hours of Sleep',               24,  '#1f77b4'),
    ("focus_level",                0, slice(2, 4), 'Focus Level (1-10)',            'Your Focus Level',             10,  '#ff7f0e'),
    ("stress_level",               0, slice(4, 6), 'Stress Level (1-10)',           'Your Stress Level',            10,  '#d62728'),
    ("social_activity_level",      0, slice(6, 8), 'Social Activity Level (1-10)',  'Your Social Activity Level',   10,  '#b1bd22'),
    ("mental_wellness_risk_score", 1, slice(0, 4), 'Mental wellness score (0-100)', 'Your Mental Wellness Scores',  100, '#2ca02c'),
    ("burnout_risk_score",         1, slice(4, 8), 'Burnout Risk Score (0-100)',    'Your Burnout Risk Scores',     100, '#9467bd'),
]

#Check if matplotlib can open a window (False when there is no display, e.g. headless Docker)
def can_show_window():
    import matplotlib.pyplot as plt    # NEW: lazy import
    from matplotlib.backends import backend_registry, BackendFilter    # NEW: lazy import
    interactive = backend_registry.list_builtin(BackendFilter.INTERACTIVE)
    return plt.get_backend().lower() in [b.lower() for b in interactive]


# Takes the user id and records file directly
def show_trends(uid, db, output_file=OUTPUT_FILE):
    user_records = get_user_records(uid, db)
    if len(user_records) < 2:
        print("You do not have enough records to do this comparison\nYou need to have at least 2 survey attempts")
        Console.pause()
        return

    import matplotlib.pyplot as plt

    #As records are stored newest first; reverse so the graph runs oldest -> newest
    required_data = get_user_int_records(user_records, uid)[::-1]
    x_axis = list(range(1, len(required_data) + 1))

    # initialising the graph
    figure = plt.figure(figsize=(12, 8))
    figure.suptitle('Personal Wellness Tracking Dashboard', fontsize=16, fontweight='bold')
    grid_space = figure.add_gridspec(2, 8)

    # create each graph
    for key, row, columns, ylabel, title, ymax, colour in CHARTS:
        values = [entry[key] for entry in required_data]
        axis = figure.add_subplot(grid_space[row, columns])
        axis.set(xlabel='Attempts', ylabel=ylabel, title=title)
        axis.set_xticks(x_axis)
        axis.set_ylim(0, ymax)
        axis.plot(x_axis, values, marker='o', color=colour, linewidth=2)
        axis.fill_between(x_axis, values, color=colour, alpha=0.15)

    # displaying the graph
    plt.tight_layout()
    plt.savefig(output_file)

    if can_show_window():
        Console.notice(f'Graph saved as {output_file}. Close the graph window to continue...')
        plt.show()  #Blocks until the graph window is closed
        plt.close(figure)
    else:
        #No display (e.g. Docker without X11), so the graph can only be saved
        plt.close(figure)
        Console.notice(f'No display found, graph saved as {output_file}')
        Console.pause()