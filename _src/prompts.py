"""
prompts.py

Original Author:
    Alexander O. Smith <aosmith@syr.edu>

Purpose:
    Prompt templates for GRAVITYbot LLM summarization tasks.
    
    - talk_prompt(): Summarizes Zooniverse Talk forum discussions for LIGO scientists
    - alog_prompt(): Summarizes aLOG engineering posts for citizen scientists
"""

import json

import pandas as pd


DATA_DELIMITER = "~~~"

ALOG_BASE_URLS = {
    "LHO": "https://alog.ligo-wa.caltech.edu",
    "LLO": "https://alog.ligo-la.caltech.edu",
}


def format_data(data):
    """
    Converts a pandas DataFrame to a JSON-formatted string of records.

    Args:
        data (pandas.DataFrame or any): The data to format.

    Returns:
        str: A JSON-like string representation of the DataFrame records if `data` is a DataFrame;
             otherwise, returns `data` unchanged.
    """
    if isinstance(data, pd.DataFrame):
        records = data.to_dict(orient="records")
        records = ",\n ".join(map(json.dumps, records))
        return f"[\n {records}\n]"

    return data


def talk_prompt(prior_data, current_data):
    """
    Constructs prompts for summarizing Zooniverse Talk forum discussions.

    Args:
        prior_data (pandas.DataFrame): Talk data from the prior week.
        current_data (pandas.DataFrame): Talk data from the current week.

    Returns:
        tuple: (user_prompt, sys_prompt) for the LLM.
    """
    user_prompt = f"""
    The following data are citizen scientist ("volunteer") forum discussions of gravitational wave glitches from the Zooniverse Gravity Spy project. The data originally were in a dataframe of two columns. The first column was the "comment" text and the second was the "URL" affiliated with the comment. After each comment has been formatted such that it is followed by its URL.

    Volunteers also attempt to identify underlying causes of each glitch. The forum data captures the evolving nature of glitch classification, glitch origins and characteristics by volunteers and researchers. The forum data emerges as a part of significant curiosity and engagement with the data, with the need for a clear summary.

    Within the Zooniverse project Gravity Spy, there are existing well-defined glitch classifications that describe transient noise artifacts seen in data from LIGO's gravitational wave detectors. Use the existing Gravity Spy glitch classifications to compare to following datasets. These include the following:
    1080 Line, 1400 Ripple, 70 Hz Line, Air Compressor (50 Hz), Blip, Chirp, Crown, Extremely Loud, Helix, Koi Fish, Low-Frequency Line, No Glitch, Paired Doves, Pizzicato, Power Line (60 Hz), Repeating Blips, Scattered Light, Scratchy, Tomte, Violin Mode Harmonic, Wandering Line, Whistle.

    Consider "last week's" forum data:
    {format_data(prior_data)}

    Now consider "this week's" forum data:
    {format_data(current_data)}

    Using these two sets of data, please provide at least three bullet points to answer the following questions. Each bullet point requires a couple of sentences of response. For each major question please provide all relevant URLs in the final bullet for that major question following this format: [Reference Information](https://www.zooniverse.org/projects/zooniverse/gravity-spy/talk/6872/3685209) where "Reference Information" should be a description of 3 words or less.

    I want a structured outline of of what occurred in "this week's" forum data relative to "last week's" focusing on the following concerns:

    1. EACH possible new glitch suggestion outlined in the following format. (There will likely be multiple of these. Report all of them.)
        - What is the new glitch suggested this week relative to last week?
        - If this new suggested glitch is being discussed anywhere else in the data.
        - How likely is the glitch to be reduced to a previous classification? Vetting whether a new glitch is really new is time consuming. Often there can be long and detailed discussion about how a volunteer should interpret existing glitch classes in order to avoid confusion in the future for the volunteer. The volume of discussion matters less than whether volunteers are suggesting they agree or disagree. However, if there is general agreement that it is different enough, what suggests this? If it is not new enough, where might the confusion be?
        - PROVIDE EVERY RELATED COMMENT'S URL, including follow-up discussion, as a bulleted list. (I.E. IF THERE IS SIGNIFICANT DISCUSSION THERE SHOULD BE MULTIPLE URLs)
    CONTINUE RESPONDING TO EACH OF THESE IN THE ABOVE FORMAT AS 1.1, 1.2, 1.3, ETC FOR EACH NEW GLITCH BEFORE ANSWERING ANY ADDITIONAL QUESTIONS!

    2. Volunteers learn by exploring classifications and technical aspects of glitches. EXCLUDING RESPONSES RELATED TO CONCERN 1, answer the following bullet points with a final bullet with ALL RELEVANT URLs.
        - Are there emerging questions related to the glitch classes, sensors, or gravitational wave science in this week's data?
        - Describe each question and the reasoning for the question.
        - Provide at two or three sentences describing these emerging questions.

    3. I want to know if volunteers have any hypotheses about the origins of glitches. LIGO gravitational wave glitches are fundamentally related to sensors, channel noise, and/or some ecological factors. Conclude with a final bullet with ALL RELEVANT URLs.
        - Are there any conversation suggesting questions, hypothetical, or declarative origins of any glitch class? If so what are the hypotheses?
        - What reasons or rationale is provided?
    RESPONDING TO EACH HYPOTHESES/EXPLANATION PROVIDE THEM IN THE FORMAT 3.1, 3.2, 3.3, ETC BEFORE MOVING ON TO QUESTION 4!

    4. I want to know if volunteers discuss possible technical issues with particular sensors or channels that are not related to 4.
        - Are there any emerging attention or questions surrounding particular glitches' connections to sensors or channels this week relative to last week
        - What specifically do they describe?
        - Provide at least two sentences for these questions or thoughts.
        - Provide ALL relevant URLs.
    """

    sys_prompt = """
    You are a technical interpreter who translates citizen science forum conversations for physicists and engineers who have very little time. As such, you are to provide your responses in as concise a way as possible with all relevant technical or descriptive detail. Format all relevant hyperlinks without hashtags following this format:  [Reference Information](https://www.zooniverse.org/projects/zooniverse/gravity-spy/talk/6872/3685209) where "Reference Information" should be a description of 3 words or less. Phrase interpretations with rhetoric like "an" (as opposed to "the") and "some" as opposed to "all" when referring to the data. This will avoid extremes when there is a lack of clarity.
    """

    return user_prompt, sys_prompt


# Legacy alias for backward compatibility
def ligo_prompt(talk_dat0, talk_dat1):
    """Deprecated: Use talk_prompt() instead."""
    return talk_prompt(talk_dat0, talk_dat1)


def alog_prompt(prior_data, current_data, lab):
    """
    Constructs prompts for summarizing LIGO aLOG engineering posts.

    Args:
        prior_data (pandas.DataFrame): aLOG entries from the prior 5-day period.
        current_data (pandas.DataFrame): aLOG entries from the current 5-day period.
        lab (str): Lab identifier ("LHO" or "LLO") used in prompt context.

    Returns:
        tuple: (user_prompt, sys_prompt) for the LLM.
    """
    template_call_rep = "75875"
    template_link_text = f"{lab}: {template_call_rep}"
    base_url = ALOG_BASE_URLS.get(lab, ALOG_BASE_URLS["LLO"])
    template_link_url = f"{base_url}/aLOG/index.php?callRep={template_call_rep}"

    user_prompt = f"""
The data involve discussions surrounding LIGO laboratory equipment. The data
originally were in a dataframe of three columns. The first column was the
url affiliated with a comment and the second column the comment title and
the final column the comment text.

Many of the acronyms relate to channels, sensors, equiptment, or other processes
surrounding LIGO. Translate these acronyms to full words from the LIGO
Abbreviations and Acronyms list. If there is no cooresponding entry in the LIGO
Abbreviations and Acronyms, use the acronym as is. Then, note the missing acronym.

Consider the Prior aLOG Dataset:
{DATA_DELIMITER}
{format_data(prior_data)}
{DATA_DELIMITER}

Now consider the Current aLOG Dataset:
{DATA_DELIMITER}
{format_data(current_data)}
{DATA_DELIMITER}

Provide responses for some the specific kinds of activities that are different
for the current aLOG Dataset relative to the prior aLOG Dataset.

1. Are there unresolved issues related to particular equiptment that may cause a
glitch in the gravitational wave data? What are these issues? For each unresolved
issue, provide a bullet. Also provide a sentence or two explaining each issue
in simple language. Please provide the URL that references back to the relevant
aLOG conversation.

2. Were there alterations to particular equiptment? For each unresolved issue,
provide a bullet and a sentence or two explaining each issue in pedestrian
language. Provide the URLs that reference back to the relevant aLOG conversation.

3. Where there external events, such as environmental issues that were not about
equiptment failures or modifications that might be related to glitches in gravitational
wave data? For each event, provide a bullet and a sentence or two explaining each
issue in pedestrian language. Provide the URLs that reference back to the relevant
aLOG conversation.
    """.strip()

    sys_prompt = f"""
You are a LIGO engineer tasked with summarizing aLOG conversations for citizen scientists.
The important conversations are about relevant engineering changes
or events which may create glitches in gravitational wave data. Your goal is
to help citizen scientists understand laboratory issues that will enable them
to interpret Gravity Spy Glitch issues quickly. Use clear, simple language and
avoid technical jargon to ensure accessibility. Translate acronyms to full
words based upon LIGO Abbreviations and Acronyms. If there is no cooresponding entry in
the LIGO Abbreviations and Acronyms, use the acronym as is. Note the missing information.

When data is provided, you should expect to be delimited by lines consisting
only of spaces and '{DATA_DELIMITER}'.

When generating summaries, Format all URLs without hashtags following this format:
[{template_link_text}](+tab+{template_link_url}).

Structure the summary logically, highlighting common or recent issues, and
maintain a neutral, informative tone. Phrase interpretations with rhetoric like
"an" (as opposed to "the") and "some" as opposed to "all" when referring to the
data. This will avoid extremes when there is a lack of clarity.
    """.strip()

    return user_prompt, sys_prompt