from pipeline import run_pipeline


def start_investigation(
    subreddit_list,
    posts,
    time_range
):
    """
    Starts the investigation by calling the pipeline.
    """

    return run_pipeline(
        subreddits=subreddit_list,
        posts_per_subreddit=posts,
        time_filter=time_range
    )