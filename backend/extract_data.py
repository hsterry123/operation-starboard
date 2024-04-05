# import libraries
import lancedb
from schema import Clip
import subprocess
import cv2

import vertexai
from vertexai.vision_models import (
    MultiModalEmbeddingModel,
    Video,
    VideoSegmentConfig,
)


# An array of the video caption pairs
clips_and_captions = [{'clip_src': '/file/path/1', 'cap_src': '/file/path/2'},
                      {}, {}]

# connect to the lancedb and define the schema
db = lancedb.connect("./data/db")
table = db.create_table("videos", schema=Clip,
                        exist_ok=True)


# Specify the location of your Vertex AI resources
location = "us-central1"
project_id = "innovation-fest-2024"

# Define the threshold for scene changes
threshold = 0.3


def embed_clip(video_path, location, project_id, paragraph, start_time,
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
        contextual_text=paragraph,
        dimension=1408,
    )

    return embeddings


# Timestamp function
# - Run the video through FFMPEG to get the timestamps of the scene changes
def get_timestamps(clips_and_captions, threshold):
    # Loop through the clips and captions
    for item in clips_and_captions:
        # Get the timestamps of the scene changes
        cmd_file = item['clip_src']
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
        vidcap = cv2.VideoCapture(item['clip_src'])

        # get the framerate of the video
        fps = vidcap.get(cv2.CAP_PROP_FPS)

        # translate the frame of a change to a time stamp
        for i in range(len(scene_changes)):
            scene_changes[i] = scene_changes[i] / fps  # time in seconds of
        # each scene change

        vidcap.release()

        return scene_changes


# Use those time stamps to create a paragraph from the caption data
# - stored as string
# inputs: clips_and_captions, timestamps
# timestamps: [float of first scene change, float of second scene change, ...]
def get_paragraph(clips_and_captions, start_time, end_time):
    # Loop through the clips and captions
    for item in clips_and_captions:
        # Get the caption data
        with open(item['cap_src'], 'r') as file:
            caption = file.read()

            return caption

        # TODO: READ THE CAPTION FILE AND GET THE PARAGRAPH
        # pair = { 00:32:22, 'This is a caption. This is another caption.'}
        # for timestamp in timestamps:
        # if pair[0] < timestamp < pair[1]:
        #     paragraph += pair[2]

        # return paragraph


# create a schema instance of the clip given the timestamps
# and the caption paragraph
def createClip(clip_src, scene_changes, client, location, project_id,
               model_id):
    # find scene using scenechanges

    # Get the timestamps of the scene and the scene number
    timestamps = []
    # get the paragraph for that scene
    paragraph = get_paragraph(clips_and_captions, timestamps[0], timestamps[1])

    # Embed the video
    # TODO: ONLY EMBED THE PORTION IN THAT SCENE
    embeds = embed_clip(clip_src, location, project_id, paragraph, timestamps[0], timestamps[1])

    vid_vector = embeds.video_embeddings[0]
    cap_vector = embeds.text_embedding
    # Create the Clip instance
    clip = Clip(
        id=0,       # \
        episode=0,  # | These are determined by the above
        clip=0,     # /
        start_time=timestamps[0],
        end_time=timestamps[1],
        caption=paragraph,
        src=clip_src,
        vid_vector=vid_vector,
        cap_vector=cap_vector
    )

    return clip


# insert the clip into the database
def add_clip(clip, table):
    table.add(clip)
