from django import template
from math import ceil


register = template.Library()


@register.filter
def int_or_1(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return 1


@register.simple_tag
def get_last_page_num(project_count, page_size):
    return ceil(project_count / page_size)


@register.simple_tag
def set_query_parameter(url, param_name, param_value):
    from urllib.parse import (
        urlencode,
        parse_qs,
        urlsplit,
        urlunsplit,
    )
    scheme, netloc, path, query_string, fragment = urlsplit(url)
    query_params = parse_qs(query_string)
    if param_name == 'page':
        query_params['page'] = [param_value]
    elif param_name in query_params:
        if str(param_value) not in query_params[param_name]:
            query_params[param_name] += [param_value]
    else:
        query_params[param_name] = [param_value]
    new_query_string = urlencode(query_params, doseq=True)
    return urlunsplit((scheme, netloc, path, new_query_string, fragment))
