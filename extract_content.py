import pandas as pd
from meetings import MeetingTranscript
from multiprocessing.dummy import Pool
from tqdm import tqdm
from evaluate_is_related import is_related_mp
from config import base_dir

if __name__ == '__main__':
    documents = [
        # MeetingTranscript(base_dir + '/pdf/3.pdf', [[1]]),
        MeetingTranscript(base_dir + '/pdf/3.pdf', [[1, 25]]),
        MeetingTranscript(base_dir + '/pdf/4.pdf', [[28, 31]]),
        MeetingTranscript(base_dir + '/pdf/5.pdf', [[26, 27]])
    ]

    pd.to_pickle(documents, base_dir + '/documents_no_related.pkl')

    for document in documents:
        print(f'Processing "is_related": {document.name}')
        args = [
            (
                record['translated'],
                document.pages.loc[record['page']]['translated']
            )
            for record in document.speaker_sides.to_dict('records')
        ]
        with Pool() as pool:
            results = list(tqdm(pool.imap(is_related_mp, args), total=len(document.speaker_sides)))
        document.speaker_sides[['type', 'reasoning', 'comment_interpretation']] = results
        document.speaker_sides['is_related'] = document.speaker_sides['type'].apply(lambda x: 0 if x == 'none' else 1)

    pd.to_pickle(documents, base_dir + '/documents.pkl')

    print('Done.')
