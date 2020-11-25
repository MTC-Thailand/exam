# coding: utf-8
def generate_code(affil):
    subjects = ['la', 'cc', 'mi', 'im', 'bb', 'ms', 'he']
    accounts = ['{}{}{}'.format(affil,sbj,2563) for sbj in subjects]
    pwds = [''.join(random.sample(string.ascii_letters, 6)) for sbj in subjects]
    return {'account': accounts, 'subjects': subjects, 'passwords' : pwds}
