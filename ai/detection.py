from ultralytics import YOLO

model = YOLO("yolo11n.pt")

results = model("https://ultralytics.com/images/bus.jpg")

for result in results:
    result.save(filename="yolo_result.jpg")

print("YOLO detection completed!")
print("Result saved as yolo_result.jpg")
