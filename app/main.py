"""FastAPI app for Scrivener to Obsidian converter."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .converter import convert_project

app = FastAPI(title="Scrivener to Obsidian Converter")

# Serve static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


class ConvertRequest(BaseModel):
    scriv_path: str
    output_path: str


class ConvertResponse(BaseModel):
    success: bool
    message: str
    documents_converted: int = 0
    folders_created: int = 0
    errors: list[str] = []


@app.get("/")
async def index():
    """Serve the main page."""
    return FileResponse(static_dir / "index.html")


@app.post("/convert", response_model=ConvertResponse)
async def convert(request: ConvertRequest):
    """Convert a Scrivener project to Obsidian vault."""
    scriv_path = Path(request.scriv_path)
    output_path = Path(request.output_path)

    # Validate Scrivener path
    if not scriv_path.exists():
        raise HTTPException(status_code=400, detail="Scrivener project not found")

    if not scriv_path.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")

    if not scriv_path.suffix == ".scriv":
        raise HTTPException(status_code=400, detail="Not a Scrivener project (.scriv)")

    # Run conversion
    result = convert_project(scriv_path, output_path)

    if result.success:
        message = f"Converted {result.documents_converted} documents"
        if result.folders_created > 0:
            message += f" and created {result.folders_created} folders"
    else:
        message = "Conversion failed"
        if result.errors:
            message += f": {result.errors[0]}"

    return ConvertResponse(
        success=result.success,
        message=message,
        documents_converted=result.documents_converted,
        folders_created=result.folders_created,
        errors=result.errors,
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


def run_app():
    """Run the app with uvicorn."""
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
