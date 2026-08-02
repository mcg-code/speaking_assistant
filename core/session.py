from typing import Dict
from core.prompts import SYSTEM_PROMPT, FEEDBACK_PROMPT
from services import llm_service, tts_service, storage_service, memory_service

class PracticeSession:
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.model_name = config.get("model_name", "qwen2.5:3b")
        self.obsidian_path = config.get("obsidian_path", "")
        
        # Inject memory
        past_mistakes = memory_service.get_relevant_mistakes_text()
        system_prompt = SYSTEM_PROMPT.format(past_mistakes=past_mistakes)
        
        self.history = [{'role': 'system', 'content': system_prompt}]

    def process_user_input(self, user_text: str) -> str:
        """Processes the user's input, sends it to the LLM, and speaks the response."""
        self.history.append({'role': 'user', 'content': user_text})
        
        try:
            ai_reply = llm_service.chat(self.model_name, self.history)
            self.history.append({'role': 'assistant', 'content': ai_reply})
            tts_service.speak(ai_reply)
            return ai_reply
        except Exception as e:
            return f"Error: {str(e)}"

    def end_session_and_generate_feedback(self) -> str:
        """Analyzes the session history, generates feedback, and saves it."""
        # Filter out system prompts and clearly tag roles for the transcription
        transcription_lines = []
        student_lines = []
        for msg in self.history:
            if msg['role'] == 'user':
                transcription_lines.append(f"STUDENT: {msg['content']}")
                student_lines.append(f"- {msg['content']}")
            elif msg['role'] == 'assistant':
                transcription_lines.append(f"EXAMINER: {msg['content']}")
        
        if not transcription_lines:
            return "No conversation history found to analyze."
            
        transcription_text = "\n".join(transcription_lines)
        student_text = "\n".join(student_lines)
        
        analysis_request = [
            {'role': 'system', 'content': FEEDBACK_PROMPT},
            {'role': 'user', 'content': f"Here are the sentences spoken by the STUDENT:\n\n{student_text}"}
        ]
        
        try:
            feedback = llm_service.chat(self.model_name, analysis_request)
            saved_path = storage_service.save_feedback_report(
                self.obsidian_path, 
                transcription_text, 
                feedback
            )
            
            # Store in long-term memory
            memory_service.store_mistakes(self.model_name, feedback)
            
            return feedback, saved_path
        except Exception as e:
            return f"Error generating feedback: {str(e)}", None
