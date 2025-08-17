import platform

this_platform = platform.platform().split('-')[0]

if 'macOS' in this_platform:
    base_dir = '/Users/itamartrainin/data/law_human_freedom'
elif 'Linux' in this_platform:
    base_dir = '/cs/labs/oabend/itamar.trainin/data/law_human_freedom'
else:
    raise Exception('Unknown platform')
