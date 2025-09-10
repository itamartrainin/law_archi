import pandas as pd
from config import base_dir

#%%
documents = pd.read_pickle(base_dir + '/documents.pkl')

#%%

#%%
for document in documents:
    document.clean_participants_list_str = '\n'.join([p['name'] for p in document.participants.values()])
    document.do_extract_ref_participants()
    print()

#%%
documents.to_pickle(base_dir + '/documents_new.pkl')