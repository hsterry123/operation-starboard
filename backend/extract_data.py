# import libraries
import lancedb
from schema import Clip
import subprocess
import cv2
# import datetime

import vertexai
from vertexai.vision_models import (
    MultiModalEmbeddingModel,
    Video,
    VideoSegmentConfig,
)


# An array of the video caption pairs
clips = ['/Users/alexander.johnson/Downloads/Clips/'
         + 'GHOSTS_0305_FINAL_UHD_SDR_328066a1-61d1-44e0-9869-fc97f1e00b93_R0.mp4',
         '/Users/alexander.johnson/Downloads/Clips/' +
         'TRACKER_0106_ORIG_PROD_UHD_SDR_f03ddea9-716a-4ee2-ae5e-351d7e2cc99d_R0.mp4',
         '/Users/alexander.johnson/Downloads/Clips/' +
         'HDPPLUSJOP103A_Joe_Pickett_103_012822_MASTER.mp4']

# connect to the lancedb and define the schema
db = lancedb.connect("./data/db")
table = db.create_table("videos", schema=Clip,
                        exist_ok=True)


# Specify the location of your Vertex AI resources
location = "us-west1-a"
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
# output: [[scene_change1_start, scene_change1_end], [scene_change2_start,
# scene_change2_end], ...]
def get_timestamps(clip_src, threshold):
    # Get the timestamps of the scene changes
    cmd_file = clip_src
    cmd_file = cmd_file.replace(' ', '\\ ')

    print(cmd_file)

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

    out = proc.stderr
    print(out)

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

    end_time = vidcap.get(cv2.CAP_PROP_FRAME_COUNT) / fps

    # transate the time of the scene changes to a timestamp with start and end
    timestamps = []
    timestamps.append([0, scene_changes[0]])
    for scene in range(len(scene_changes) - 1):
        timestamps.append([scene_changes[scene], scene_changes[scene + 1]])
    timestamps.append([scene_changes[-1], end_time])

    # this loses the last scene, leaving for time purposes

    return timestamps


# create a schema instance of the clip given the timestamps
# and the caption paragraph
# inputs:
    # clip_src: clip file
    # timestamps: [scene_start_time, scene_end_time]
    # scene_number: scene number
    # location: location of the vertex ai resources
    # project_id: project id
# output: Clip instance
def createClip(clip_src, start, end, scene_number, location, project_id):

    # Embed the video
    embeds = embed_clip(clip_src, location, project_id,
                        start, end)

    vid_vector = embeds.video_embeddings[0]

    id = 0
    ep = 0

    if 'GHOSTS' in clip_src:
        id = 61457875
        ep = 305

    elif 'TRACKER' in clip_src:
        id = 941410057
        ep = 106

    elif 'Joe_Pickett' in clip_src:
        id = 61465429
        ep = 103

    # Create the Clip instance
    clip = Clip(
        id=id,       # \
        episode=ep,  # | These are determined by the above
        clip=scene_number,
        start_time=start,
        end_time=end,
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

        for scene_number, timestamps in enumerate(scene_changes):
            # Create the Clip instance
            clip = createClip(clip_src, scene_number, timestamps[0],
                              timestamps[1], location, project_id)

            # Add the Clip to the database
            add_clip(clip, table)

    return


if __name__ == "__main__":
    main()
