"""Public facts about MORIQ, shown with their sources.

These facts are display content, not knowledge sources. They stay out of the
registry and out of model prompts: public listings do not establish internal
practice, and the firm's own award claims are reported as claims.
"""

PROFILE = {
    'name': 'MORIQ Interiors & Design Consultants',
    'checked': '2026-11-04',
    'notice': 'From public listings, not an approved MORIQ source. The firm should confirm these details.',
    'facts': [
        {'text': 'Architecture office based in Hyderabad, India, with published work focused on residential '
                 'architecture and interior design.', 'source': 'ArchDaily', 'url': 'https://www.archdaily.com/office/moriq'},
        {'text': 'Lists architecture, interior design and landscape design services, in Banjara Hills, Hyderabad, '
                 'serving Hyderabad and the Middle East.', 'source': 'Houzz', 'url': 'https://www.houzz.com/pro/moriq321'},
        {'text': 'Lists Mr. Riyaz Quraishi as Chief Consultant and Mrs. Simeen Quraishi as Associate Consultant.',
         'source': 'Houzz', 'url': 'https://www.houzz.com/pro/moriq321'},
        {'text': 'Courtyard Villa: Hyderabad, 2017, described by the architects as a north-facing, vaastu-compliant '
                 'family home on a linear plot.', 'source': 'ArchDaily',
         'url': 'https://www.archdaily.com/913785/courtyard-villa-moriq'},
        {'text': 'Amwaj Villa: Amwaj, Bahrain, 2015, with architecture, interiors and landscape credited to MORIQ.',
         'source': 'ArchDaily', 'url': 'https://www.archdaily.com/954404/amwaj-villa-moriq'},
        {'text': 'Villa 430: Hyderabad, 2017, credited to MORIQ.', 'source': 'ArchDaily',
         'url': 'https://www.archdaily.com/896185/villa-430-moriq'},
        {'text': 'The firm reports winning the first Trends Excellence Awards for Architecture and Design in 2012 and '
                 'a National Award for excellence in design for 2016. These are the firm\'s own statements.',
         'source': 'Houzz', 'url': 'https://www.houzz.com/pro/moriq321'},
    ],
}

WORKSPACES = [
    {'id': 'architecture', 'name': 'Architecture', 'description': 'Planning, form, climate, orientation'},
    {'id': 'interiors', 'name': 'Interiors', 'description': 'Space, material, light, detail'},
    {'id': 'landscape', 'name': 'Landscape', 'description': 'Courtyards, planting, thresholds'},
]


def profile_text():
    lines = [PROFILE['notice'], '']
    lines.extend(f"- {fact['text']} ({fact['source']})" for fact in PROFILE['facts'])
    return '\n'.join(lines)
