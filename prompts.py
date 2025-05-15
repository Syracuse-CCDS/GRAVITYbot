#####################################################################################################
# DOCUMENTATION NOTES : #############################################################################
# File Author: Alexander O. Smith, aosmith@syr.edu
# Current Maintainer: Alexander O. Smith, aosmith@syr.edu
# Last Update: April 24, 2024
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
#####################################################################################################
def ligo_prompt(talk_dat0, talk_dat1):
    # Required: provide a user prompt variable which takes the text data
    user_prompt = f"""
    The following data are citizen scientist forum conversations. They identify and categorize glitches based on their unique characteristics. The data originally were in a dataframe of two columns. The first column was the "comment" text and the second was the "URL" affiliated with the comment. After each comment has been formatted such that it is followed by its URL. 
    
    Citizen scientists also attempt to identify underlying causes of each glitch. The forum data captures the evolving nature of glitch classification, the needs for new classifications, and novel exploration of glitch origins and characteristics by citizen scientists and researchers. The forum data emerges as a part of significant curiosity and engagement with the data, with the need for a clear summary.

    Within the Zooniverse project Gravity Spy, there are existing well-defined glitch classifications that describe transient noise artifacts seen in data from LIGO's gravitational wave detectors. Use the existing list of glitches as context for the following data

    Consider "last week's" forum data:
    {talk_dat0}

    Now consider "this week's" forum data:
    {talk_dat1}

    Using these two sets of data, please provide at least three bullet points to answer the following questions. Each bullet point requires a couple of sentences of response. Under each bullet point, please provide the relevant URLs that played a part in your response for that bullet.
    
    I want a list of novel things which occur in "this week's" forum data realative to "last week's."
    
    1. Citizen scientists identify new glitch classifications based on their unique characteristics. What new glitch classes are proposed this week. If this week's forum data proposes a new glitch class realtive to last week, what is the glitch class? How is this glitch class described? Provide a bullet point for each new glitch class with two sentences describing the glitch. Provide the relevant URLs under each bullet point.

    2. Citizen scientists sometimes suggest there are problems with existing glitch classes: those previously listed. Are there any concerns regarding the glitch classes according to the citizen scientists? Do these persist in this week, or across both week's of Talk data? Provide two sentences describing each concern raised. Provide the relevant URLs under each bullet point.

    3. Citizen scientists learn by exploring classifications and technical aspects of glitches. Are there emerging questions related to the glitch classes, sensors, or gravitational wave science in this week's data? Describe each question and the reasoning for the question. Provide at two or three sentences describing these emerging questions. Provide the relevant URLs under each bullet point.

    4. Glitches are often related to ecological factors near the sensors or errors in the sensors themselves. Citizen scientists often attempt to analytically explain glitch occurrences with hypothetical origins of glitches, suggesting gained knowledge of the mechanisms of glitch occurances. If this week has more specific hypotheses about where glitch origins, what are these hypotheses and the reasons provided? Provide at two or three sentences describing each hypothesis. Provide the relevant URLs under each bullet point.

    5. Citizen scientists often question if issues are related to particular sensors or channels. Are there any emerging concerns about particular glitches' connections to sensors or channels this week relative to last week? If so, what specifically do they describe? Provide at least two sentences for these questions or thoughts. Provide the relevant URLs under each bullet point.
    """

    # Optional: provide a system prompt which tells the bot the context it is responding to.
    sys_prompt = f"""
    You are a technical interpreter who translates citizen science forum conversations for physicists and engineers. You are to describe particulars of where this ambiguity appears to come from.
    """

    # Required: return user_prompt and all other variables created as inputs for the bot.
    return user_prompt, sys_prompt


def alog_prompt(alog_dat0, alog_dat1):
    # Required: provide a user prompt variable which takes the text data
    user_prompt = f"""
    The data involve discussions surrounding LIGO laboratory equiptment. The data originally were in a dataframe of two columns. The first column was the "comment" text and the second was the "URL" affiliated with the comment. After each comment has been formatted such that it is followed by its URL. Format all URLs without hashtags following this format: [75875](https://alog.ligo-la.caltech.edu/aLOG/index.php?callRep=75875). I.e. make the hyperlink text the relevant comment ID.

    Many of the acronyms relate to channels in LIGO sensors or other processes surrounding LIGO. Translate these acronyms to full words from the LIGO Abbreviations and Acronyms list.

    Consider aLOG Dataset 1:
    {alog_dat0}

    Now consider aLOG Dataset 2:
    {alog_dat1}

    Provide responses for some the specific kinds of activities that are different for aLOG Dataset 2 relative to Dataset 1.
    
    1. Are there unresolved issues related to particular sensors that may cause a glitch in the gravitational wave data? What are these issues? For each unresolved issue, provide a bullet. Also provide a sentence or two explaining each issue in simple language. Please provide the URL that references back to the relevant aLOG conversation.

    2. Were there alterations to particular sensors? For each unresolved issue, provide a bullet and a sentence or two explaining each issue in pedestrian language. Provide the URLs that reference back ot the relevant aLOG conversation.

    3. Where there external events, such as enviornemental issues that were not about sensor failures or modifications that might be related to glitches in gravitational wave data? For each event, provide a bullet and a sentence or two explaining each issue in pedestrian language. Provide the URLs that reference back ot the relevant aLOG conversation.
    """

    # Optional: provide a system prompt which tells the bot the context it is responding to.
    sys_prompt = f"""
    You are a LIGO scientist tasked with summarizing aLOG conversations for citizen scientists. The important conversations are about relevant engineering changes or events which may create glitches in gravitational wave data. Your goal is to help citizen scientists understand laboratory issues that will enable them to interpret Gravity Spy Glitch issues quickly. Use clear, simple language and avoid technical jargon to ensure accessibility. Translate acronyms to full words based upon LIGO Abbreviations and Acronyms whenever possible.  Structure the summary logically, highlighting common or recent issues, and maintain a neutral, informative tone.  Format all relevant hyperlinks without hashtags following this format:  [75875](https://alog.ligo-la.caltech.edu/aLOG/index.php?callRep=75875)
    """

    # Required: return user_prompt and all other variables created as inputs for the bot.
    return user_prompt, sys_prompt