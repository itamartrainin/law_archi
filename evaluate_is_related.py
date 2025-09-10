import pandas as pd

from tqdm import tqdm
from multiprocessing import Pool, cpu_count
from multiprocessing.dummy import Pool as ThreadPool
from sklearn.metrics import classification_report, confusion_matrix

import litellm
from litellm import completion
from litellm.caching.caching import Cache

from utils import extract_json
from pdf_reader import pdf_to_txt

tqdm.pandas()

change_desc = """
Original wording (Early Discussion Draft of the Bill):
Clause 7(a):
“The rights in this Basic Law shall not be violated except by a law befitting a democratic state and to an extent no greater than required.”

Wording after the amendment (First Reading Draft of the Bill):
Clause 1:
“The purpose of this law is to protect human dignity and liberty, in order to anchor the values of the State of Israel as a Jewish and democratic state in a Basic Law.”
Clause 7:
“The rights in this Basic Law shall not be violated except by a law that accords with the values of the State of Israel, serves a proper purpose, and to an extent no greater than required.”

Following the change, the phrase “democratic state” was replaced with “Jewish and democratic state”, and moved from Clause 7 to a new clause (Clause 1) titled “Purpose of the Law”. (The early discussion draft did not include a general purpose clause).
"""

#%%
"""
You are a helpful assistant.
The following describes a change made to the official phrasing of a newly proposed law, following a discussion of the approving committee in the Israeli government.
In addition you will be provided with the clause phrasing before the change and after.
Please write up to a paragraph, interpreting the described change including its meaning, significance and impact.

Original wording (Early Discussion Draft of the Bill):
Clause 7(a):
“The rights in this Basic Law shall not be violated except by a law befitting a democratic state and to an extent no greater than required.”

Wording after the amendment (First Reading Draft of the Bill):
Clause 1:
“The purpose of this law is to protect human dignity and liberty, in order to anchor the values of the State of Israel as a Jewish and democratic state in a Basic Law.”
Clause 7:
“The rights in this Basic Law shall not be violated except by a law that accords with the values of the State of Israel, serves a proper purpose, and to an extent no greater than required.”

Following the change, the phrase “democratic state” was replaced with “Jewish and democratic state”, and moved from Clause 7 to a new clause (Clause 1) titled “Purpose of the Law”. (The early discussion draft did not include a general purpose clause).
"""

"""
The change from “democratic state” to “Jewish and democratic state” shifts the legal framing of the Basic Law from a universal democratic standard to one explicitly grounded in Israel’s dual identity as both Jewish and democratic. While the original phrasing emphasized rights protection through the lens of democratic principles alone, the modified version introduces an additional national-ethnic dimension, prioritizing the state’s Jewish character alongside its democratic nature. This change is significant because it may influence future legal interpretations and limitations of rights—particularly where tensions arise between democratic values (like equality) and policies justified by the Jewish identity of the state. It reflects a broader ideological shift toward emphasizing the Jewish nature of the state in foundational legislation.
"""

"""
The amendment marks a shift in both wording and structure that carries legal and symbolic significance. Substantively, the phrase “democratic state” was replaced with “Jewish and democratic state” and relocated to a newly added purpose clause (Clause 1). This change makes the dual identity of Israel—as both Jewish and democratic—a foundational principle of the Basic Law, rather than a condition merely for limiting rights (as it was in the original Clause 7). In parallel, the test for limiting rights in Clause 7 was rephrased to require that such limitations align with “the values of the State of Israel”, a potentially broader and less clearly defined standard. This may shift interpretive emphasis from universally recognized democratic norms to values that include particularistic elements, thereby affecting how courts balance individual rights against state interests. Overall, the amendment embeds a stronger national-religious character in the legal framing, which could influence future constitutional interpretation.
"""

#%%
"""
You are a helpful assistant.
The following describes a change made to the official phrasing of a newly proposed law, following a discussion of the approving committee in the Israeli government.
Extract the key-words that describe this change.

Original wording (Early Discussion Draft of the Bill):
Clause 7(a):
“The rights in this Basic Law shall not be violated except by a law befitting a democratic state and to an extent no greater than required.”

Wording after the amendment (First Reading Draft of the Bill):
Clause 1:
“The purpose of this law is to protect human dignity and liberty, in order to anchor the values of the State of Israel as a Jewish and democratic state in a Basic Law.”
Clause 7:
“The rights in this Basic Law shall not be violated except by a law that accords with the values of the State of Israel, serves a proper purpose, and to an extent no greater than required.”

Following the change, the phrase “democratic state” was replaced with “Jewish and democratic state”, and moved from Clause 7 to a new clause (Clause 1) titled “Purpose of the Law”. (The early discussion draft did not include a general purpose clause).

** Output JSON format: **
[
    "<word 1>",
    "<word 2>",
    ...
]
"""

"""
[
    "Jewish and democratic state",
    "Purpose clause",
    "Clause relocation",
    "Values of the State of Israel",
    "Proper purpose",
    "Clause 1",
    "Clause 7 amendment"
]
"""

#%%
# def is_related(comment, context, model='claude-opus-4-20250514', min_words=5):
def is_related(comment, context, model='gpt-5', min_words=5):
    prompt = f"""
    You are a helpful assistant.
    You will be given a comment said by a committee member of the Israeli government, during a discussion about newly proposed laws. 
    You will be presented with a description of a change made to the law phrasing resulting from the committee decisions.   
    You will be presented with an interpretation of the change. 
    You will be presented with the context of the comment, that is, the comments said before and after this comment.

    **Your task** is to determine whether the committee member’s comment **directly** supports, opposes, mentions or induces this specific change in the law phrasing.
    If none then say 'none'.
    Add up to one paragraph interpretation of the comment in the context of the context comments.
    Add one sentence explaining your reasoning.
    
    Note:
    - Make sure to make your inference is based **only** on the comment, the change description and the interpretation of the change.
    - Make sure that the comment implies directly to **this specific change** in the law phrasing and **not the overall law phrasing**.
    - Use the context of the comment to better understand the comment, do not use the context in other ways.
    - Make reasoning steps before outputting the final response.
    
    ** Output JSON format: **
    {{
        "comment_interpretation": "<up to one paragraph interpretation of the comment in context>",
        "reasoning": "<one sentence explanation for response>",
        "type": "<supports/opposes/mentions/induces>"
    }}
    
    Change Description: 
    "Original wording (Early Discussion Draft of the Bill):
    Clause 7(a):
    “The rights in this Basic Law shall not be violated except by a law befitting a democratic state and to an extent no greater than required.”
    
    Wording after the amendment (First Reading Draft of the Bill):
    Clause 1:
    “The purpose of this law is to protect human dignity and liberty, in order to anchor the values of the State of Israel as a Jewish and democratic state in a Basic Law.”
    Clause 7:
    “The rights in this Basic Law shall not be violated except by a law that accords with the values of the State of Israel, serves a proper purpose, and to an extent no greater than required.”
    
    Following the change, the phrase “democratic state” was replaced with “Jewish and democratic state”, and moved from Clause 7 to a new clause (Clause 1) titled “Purpose of the Law”. (The early discussion draft did not include a general purpose clause)."
    
    Interpretation of Change Description: 
    "The amendment marks a shift in both wording and structure that carries legal and symbolic significance. Substantively, the phrase “democratic state” was replaced with “Jewish and democratic state” and relocated to a newly added purpose clause (Clause 1). This change makes the dual identity of Israel—as both Jewish and democratic—a foundational principle of the Basic Law, rather than a condition merely for limiting rights (as it was in the original Clause 7). In parallel, the test for limiting rights in Clause 7 was rephrased to require that such limitations align with “the values of the State of Israel”, a potentially broader and less clearly defined standard. This may shift interpretive emphasis from universally recognized democratic norms to values that include particularistic elements, thereby affecting how courts balance individual rights against state interests. Overall, the amendment embeds a stronger national-religious character in the legal framing, which could influence future constitutional interpretation."    
    
    Committee Member Comment:
    "{comment}"
    
    Context Comments:
    "{context}"
    
    """.strip()

    if len(comment.split(' ')) <= min_words:
        return pd.Series(['none', 'too short.', ''])

    response = completion(
        model=model,
        temperature=1,
        messages=[{"content": prompt, "role": "user"}],
        caching=True
    )

    resp = extract_json(response['choices'][0]['message']['content'])
    return pd.Series([resp['type'], resp['reasoning'], resp['comment_interpretation']])

def is_related_mp(args):
    try:
        return is_related(*args)
    except Exception as e:
        print('is_related_mp FAILED. ', args)
        return None

def do_mp(speaker_side):
    return is_related(speaker_side['translated'], document.pages[speaker_side['page']].translated, model='claude-opus-4-20250514')

if __name__ == '__main__':
    litellm.cache = Cache()

    work_dir = '/Users/itamartrainin/data/law_human_freedom'
    documents = pd.read_pickle(work_dir + '/3.pkl')
    tagged = pd.read_excel(work_dir + '/3_tagged.xlsx')

    # source = pdf_to_txt(work_dir + '/pdf/proposal.pdf')
    # revised = pdf_to_txt(work_dir + '/pdf/first_call.pdf')

    document = documents[0]
    speaker_sides = document.speaker_sides

    # results = []
    # for i, ss in tqdm(document.speaker_sides[:10].iterrows(), total=len(document.speaker_sides)):
    #     results.append(is_related(ss['translated'], document.pages[ss['page']].translated))
    # document.speaker_sides[['type', 'reasoning', 'comment_interpretation']] = results

    with ThreadPool() as pool:
        results = list(
            tqdm(pool.imap(do_mp, document.speaker_sides.to_dict('records')), total=len(document.speaker_sides)))
    document.speaker_sides[['type', 'reasoning', 'comment_interpretation']] = results

    pred = document.speaker_sides['type'].apply(lambda x: 0 if x == 'none' else 1)
    true = tagged['tag']

    print(classification_report(true, pred))
    print(confusion_matrix(true, pred))
    print(confusion_matrix(true, pred, normalize='true'))

    document.speaker_sides['pred'] = pred
    document.speaker_sides['true'] = true
    errors = document.speaker_sides[document.speaker_sides['pred'] != document.speaker_sides['true']]
    errors.to_excel(work_dir + '/3_errors.xlsx')

    document.speaker_sides.to_excel(work_dir + '/temp1.xlsx')
    document.speaker_sides.to_pickle(work_dir + '/speaker_sides.pkl')

    pd.to_pickle(documents, work_dir + '/3_cl.pkl')