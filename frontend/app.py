import streamlit as st
import lancedb
import subprocess
import time
from embed import embed_text

threshold = 0.7

# Create or connect to the database
@st.cache_resource
def connect_db():
    db = lancedb.connect("../data/db")
    table = db.open_table("videos")
    return table


table = connect_db()

def build_video_results(videos): 
    results = []
    for i, video in enumerate(videos):
      src = video['src'].replace('alexander.johnson/Downloads/Clips/', 'olivia.baldwin-geilin/clips/')

      start = video['start_time']
      end = video['end_time']

      # Ignore clips that are too short or not relevant
      if end - start < 1 or video['_distance'] < threshold:
        continue

      cmd = ['ffmpeg', '-y', '-ss', str(start), '-to', str(end), '-i', src, '-c:v', 'copy', '-c:a', 'copy', 'output'+str(i)+'.mp4']
      cmd = " ".join(cmd)

      # Run FFmpeg command
      proc = subprocess.run(cmd, shell=True, capture_output=True)
      # print(proc.stderr)

      results.append("output"+str(i)+".mp4")
    return results

def search_videos(query, filters=None):
    print(f'searching for videos with {query}...')
    # Embed the query
    text_embedding = embed_text(query)

    text_embedding = text_embedding.detach().cpu().numpy()[0].tolist()
    # Get the video embeddings from the database
    if filters:
        filter_str = str(tuple(filters)).replace(",)", ")")
        results = table.search(text_embedding)\
                   .where(f"id IN {filter_str}")\
                   .metric("cosine")\
                   .limit(20)\
                   .to_list()
    else: 
        results = table.search(text_embedding)\
                   .metric("cosine")\
                   .limit(20)\
                   .to_list()
    return results

def build_data_tab(tab3):
    with tab3:
        st.write("Database")
        data = table.to_pandas()
        st.write(data)

def main():
    st.title('StarBoard')
    st.write("Welcome to the Video Search App." +
             " You can search for videos using text queries.")

    # Search for user Query 

    search_query = st.text_input("Search:")
    active_filter = st.toggle("Filter")

    show_mappings = {61457875: 'Ghosts', 941410057: 'Tracker', 61465429: 'Joe Pickett'}
    title_options = [61457875, 941410057, 61465429]

    filters = None
    if(active_filter):
        filters = st.multiselect("Show Title", title_options, format_func=lambda x: show_mappings[x])

    if search_query:
        results = build_video_results(search_videos(search_query, filters))
        st.subheader(f"Search Results ({len(results)}):")
        if len(results) == 0:
            st.write("No results found.")
        else:
            # display in grid
            col1, col2 = st.columns(2)
            for i, result in enumerate(results):
                if i % 2 == 0:
                    with col1:
                        st.video(result)
                else:
                    with col2:
                        st.video(result)
    else:
        st.write("Enter a search query.")

if __name__ == "__main__":
    main()