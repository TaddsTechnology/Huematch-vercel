import gradio as gr
import tensorflow as tf
from sklearn.cluster import KMeans
import numpy as np
import cv2
from webcolors import hex_to_rgb, rgb_to_hex
from scipy.spatial import KDTree
from collections import Counter

model = tf.keras.models.load_model("model.h5")

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

    
    mask = ~np.all(img == [0, 0, 0], axis=-1) # Mask to exclude black pixels

    
    non_black_pixels = img[mask] # Extract non-black pixels

    
    k_cluster = KMeans(n_clusters=3, n_init="auto") # Apply KMeans clustering on non-black pixels
    k_cluster.fit(non_black_pixels)




    width = 300
    palette = np.zeros((50, width, 3), dtype=np.uint8)
    
    n_pixels = len(k_cluster.labels_)
    counter = Counter(k_cluster.labels_)
    
    perc = {i: np.round(counter[i] / n_pixels, 2) for i in counter}
    perc = dict(sorted(perc.items()))

    cluster_centers = k_cluster.cluster_centers_
    
    # print("Cluster Percentages:", perc)
    # print("Cluster Centers (RGB):", cluster_centers)

    val = list(perc.values())
    val.sort()
    res = val[-1]
    print(res)
    sec_high_val = list(perc.keys())[list(perc.values()).index(res)]
    rgb_list = cluster_centers[sec_high_val]

    step = 0
    for idx, center in enumerate(k_cluster.cluster_centers_):
        width_step = int(perc[idx] * width + 1)
        palette[:, step:step + width_step, :] = center
        step += width_step
    
    return rgb_list

def closest_tone_match(rgb_tuple):
    skin_tones = {'Monk 10': '#292420', 'Monk 9': '#3a312a', 'Monk 8':'#604134', 'Monk 7':'#825c43', 'Monk 6':'#a07e56', 'Monk 5':'#d7bd96', 'Monk 4':'#eadaba', 'Monk 3':'#f7ead0', 'Monk 2':'#f3e7db', 'Monk 1':'#f6ede4'}

    rgb_values = []
    names = []
    for monk in skin_tones:
        names.append(monk)
        rgb_values.append(hex_to_rgb(skin_tones[monk]))
    
    kdt_db = KDTree(rgb_values)
    distance, index = kdt_db.query(rgb_tuple)
    monk_hex = skin_tones[names[index]]
    derived_hex = rgb_to_hex((int(rgb_tuple[0]), int(rgb_tuple[1]), int(rgb_tuple[2])))
    return names[index],monk_hex,derived_hex 

def process_image(image_path):

    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    image_x = cv2.resize(image, (512, 512))
    image_norm = image_x / 255.0
    image_norm = np.expand_dims(image_norm, axis=0).astype(np.float32)
    
    pred = model.predict(image_norm)[0]
    pred = np.argmax(pred, axis=-1).astype(np.int32)
    
    face_skin = face_skin_extract(pred, image_x)
    face_skin_vis = cv2.imread(face_skin)
    dominant_color_rgb = extract_dom_color_kmeans(face_skin)
    
    monk_tone, monk_hex, derived_hex = closest_tone_match(
        (dominant_color_rgb[0], dominant_color_rgb[1], dominant_color_rgb[2])
    )
    
    return [monk_tone,derived_hex,monk_hex,face_skin_vis]
    

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