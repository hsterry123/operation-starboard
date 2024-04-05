import lancedb
from schema import Clip
import numpy as np

db = lancedb.connect("./dummy_data/db")
table = db.create_table("videos", schema=Clip, mode="overwrite")

clips = [["Users/olivia.baldwin-geilin/clips&captions/TRACKER_0106_ORIG_PROD_UHD_SDR_f03ddea9-716a-4ee2-ae5e-351d7e2cc99d_R0-002.mp4", 941410057, 106],
         ["/Users/olivia.baldwin-geilin/clips&captions/HDPPLUSJOP103A_Joe_Pickett_103_012822_MASTER-001.mp4", 61465429, 103],
         ["/Users/olivia.baldwin-geilin/clips&captions/GHOSTS_0305_FINAL_UHD_SDR_328066a1-61d1-44e0-9869-fc97f1e00b93_R0.mp4", 61457875, 305]]

def addclips():
  data = []
  for video in clips: 
    for i in range(50):
      clip = Clip(
        id=video[1],
        episode=video[2],
        clip=i,
        start_time=i*10,
        end_time=(i+1)*10,
        caption="This is a caption",
        src="Users/olivia.baldwin-geilin/clips&captions/TRACKER_0106_ORIG_PROD_UHD_SDR_f03ddea9-716a-4ee2-ae5e-351d7e2cc99d_R0-002.mp4",
        vid_vector=np.random.random((1408))
      )
      data.append(clip)
  return data


def main():
  data = addclips();
  table.add(data)
  return


if __name__ == "__main__":
  main()