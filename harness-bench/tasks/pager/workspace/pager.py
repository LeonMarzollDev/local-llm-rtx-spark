"""Split a list into pages. Pages are numbered from 1."""


def total_pages(n_items, per_page):
    """Number of pages for n_items items (at least 1, also for an empty list)."""
    if per_page < 1:
        raise ValueError("per_page must be at least 1")
    return n_items // per_page + 1


def paginate(items, page, per_page=10):
    """The items on the given page (1-based). A page outside 1..total_pages raises IndexError."""
    pages = total_pages(len(items), per_page)
    if page < 1 or page > pages:
        raise IndexError(f"page {page} out of range 1..{pages}")
    start = page * per_page
    return items[start:start + per_page]
