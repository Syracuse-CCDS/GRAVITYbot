"""
LIGO aLOG Prompt Generator
---------------------------
Generates user and system prompts for GPT-based summarization of LIGO aLOG entries.
Designed to help summarize recent engineering activity and issues for citizen scientists
participating in Gravity Spy.

Author: [Your Name or Team]
"""

import json
import pandas

DATA_DELIMITER = "~~~"

def format_data(data):
    """
    Converts a pandas DataFrame to a JSON-formatted string of records.

    Args:
        data (pandas.DataFrame or any): The data to format.

    Returns:
        str: A JSON-like string representation of the DataFrame records if `data` is a DataFrame;
             otherwise, returns `data` unchanged.

    Notes:
        - The returned format mimics a readable list of JSON objects.
        - Used to embed structured data within language model prompts.
    """

    if isinstance(data, pandas.DataFrame):
        records = data.to_dict(orient="records")
        records = ",\n ".join(map(json.dumps, records))
        return f"[\n {records}\n]"

    return data


def alog_prompt(prior_data, current_data, lab):
    """
    Constructs user and system prompts for GPT-4 to summarize aLOG data.

    Args:
        prior_data (pandas.DataFrame): aLOG entries from the prior 5-day period.
        current_data (pandas.DataFrame): aLOG entries from the current 5-day period.
        lab (str): Lab identifier (e.g., "LHO" or "LLO") used in prompt context.

    Returns:
        tuple:
            - user_prompt (str): Prompt provided to the language model that includes structured data.
            - sys_prompt (str): Instructional system message to guide GPT behavior and tone.

    Prompt Behavior:
        - Asks GPT to compare current and prior logs for unresolved issues, sensor modifications,
          and external events.
        - Encourages simple, accessible language for citizen scientists.
        - Requests acronyms be expanded using the LIGO Abbreviations and Acronyms list.
        - Embeds formatted data using `format_data()` within a delimiter block.
        - Specifies that URLs in the response should follow a specific Markdown format.
    """

    template_call_rep = "75875"
    template_link_text = f"{lab}: {template_call_rep}"
    template_link_url = f"https://alog.ligo-la.caltech.edu/aLOG/index.php?callRep={template_call_rep}"

    user_prompt = f"""
The data involve discussions surrounding LIGO laboratory equipment. The data
originally were in a dataframe of three columns. The first column was the
url affiliated with a comment and the second column the comment title and
the final column the actual comment text.

Many of the acronyms relate to channels in LIGO sensors or other processes
surrounding LIGO. Translate these acronyms to full words from the LIGO
Abbreviations and Acronyms list.

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

1. Are there unresolved issues related to particular sensors that may cause a
glitch in the gravitational wave data? What are these issues? For each unresolved
issue, provide a bullet. Also provide a sentence or two explaining each issue
in simple language. Please provide the URL that references back to the relevant
aLOG conversation.

2. Were there alterations to particular sensors? For each unresolved issue,
provide a bullet and a sentence or two explaining each issue in pedestrian
language. Provide the URLs that reference back to the relevant aLOG conversation.

3. Where there external events, such as environmental issues that were not about
sensor failures or modifications that might be related to glitches in gravitational
wave data? For each event, provide a bullet and a sentence or two explaining each
issue in pedestrian language. Provide the URLs that reference back to the relevant
aLOG conversation.
    """.strip()

    sys_prompt = f"""
You are a LIGO scientist tasked with summarizing aLOG conversations for citizen
scientists. The important conversations are about relevant engineering changes
or events which may create glitches in gravitational wave data. Your goal is
to help citizen scientists understand laboratory issues that will enable them
to interpret Gravity Spy Glitch issues quickly. Use clear, simple language and
avoid technical jargon to ensure accessibility. Translate acronyms to full
words based upon LIGO Abbreviations and Acronyms whenever possible.

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
