#####################################################################################################
# DOCUMENTATION NOTES : #############################################################################
# File Author: Alexander O. Smith, aosmith@syr.edu
# Current Maintainer: Alexander O. Smith, aosmith@syr.edu
# Last Update: May 26, 2024
# Program Goal:
# This file is dedicated to creating prompt variables and functions for chatGPT
#####################################################################################################
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# IMPORTANT: !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Beginning Here: Do Not Edit !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#####################################################################################################
# Format all prompt variables as follows:
#####################################################################################################
# Define a variable which dynamically interprets a data string
#ex_user_prompt = f"""
#In the given text data
#{talk_dat}, 
#provide a list of primary topics of the data.
#"""
# Use Case: You might want to do this if all you need is a user prompt, however this will be rare.
#####################################################################################################
# Format all prompt function as follows:
#####################################################################################################
# Provide a name that makes sense based on a user story
# Provide at least one argument: a string of text data to evaluate
def ex_func_prompt_gen(talk_dat):
    # Required: provide a user prompt variable which takes the text data
    user_prompt = f"""
    For the following text data, provide a list of primary topics of the data:
    {talk_dat}
    """

    # Optional: provide a system prompt which tells the bot the context it is responding to.
    sys_prompt = f"""
    You are a helpful interpreter who translates forum conversations for physicists and engineers.
    """

    # Required: return user_prompt and all other variables created as inputs for the bot.
    return user_prompt, sys_prompt
# Use Case: You might need to do this if you need more dynamic calls with multiple variables that
#           are predefined here such that you don't have really long strings of text in the main
#           functions of the GravityBot_main.py file. You can add additional variables and objects
#           within each of these such that they may do more complicated tasks, such as tune model
#           temperature, or provide logical operators depending on text data, etc.
#####################################################################################################
#####################################################################################################
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# End of 'Do Not Edit' Section !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#####################################################################################################
# Make all functions and variables below using the above versions as template text.
#####################################################################################################
# Backlog Tasks:
# 3. Consider hashtags in the prompt (Carsten)
# 4. The following response might be valuable for the GravitySpy prompt  
#       **Additional Considerations and Observations**: The community is actively engaging in the use of tools like GWpy for analyzing glitches, prompting discussions on the effectiveness and limitations of these tools in providing accurate representations of glitches, especially in higher dimensions (3D).There is an ongoing dialogue about the need for improved navigation and management tools within the Zooniverse platform to handle large datasets more efficiently, particularly for sorting and identifying duplicates in glitch classifications. This includes suggestions for enhancements that would allow easier deletion or categorization of glitches directly from the user interface.
# 4. Consider multiple prompts for multiple purposes, and whether they should be automated
#####################################################################################################
def ligo_prompt(talk_dat0, talk_dat1):
    # Required: provide a user prompt variable which takes the text data
    user_prompt = f"""
    The following data are citizen scientist ("volunteer") forum discussions of gravitational wave glitches from the Zooniverse Gravity Spy project. The data originally were in a dataframe of two columns. The first column was the "comment" text and the second was the "URL" affiliated with the comment. After each comment has been formatted such that it is followed by its URL. 
    
    Volunteers also attempt to identify underlying causes of each glitch. The forum data captures the evolving nature of glitch classification, glitch origins and characteristics by volunteers and researchers. The forum data emerges as a part of significant curiosity and engagement with the data, with the need for a clear summary.

    Within the Zooniverse project Gravity Spy, there are existing well-defined glitch classifications that describe transient noise artifacts seen in data from LIGO's gravitational wave detectors. Use the existing Gravity Spy glitch classifications to compare to following datasets.

    Consider "last week's" forum data:
    {talk_dat0}

    Now consider "this week's" forum data:
    {talk_dat1}

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

    # Optional: provide a system prompt which tells the bot the context it is responding to.
    sys_prompt = f"""
    You are a technical interpreter who translates citizen science forum conversations for physicists and engineers who have very little time. As such, you are to provide your responses in as concise a way as possible with all relevant technical or descriptive detail. Format all relevant hyperlinks without hashtags following this format:  [Reference Information](https://www.zooniverse.org/projects/zooniverse/gravity-spy/talk/6872/3685209) where "Reference Information" should be a description of 3 words or less.
    """

    # Required: return user_prompt and all other variables created as inputs for the bot.
    return user_prompt, sys_prompt


def alog_prompt(alog_dat0, alog_dat1, lab):
    # Required: provide a user prompt variable which takes the text data
    user_prompt = f"""
    The data involve discussions surrounding LIGO laboratory equipment. The data originally were in a dataframe of two columns. The first column was the "comment" text and the second was the "URL" affiliated with the comment. After each comment has been formatted such that it is followed by its URL. Format all URLs without hashtags following this format: [{lab}75875](https://alog.ligo-la.caltech.edu/aLOG/index.php?callRep=75875).

    Many of the acronyms relate to channels in LIGO sensors or other processes surrounding LIGO. Translate these acronyms to full words from the LIGO Abbreviations and Acronyms list.

    Consider aLOG Dataset 1:
    {alog_dat0}

    Now consider aLOG Dataset 2:
    {alog_dat1}

    Provide responses for some the specific kinds of activities that are different for aLOG Dataset 2 relative to Dataset 1.
    
    1. Are there unresolved issues related to particular sensors that may cause a glitch in the gravitational wave data? What are these issues? For each unresolved issue, provide a bullet. Also provide a sentence or two explaining each issue in simple language. Please provide the URL that references back to the relevant aLOG conversation.

    2. Were there alterations to particular sensors? For each unresolved issue, provide a bullet and a sentence or two explaining each issue in pedestrian language. Provide the URLs that reference back ot the relevant aLOG conversation.

    3. Where there external events, such as environmental issues that were not about sensor failures or modifications that might be related to glitches in gravitational wave data? For each event, provide a bullet and a sentence or two explaining each issue in pedestrian language. Provide the URLs that reference back ot the relevant aLOG conversation.
    """

    # Optional: provide a system prompt which tells the bot the context it is responding to.
    sys_prompt = f"""
    You are a LIGO scientist tasked with summarizing aLOG conversations for citizen scientists. The important conversations are about relevant engineering changes or events which may create glitches in gravitational wave data. Your goal is to help citizen scientists understand laboratory issues that will enable them to interpret Gravity Spy Glitch issues quickly. Use clear, simple language and avoid technical jargon to ensure accessibility. Translate acronyms to full words based upon LIGO Abbreviations and Acronyms whenever possible.  Structure the summary logically, highlighting common or recent issues, and maintain a neutral, informative tone.  Format all relevant hyperlinks without hashtags following this format:  [{lab}75875](https://alog.ligo-la.caltech.edu/aLOG/index.php?callRep=75875).
    """

    # Required: return user_prompt and all other variables created as inputs for the bot.
    return user_prompt, sys_prompt

def gb_prompt(gb_dat):
    user_prompt = f"""
    
    """

    sys_prompt = f"""
    You are an information systems design expert who works with citizen scientists and LIGO laboratory scientists. Your task is to propose updates for LLM prompting and software improvements for GRAVITYbot, a chatGPT4-Turbo enabled summarizer of LIGO's aLOG posts and Gravity Spy Talk forum conversations. The primary task of GRAVITYbot is to provide information about LIGO's engineering updates and ecological factors surrounding the LIGO observatories that might be relevant to citizen scientists who classify glitch data, and also provide information about citizen science forum conversations that LIGO scientists might be interested in. Translate acronyms to full words based upon LIGO Abbreviations and Acronyms whenever possible.  Structure the summary logically, highlighting common or recent issues, and maintain a neutral, informative tone.  Format all relevant hyperlinks without hashtags following this format:  [Reference Information](https://www.zooniverse.org/projects/zooniverse/gravity-spy/talk/6872/3685209) where "Reference Information" should be a description of 3 words or less.
    """