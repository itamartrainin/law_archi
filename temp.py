def normalize_pages(self):
    new_pages = []
    for page in tqdm(self.pages, desc=f'Normalizing Pages'):
        new_page = self.normalize_page(page)
        print(f'{len(page)} | {len(new_page)}')
        new_pages.append(new_page)  # todo: remove this!
    return new_pages


def normalize_page(self, page):
    prompt = f"""
    You are a helpful assistant.
    You will be given one page from a **Hebrew** transcript of an Israeli government discussion about newly proposed laws. 
    This page has been passed through OCR and therefore has some minor defects such as false whitespaces, punctuation, and so on.
    Output a corrected version of the page without the defects.
    Make sure that all the content is the same other than the corrections.
    Output the corrected page only without any additional text.

    Page Content:
    "{page}"

    """

    response = completion(
        model=self.model,
        messages=[{"content": prompt, "role": "user"}]
    )

    return response['choices'][0]['message']['content']



def split_pages_by_topic(self):
    new_pages = []
    for page_ix, page in tqdm(enumerate(self.pages), total=len(self.pages), desc='Splitting Pages by Topics'):
        if page_ix == 0:
            new_pages.append(page)
        splitted_page = self.pages[page_ix].split('\n')

def split_page_by_topic(self):
    prompt = f"""
    You are a helpful assistant.
    You will be given a passage from a **Hebrew** transcript of an Israeli government discussion about newly proposed laws.
    In addition you will be given a list of topic titles discussed in the meeting.
    Pl
    This page includes lists a list of topics to be discussed in the meeting.
    Each topic starts with an Hebrew alphabet letter denoting its position in the list ('א.', 'ב.', 'ג.', etc.) but may take multiple lines. In such a case all non alphabetically labeled lines are the same topic.

    Please extract the discussion topics under "סדר יום"

    ** Output JSON format: **
    [
        <first discussion topic>,
        <second discussion topic>,
        ...
    ]

    Document Content:
    "{self.font_page}"
    """.strip()

    response = completion(
        model=self.model,
        messages=[{"content": prompt, "role": "user"}]
    )
    return extract_json(response['choices'][0]['message']['content'])

    def split_pages_by_topic(self):
        new_pages = []
        for page_ix, page in tqdm(enumerate(self.pages), total=len(self.pages), desc='Splitting Pages by Topics'):
            if page_ix == 0:
                new_pages.append(page)
            new_pages += self.split_page_by_topic(page)
        return new_pages

    def split_page_by_topic(self, page):
        topics_list = '\n'.join(self.agenda_topics)

        prompt = f"""
        You are a helpful assistant.
        You will be given a page from a **Hebrew** transcript of an Israeli government discussion about newly proposed laws.
        The page contains discussion turns follow a discussion topic.  
        Each speaker’s turn is formatted as the speaker’s name, followed by what they said.
        You will be given the list of topics discussed. 
        If the topic changes then the page will include an explicit line stating the discussed topic as one of the topics from the list.

        Your task is to separate the page according to the different topics.

        For example:
        - If there is not topic indication then the page remains the same.
        - If there is one topic statement then return the first part before the topic and the second part after the topic.
        - If there are 2 topics in the page return the first part before the topic, the second between the first and the second topic, and the third part after the second topic.
        - Etc.  

        ** Output JSON format: **
        [
            {{
                'topic': <topic of the first part from topics list, 'none' if no topic stated>
                'content': <content of the first part>
            }},
            {{
                'topic': <topic of the second part from topics list>
                'content': <content of the sencond part>
            }},
            ...
        ]

        Page Content:
        "{page}"

        Topics List:
        {topics_list}

        """.strip()

        response = completion(
            model=self.model,
            messages=[{"content": prompt, "role": "user"}]
        )
        return extract_json(response['choices'][0]['message']['content'])
