from flask import Flask, render_template, request
import os
import cv2
import torch
import folium

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads/'
OUTPUT_FOLDER = 'static/output/'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Load YOLOv5 model once
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True, trust_repo=True)

def detect_animals(file_path, output_path):
    # Read image/video (we handle image for now)
    frame = cv2.imread(file_path)
    if frame is None:
        return 0, file_path

    # YOLO detection
    results = model(frame)
    detections = results.pandas().xyxy[0]  # bounding boxes as DataFrame

    # Filter animals you care about
    animals = detections[detections['name'].isin(['cow', 'sheep', 'horse', 'dog'])]

    herd_count = len(animals)

    for _, row in animals.iterrows():
        x1, y1, x2, y2 = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, row['name'], (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

    # Save processed image
    cv2.imwrite(output_path, frame)

    # Optional map alert
    map_path = os.path.join(OUTPUT_FOLDER, 'map.html')
    herd_map = folium.Map(location=[30.0, 70.0], zoom_start=6)
    folium.Marker([30.0, 70.0], tooltip=f'Herd detected: {herd_count}').add_to(herd_map)
    herd_map.save(map_path)

    return herd_count, output_path

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

            output_path = os.path.join(app.config['OUTPUT_FOLDER'], file.filename)
            herd_count, processed_file = detect_animals(file_path, output_path)

            return render_template('index.html', 
                                   herd_count=herd_count, 
                                   processed_file=processed_file)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)