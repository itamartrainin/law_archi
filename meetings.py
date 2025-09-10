import os
import pandas as pd

from tqdm import tqdm
from litellm import completion

from objects import MeetingTypes, LLM
from utils import extract_json, translate
from pdf_reader import pdf_to_pages

tqdm.pandas()

class Page:
    def __init__(self, page_number, content):
        self.page_number = page_number
        self.content = content
        self.translated = None

class MeetingTranscript:
    def __init__(self, path_to_file, relevant_pages=None, type=MeetingTypes.LAW_COMMITTEE.value, model=LLM.DEFAULT.value):
        print(f'Processing Document: {path_to_file}')

        self.name = os.path.basename(path_to_file)
        self.relevant_pages = relevant_pages
        self.type = type
        self.model = model

        self.raw_pages = pdf_to_pages(path_to_file)

        self.front_page = self.raw_pages.iloc[0]
        self.pages = self.filter_relevant_pages()

        self.do_translate()
        self.do_extract_speaker_sides()
        self.do_extract_participants()
        self.do_extract_ref_participants()

        print('Init Done.')

        # self.font_page = self.raw_pages.iloc[0]
        # self.pages = self.pages[:2]  # todo: remove this!
        # self.pages = [self.pages[0], self.pages[1], self.pages[2], self.pages[25]] # todo: remove this!
        # self.agenda_topics = self.get_agenda_topics()
        # self.pages = self.add_topic_markings()
        # self.speaker_sides = self.get_document_speaker_sides()

    def do_translate(self):
        print('Translating Pages')
        self.pages['translated'] = self.pages['content'].progress_apply(translate)
        self.front_page['translated'] = translate(self.front_page['content'])

    def do_extract_speaker_sides(self):
        self.speaker_sides = self.get_document_speaker_sides()

    def do_extract_participants(self):
        self.participants = self.get_participants()
        self.clean_participants_list_str = '\n'.join([p['name'] for p in self.participants.values()])
        self.participant_map = self.get_participant_mapping()
        self.speaker_sides[['norm_speaker', 'position', 'title']] = self.speaker_sides['speaker'].apply(self.map_speakers)

    def do_extract_ref_participants(self):
        self.speaker_sides[['ref_participants', 'norm_ref_participants']] = self.speaker_sides['content'].progress_apply(self.extract_ref_participant)

    def filter_relevant_pages(self):
        filtered_pages = []
        for one_range in self.relevant_pages:
            if len(one_range) == 1:
                filtered_pages.append(self.raw_pages[self.raw_pages.index == 1])
            elif len(one_range) == 2:
                filtered_pages.append(self.raw_pages[one_range[0]:one_range[1] + 1])
            else:
                raise ValueError("Invalid Page Range")
        return pd.concat(filtered_pages)

    def get_document_speaker_sides(self):
        speaker_sides = []
        for i, row in tqdm(self.pages.iterrows(), total=len(self.pages), desc=f'Extracting Speaker Sides'):
            if self.type == MeetingTypes.LAW_COMMITTEE and row['page_num'] == 0:
                continue  # Info Page
            page_sides = self.get_page_speaker_sides(row['content'])
            for s in page_sides:
                content = s['content']
                translated = translate(content, self.model)
                speaker_sides.append([row['page_num'], s['speaker'], content, translated])
        return pd.DataFrame(speaker_sides, columns=['page', 'speaker', 'content', 'translated'])

    def get_page_speaker_sides(self, page_content):
        prompt = f"""
        You are a helpful assistant.
        You will be given a **Hebrew** transcript of an Israeli government discussion about newly proposed laws. 
        Each speaker’s turn is formatted as the speaker’s name, followed by what they said.
        Your task is to extract each individual speaker turn, that is - each time a speaker begins speaking, and return a list of speaker-content pairs.

        If the same speaker speaks multiple times in the segment, each of their turns should appear as a **separate entry** in the output.
        If it is not a speaker turn, ignore it.

        ** Output JSON format: **
        [
            {{
                "speaker": "<speaker name>",
                "content": "<what the speaker said>"
            }},
            ...
        ]
        Segment Text: 
        "{page_content}"
        """.strip()

        response = completion(
            model=self.model,
            temperature=0,
            messages=[{"content": prompt, "role": "user"}]
        )

        return extract_json(response['choices'][0]['message']['content'])

    def get_participants(self):
        prompt = f"""
        You are a helpful assistant.
        You will be given one page from a **Hebrew** transcript of an Israeli government discussion about newly proposed laws. 
        This page includes lists of participants in the discussion.

        Extract the participant names under "חברי הועדה", "מוזמנים", "יועץ משפטי", "מזכיר הוועדה", or "קצרן"
        In addition extract their title if available. The title is noted after the name and is separated by a '-'.

        ** Output JSON format: **
        [
            {{ 
                "name": <first participant name>,
                "position": <is first participant from "חברי הועדה" or "מוזמנים">,
                "title": <first participant title>
            }},
            {{ 
                "name": <second participant name>,
                "position": <is second participant from "חברי הועדה" or "מוזמנים">,
                "title": <second participant title>
            }},
            ...
        ]

        Page Content: 
        "{self.front_page['content']}"
        """.strip()

        response = completion(
            model=self.model,
            temperature=0,
            messages=[{"content": prompt, "role": "user"}]
        )

        resp = extract_json(response['choices'][0]['message']['content'])
        return {p['name']: p for p in resp}

    def get_participant_mapping(self):
        mapping = {}
        speakers_noisy = self.speaker_sides['speaker'].drop_duplicates()
        for speaker in tqdm(speakers_noisy, total=len(speakers_noisy), desc='Mapping Speakers'):
            mapping[speaker] = self.get_static_name(speaker)
        return mapping

    def get_static_name(self, query_name):
        prompt = f"""
        You are a helpful assistant.
        You will be presented with a static list of names in **Hebrew** and a separate query name also in **Hebrew** and a separate query name also in **Hebrew**.
        Indicate which name in the list best matches the query name.

        Static Names List: 
        "{self.clean_participants_list_str}"

        Query Name: "{query_name}"

        ** Output JSON format: **
        {{
            "name": "<name from list that best matches Query Name>"
        }}
        """.strip()

        response = completion(
            model=self.model,
            temperature=0,
            messages=[{"content": prompt, "role": "user"}]
        )

        try:
            return extract_json(response['choices'][0]['message']['content'])['name']
        except:
            return None

    def map_speakers(self, speaker):
        mapped_speaker = self.participants[self.participant_map[speaker]]
        return pd.Series([mapped_speaker['name'], mapped_speaker['position'], mapped_speaker['title']])

    def get_agenda_topics(self):
        prompt = f"""
        You are a helpful assistant.
        You will be given one page from a **Hebrew** transcript of an Israeli government discussion about newly proposed laws. 
        This page includes lists a list of topics to be discussed in the meeting.
        Each topic starts with an Hebrew alphabet letter denoting its position in the list ('א.' + 'ב.' + 'ג.', etc.) but may take multiple lines. In such a case all non alphabetically labeled lines are the same topic.
        Make sure each topic starts with an alphabetic letter denoting its position in the list.

        Please extract the discussion topics under "סדר יום"

        ** Output JSON format: **
        [
            <first discussion topic>,
            <second discussion topic>,
            ...
        ]

        Document Content:
        "{self.front_page}"
        """.strip()

        response = completion(
            model=self.model,
            temperature=0,
            messages=[{"content": prompt, "role": "user"}]
        )
        return extract_json(response['choices'][0]['message']['content'])

    def add_topic_markings(self, k=4):
        titles = self.agenda_topics.copy()
        for page_ix, page in enumerate(self.pages):
            if page_ix == 0:
                continue

            sentences = page.content.split('\n')
            for sentence_ix in tqdm(range(0, len(sentences), k), total=len(sentences) // k + 1,
                                    desc=f'Adding Topic Markings (page: {page_ix})'):
                titles_copy = titles.copy()
                for title in titles_copy:
                    segment = '\n'.join(sentences[sentence_ix:sentence_ix + k])
                    is_contain = self.is_contain_topic_declaration(segment, title)
                    if is_contain:
                        title_ix = titles.index(title)
                        sentences[sentence_ix] = f'<|topic_change|><|topic_id:{title_ix}|>' + sentences[sentence_ix]
                        del titles[titles.index(title)]
                        break
            self.pages[page_ix].content = '\n'.join(sentences)
        return self.pages

    def is_contain_topic_declaration(self, segment, title):
        prompt = f"""
        You are a helpful assistant.
        You will be given a short text segment and a title, both in **Hebrew**.
        Your task is to determine if the title appears in the segment explicitly.
        Note the title does not have to appear exactly in the segment, it could have minor differences such as punctuation, whitespace, etc.

        Add one sentence explaining your reply.

        ** Output JSON format **:
        {{
            "is_contain_title": "<True/False>",
            "explanation": "<one sent explanation of your reply.>",
        }}

        Segment: {segment}
        Title: {title}
        """.strip()

        response = completion(
            model=LLM.CHEAP.value,
            temperature=0,
            messages=[{"content": prompt, "role": "user"}]
        )
        try:
            response = extract_json(response['choices'][0]['message']['content'].lower())
        except:
            return False

        if 'true' in response['is_contain_title'].lower():
            return True
        elif 'false' in response['is_contain_title'].lower():
            return False
        else:
            return False

    def extract_ref_participant(self, comment):
        prompt = f"""
        You are a helpful assistant.
        You will be given a transcription in **Hebrew** of a person talking. 
        The person who is talking may be referencing other people.
        
        Your task is to extract all the people referenced by the speaker.
        If a person is mentioned multiple times, include the name multiple times in the list.

        ** Output JSON format: **
        [
            "<first person name>"
            "<second person name>"
            ...
        ]
        
        Hebrew Transcription: 
        "{comment}"
        """.strip()

        response = completion(
            model=self.model,
            temperature=0,
            messages=[{"content": prompt, "role": "user"}]
        )

        names = extract_json(response['choices'][0]['message']['content'])
        normalized_names = [self.get_static_name(n) for n in names]

        return pd.Series([names, normalized_names])