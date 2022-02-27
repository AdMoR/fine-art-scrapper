import re


def handle_missing_line_return(str_):
    str_ = re.sub(r"(?P<end>[a-z])(?P<start>[0-9])", r"\g<end> \g<start>", str_)
    return re.sub(r"(?P<end>[a-z0-9])(?P<start>[A-Z])", r"\g<end>\n\g<start>", str_)
