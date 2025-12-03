# Overview

This document represents the specification of how this tool should work. The code in this repo will be based on this document. 
Any user-facing changes such as functionality or UI, will be start with changes in this doc which will then result in changes in code.

The goal of this tool is to assess the quality of information provided by various service about Medicare to end users. This represents the initial MVP version of this tool. 

Motivation: AI has the potential to improve people's ability to access Medicare services by, among other things, improving their understanding of what is available and how to access it. 
This project is intended to explore how we can assess the quality of AI advice in order to understand whether is useful and to understand how it can be improved.

# Approach
For this MVP version we will create a tool that progammatically captures responses from LLM-based tools, assesses these responses based on a set of known correct answers, and provides reporting on the results.

# Plan for MVP 1.0
- Develop an end-to-end of a measurement system for assessing LLM based responses to a standard set of questions. Goal it is to build out a scaffolding for an end-to-end system.
- Create a ground truth set of 20 questions and answers. 
- Programmatically hit 3 LLMs with these test questions and capture the responses.
- Score the results using a semantic comparison.
- Report on the results
- This should be extensible to add more questions, different assessment menthodologies and different sources of information (ie other LLMS or different inputs for those LLMs)


