from mudpy.driver import config

def has_color(term):
    if term in config.term.color_types:
        return True
    for termtype in config.term.color_types:
        if term.startswith(termtype):
            return True
    return False

