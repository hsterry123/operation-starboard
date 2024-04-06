# Import the necessary libraries
import torch
from PIL import Image
import clip

# Load the model
# Use CUDA if available, else use CPU
device = "cuda" if torch.cuda.is_available() else "cpu"

# Load the pretrained CLIP model and the associated preprocessing function
model, preprocess = clip.load("ViT-B/32", device=device)

# Define a function to convert text into a format suitable for the model, and
# get its embedding
def embed_text(text):
    # Run the model in no_grad mode to prevent the computation graph from
    # being built (saves memory)
    with torch.no_grad():
        # Tokenize the text and move it to the appropriate device
        text_encoded = clip.tokenize([text]).to(device)

        # Pass the tokenized text through the model to get the text embeddings
        text_embedding = model.encode_text(text_encoded)
    return text_embedding