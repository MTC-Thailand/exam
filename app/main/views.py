from . import mainbp as main


@main.route('/')
def index():
    return 'Main Index'