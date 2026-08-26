from pydantic import BaseModel


class ORMModel(BaseModel):
    """Base for response schemas built from ORM objects."""

    model_config = {"from_attributes": True}
