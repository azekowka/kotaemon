import shutil
import tempfile
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, UploadFile, File as FastAPIFile, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ktem.index.file.index import FileIndex # Import FileIndex
from ktem.index.file.pipelines import IndexDocumentPipeline # Import IndexDocumentPipeline

from ..dependencies import get_application, get_index_manager, get_db
from kotaemon.base import Document # Import Document

router = APIRouter(prefix="/files", tags=["Files"])

class IndexFileResponse(BaseModel):
    file_id: str
    file_name: str
    status: str
    message: str = None

@router.post("/upload")
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    reindex: bool = False,
    user_id: str = "default",
    app_instance: get_application = Depends(),
    index_manager: get_index_manager = Depends(),
    db: Session = Depends(get_db),
) -> IndexFileResponse:
    """Upload a file for indexing."""
    # Get the default file index
    # Use .info() to get a dictionary of indices
    all_indices = index_manager.info()
    if not all_indices:
        raise HTTPException(status_code=500, detail="No file indices available.")

    file_index_id = list(all_indices.keys())[0]
    file_index: FileIndex = all_indices[file_index_id]

    # Dynamically get the Source and Index models from the active FileIndex
    Source = file_index._resources["Source"]
    Index = file_index._resources["Index"]

    # Existing file check by name
    existing_file = db.query(Source).filter_by(name=file.filename, user=user_id).first()

    if existing_file and not reindex:
        raise HTTPException(status_code=409, detail=f"File '{file.filename}' already exists. Use reindex=true to overwrite.")

    # Save the file temporarily
    temp_file_path = Path(tempfile.gettempdir()) / file.filename
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Prepare document for indexing
        document = Document(uri=str(temp_file_path), text=file.filename)

        # Get the indexing pipeline from the FileIndex instance
        indexing_pipeline: IndexDocumentPipeline = file_index.get_indexing_pipeline({}, user_id)

        # Run the indexing pipeline
        for _ in indexing_pipeline.stream(document):
            pass  # Stream the document through the pipeline

        # After successful indexing, clean up temporary file
        temp_file_path.unlink()

        # Find the newly indexed source document to get its ID
        new_source = db.query(Source).filter_by(name=file.filename, user=user_id).first()
        if not new_source:
            raise HTTPException(status_code=500, detail="Failed to retrieve indexed file information.")

        return IndexFileResponse(file_id=new_source.id, file_name=file.filename, status="success", message="File indexed successfully")
    except Exception as e:
        # Clean up temporary file on error
        if temp_file_path.exists():
            temp_file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to upload and index file: {e}")

@router.get("/", response_model=List[IndexFileResponse])
async def get_files(
    user_id: str = "default",
    app_instance: get_application = Depends(),
    index_manager: get_index_manager = Depends(),
    db: Session = Depends(get_db),
) -> List[IndexFileResponse]:
    """List all indexed files."""
    all_indices = index_manager.info()
    if not all_indices:
        return [] # No indices, no files

    file_index_id = list(all_indices.keys())[0]
    file_index: FileIndex = all_indices[file_index_id]
    Source = file_index._resources["Source"]
    files = db.query(Source).filter_by(user=user_id).all()
    return [
        IndexFileResponse(file_id=f.id, file_name=f.name, status="indexed") for f in files
    ]

@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    user_id: str = "default",
    app_instance: get_application = Depends(),
    index_manager: get_index_manager = Depends(),
    db: Session = Depends(get_db),
):
    """Delete an indexed file."""
    all_indices = index_manager.info()
    if not all_indices:
        raise HTTPException(status_code=500, detail="No file indices available.")

    file_index_id = list(all_indices.keys())[0]
    file_index: FileIndex = all_indices[file_index_id]
    Source = file_index._resources["Source"]

    file_to_delete = db.query(Source).filter_by(id=file_id, user=user_id).first()
    if not file_to_delete:
        raise HTTPException(status_code=404, detail="File not found.")

    # In a real scenario, you'd also need to delete from vector/doc store
    # For now, we only remove the database entry
    db.delete(file_to_delete)
    db.commit()

    return {"message": f"File {file_id} deleted successfully"}

@router.post("/upload_url")
async def upload_url(
    url: str,
    reindex: bool = False,
    user_id: str = "default",
    app_instance: get_application = Depends(),
    index_manager: get_index_manager = Depends(),
    db: Session = Depends(get_db),
) -> IndexFileResponse:
    """Upload a URL for indexing."""
    try:
        file_index: FileIndex = None
        for index in index_manager.indices:
            if isinstance(index, FileIndex):
                file_index = index
                break
        
        if not file_index:
            raise HTTPException(status_code=404, detail="File index not found")

        indexing_pipeline: IndexDocumentPipeline = file_index.get_indexing_pipeline(app_instance.default_settings.flatten(), user_id)

        file_id = None
        errors = []
        async for doc in indexing_pipeline.stream(file_path=url, reindex=reindex):
            if doc.channel == "index" and doc.content.get("status") == "success":
                file_id = doc.content.get("file_id")
            elif doc.channel == "index" and doc.content.get("status") == "failed":
                errors.append(doc.content.get("message"))

        if file_id:
            return IndexFileResponse(file_id=file_id, file_name=url, status="success")
        else:
            raise HTTPException(status_code=500, detail=f"URL indexing failed: {', '.join(errors)}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@router.get("/list_indices")
async def list_indices(
    app_instance: get_application = Depends(),
    index_manager: get_index_manager = Depends(),
):
    """List available indices."""
    indices_info = [{
        "id": index.id,
        "name": index.name,
        "type": index.__class__.__name__,
        "config": index.config
    } for index in index_manager.indices]
    return {"indices": indices_info}
