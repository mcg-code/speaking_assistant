import os
from datetime import datetime

def save_feedback_report(obsidian_path: str, transcription: str, feedback: str) -> str:
    """
    Saves the session transcription and feedback into a Markdown file
    in the specified Obsidian vault path.
    
    Returns:
        The full path to the created file.
    """
    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"English_Feedback_{date_str}.md"
    full_path = os.path.join(obsidian_path, filename)
    
    # Ensure the directory exists
    os.makedirs(obsidian_path, exist_ok=True)
    
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(f"# English Speaking Session Feedback - {date_str}\n\n")
        f.write("## Transcription\n```text\n")
        f.write(transcription)
        f.write("\n```\n\n## Feedback & Mistakes\n")
        f.write(feedback)
        
    return full_path
