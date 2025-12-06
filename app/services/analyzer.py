import httpx
import json
from typing import Dict, Any, Optional
from app.config import get_settings


settings = get_settings()


class AnalyzerService:
    """
    Service for analyzing documents using OpenRouter LLM API
    """

    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.base_url = settings.openrouter_base_url
        self.model = settings.openrouter_model

    def _create_analysis_prompt(self, text: str) -> str:
        """
        Create a detailed prompt for the LLM to analyze the document.

        Args:
            text: Extracted text from document.
        :param text:
        :return:
        """
        prompt = f"""Analyze the following document and provide:
1. A concise summary. (2-5 sentences).
2. The document type (choose from: invoice, CV/resume, report, letter, contract, receipt, form, other)
3. Extract relevant metadata based on document type:
   - For invoices: invoice_number, date, total_amount, vendor, customer.
   - For CVs: candidate_name, email, phone, years_of_experience, key_skills
   - For reports: report_title, date, author, department
   - For letters: sender, recipient, date, subject.
   - For contracts: parties_involved, contract_date, contract_type, expiry_date
   - For receipts: merchant, date, total_amount, payment_method
   - For other types: extract any relevant dates, names, amounts, or key information.
   
Document text:
{text[:4000]}

Respond ONLY with valid JSON in this exact format (no markdown, no code blocks):
{{
"summary": "Your concise summary here.",
"document_type": "invoice|CV|report|letter|contract|receipt|form|other",
"metadata": {{
    "key1": "value1",
    "key2": "value2"
    }}
}}"""
        return prompt

    async def analyze_document(self, text: str) -> Dict[str, Any]:
        """
        Send document text to OpenRouter API for analysis
        :param text:
        :return: Dict containing summary, document_type, metadata
        """
        if not self.api_key:
            raise Exception("OpenRouter API key not configured. Please set OPENROUTER_API_KEY in environment variables.")

        if not text or len(text.strip()) < 10:
            raise Exception("Document text is too short or empty for analysis")

        # Prepare the API request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost:8000", # Optional: for OpenRouter analytics
            "X-Title": "Document Analyzer" # Optional: for OpenRouter analytics
        }

        prompt = self._create_analysis_prompt(text)
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3, # Lower temperature for more consistent results
            "max_tokens": 1000
        }

        try:
            # Make async HTTP request to OpenRouter API
            async with httpx.AsyncClient(timeout=60.0) as client:
                # print("making request to OpenRouter API...")
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )

                # Check if request was successful
                if response.status_code != 200:
                    error_detail = response.text
                    raise Exception(f"OpenRouter API error {response.status_code}: {error_detail}")

                # Parse response
                response_data = response.json()
                # print(f"OpenRouter API response: {response_data}")

                # Extract the AI's message
                if "choices" not in response_data or len(response_data["choices"]) == 0:
                    raise Exception("Invalid response from OpenRouter API: 'choices' missing")

                ai_message = response_data["choices"][0]["message"]["content"]


                # Parse JSON response from AI
                analysis_result = self._parse_ai_response(ai_message)

                # print(f"Analysis result: {analysis_result}")

                return analysis_result

        except httpx.TimeoutException:
            raise Exception("Request to OpenRouter API timed out")
        except httpx.RequestError as e:
            raise Exception(f"Network error while contacting OpenRouter API: {str(e)}")
        except json.JSONDecoder as e:
            raise Exception(f"Failed to parse OpenRouter API response: {str(e)}")
        except Exception as e:
            raise Exception(f"Analysis failed: {str(e)}")

    def _parse_ai_response(self, ai_message: str) -> Dict[str, Any]:
        """
        Parse the AI's response and extract structured data.


        :param ai_message: Raw response from the AI.
        :return: Dict with summary, document_type, metadata
        """
        try:
            # Remove markdown code blocks if present
            cleaned_message = ai_message.strip()
            if cleaned_message.startswith("```"):
                # Remove ```json or ``` from start
                cleaned_message = cleaned_message.split("\n", 1)[1]
            if cleaned_message.endswith("```"):
                # Remove ``` from end
                cleaned_message = cleaned_message.rsplit("\n", 1)[0]

            cleaned_message = cleaned_message.strip()

            # Parse JSON
            result = json.loads(cleaned_message)

            # Validate required fields
            if "summary" not in result:
                raise ValueError("Missing 'summary' filed in AI response")
            if "document_type" not in result:
                raise ValueError("Missing 'document_type' filed in AI response")
            if "metadata" not in result:
                result["metadata"] = {}

            return {
                "summary": result["summary"],
                "document_type": result["document_type"],
                "metadata": result["metadata"],
            }

        except json.JSONDecodeError as e:
            return {
                "summary": ai_message[:500],
                "document_type": "unknown",
                "metadata": {"error": "Failed to parse structured response", "raw_response": ai_message[:200]},
            }
        except Exception as e:
            raise Exception(f"Failed to parse AI response: {str(e)}")

# Singleton instance
analyzer_service = AnalyzerService()


