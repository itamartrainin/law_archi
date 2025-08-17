import pandas as pd
from meetings import MeetingTranscript
from multiprocessing.dummy import Pool
from tqdm import tqdm
from evaluate_is_related import is_related_mp

if __name__ == '__main__':
    work_dir = '/Users/itamartrainin/data/law_human_freedom'

    documents = [
        MeetingTranscript(work_dir + '/pdf/3.pdf', [[1, 25]]),
        MeetingTranscript(work_dir + '/pdf/4.pdf', [[28, 31]]),
        MeetingTranscript(work_dir + '/pdf/5.pdf', [[26, 27]])
    ]

    for document in documents:
        print(f'Processing "is_related": {document.name}')
        with Pool() as pool:
            results = list(
                tqdm(pool.imap(is_related_mp, document.speaker_sides.to_dict('records')), total=len(document.speaker_sides)))
        document.speaker_sides[['type', 'reasoning', 'comment_interpretation']] = results
        document.speaker_sides['is_related'] = document.speaker_sides['type'].apply(lambda x: 0 if x == 'none' else 1)

    pd.to_pickle(documents, work_dir + '/documents.pkl')

    print('Done.')
