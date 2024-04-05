import lancedb

def main():
  # View Dummy data
  db = lancedb.connect("./dummy_data/db")
  tbl = db.open_table("videos")
  print(tbl.to_pandas())
  return


if __name__ == "__main__":
  main()