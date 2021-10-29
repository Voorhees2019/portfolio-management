from django import template
from math import ceil


register = template.Library()


@register.filter
def to_int(value):
    try:
        return int(value)
    except:
        return 1


@register.filter
def prev_page_num(value):
    return value - 1


@register.filter
def next_page_num(value):
    return value + 1


@register.simple_tag
def get_last_page_num(project_count, page_size):
    return ceil(project_count / page_size)


@register.simple_tag
def set_page_parameter(url, page_num):
    from urllib.parse import (
        urlencode,
        parse_qs,
        urlsplit,
        urlunsplit,
    )
    scheme, netloc, path, query_string, fragment = urlsplit(url)
    query_params = parse_qs(query_string)
    query_params['page'] = [page_num]
    new_query_string = urlencode(query_params, doseq=True)
    return urlunsplit((scheme, netloc, path, new_query_string, fragment))
