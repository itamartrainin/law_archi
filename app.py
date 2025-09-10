import numpy as np
import pandas as pd
import altair as alt
import streamlit as st
import plotly.graph_objects as go
from pyvis.network import Network
from streamlit_plotly_events import plotly_events
import streamlit.components.v1 as components


############################################
#              Functions              #
############################################

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

############################################
#             Initializations              #
############################################

if "post_init" not in st.session_state:
    st.session_state['post_init'] = True
    # st.session_state.work_dir = '/Users/itamartrainin/data/law_human_freedom'
    st.session_state.documents = pd.read_pickle('documents.pkl')

    st.session_state.documents[0].name = '01/07/1991 - הכנה לקריאה ראשונה - ועדת החוקה, חוק ומשפט'
    st.session_state.documents[1].name = '15/07/1991 - הכנה לקריאה ראשונה - ועדת החוקה, חוק ומשפט'
    st.session_state.documents[2].name = '28/10/1991 - הכנה לקריאה ראשונה - ועדת החוקה, חוק ומשפט'

    st.session_state.changes_desc = """
    | נוסח מקורי | נוסח מעודכן | תיאור השינוי      |
    |---------|-----|-----------|
    | סיגים 7 . (א) אין פוגעים בזכויות שבחוק יסוד זה אלא בחוק ההולם מדינה דמוקרטית ובמידה שאינה עולה על הנדרש.   | 1. מטרת חוק זה היא להגן על כבוד האדם וחירותו, כדי לעגן את ערכיה של מדינת ישראל כמדינה יהודית ודמוקרטית, בחוק יסוד.  | בעקבות השינוי, הביטוי "מדינה דמוקרטית" הפך ל"מדינת יהודית ודמוקרטית", ועבר מסעיף 7 לסעיף חדש (1) שכותרתו "מטרת החוק". (בהצעת החוק לדיון מוקדם לא היה סעיף מטרה כללי).  |
    """

    st.session_state.all_speaker_sides = pd.concat([d.speaker_sides for d in st.session_state.documents])

    st.session_state.titles = [d.name for d in st.session_state.documents]

    for d in st.session_state.documents:
        d.speaker_sides['smoothed'] = smooth_binary_vector(d.speaker_sides['is_related'])

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

############################################
#                  Changes                 #
############################################

st.markdown('### תיאור השינוי בנוסח החוק')
st.markdown(st.session_state.changes_desc)

############################################
#                Timeline                  #
############################################

st.markdown('### הערות שהשפיעו על השינוי על ציר-הזמן')


smoothing = st.toggle('בטל קיבוץ', value=False)
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
    orig_vals = doc.speaker_sides['is_related']
    smoothed_vals = doc.speaker_sides['smoothed']
    vals = orig_vals if smoothing else smoothed_vals
    title = doc.name
    all_values.extend(vals)
    all_orig_values.extend(orig_vals)
    all_titles.extend([title]*len(orig_vals))
    all_msg_no.extend(list(range(len(orig_vals))))
    hover_text.extend([
        f"שם מסמך: {title}<br> "
        f"מספר הודעה: {i + 1}<br>"
        f"דובר: {row['speaker']}<br>"
        f" תפקיד: {row['position']}<br>"
        f"האם השפיע על שינוי: {'כן' if row['is_related'] == 1 else 'לא'}"
        for i, row in doc.speaker_sides.iterrows()
    ])
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
    line_shape='hv',#'linear',  # horizontal-vertical steps
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

############################################
#              Speaker Counts              #
############################################

st.session_state.cancel_filtered_counts = st.toggle('הצג ספירה לפי כלל ההתבטאויות', value=False)

if st.session_state.cancel_filtered_counts:
    sc = st.session_state.all_speaker_sides
else:
    sc = st.session_state.all_speaker_sides[st.session_state.all_speaker_sides['is_related'] == 1]

c1, c2 = st.columns(2)

with c1:
    st.markdown('### ספירת התבטאויות לפי דובר')
    vc = sc['norm_speaker'].value_counts().reset_index()
    vc.columns = ['speaker', 'count']

    # Sort descending and preserve speaker order
    vc = vc.sort_values(by='count', ascending=False)
    vc['speaker'] = pd.Categorical(vc['speaker'], categories=vc['speaker'], ordered=True)

    # Altair bar chart
    chart = alt.Chart(vc).mark_bar().encode(
        x=alt.X('speaker:N', sort=None, axis=alt.Axis(labelAngle=45)),
        y=alt.Y('count:Q')
    )

    st.altair_chart(chart, use_container_width=True)
with c2:
    st.markdown('### ספירת התבטאויות לפי תפקיד')

    vc = sc['position'].value_counts().reset_index()
    vc.columns = ['position', 'count']

    # Sort descending and preserve speaker order
    vc = vc.sort_values(by='count', ascending=False)
    vc['position'] = pd.Categorical(vc['position'], categories=vc['position'], ordered=True)

    # Altair bar chart
    chart = alt.Chart(vc).mark_bar().encode(
        x=alt.X('position:N', sort=None, axis=alt.Axis(labelAngle=45)),
        y=alt.Y('count:Q')
    )

    st.altair_chart(chart, use_container_width=True)

st.divider()

############################################
#             Message Contents             #
############################################

st.markdown('### תוכן הדיונים')

c1, c2 = st.columns([1, 5])
with c1:
    st.markdown('בחר מסמך להצגה:')
    for i, title in enumerate(st.session_state.titles):
        if st.button(title):#, type='primary' if i == st.session_state.doc_ix else 'secondary'):
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

    total_msgs = len(st.session_state.documents[st.session_state.doc_ix].speaker_sides)

    # for i, row in st.session_state.documents[st.session_state.doc_ix].speaker_sides.iterrows():
    if st.session_state.msg_ix < st.session_state.display_size:
        st.session_state.msg_ix = st.session_state.display_size
    elif st.session_state.msg_ix > total_msgs - st.session_state.display_size:
        st.session_state.msg_ix = total_msgs - st.session_state.display_size

    lower = st.session_state.msg_ix - st.session_state.display_size
    upper = st.session_state.msg_ix + st.session_state.display_size + 1
    with c13:
        st.write(f'מציג התייחסיות: ({lower + 1}-{upper + 1}/{total_msgs})')

    for i in range(lower, upper):
        try:
            row = st.session_state.documents[st.session_state.doc_ix].speaker_sides.iloc[i]
        except:
            row = st.session_state.documents[st.session_state.doc_ix].speaker_sides.iloc[st.session_state.display_size]
        # if i == st.session_state.selected_msg_ix:
        if i == st.session_state.selected_msg_ix and st.session_state.doc_ix == st.session_state.selected_doc_ix:
            with st.chat_message("user", avatar="️⬅️"):
                st.markdown(f"(#{i+1})\t<u>**{row['speaker']}**</u>: {row['content']}", unsafe_allow_html=True)
        elif row['is_related'] == 1:
            with st.chat_message("user", avatar="⭐"):
                st.markdown(f"(#{i+1})\t<u>**{row['speaker']}**</u>: {row['content']}", unsafe_allow_html=True)
        else:
            with st.chat_message("user"):
                st.markdown(f"(#{i+1})\t<u>**{row['speaker']}**</u>: {row['content']}", unsafe_allow_html=True)


############################################
#              Mentions Graph              #
############################################

st.title("הזכורים הדדיים")

# (u, v, weight)
edges = [
    ("A", "B", 1),
    ("A", "C", 3),
    ("B", "D", 2),
    ("C", "D", 5),
    ("C", "E", 1),
]

# Use inlined resources so nothing is written to disk
net = Network(height="600px", width="100%", cdn_resources="in_line")

for u, v, w in edges:
    net.add_node(u)
    net.add_node(v)
    net.add_edge(u, v, width=w, title=f"weight={w}")  # thickness encodes weight

html = net.generate_html()  # returns the HTML string
st.components.v1.html(html, height=620, scrolling=True)