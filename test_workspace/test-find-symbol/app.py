from constants import MAX_RETRIES


def run():
    # MAX_RETRIES is used to limit retry attempts in this loop.
    for _ in range(MAX_RETRIES):
        print("retry")
