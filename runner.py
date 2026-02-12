import argparse
import asyncio
import json
import logging
import sys
import traceback

from fastapi.exceptions import ValidationException
from dotenv import load_dotenv

from app.api.schemas.adapters import AdapterSyncRequest
from app.services.sync_engine import run_adapter_sync
from app.adapters.errors import (
    AuthenticationError,
    FetchError,
    NormalizationError
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Run adapter ingestion synchronously (no celery)',
    )

    parser.add_argument(
        "--adapter",
        required=True,
        help="Adapter type (e.g github,aws)"
    )

    parser.add_argument(
        "--config",
        required=True,
        help="path to adapter config file"
    )

    return parser.parse_args()


def load_config(path: str) -> dict:
    try:
        with open(path, "r") as f:
            return json.load(f)

    except FileNotFoundError:
        logger.error(f"Config file not found:{path}")
        sys.exit(1)
    except json.decoder.JSONDecodeError as e:
        logger.error(f"Config file invalid:{path}")
        logger.error(str(e))
        sys.exit(1)


def main():
    args = parse_args()
    config = load_config(args.config)

    adapter_name = args.adapter.strip().lower()

    # load_dotenv()

    try:
        AdapterSyncRequest(config=config)
    except ValidationException as e:
        logger.error("Config validation failed")
        logger.error(str(e))
        sys.exit(1)

    logger.info(f"Running adapter '{args.adapter}' with config '{args.config}'")

    try:

        result = asyncio.run(run_adapter_sync(
            adapter_type=adapter_name,
            config=config
        ))

    except AuthenticationError as e:
        logger.error(f"Authentication error {e}")
        sys.exit(2)
    except FetchError as e:
        logger.error(f"Fetch error {e}")
        sys.exit(3)
    except NormalizationError as e:
        logger.error(f"Normalization error {e}")
        sys.exit(4)
    except Exception as e:
        logger.error("Adapter execution failed:")
        logger.error(traceback.format_exc())
        sys.exit(1)

    logger.info("Sync completed successfully")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
