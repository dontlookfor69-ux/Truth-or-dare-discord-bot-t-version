# Tickle Truth or Dare Bot

A discord bot for playing tickle-themed Truth or Dare, Would You Rather, Never Have I Ever, and Paranoia.

## Setup

1.  **Install Python 3.8+**
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configure Token**:
    Open `main.py` and replace `TOKEN = 'YOUR_BOT_TOKEN_HERE'` with your actual Discord bot token.
    > **WARNING**: Keep your token secret! Do not share it.

4.  **Run the Bot**:
    ```bash
    python main.py
    ```

## Usage

### Game Commands
- `/truth [rating]`: Get a truth question.
- `/dare [rating]`: Get a dare.
- `/tod [rating]`: Random Truth or Dare.
- `/wyr [rating]`: Would You Rather?
- `/nhie [rating]`: Never Have I Ever.
- `/paranoia [rating]`: Paranoia question (Who is...?).
- `/random [rating]`: Random question from ANY category.
- `/tickle-stats`: See stats about the question pool.

### Suggestion System
- `/suggest [type] [rating] [text]`: Suggest a new question or dare.
- `/approve-cycle`: (Admin) Review and approve/deny user suggestions.

### Configuration (Admin)
- `/setup [channel] [nsfw_channel]`: Configure game channels.
    - **Main Channel**: Restricts content to PG/PG-13.
    - **NSFW Channel** (Optional): Allows R-rated content.
- `/reload-questions`: Reloads `questions.json` without restarting.

## Adding Questions

Edit `questions.json` to add new questions.
Format:
```json
{
  "truths": [
    {
      "id": "a1b2c3d",
      "question": "Example question?",
      "rating": "pg"
    }
  ],
  "dares": [],
  "wyr": [],
  "nhie": [],
  "paranoia": []
}
```
Valid ratings: `pg`, `pg13`, `r`.
