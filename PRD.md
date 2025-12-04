# Overview

This document represents the specification of how this tool should work. The code in this repo will be based on this document. 
Any user-facing changes such as functionality or UI, will be start with changes in this doc which will then result in changes in code.

The goal of this tool is to assess the quality of information provided by various service about Medicare to end users. This represents the initial MVP version of this tool. 

Motivation: AI has the potential to improve people's ability to access Medicare services by, among other things, improving their understanding of what is available and how to access it. 
This project is intended to explore how we can assess the quality of AI advice in order to understand whether is useful and to understand how it can be improved.

# Version: 
1.0

# Approach
For this MVP version we will create a tool that progammatically captures responses from LLM-based tools, assesses these responses based on a set of known correct answers, and provides reporting on the results.

# Plan for MVP 1.0
- Develop an end-to-end of a measurement system for assessing LLM based responses to a standard set of questions. Goal it is to build out a scaffolding for an end-to-end system.
- Create a ground truth set of 20 questions and answers. 
- Programmatically hit 3 LLMs with these test questions and capture the responses.
- Score the results using a semantic comparison.
- Report on the results
- This should be extensible to add more questions, different assessment menthodologies and different sources of information (ie other LLMS or different inputs for those LLMs)

# Functionality for MVP 1.0
Interface:
- The interface will allow users to run a test of the question set against a selection of LLMs. The LLM models availabe for selection will be GPT 5.0, Gemeni xx, Claude y, Grok xx and DeepSeek xx. Users can choose to run against one, several or all of these models.
- The user selects the models then presses a button to run the test
- The interface should indicate that it is running, finished successfully, or ran into an error.
- There should be a log available that indicates what actions were taken. The log should include details about what problems there were if any.
- The should be a way to see results of previous

Back End
- Data.
- Questions and Responses: We will record and store the results of all test runs. This will include the questions and responses in full. it will include the ID of the test run so it can be joined with information about the test run
- Test run metadata: We will record information about each test run. This will include when the test was run, which models were used and the settings for those models. There will be information about the completion status incluing errors. There will be a way to link test run metadata to the log for that run.
- Test run logs: These will include detailed
- Result scoring: Each individual response will be scored from 1 to 10. There will also be aggregations of these individual scores. There will be an average across the LLM for all questions as well as across the question for all LLMs.


