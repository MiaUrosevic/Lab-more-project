# Local Project Chat Agent

![doctests](https://img.shields.io/github/actions/workflow/status/MiaUrosevic/Lab-more-project/doctests.yml?label=doctests)
![integration-tests](https://img.shields.io/github/actions/workflow/status/MiaUrosevic/Lab-more-project/integration-tests.yml?label=integration-tests)
![flake8](https://img.shields.io/github/actions/workflow/status/MiaUrosevic/Lab-more-project/flake8.yml?label=flake8)
<!--
![coverage](https://img.shields.io/badge/coverage-91%25-brightgreen)
how can I trust this since you don't run the coverage in the github actions?
-->
![pypi](https://img.shields.io/pypi/v/cmc-csci40-mia)

A command-line AI agent for inspecting local software projects with safe built-in tools like `ls`, `cat`, `grep`, `calculate`, and `compact`. It supports both manual slash commands and automatic tool use for common project questions.

<!--
nothing about your demo gif, test cases, or README examples actually shows your project calling the LLM anywhere;
it is all hard coded stuff
-->
![demo](demo.gif)

<!--
features list reads like AI slop; it should be incorporated directly into the usage

the installation instructions were incorrect
-->

## Usage

```bash
$ chat "what is 2 + 2?"
$ chat --debug "what files are in the .github folder?"
$ chat --provider groq "show me README.md"
```

This shows the agent answering a high-level question about a real scraping project.

```bash
$ cd test_projects/webscraping_project
$ chat "what is this project about?"
```
<!--
minor: if you pip install, then you don't need to use the python3 chat.py command, and you can run from any folder

major problem: you don't actually show what the output looks like; how is the reader supposed to know what your project does if you don't tell them?
-->

This shows the agent inspecting implementation details across source files.

```bash
$ cd test_projects/markdown_compiler
$ python ../../chat.py "find def in *.py"
```

This example shows the agent reading and summarizing files from a real webpage project.

```bash
$ cd test_projects/Mia.Urosevic.github.io
$ python ../../chat.py "show me README.md"
```
