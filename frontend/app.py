import streamlit as st
import lancedb

# Create or connect to the database
@st.cache_resource
def connect_db():
    db = lancedb.connect("../dummy_data/db")
    table = db.open_table("videos")
    return table


table = connect_db()

def search_videos(query, data):
    results = []
    for item in data:
        if query.lower() in item.lower():
            results.append(item)
    return results

def build_upload_tab(tab1): 
    with tab1:
      st.video(data="https://www.youtube.com/watch?v=9bZkp7q19f0")

def build_data_tab(tab3):
    with tab3:
        st.write("Database")
        data = table.to_pandas()
        st.write(data)

def main():
    st.title('StarBoard')
    st.write("Welcome to the Video Search App." +
             " You can search for videos using text queries.")

    data = []

    search_query = st.text_input("Search:", "")
    if search_query:
        results = search_videos(search_query, data)
        st.subheader(f"Search Results ({len(results)}):")
        if len(results) == 0:
            st.write("No results found.")
        else:
            # display in grid
            col1, col2, col3 = st.columns(3)
            for i, result in enumerate(results):
                if i % 3 == 0:
                    col1.write(result)
                elif i % 3 == 1:
                    col2.write(result)
                else:
                    col3.write(result)
    else:
        st.write("Enter a search query.")

    tab1, tab2, tab3 = st.tabs(["Upload", "Search", "Database"])

    build_upload_tab(tab1)
    # build_search_tab(tab2)
    build_data_tab(tab3)

if __name__ == "__main__":
    main()