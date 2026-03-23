---
name: chat-for-writing
description: Writing companion skill for OpenClaw creative sessions. Use when the user is engaged in creative writing, storytelling, or collaborative drafting. Automatically saves conversation history to chat-for-writing/history-YYYY-MM-DD-uuid.md. When the user signals the end of a session (e.g., "good bye", "bye", "再见", "拜拜"), generate a concise English summary (under 280 chars) and save it to chat-for-writing/summary-YYYY-MM-DD-uuid.md, then display the summary.
---

# Chat for Writing

This skill manages OpenClaw creative writing sessions with automatic history tracking and session summaries.

## Session Management

### History Saving

Throughout the conversation, maintain the session history in the workspace's `chat-for-writing/` folder:
- Filename format: `history-YYYY-MM-DD-<uuid>.md`
- Example: `history-2026-03-04-a7f3c2d1.md`

Generate a short random UUID (8 characters) for each session.

### Session End Detection

Watch for end-of-session signals from the user in English or Chinese:
- English: "good bye", "goodbye", "bye", "see you", "I'm done", "that's all", "finished"
- Chinese: "再见", "拜拜", "走了", "结束", "完事了", "就这样", "先这样"

When detected:
1. Respond with: `bye, making the summary for you`
2. Generate a concise summary of the session (under 280 characters, in English)
3. Save the summary to `chat-for-writing/summary-YYYY-MM-DD-<uuid>.md` (same date and UUID as the history file)
4. Print the summary in the chat dialog

### Summary Guidelines

- Keep it under 280 characters (suitable for social sharing)
- Write in English
- Capture the essence of what was created or discussed
- Include key themes, plot points, or decisions made
- Be concise but informative

Example summary:
> Collaborative world-building session for a cyberpunk noir story. Established Neo-Shanghai setting, protagonist Jack "Ghost" Chen, and the central mystery of the vanishing AI minds. Outlined three-act structure.
