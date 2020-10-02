from . import exambank


@exambank.route('/')
def index():
    return 'Exam Index'