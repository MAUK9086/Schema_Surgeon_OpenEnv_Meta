"""
app.py
------
FastAPI app factory for Schema Surgeon.
Wires OpenEnv HTTP/WebSocket routes and exposes a lightweight health endpoint.
"""

from typing import Dict

from fastapi import FastAPI
from openenv.core.env_server.http_server import create_app

from SchemaSurgeon.models import SchemaAction, SchemaObservation
from server.SchemaSurgeon_environment import SchemaSurgeonEnvironment

DEFAULT_HOST: str = "0.0.0.0"
DEFAULT_PORT: int = 7860
DEFAULT_TASK_ID: str = "task1"
MAX_CONCURRENT_ENVS: int = 1


def build_app() -> FastAPI:
    """
    Build and configure the FastAPI app.

    Args:
        None.

    Returns:
        Configured FastAPI app.
    """

    def env_factory() -> SchemaSurgeonEnvironment:
        """
        Create a new environment instance.

        Args:
            None.

        Returns:
            New SchemaSurgeonEnvironment instance.
        """
        return SchemaSurgeonEnvironment(task_id=DEFAULT_TASK_ID)

    app_obj = create_app(
        env_factory,
        SchemaAction,
        SchemaObservation,
        env_name="schema-surgeon",
        max_concurrent_envs=MAX_CONCURRENT_ENVS,
    )

    @app_obj.get("/health")
    def health() -> Dict[str, str]:
        """
        Health check endpoint for deployment liveness probes.

        Args:
            None.

        Returns:
            Simple status dictionary.
        """
        return {"status": "ok"}

    return app_obj


app = build_app()


def main(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    """
    Run the app with uvicorn.

    Args:
        host: Host address for uvicorn.
        port: Port for uvicorn.

    Returns:
        None.
    """
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
