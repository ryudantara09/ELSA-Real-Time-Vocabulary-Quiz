# Real-Time Vocabulary Quiz Coding Challenge

## Overview

Welcome to the Real-Time Quiz coding challenge! Your task is to create a technical solution for a real-time quiz feature for an English learning application. This feature will allow users to answer questions in real-time, compete with others, and see their scores updated live on a leaderboard.

## Acceptance Criteria

1. **User Participation**:
   - Users should be able to join a quiz session using a unique quiz ID.
   - The system should support multiple users joining the same quiz session simultaneously.

2. **Real-Time Score Updates**:
   - As users submit answers, their scores should be updated in real-time.
   - The scoring system must be accurate and consistent.

3. **Real-Time Leaderboard**:
   - A leaderboard should display the current standings of all participants.
   - The leaderboard should update promptly as scores change.

## Challenge Requirements

### Collaborating with AI: A Core Requirement
Modern software engineering requires effective collaboration with AI. Therefore, **this challenge requires using Generative AI tools (like GitHub Copilot, Gemini, Claude, Cursor AI, etc.)**. Treat them as essential partners for tasks such as brainstorming designs, accelerating coding, refactoring, generating documentation, creating test cases, or debugging complex issues.

This challenge assesses your core technical skills and ability to strategically leverage AI to enhance productivity and solution quality. **You must demonstrate and document your AI usage** throughout the design and implementation process as specified below; this is a key evaluation criterion. Show us how you integrate these powerful tools into your workflow responsibly and effectively.

### Part 1: System Design

1. **System Design Document**:
   - **Architecture Diagram**: Create an architecture diagram illustrating component interactions (server, client apps, database, real-time communication layer, etc.).
   - **Component Description**:  Describe each component's role.
   - **Data Flow**: Explain how data flows through the system from when a user joins a quiz to when the leaderboard is updated.
   - **Technologies and Tools**: List and justify the technologies and tools chosen for each component.

### Part 2: Implementation

1. **Pick a Component**:
   - Implement one core real-time component (e.g., the server handling connections/scoring/leaderboard, or a client demonstrating real-time updates). Use technologies you prefer. Mock the rest of the system.

2. **Requirements for the Implemented Component**:
   - **Real-time Quiz Participation**: Users should be able to join a quiz session using a unique quiz ID.
   - **Real-time Score Updates**: Users' scores should be updated in real-time as they submit answers.
   - **Real-time Leaderboard**: A leaderboard should display the current standings of all participants in real-time.

3. **AI Collaboration in Implementation (Required Documentation)**:
   - Clearly indicate (e.g., via code comments or separate documentation) code sections generated or **significantly assisted** by GenAI tools. Use your judgment to identify where AI played a meaningful role beyond simple auto-completion. **Some level of AI assistance in implementation is expected**.
   - For these sections, describe:
      - The tool and task (e.g., "Used ChatGPT to generate initial WebSocket server setup," "Refactored scoring logic with Copilot suggestions").
      - The prompts or interaction nature.
      - **Crucially**: The steps you took to **verify, test, debug, and refine** the AI-assisted code to ensure its correctness, efficiency, and alignment with requirements. Demonstrating this verification process is mandatory.

4. **Build For the Future**:
   - **Scalability**: Design and implement your component with scalability in mind. Consider how the system would handle a large number of users or quiz sessions. Discuss any trade-offs you made in your design and implementation.
   - **Performance**: Your component should perform well even under heavy load. Consider how you can optimize your code and your use of resources to ensure high performance.
   - **Reliability**: Your component should be reliable and handle errors gracefully. Consider how you can make your component resilient to failures.
   - **Maintainability**: Your code should be clean, well-organized, and easy to maintain. Consider how you can make it easy for other developers to understand and modify your code.
   - **Monitoring and Observability**: Discuss how you would monitor the performance of your component and diagnose issues. Consider how you can make your component observable.

## Submission Guidelines

Candidates are required to submit the following:

1. **System Design Documents**: Including all sections from Part 1, ensuring the **AI Collaboration in Design** section details your mandatory AI usage.

2. **Working Code**:
   - Your implemented component.
   - Clear documentation/comments on **AI Collaboration in Implementation**, demonstrating the required AI usage and verification.
   - Code considering scalability, performance, etc.
   - Instructions to run the code/tests.

3. **Video Submission**:
   - Short video **(strictly 5-10 minutes)**. Quality matters!
   - Address:
      - **Introduction**: You!
      - **Assignment Overview**: Your understanding.
      - **Solution Overview**: Your design & implementation highlights.
      - **AI Collaboration Story (Required)**: Dedicate time (e.g., 1-2 minutes) to discuss your mandatory collaboration with GenAI tools:
         - Which AI partners did you work with and for which specific tasks during the challenge?
         - How did they help you succeed or accelerate your work? Provide concrete examples.
         - What challenges or limitations did you encounter while working with AI?
         - **Most importantly**, walk us through your process for ensuring the quality, correctness, and security of AI-assisted output. How did you test and verify? (This part is critical!)
      - **Demo**: Show your code/tests in action.
      - **Conclusion**: Learnings, challenges, future ideas.

## Solution

People create a quiz, share its ID, and join with a display name. Each person answers five vocabulary questions. The first answer is final. A correct answer adds 1 point. Everyone in that quiz sees the leaderboard update over a WebSocket. Another quiz does not.

A picture of the pieces and the live answer flow is in [docs/how-it-works.md](docs/how-it-works.md). The design, including what is built and what is only planned, is in [docs/system-design.md](docs/system-design.md). How Cursor was used, reviewed, and checked is in [docs/ai-collaboration.md](docs/ai-collaboration.md).

### Architecture

One Vue 3 app talks to one FastAPI process. REST creates the quiz and the participant. The WebSocket carries questions, answers, and the leaderboard. `QuizService` owns scoring and leaderboard order. Sessions and socket rooms are in memory. Redis, a database, and authentication are not implemented.

### Stack

- Python, FastAPI, Uvicorn, and the `websockets` library
- Vue 3, TypeScript, and Vite
- pytest for the API, Vitest and Vue Test Utils for the page

### Run the app

Use two terminals. Start the API first.

From `backend`:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

From `frontend`:

```powershell
npm install
npm run dev
```

Open http://127.0.0.1:5173. The dev server proxies `/quizzes` and `/ws` to the API. `GET http://127.0.0.1:8000/health` returns `{"status":"ok"}`.

### Run the tests

From `backend`:

```powershell
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m pytest
```

From `frontend`:

```powershell
npm install
npm test
```

### Demo

1. Start the API and the Vue app.
2. In the first window, choose **Create quiz**, enter a name, and choose **Join quiz**.
3. Copy the quiz ID into a second window, enter a different name, and join.
4. In the first window, answer the first question. Both leaderboards update. A correct answer shows score 1 for that person only.
5. Refresh the first window. The same person, score, and question come back.
6. Choose **Leave quiz** to return to the join form.

A second quiz ID does not show the first quiz's participants. Restarting the API clears in-memory sessions. The page then asks the person to join again.
