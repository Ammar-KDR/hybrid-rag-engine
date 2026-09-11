from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from rag.factory import create_rag_pipeline
from rag.ingestion.registry import DocumentRegistry
from rag.ingestion.service import IngestionService

from rag.api.errors import (
    AppError,
    app_error_handler,
)

from rag.api.routes.ask import (
    router as ask_router,
)
from rag.api.routes.ingest import (
    router as ingest_router,
)
from rag.api.routes.documents import (
    router as documents_router,
)
from rag.observability.logging import (
    configure_logging,
)
import logging

logger = logging.getLogger(
    "rag.api.app"
)


# =========================================================
# Application lifecycle
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
    "application_initializing"
    )

    # -----------------------------------------------------
    # Create the existing Day 1-10 RAG pipeline once
    # -----------------------------------------------------

    pipeline = create_rag_pipeline()

    app.state.rag_pipeline = pipeline


    # -----------------------------------------------------
    # Extract reusable retrieval dependencies
    # -----------------------------------------------------

    hybrid_retriever = pipeline.retriever

    dense_retriever = (
        hybrid_retriever.dense_retriever
    )


    # -----------------------------------------------------
    # Load persistent document registry
    # -----------------------------------------------------

    registry = DocumentRegistry(
        Path("data/registry.json")
    )

    app.state.document_registry = registry


    # -----------------------------------------------------
    # Create ingestion service
    # -----------------------------------------------------

    ingestion_service = IngestionService(
        data_path=Path("data/raw"),

        registry=registry,

        embedding_service=(
            dense_retriever.embedding_service
        ),

        vector_store=(
            dense_retriever.vector_store
        ),

        collection_name=(
            dense_retriever.collection_name
        ),

        hybrid_retriever=(
            hybrid_retriever
        ),
    )

    app.state.ingestion_service = (
        ingestion_service
    )

    logger.info(
    "application_ready"
    )

    yield

    logger.info(
    "application_shutting_down"
    )

# =========================================================
# Logging
# =========================================================
configure_logging()

# =========================================================
# FastAPI application
# =========================================================

# app = FastAPI(
#     title="Hybrid RAG API",
#     version="1.0.0",
#     lifespan=lifespan,
# )


# # =========================================================
# # Exception handlers
# # =========================================================

# app.add_exception_handler(
#     AppError,
#     app_error_handler,
# )


# # =========================================================
# # Routers
# # =========================================================

# app.include_router(
#     ask_router,
#     prefix="/v1",
# )

# app.include_router(
#     ingest_router,
#     prefix="/v1",
# )

# app.include_router(
#     documents_router,
#     prefix="/v1",
# )



def create_app(
    lifespan_handler=lifespan,
) -> FastAPI:

    application = FastAPI(
        title="Hybrid RAG API",
        version="1.0.0",
        lifespan=lifespan_handler,
    )

    application.add_exception_handler(
        AppError,
        app_error_handler,
    )

    application.include_router(
        ask_router,
        prefix="/v1",
    )

    application.include_router(
        ingest_router,
        prefix="/v1",
    )

    application.include_router(
        documents_router,
        prefix="/v1",
    )

    return application


app = create_app()