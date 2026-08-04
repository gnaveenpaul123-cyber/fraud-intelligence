from controller import start_investigation


def start_worker(
    subreddits,
    posts,
    time_range,
    progress_callback,
):
    print("worker started")
    return start_investigation(
        subreddits,
        posts,
        time_range,
        progress_callback,
    )