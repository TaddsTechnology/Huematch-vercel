import gradio as gr
import tensorflow as tf
from sklearn.cluster import KMeans
import numpy as np
import cv2
from webcolors import hex_to_rgb, rgb_to_hex
from scipy.spatial import KDTree
from collections import Counter

try:
    model = tf.keras.models.load_model("model.h5")
    print("Model loaded successfully")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

classes = [
    "background", "skin", "left eyebrow", "right eyebrow",
    "left eye", "right eye", "nose", "upper lip", "inner mouth",
    "lower lip", "hair"
]

def face_skin_extract(pred, image_x):
    output = np.zeros_like(image_x, dtype=np.uint8)
    mask = (pred == 1)
    output[mask] = image_x[mask]
    return output

def extract_dom_color_kmeans(img):
    # Check if image has skin pixels
    mask = ~np.all(img == [0, 0, 0], axis=-1) # Mask to exclude black pixels
    non_black_pixels = img[mask] # Extract non-black pixels
    
    # If no skin pixels found, return a default color
    if len(non_black_pixels) == 0:
        print("No skin pixels found, returning default color")
        return np.array([200, 150, 120])  # Default skin tone
    
    print(f"Found {len(non_black_pixels)} skin pixels")
    
    # Use fewer clusters for better skin tone detection
    k_cluster = KMeans(n_clusters=min(3, len(non_black_pixels)), n_init="auto", random_state=42)
    k_cluster.fit(non_black_pixels)
    
    # Get cluster information
    n_pixels = len(k_cluster.labels_)
    counter = Counter(k_cluster.labels_)
    
    perc = {i: np.round(counter[i] / n_pixels, 2) for i in counter}
    perc = dict(sorted(perc.items()))
    
    cluster_centers = k_cluster.cluster_centers_
    
    print("Cluster Percentages:", perc)
    print("Cluster Centers (RGB):", cluster_centers)
    
    # Get the most dominant cluster (highest percentage)
    dominant_cluster_idx = max(perc, key=perc.get)
    dominant_color = cluster_centers[dominant_cluster_idx]
    
    print(f"Dominant cluster index: {dominant_cluster_idx}")
    print(f"Dominant color RGB: {dominant_color}")
    
    return dominant_color

def closest_tone_match(rgb_tuple):
    skin_tones = {'Monk 10': '#292420', 'Monk 9': '#3a312a', 'Monk 8':'#604134', 'Monk 7':'#825c43', 'Monk 6':'#a07e56', 'Monk 5':'#d7bd96', 'Monk 4':'#eadaba', 'Monk 3':'#f7ead0', 'Monk 2':'#f3e7db', 'Monk 1':'#f6ede4'}

    print(f"Input RGB tuple: {rgb_tuple}")
    
    rgb_values = []
    names = []
    for monk in skin_tones:
        names.append(monk)
        rgb_values.append(hex_to_rgb(skin_tones[monk]))
    
    print(f"Monk skin tone RGB values: {list(zip(names, rgb_values))}")
    
    kdt_db = KDTree(rgb_values)
    distance, index = kdt_db.query(rgb_tuple)
    
    print(f"Closest match index: {index}, distance: {distance}")
    print(f"Matched tone: {names[index]}")
    
    monk_hex = skin_tones[names[index]]
    derived_hex = rgb_to_hex((int(rgb_tuple[0]), int(rgb_tuple[1]), int(rgb_tuple[2])))
    
    print(f"Returning: {names[index]}, {monk_hex}, {derived_hex}")
    
    return names[index],monk_hex,derived_hex

def process_image(image_path):
    print(f"Processing image: {image_path}")
    
    if model is None:
        print("Model is not loaded, returning default values")
        return ["Monk 3", "#f7ead0", "#f7ead0", np.zeros((512, 512, 3), dtype=np.uint8)]
    
    try:
        image = cv2.imread(image_path)
        if image is None:
            print("Failed to load image")
            return ["Monk 3", "#f7ead0", "#f7ead0", np.zeros((512, 512, 3), dtype=np.uint8)]
            
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        image_x = cv2.resize(image, (512, 512))
        image_norm = image_x / 255.0
        image_norm = np.expand_dims(image_norm, axis=0).astype(np.float32)
        
        print("Making prediction...")
        pred = model.predict(image_norm)[0]
        pred = np.argmax(pred, axis=-1).astype(np.int32)
        
        print("Extracting skin...")
        face_skin = face_skin_extract(pred, image_x)
        
        print("Extracting dominant color...")
        dominant_color_rgb = extract_dom_color_kmeans(face_skin)
        
        print("Finding closest tone match...")
        monk_tone, monk_hex, derived_hex = closest_tone_match(
            (dominant_color_rgb[0], dominant_color_rgb[1], dominant_color_rgb[2])
        )
        
        return [monk_tone,derived_hex,monk_hex,face_skin]
        
    except Exception as e:
        print(f"Error processing image: {e}")
        return ["Monk 3", "#f7ead0", "#f7ead0", np.zeros((512, 512, 3), dtype=np.uint8)]
    

inputs = gr.Image(type="filepath", label="Upload Face Image")
outputs = [
    gr.Label(label="Monk Skin Tone"),          
    gr.ColorPicker(label="Derived Color"),   
    gr.ColorPicker(label="Closest Monk Color"),
    # gr.JSON(label="Dominant RGB Values"),      
    # gr.Image(label="Skin Mask Visualization")
]

interface = gr.Interface(
    fn=process_image,
    inputs=inputs,
    outputs=outputs,
    title="Skin Tone Analysis",
    description="Upload a face image to analyse skin tone and find closest Monk skin tone match."
)

if __name__ == "__main__":
    interface.launch()