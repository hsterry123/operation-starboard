from lancedb.pydantic import Vector, LanceModel


class Clip(LanceModel):
    id: int
    episode: int
    clip: int
    start_time: float
    end_time: float
    src: str
    vid_vector: Vector(768)
