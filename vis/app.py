import json
import pandas as pd
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from scipy.ndimage import uniform_filter1d
from scipy.ndimage import maximum_filter1d
from streamlit_plotly_events import plotly_events
import streamlit.components.v1 as components
from streamlit_javascript import st_javascript
import time

def smooth_binary_vector(vec, window_size=6, k=3):
    vec = np.array(vec)

    padded = np.pad(vec, (window_size // 2, window_size // 2), mode='edge')
    smoothed = np.array([
        1 if (np.sum(padded[i:i + window_size]) >= k) else 0
        for i in range(len(vec))
    ])

    # # Edge Cases
    # pad = 1
    # padded = np.pad(smoothed, (pad, pad), mode='edge')
    # smoothed = np.array([
    #     1 if (
    #             (vec[i - pad] == 1 and padded[i+1] == 1) or
    #             (padded[i - 1] == 1 and padded[i + 1] == 1)
    #     ) else smoothed[i - pad]
    #     for i in range(1, len(padded) - 1)
    # ])

    for i in range(0, smoothed.shape[0], 1):
        if i > 0 and smoothed[i] == 1 and smoothed[i - 1] == 0:
            smoothed[i - window_size // 2:i] = 1
    for i in range(smoothed.shape[0], 0, -1):
        if i < smoothed.shape[0] - 1 and smoothed[i] == 1 and smoothed[i] == 1:
            smoothed[i:i + window_size // 2] = 1

    return smoothed

if "post_init" not in st.session_state:
    st.session_state['post_init'] = True
    st.session_state.work_dir = '/Users/itamartrainin/data/law_human_freedom'
    st.session_state.documents = pd.read_pickle(st.session_state.work_dir + '/temp.pkl')
    st.session_state.titles = [d['title'] for d in st.session_state.documents]

    st.session_state.documents[-1]['speaker_sides'] = pd.DataFrame([[0,1,1]], columns=['speaker', 'content', 'pred'])

    for d in st.session_state.documents:
        d['speaker_sides']['smoothed'] = smooth_binary_vector(d['speaker_sides']['pred'])

    st.session_state.doc_ix = 0
    st.session_state.msg_ix = 0
    st.session_state.selected_doc_ix = -1
    st.session_state.selected_msg_ix = -1

    st.session_state.display_size = 3

st.set_page_config(layout="wide")
st.markdown("""
    <style>
    body {
        direction: rtl;
        text-align: right;
    }
    .stTextInput > div > input {
        direction: rtl;
        text-align: right;
    }
    .stTextArea > div > textarea {
        direction: rtl;
        text-align: right;
    }
    .stMarkdown {
        direction: rtl;
        text-align: right;
    }
    </style>
""", unsafe_allow_html=True)

st.title("ארכיאולוגיה של חוקים")

st.markdown('### תיאור השינוי בנוסח החוק')
st.write("""
נוסח מקורי (הצעת חוק לדיון מוקדם):  סעיף 7(א): " אין פוגעים בזכויות שבחוק יסוד זה אלא בחוק ההולם מדינה דמוקרטית ובמידה שאינה עולה על הנדרש."
נוסח אחרי השינוי (הצעת חוק לקריאה ראשונה): סעיף 1: "מטרת חוק זה היא להגן על כבוד האדם וחירותו, כדי לעגן את ערכיה של מדינת ישראל כמדינה יהודית ודמוקרטית, בחוק יסוד"; סעיף 7: "אין פוגעים בזכויות שבחוק­-יסוד זה אלא בחוק ההולם את ערכיה של מדינת ישראל, שנועד לתכלית ראויה, ובמידה שאינה עולה על הנדרש."


כלומר – בעקבות השינוי, הביטוי "מדינה דמוקרטית" הפך ל"מדינת יהודית ודמוקרטית", ועבר מסעיף 7 לסעיף חדש (1) שכותרתו "מטרת החוק". (בהצעת החוק לדיון מוקדם לא היה סעיף מטרה כללי).
""")

st.markdown('### הערות שהשפיעו על השינוי על ציר-הזמן')


smoothing = st.toggle('Identify Regions', value=True)
# c1, c2, _ = st.columns([1,2,7])
# with c1:
#     smoothing = st.toggle('החלקה', value=True)
# with c2:
#     window_size = st.number_input("גודל חלון", value=5)
#     k = st.number_input("מספר מינימלי של ערכים 1 בחלון", value=3)

all_values = []
all_orig_values = []
all_titles = []
all_msg_no = []
hover_text = []
doc_indices = []
doc_boundaries = []
doc_titles = []

current_index = 0
for doc in st.session_state.documents:
    orig_vals = doc["speaker_sides"]['pred']
    smoothed_vals = doc["speaker_sides"]['smoothed']
    vals = smoothed_vals if smoothing else orig_vals
    title = doc["title"]
    all_values.extend(vals)
    all_orig_values.extend(orig_vals)
    all_titles.extend([title]*len(orig_vals))
    all_msg_no.extend(list(range(len(orig_vals))))
    hover_text.extend([f"Document: {title}<br>Msg No.: {i + 1}<br>Value: {v}" for i, v in enumerate(orig_vals)])
    doc_indices.extend([title] * len(vals))
    doc_boundaries.append(current_index)
    doc_titles.append(title)
    current_index += len(vals)
doc_boundaries.append(current_index)  # Final boundary

x = list(range(len(all_values)))

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=x,
    y=all_values,
    mode='lines+markers',
    line_shape='linear',  # horizontal-vertical steps
    hovertext=hover_text,
    hoverinfo='text',
    # marker=dict(size=2, color='#6A5ACD'),
    marker=dict(
        size=4,
        # size=[4 if v == 1 else 0 for v in all_orig_values],
        color=['#FA5053' if v == 1 else '#6A5ACD' for v in all_orig_values]
    ),
    line=dict(color='#6A5ACD', width=0.5),
    # name="Binary Value"
))

# Add vertical lines for document boundaries
for i in range(len(st.session_state.documents)):
    fig.add_shape(
        type="line",
        x0=doc_boundaries[i],
        y0=-0.1,
        x1=doc_boundaries[i],
        y1=1.2,
        line=dict(color="#FA5053", dash="dash", width=1),
    )
    # Add document name annotation
    mid = (doc_boundaries[i] + doc_boundaries[i+1]) / 2
    fig.add_annotation(
        x=mid,
        y=1.1,
        text=doc_titles[i],
        showarrow=False,
        font=dict(size=10),
        yanchor='bottom'
    )

# Update layout for scrollability and style
fig.update_layout(
    height=400,
    xaxis=dict(
        title="Sentence Index",
        rangeslider=dict(visible=True),  # adds scroll bar
    ),
    yaxis=dict(
        title="Value",
        tickvals=[0, 1],
        range=[-0.1, 1.2],
    ),
    margin=dict(t=50, b=50),
    hovermode="closest",
)

selected_points = plotly_events(fig, click_event=True, hover_event=False)
if selected_points:
    doc_ix = st.session_state.titles.index(all_titles[selected_points[0]['x']])
    msg_ix = all_msg_no[selected_points[0]['x']]
    if st.session_state.selected_doc_ix != doc_ix and st.session_state.selected_msg_ix != msg_ix:
        st.session_state.doc_ix = doc_ix
        st.session_state.msg_ix = msg_ix
        st.session_state.selected_doc_ix = doc_ix
        st.session_state.selected_msg_ix = msg_ix

st.divider()

st.markdown('### תוכן הדיונים')

c1, c2 = st.columns([1, 5])
with c1:
    for i, title in enumerate(st.session_state.titles):
        if st.button(title):
            print(title)
            st.session_state.doc_ix = i
            st.session_state.msg_ix = 0
            st.session_state.selected_doc_ix = -1
            st.session_state.selected_msg_ix = -1
    # doc_title = st.radio('מסמך להצגה', st.session_state.titles)
    # st.session_state.doc_ix = st.session_state.titles.index(doc_title)
with c2:
    st.markdown(f'### {st.session_state.titles[st.session_state.doc_ix]}')

    c11, c12, c13 = st.columns([1, 1, 10])
    with c11:
        if st.button('הקודם', type='primary'):
            st.session_state.msg_ix -= 1
    with c12:
        if st.button('הבא', type='primary'):
            st.session_state.msg_ix = st.session_state.msg_ix + 1

    total_msgs = len(st.session_state.documents[st.session_state.doc_ix]['speaker_sides'])

    # for i, row in st.session_state.documents[st.session_state.doc_ix]['speaker_sides'].iterrows():
    if st.session_state.msg_ix < st.session_state.display_size:
        st.session_state.msg_ix = st.session_state.display_size
    elif st.session_state.msg_ix > total_msgs - st.session_state.display_size:
        st.session_state.msg_ix = total_msgs - st.session_state.display_size

    lower = st.session_state.msg_ix - st.session_state.display_size
    upper = st.session_state.msg_ix + st.session_state.display_size + 1
    with c13:
        st.write(f'מציג התייחסיות: ({lower + 1}-{upper + 1}/{total_msgs})')

    for i in range(lower, upper):
        row = st.session_state.documents[st.session_state.doc_ix]['speaker_sides'].iloc[i]
        # if i == st.session_state.selected_msg_ix:
        if i == st.session_state.selected_msg_ix and st.session_state.doc_ix == st.session_state.selected_doc_ix:
            with st.chat_message("user", avatar="⭐️"):
                st.markdown(f"(#{i+1})\t<u>**{row['speaker']}**</u>: {row['content']}", unsafe_allow_html=True)
        else:
            with st.chat_message("user"):
                st.markdown(f"(#{i+1})\t<u>**{row['speaker']}**</u>: {row['content']}", unsafe_allow_html=True)

