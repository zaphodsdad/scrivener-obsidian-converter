"""FastAPI app for Scrivener to Obsidian converter."""

import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .converter import convert_project


def open_file_dialog(dialog_type: str = "directory", title: str = "Select", default_name: str = "") -> str | None:
    """Open a native file dialog using osascript (macOS)."""
    if sys.platform != "darwin":
        return None

    if dialog_type == "scriv":
        # Select .scriv bundle (appears as file in Finder)
        script = f'''
        tell application "Finder"
            activate
        end tell
        set chosenFile to choose file with prompt "{title}" of type {{"com.literatureandlatte.scrivener3.project", "scriv"}}
        return POSIX path of chosenFile
        '''
    elif dialog_type == "new_folder":
        # Let user choose location and name for new folder
        script = f'''
        tell application "Finder"
            activate
        end tell
        set defaultName to "{default_name}"
        set savePath to choose file name with prompt "{title}" default name defaultName
        return POSIX path of savePath
        '''
    else:
        # Regular folder picker for output
        script = f'''
        tell application "Finder"
            activate
        end tell
        set chosenFolder to choose folder with prompt "{title}"
        return POSIX path of chosenFolder
        '''

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            path = result.stdout.strip()
            # Remove trailing slash for consistency
            return path.rstrip("/")
        return None
    except Exception:
        return None

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


class SelectResponse(BaseModel):
    success: bool
    path: str | None = None
    error: str | None = None


@app.post("/select-scriv", response_model=SelectResponse)
async def select_scriv():
    """Open a file dialog to select a Scrivener project."""
    path = open_file_dialog(
        dialog_type="scriv",
        title="Select your Scrivener project (.scriv folder)"
    )

    if not path:
        return SelectResponse(success=False, error="No folder selected")

    # Validate it's a .scriv folder
    if not path.endswith(".scriv"):
        return SelectResponse(
            success=False,
            error="Please select a Scrivener project (.scriv folder)"
        )

    return SelectResponse(success=True, path=path)


class SelectOutputRequest(BaseModel):
    default_name: str = "My Vault"


@app.post("/select-output", response_model=SelectResponse)
async def select_output(request: SelectOutputRequest = None):
    """Open a file dialog to create/select output folder."""
    default_name = request.default_name if request else "My Vault"

    path = open_file_dialog(
        dialog_type="new_folder",
        title="Save Obsidian vault as",
        default_name=default_name
    )

    if not path:
        return SelectResponse(success=False, error="No location selected")

    return SelectResponse(success=True, path=path)


def run_app():
    """Run the app with uvicorn."""
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
