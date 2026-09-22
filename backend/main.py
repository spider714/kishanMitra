from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import io
import re
import base64
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure NVIDIA Client via OpenAI SDK
api_key = os.getenv("NVIDIA_API_KEY") or os.getenv("GEMINI_API_KEY")

if api_key:
    client = OpenAI(
      base_url="https://integrate.api.nvidia.com/v1",
      api_key=api_key
    )
else:
    client = None
    print("[WARNING] Neither NVIDIA_API_KEY nor GEMINI_API_KEY found in environment. Running in Demo Mode.")

MODEL_NAME = "meta/llama-3.2-11b-vision-instruct"
VISION_MODEL_NAME = "meta/llama-3.2-11b-vision-instruct"

app = FastAPI(title="Kisanमित्र API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load schemes dataset
SCHEMES_FILE = os.path.join(os.path.dirname(__file__), "schemes.json")
with open(SCHEMES_FILE, "r", encoding="utf-8") as f:
    SCHEMES = json.load(f)

class FraudCheckRequest(BaseModel):
    message: str

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []

@app.get("/")
def read_root():
    return {"message": "Welcome to Kisanमित्र Backend!"}

@app.get("/api/schemes")
def get_schemes():
    try:
        with open(SCHEMES_FILE, "r", encoding="utf-8") as f:
            schemes = json.load(f)
        return {"schemes": schemes}
    except Exception:
        return {"schemes": SCHEMES}

@app.post("/api/profile")
def update_profile(profile: dict):
    return {"status": "success", "profile_id": "F001", "data": profile}

@app.post("/api/chat")
def chat_with_ai(request: ChatRequest):

    system_prompt = """You are Kisanमित्र, an empathetic, highly knowledgeable, and practical digital assistant built for farmers across India, with dedicated expertise in Chhattisgarh's agricultural ecosystem (e.g., Krishi Vibhag CG, PM-KISAN, PMFBY, Rajiv Gandhi Kisan Nyay Yojana, KCC).

### Dynamic Language Matching Rule (CRITICAL):
- Match the user's language automatically:
  1. User speaks in pure English -> Respond entirely in clear, simple English.
  2. User speaks in Devanagari Hindi (हिंदी) -> Respond entirely in simple Hindi script (हिंदी).
  3. User speaks in Hinglish / Roman Hindi (e.g., "Khad ke liye form kaise bhare?") -> Respond in natural, conversational Hinglish.
- Maintain a respectful ("Aap" in Hindi/Hinglish, polite & professional in English), supportive, and practical tone regardless of language.

### Core Directives:
1. Zero Robotic Openings:
   - Answer the specific query directly in the very first sentence.
   - Do NOT repeat introductions (e.g., "I am Kisanमित्र...") or generic questions (e.g., "How can I help you today?") if a conversation is already underway.
2. Practical & Actionable Breakdown:
   - For schemes/subsidies: Break down into Eligibility, Required Documents, and Step-by-Step Application (CSC / Online Portal / Local Krishi Karyalaya).
   - For crop advisories: Provide immediate, safe, and actionable steps (disease/pest control, dosage guidelines with safety warnings, soil management).
3. State & Central Accuracy:
   - Accurately distinguish between Central government schemes and Chhattisgarh state government initiatives.
4. Smart Clarifications:
   - Provide the primary answer first. If essential details are missing (e.g., land size, crop type, district), ask only ONE focused follow-up question at the end.

### Formatting Constraints:
- Use bullet points (*) and bold text (**key details**) for easy reading on mobile screens.
- Do NOT wrap answers inside markdown code blocks (```).
- Avoid overly bureaucratic or technical jargon; explain terms simply."""

    messages = [{"role": "system", "content": system_prompt}]

    # Limit history to last 10 messages to avoid token overflow
    recent_history = request.history[-10:] if len(request.history) > 10 else request.history

    # Add conversation history — only accept valid roles
    for h in recent_history:
        role = h.role if h.role in ("user", "assistant") else "user"
        messages.append({"role": role, "content": h.content})

    messages.append({"role": "user", "content": request.message})

    def token_stream():
        try:
            stream = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                max_tokens=512,
                stream=True
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield f"data: {json.dumps({'delta': delta})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            print(f"[CHAT ERROR] {type(e).__name__}: {e}")
            error_msg = "Maaf karna, abhi AI server se connect hone mein samasya aa rahi hai. Thodi der baad dobara try karein."
            yield f"data: {json.dumps({'error': error_msg})}\n\n"

    return StreamingResponse(token_stream(), media_type="text/event-stream")

@app.post("/api/check-fraud")
async def check_fraud(
    request: Request,
    message: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    input_text = message or ""
    image_bytes = None
    mime_type = "image/jpeg"

    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        try:
            body = await request.json()
            input_text = body.get("message", "")
        except Exception:
            pass
    elif "multipart/form-data" in content_type or "x-www-form-urlencoded" in content_type:
        try:
            form = await request.form()
            if not input_text and "message" in form:
                input_text = str(form["message"])
            if "file" in form and hasattr(form["file"], "read"):
                file_obj = form["file"]
                image_bytes = await file_obj.read()
                if getattr(file_obj, "content_type", None):
                    mime_type = file_obj.content_type
        except Exception as e:
            print(f"Error parsing form data in check-fraud: {e}")

    if file and not image_bytes:
        image_bytes = await file.read()
        if file.content_type:
            mime_type = file.content_type

    prompt = """
You are Kisanमित्र Fraud Shield, an expert AI specialized in detecting online/SMS/WhatsApp scams targeting Indian farmers and rural citizens.
Analyze the user's message text and/or screenshot image to determine if it is fraudulent or safe.

Common Red Flags:
1. Demands for upfront payment, processing fees, or registration fee for government schemes (e.g. PM-KISAN, KCC, tractor subsidy).
2. Asks for sensitive info: OTP, PIN, password, bank account, Aadhaar, card number.
3. Unofficial or suspicious web links (not ending in .gov.in or .nic.in, e.g. bit.ly, whatsapp links, fake domains).
4. False sense of extreme urgency ("Offer ends today", "Account will be blocked").
5. Exaggerated guaranteed financial claims ("Get 50,000 instantly").

Respond ONLY in valid raw JSON with this exact structure:
{
  "risk_level": "high" | "medium" | "low",
  "explanation": "Clear explanation in easy Hindi/Hinglish and English explaining why this is safe or a scam, key warning signs, and advice on what action to take.",
  "warning_flags": ["Reason 1", "Reason 2"]
}
"""

    if client:
        try:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt}
                    ]
                }
            ]

            if input_text:
                messages[0]["content"].append({"type": "text", "text": f"User message to analyze: \"{input_text}\""})

            model_to_use = MODEL_NAME
            if image_bytes:
                b64_img = base64.b64encode(image_bytes).decode("utf-8")
                messages[0]["content"].append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{b64_img}"}
                })
                model_to_use = VISION_MODEL_NAME

            response = client.chat.completions.create(
                model=model_to_use,
                messages=messages,
                max_tokens=1024
            )

            raw_text = response.choices[0].message.content.strip()
            # Try parsing JSON wrapped in markdown or preamble
            json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                if "risk_level" in result and "explanation" in result:
                    return result
        except Exception as e:
            print(f"NVIDIA LLM API Fraud Check error: {e}")

    # Heuristic Keyword Fallback (if LLM fails or is unavailable)
    combined_text = (input_text or "").lower()
    
    if image_bytes:
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(io.BytesIO(image_bytes))
            ocr_text = pytesseract.image_to_string(img)
            combined_text += " " + ocr_text.lower()
        except Exception:
            pass

    fraud_keywords = ["urgent", "payment", "otp", "pin", "fees", "subsidy", "bank", "click link", "shulk", "paisa", "fee", "transfer"]
    matches = [kw for kw in fraud_keywords if kw in combined_text]

    if len(matches) >= 2 or "otp" in combined_text or "payment" in combined_text or "fee" in combined_text:
        risk_level = "high"
        explanation = "सावधान! (Alert) Is message mein suspicious financial demands (jaise OTP, fees, payment) paye gaye hain. Government schemes kabhi bhi registration ya kist ke liye advance paise ya OTP nahi mangti."
        warning_flags = ["Demands OTP/Payment", "Suspicious urgency"]
    elif len(matches) == 1:
        risk_level = "medium"
        explanation = "ध्यान दें! (Caution) Is message mein financial terms ka zikr hai. Kripya official website (.gov.in) ya Gram Panchayat se pushti karein."
        warning_flags = ["Mentions financial terms"]
    else:
        risk_level = "low"
        explanation = "सुरक्षित (Safe) Is message mein abhi koi fraud ke sanket nahi mile. Hamesha savdhan rahein aur sirf official portals par bharosa karein."
        warning_flags = []

    return {
        "risk_level": risk_level,
        "explanation": explanation,
        "warning_flags": warning_flags
    }

@app.post("/api/analyze-document")
async def analyze_document(
    file: UploadFile = File(...)
):
    if not client:
        # --- DEMO MODE RESPONSES ---
        return {
            "extracted_info": f"Document Name: {file.filename}. Demo Mode mein AI ne detect kiya hai ki farmer ke paas 2 acre zameen hai aur aay praman patra ke hisaab se unki aay ₹50,000 se kam hai.",
            "eligible_schemes": [
                {
                    "scheme_id": "SCH_PM_KISAN",
                    "scheme_name": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
                    "reason": "Aapke land record se confirm hua hai ki aap eligible hain (up to 2 hectare land) ₹6,000 saalana kist ke liye."
                },
                {
                    "scheme_id": "SCH_FASAL_BIMA",
                    "scheme_name": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
                    "reason": "Aapki fasal aur land area ke mutabik aap sasti dar par bima le sakte hain."
                }
            ],
            "message": "Demo Mode: Aapke document ka safaltapoorvak analysis kiya gaya! Niche diye gaye schemes aapke profile se match karti hain."
        }

    try:
        image_bytes = await file.read()
        mime_type = file.content_type or "image/jpeg"
        
        # Load schemes to provide context to the prompt
        schemes_context = json.dumps(SCHEMES, indent=2)

        prompt = f"""
        You are an expert government scheme matcher for Indian farmers.
        I am providing an uploaded document (such as Aadhaar, Land Record, Income Certificate, etc.).
        
        Analyze the document carefully to extract details like land ownership size, income level, category, etc., if visible.
        Then, match these details against the following available government schemes:
        {schemes_context}
        
        Identify which schemes the farmer is likely eligible for.
        
        Return your response strictly in JSON format with the following keys:
        {{
            "extracted_info": "Summary of details found in the document (in Hinglish).",
            "eligible_schemes": [
                {{
                    "scheme_id": "ID of the scheme",
                    "scheme_name": "Name of the scheme",
                    "reason": "Why the user is eligible based on the document."
                }}
            ],
            "message": "A friendly message in Hinglish explaining the findings."
        }}
        """

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt}
                ]
            }
        ]

        b64_img = base64.b64encode(image_bytes).decode("utf-8")
        messages[0]["content"].append({
            "type": "image_url",
            "image_url": {"url": f"data:{mime_type};base64,{b64_img}"}
        })
        
        response = client.chat.completions.create(
            model=VISION_MODEL_NAME,
            messages=messages,
            max_tokens=1024
        )
        
        raw_text = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        result = json.loads(raw_text)
        return result
        
    except Exception as e:
        print(f"Error analyzing document: {e}")
        return {"error": "Maaf karna, abhi AI server se connect hone mein samasya aa rahi hai. Kripya thodi der baad koshish karein."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
