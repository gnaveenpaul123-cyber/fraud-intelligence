from pipeline import run_pipeline


def start_investigation(
    subreddits,
    posts,
    time_range,
    progress_callback=None
):
    print("controller started")
    """
    Starts the investigation by calling the pipeline.
    """

    return run_pipeline(
        subreddits=subreddits,
        posts_per_subreddit=posts,
        time_filter=time_range,
        progress_callback=progress_callback
    )