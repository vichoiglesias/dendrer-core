"""
Seed script to add default models to the database.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.models import Model, ModelStatus
from app.utils.database import AsyncSessionLocal


async def seed_models():
    """Seed default models into the database."""

    models_data = [
        {
            "name": "mistral-7b-instruct",
            "display_name": "Mistral 7B Instruct",
            "description": "Mistral 7B v0.3 Instruct - Fast and efficient instruction-following model",
            "provider": "huggingface",
            "model_path": "mistralai/Mistral-7B-Instruct-v0.3",
            "config": {
                "quantization": None,
                "tensor_parallel_size": 1,
                "max_model_len": 32768,
            },
            "status": ModelStatus.READY,
            "tokens_per_dollar": 1000000,  # Placeholder pricing
            "supports_chat": True,
            "supports_completion": True,
            "supports_embeddings": False,
            "context_length": 32768,
            "max_tokens": 8192,
        },
        # Add more models as needed
        # {
        #     "name": "llama-3-8b-instruct",
        #     "display_name": "Llama 3 8B Instruct",
        #     "description": "Meta's Llama 3 8B Instruct model",
        #     "provider": "huggingface",
        #     "model_path": "meta-llama/Meta-Llama-3-8B-Instruct",
        #     ...
        # },
    ]

    async with AsyncSessionLocal() as session:
        for model_data in models_data:
            # Check if model already exists
            result = await session.execute(
                select(Model).where(Model.name == model_data["name"])
            )
            existing_model = result.scalar_one_or_none()

            if existing_model:
                print(f"✓ Model '{model_data['name']}' already exists, skipping...")
                continue

            # Create new model
            model = Model(**model_data)
            session.add(model)
            print(f"+ Adding model '{model_data['name']}'...")

        await session.commit()
        print(f"\n✅ Model seeding complete!")


if __name__ == "__main__":
    print("🌱 Seeding models...\n")
    asyncio.run(seed_models())
