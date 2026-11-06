# AGENTS

Instructions for coding agents working on the **Balance** project.

## Project

Create a hands-on visual introduction to algebra and serve it as a GitHub pages site.

### Core game mechanics

A central weighing scale must be kept balanced. It has a flat weighing plate on each side, visually reminiscent of a vinculum. Legal moves retain equality, while illegal moves unbalance the scale and reset the level.

Variables are represented by coloured marbles. At the start of each level they are placed on or under the weighing plates. The player must move them according to the rules of algebra.

## Structure

- Static Website
- One page per game level
- Maintain separation of concerns

### Languages

- HTML
- CSS
- JavaScript

### Hosting

GitHub Pages

#### Location

`/docs` directory

## GitHub Workflow

- Look for a feature branch that handles your task and commit to it if possible.
- If there is no existing branch for your task, create a new feature branch named `<task-name>` and commit to it.
- Commit only to the appropriate feature branch.
- Never modify the default branch directly.
- Write a message for each commit.
- Clearly sign your commit messages as an AI so that human and agentic commits can be distinguished.
- Open a draft pull request targeting `main`.
- Link the original GitHub issue where applicable.
- Document tests performed, results and limitations.
- Do not merge pull requests.
- Leave final review and merge decisions to the human.
