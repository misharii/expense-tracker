from fastapi import FastAPI, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.database import get_db, init_db
from app.services.transaction_service import TransactionService
from app.schemas import UploadResponse
import logging
import re

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Expense Tracker API - Phase 1",
    description="Parse Saudi bank SMS messages from text files",
    version="1.0.0",
)

# CORS middleware for iOS Shortcuts
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()
    logger.info("Database initialized")


def split_messages(text: str) -> list[str]:
    """
    Split text into individual transaction messages.
    Handles both single-line and multi-line messages.
    """
    # Keywords that typically start a new message
    start_keywords = [
        "شراء",
        "حوالة داخلية",
        "حوالة محلية",
        "حوالة واردة",
        "مدفوعات وزارة",
        "راتب",
        "رصيد غير كافي",
    ]

    # First, try splitting by double newlines (blank lines)
    if "\n\n" in text:
        messages = [msg.strip() for msg in text.split("\n\n") if msg.strip()]
        return messages

    # Otherwise, split by start keywords
    lines = text.split("\n")
    messages = []
    current_message = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if line starts a new message
        is_start = any(line.startswith(keyword) for keyword in start_keywords)

        if is_start and current_message:
            # Save previous message and start new one
            messages.append(" ".join(current_message))
            current_message = [line]
        else:
            current_message.append(line)

    # Add the last message
    if current_message:
        messages.append(" ".join(current_message))

    return messages


@app.post("/upload", response_model=UploadResponse)
async def upload_transactions(
    file: UploadFile = File(...), db: Session = Depends(get_db)
):
    """
    Upload a .txt file containing bank SMS messages.
    Returns parsing results including success/failure counts.
    """
    if not file.filename.endswith(".txt"):
        return UploadResponse(
            total_messages=0,
            parsed_successfully=0,
            failed=1,
            errors=[{"error": "Only .txt files are supported"}],
            created_vendors=[],
        )

    try:
        # Read file content
        content = await file.read()
        text = content.decode("utf-8")

        # Split into individual messages
        messages = split_messages(text)

        logger.info(f"Found {len(messages)} messages to parse")

        service = TransactionService(db)

        parsed_count = 0
        failed_count = 0
        errors = []
        created_vendors = set()

        for idx, message in enumerate(messages, 1):
            logger.info(f"Processing message {idx}: {message[:50]}...")
            result = service.parse_and_save_message(message)

            if result["success"]:
                parsed_count += 1
                if result.get("vendor_name"):
                    created_vendors.add(result["vendor_name"])
                logger.info(f"✓ Message {idx} parsed successfully")
            else:
                failed_count += 1
                errors.append(
                    {
                        "line": idx,
                        "message": message[:100],
                        "error": result["error"],
                    }
                )
                logger.warning(
                    f"✗ Message {idx} failed: {result['error']}"
                )

        return UploadResponse(
            total_messages=len(messages),
            parsed_successfully=parsed_count,
            failed=failed_count,
            errors=errors,
            created_vendors=list(created_vendors),
        )

    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        return UploadResponse(
            total_messages=0,
            parsed_successfully=0,
            failed=1,
            errors=[{"error": f"Server error: {str(e)}"}],
            created_vendors=[],
        )


@app.get("/health")
def health_check():
    return {"status": "healthy"}