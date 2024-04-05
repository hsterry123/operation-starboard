# import libraries
import lancedb
from schema import Clip
import subprocess
import cv2
import datetime

import vertexai
from vertexai.vision_models import (
    MultiModalEmbeddingModel,
    Video,
    VideoSegmentConfig,
)


# An array of the video caption pairs
clips = ['/Users/olivia.baldwin-geilin/clips&captions/GHOSTS_0305_FINAL_UHD_SDR_328066a1-61d1-44e0-9869-fc97f1e00b93_R0.mp4']

# connect to the lancedb and define the schema
db = lancedb.connect("./data/db")
table = db.create_table("videos", schema=Clip,
                        exist_ok=True)


# Specify the location of your Vertex AI resources
location = "us-central1"
project_id = "innovation-fest-2024"

# Define the threshold for scene changes
threshold = 0.3


def embed_clip(video_path, location, project_id, start_time,
               end_time):
    vertexai.init(project=project_id, location=location)

    model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding")
    video = Video.load_from_file(video_path)

    video_segment_config = VideoSegmentConfig(
        start_offset_sec=round(start_time),
        end_offset_sec=round(end_time),
        interval_sec=round(end_time) - round(start_time)
    )

    embeddings = model.get_embeddings(
        video=video,
        video_segment_config=video_segment_config,
        dimension=1408,
    )

    return embeddings


# Timestamp function
# - Run the video through FFMPEG to get the timestamps of the scene changes
# inputs: 
    # clip_src: clip file 
    # threshold: threshold for scene change
# output: [[scene_change1_start, scene_change1_end], [scene_change2_start, scene_change2_end], ...]
def get_timestamps(clip_src, threshold):
    # Get the timestamps of the scene changes
    cmd_file = clip_src
    if ' ' in cmd_file:
        cmd_file.replace(' ', '\\ ')

    cmd1 = [
        'ffmpeg',
        '-i', cmd_file,
        '-filter:v', f'select=\'gt(scene\\,{threshold}),showinfo\'',
        '-f', 'mp4', 'temp.mp4', '2>&1', '|', 'grep', 'showinfo',
        '|', 'grep', 'frame=\'[\\ 0-9.]*\'',  '-o', '|',
        'grep', '\'[0-9.]*\'', '-o',
    ]
    cmd1 = " ".join(cmd1)
    # Run FFmpeg command
    proc = subprocess.run(cmd1, shell=True, capture_output=True)

    scene_changes = proc.stdout.split()
    scene_changes = [int(x.decode()) for x in scene_changes]
    subprocess.run('rm temp.mp4', shell=True)

    # Make a vidcap of the video
    vidcap = cv2.VideoCapture(clip_src)

    # get the framerate of the video
    fps = vidcap.get(cv2.CAP_PROP_FPS)

    # translate the frame of a change to a time stamp
    for i in range(len(scene_changes)):
        scene_changes[i] = scene_changes[i] / fps  # time in seconds of
    # each scene change

    vidcap.release()

    # transate the time of the scene changes to a timestamp with start and end
    timestamps = []
    for scene in range(len(scene_changes) - 1):
        timestamps.append([scene_changes[scene], scene_changes[scene + 1]])

    # this loses the last scene, leaving for time purposes

    return timestamps


# create a schema instance of the clip given the timestamps
# and the caption paragraph
# inputs: 
    # clip_src: clip file
    # timestamps: [scene_start_time, scene_end_time]
    # scene_number: scene number
    # client: google cloud client
    # location: location of the vertex ai resources
    # project_id: project id
    # model_id: model id
# output: Clip instance
def createClip(clip_src, timestamps, scene_number, location, project_id):

    # Embed the video
    embeds = embed_clip(clip_src, location, project_id,
                        timestamps[0], timestamps[1])

    vid_vector = embeds.video_embeddings[0]

    # Create the Clip instance
    clip = Clip(
        id=0,       # \
        episode=0,  # | These are determined by the above
        clip=scene_number,
        start_time=timestamps[0],
        end_time=timestamps[1],
        src=clip_src,
        vid_vector=vid_vector,
    )

    return clip


# insert the clip into the database
def add_clip(clip, table):
    table.add(clip)

def main():

    # Loop through each clip and caption pair and perform the necessary steps
    for clip_src in clips:
        # Get the timestamps of the scene changes
        scene_changes = get_timestamps(clip_src, threshold)

        print(scene_changes)

    '''
        for scene_number, timestamps in enumerate(scene_changes):
            # Create the Clip instance
            clip = createClip(clip_src, scene_number, timestamps, location, project_id)

            # Add the Clip to the database
            add_clip(clip, table)
    '''

    return 


if __name__ == "__main__":
    main()