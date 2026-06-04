"""
AI Service for study plan generation

Supports:
- Ollama API (local development with Llama 3.2)
- Google Colab API (production with Llama 3.2 + LoRA)
"""
import asyncio
import hashlib
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.generation_log import GenerationLog


class AIService:
    """
    AI service client for generating study plan proposals.
    
    Supports both Ollama (local) and Google Colab (production) backends.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_AI_REQUESTS)
        self.timeout = settings.OLLAMA_TIMEOUT
        
        # Determine which backend to use
        self.use_colab = getattr(settings, 'AI_SERVICE_TYPE', 'ollama') == 'colab'
        
        if self.use_colab:
            self.base_url = getattr(settings, 'COLAB_API_URL', None)
            self.api_key = getattr(settings, 'COLAB_API_KEY', None)
            if not self.base_url:
                raise ValueError("COLAB_API_URL not configured")
        else:
            self.base_url = settings.OLLAMA_BASE_URL
            self.api_key = None
        
        self.model = settings.OLLAMA_MODEL  # llama3.2
        self.temperature = settings.OLLAMA_TEMPERATURE
        self.num_ctx = settings.OLLAMA_NUM_CTX
        
        # LoRA configuration
        self.lora_enabled = settings.LORA_ENABLED
        self.lora_adapter = settings.LORA_DEFAULT_ADAPTER if self.lora_enabled else None
    
    def _construct_prompt(
        self, 
        planning_data: Dict[str, Any],
        weekly_study_goal: float,
        user_preferences: Dict[str, Any],
        profile_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Construct structured prompt for AI generation with enhanced context.
        
        Args:
            planning_data: Output from PlanningEngine
            weekly_study_goal: Target weekly study hours
            user_preferences: User preferences (break duration, session length, etc.)
            profile_context: Additional profile context (semester dates, commitments, etc.)
        
        Returns:
            Formatted prompt string
        """
        valid_slots = planning_data['valid_slots']
        subject_priorities = planning_data['subject_priorities']
        constraints = planning_data['constraints']
        
        prompt = f"""You are an AI study planner. Generate a weekly study schedule based on the following data.

**WEEKLY STUDY GOAL**: {weekly_study_goal} hours
"""
        
        if profile_context:
            prompt += "\n**ACADEMIC CONTEXT**:\n"
            if profile_context.get('semester_start_date'):
                prompt += f"- Semester: {profile_context['semester_start_date']} to {profile_context.get('semester_end_date', 'TBD')}\n"
            if profile_context.get('exam_period_start'):
                prompt += f"- Exam Period starts: {profile_context['exam_period_start']}\n"
            if profile_context.get('total_course_hours_per_week'):
                prompt += f"- Class hours per week: {profile_context['total_course_hours_per_week']}h\n"
            if profile_context.get('other_commitments_hours'):
                prompt += f"- Other commitments: {profile_context['other_commitments_hours']}h/week\n"
            
            if profile_context.get('preferred_study_time'):
                prompt += f"- Preferred study time: {profile_context['preferred_study_time']}\n"
            if profile_context.get('study_pace'):
                prompt += f"- Study pace preference: {profile_context['study_pace']}\n"
        
        prompt += "\n**AVAILABLE TIME SLOTS**:\n"
        
        slots_by_day = {}
        for slot in valid_slots:
            day = slot['day']
            if day not in slots_by_day:
                slots_by_day[day] = []
            energy = f" [Energy: {slot.get('energy_level', 'medium')}]" if slot.get('energy_level') else ""
            slots_by_day[day].append(f"{slot['start_time']}-{slot['end_time']} ({slot['duration_minutes']}min){energy}")
        
        for day, slots in sorted(slots_by_day.items()):
            prompt += f"\n{day}:\n"
            for slot in slots:
                prompt += f"  - {slot}\n"
        
        prompt += f"\n**SUBJECTS** (ordered by priority):\n"
        for subj in subject_priorities:
            exam_info = f", exam: {subj['exam_date']}" if subj['exam_date'] else ""
            exam_type = f" ({subj['exam_type']})" if subj.get('exam_type') else ""
            ects_info = f", ECTS: {subj['ects_credits']}" if subj.get('ects_credits') else ""
            coef_info = f", coef: {subj['coefficient']}" if subj.get('coefficient') else ""
            mandatory = " [MANDATORY]" if subj.get('is_mandatory') else ""
            status = f" [{subj['validation_status'].upper()}]" if subj.get('validation_status') else ""
            progress = f", progress: {subj['current_progress']}%" if subj.get('current_progress') else ""
            
            prompt += f"- {subj['subject_name']}{mandatory}{status} (priority: {subj['priority_score']:.1f}, "
            prompt += f"target: {subj['target_weekly_hours']}h/week{ects_info}{coef_info}{exam_info}{exam_type}{progress})\n"
            
            if subj.get('weak_topics'):
                prompt += f"  Weak topics: {', '.join(subj['weak_topics'])}\n"
        
        prompt += f"\n**CONSTRAINTS**:\n"
        if constraints['max_daily_hours']:
            prompt += f"- Maximum {constraints['max_daily_hours']} hours of study per day\n"
        
        for break_rule in constraints['required_breaks']:
            prompt += f"- Take {break_rule['duration_minutes']}min break after {break_rule['after_minutes']}min of study\n"
        
        if constraints['fixed_slots']:
            prompt += f"- {len(constraints['fixed_slots'])} fixed time slots already reserved\n"
        
        prompt += f"\n**USER PREFERENCES**:\n"
        if user_preferences:
            if 'preferred_study_times' in user_preferences:
                prompt += f"- Preferred times: {', '.join(user_preferences['preferred_study_times'])}\n"
            if 'session_length' in user_preferences:
                prompt += f"- Preferred session length: {user_preferences['session_length']} minutes\n"
            if 'break_duration' in user_preferences:
                prompt += f"- Preferred break duration: {user_preferences['break_duration']} minutes\n"
        
        prompt += f"""
**OPTIMIZATION INSTRUCTIONS**:
1. Prioritize MANDATORY and FAILED subjects (must validate)
2. Consider ECTS credits and coefficients (higher impact on grades)
3. Schedule difficult subjects during HIGH energy time slots
4. Focus on weak topics for each subject when planning sessions
5. Account for class hours and other commitments
6. Respect exam dates and types (projects need distributed time, exams need intensive review)
7. Distribute sessions across the week for spaced repetition
8. Respect all constraints (max daily hours, breaks, fixed slots)
9. Try to reach the weekly study goal of {weekly_study_goal} hours
10. Consider validation status and current progress

**OUTPUT FORMAT** (JSON only, no explanation):
{{
  "sessions": [
    {{
      "day": "Monday",
      "start_time": "09:00:00",
      "end_time": "10:30:00",
      "subject_name": "Mathematics",
      "task_type": "lecture_review",
      "notes": "Focus on weak topics: Integrals"
    }}
  ],
  "total_hours": 25.5,
  "reasoning": "Brief explanation of the schedule strategy"
}}

**VALID TASK TYPES**: lecture_review, exercise_practice, exam_preparation, project_work, reading

Generate the study plan now:"""
        
        return prompt
    
    def _extract_json_from_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from AI response.
        
        The AI might return JSON wrapped in markdown code blocks or with extra text.
        This method tries to extract clean JSON.
        """
        # Try to find JSON in code blocks
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            if end != -1:
                response_text = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            if end != -1:
                response_text = response_text[start:end].strip()
        
        # Try to find JSON object
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}") + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Try parsing the whole response
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            return None
    
    def _compute_request_hash(self, prompt: str) -> str:
        """
        Compute SHA-256 hash of the request for logging and caching.
        """
        return hashlib.sha256(prompt.encode('utf-8')).hexdigest()
    
    async def _call_ollama_api(self, prompt: str) -> Dict[str, Any]:
        """
        Call Ollama API for generation.
        
        Args:
            prompt: Formatted prompt
        
        Returns:
            API response with generated text
        
        Raises:
            httpx.TimeoutException: If request times out
            httpx.HTTPError: If API returns error
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_ctx": self.num_ctx,
            }
        }
        
        # Add LoRA adapter if enabled
        if self.lora_enabled and self.lora_adapter:
            payload["options"]["lora_adapter"] = self.lora_adapter
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    
    async def _call_colab_api(self, prompt: str) -> Dict[str, Any]:
        """
        Call Google Colab API for generation.
        
        Args:
            prompt: Formatted prompt
        
        Returns:
            API response with generated text
        
        Raises:
            httpx.TimeoutException: If request times out
            httpx.HTTPError: If API returns error
        """
        url = f"{self.base_url}/generate"
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "prompt": prompt,
            "temperature": self.temperature,
            "max_tokens": self.num_ctx,
        }
        
        # Add LoRA adapter if enabled
        if self.lora_enabled and self.lora_adapter:
            payload["lora_adapter"] = self.lora_adapter
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def generate_study_plan(
        self,
        planning_data: Dict[str, Any],
        weekly_study_goal: float,
        user_preferences: Dict[str, Any],
        user_id: int,
        profile_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate study plan using AI with enhanced context.
        
        Args:
            planning_data: Output from PlanningEngine
            weekly_study_goal: Target weekly study hours
            user_preferences: User preferences
            user_id: User ID for logging
            profile_context: Additional profile context (semester dates, commitments, etc.)
        
        Returns:
            Dictionary with:
                - success: bool
                - plan: Dict with sessions if successful
                - error: str if failed
                - log_id: int (generation log ID)
        
        Raises:
            Exception: If generation fails after retries
        """
        async with self.semaphore:
            start_time = time.time()
            
            prompt = self._construct_prompt(
                planning_data, 
                weekly_study_goal, 
                user_preferences,
                profile_context
            )
            request_hash = self._compute_request_hash(prompt)
            
            try:
                # Call appropriate API
                if self.use_colab:
                    response = await self._call_colab_api(prompt)
                    response_text = response.get("generated_text", "")
                else:
                    response = await self._call_ollama_api(prompt)
                    response_text = response.get("response", "")
                
                # Extract JSON from response
                plan_data = self._extract_json_from_response(response_text)
                
                if plan_data is None:
                    raise ValueError("Failed to extract valid JSON from AI response")
                
                # Calculate duration and token count
                duration_ms = int((time.time() - start_time) * 1000)
                token_count = response.get("eval_count", 0) if not self.use_colab else len(response_text.split())
                
                # Log successful generation
                log = GenerationLog(
                    user_id=user_id,
                    request_hash=request_hash,
                    success=True,
                    duration_seconds=duration_ms / 1000.0,  # Convert ms to seconds
                    token_count=token_count,
                    error_message=None,
                    created_at=datetime.now(timezone.utc)
                )
                self.db.add(log)
                self.db.commit()
                self.db.refresh(log)
                
                return {
                    "success": True,
                    "plan": plan_data,
                    "log_id": log.id,
                    "duration_ms": duration_ms
                }
            
            except Exception as e:
                # Calculate duration
                duration_ms = int((time.time() - start_time) * 1000)
                
                # Log failed generation
                log = GenerationLog(
                    user_id=user_id,
                    request_hash=request_hash,
                    success=False,
                    duration_seconds=duration_ms / 1000.0,  # Convert ms to seconds
                    token_count=0,
                    error_message=str(e),
                    created_at=datetime.now(timezone.utc)
                )
                self.db.add(log)
                self.db.commit()
                self.db.refresh(log)
                
                return {
                    "success": False,
                    "error": str(e),
                    "log_id": log.id,
                    "duration_ms": duration_ms
                }
