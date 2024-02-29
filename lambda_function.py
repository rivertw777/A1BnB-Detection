import json
import boto3
import torch
import io
import os
import pylab
from PIL import Image, ImageDraw, ImageFont
import ultralytics
from ultralytics import YOLO

def lambda_handler(event, context):
    image_names = [path.split("photos/")[1] for path in event]

    s3 = boto3.client('s3')    
    bucket = 'a1bnb-project'
    
    # s3 폰트 다운로드
    s3.download_file(bucket, 'arial.ttf', '/tmp/arial.ttf')

    # s3 사진 다운로드
    for name in image_names:
        key = 'photos/' + name
        path = '/tmp/' + name
        s3.download_file(bucket, key, path)
        
    # 사진 가져오기
    directory = '/tmp/'
    infer_images = [Image.open(os.path.join(directory, image)) for image in image_names]

    # s3 pt 파일 다운로드
    key = 'model/detection.pt'
    path = '/tmp/detection.pt'
    s3.download_file(bucket, key, path)

    # 모델 추론
    model = YOLO('/tmp/detection.pt')
    inference_result = model(infer_images)
    torch.cuda.empty_cache()

    # detection 결과 커스텀
    image_names = event
    detection_result = custom_result(inference_result, image_names)
    
    # bbox 이미지 업로드
    draw_bbox(detection_result, image_names, infer_images)

    # 최종 결과 
    final_result = get_final_result(detection_result)
    return final_result
    
def custom_result(result, image_names):
    output = {}
    for idx, lst in enumerate(result):
        n = image_names[idx]
        output[n] = {}
        for item in lst:
            ite = json.loads(item.tojson())
            name = ite[0]["name"]
            bbox = [ite[0]["box"]["x1"], ite[0]["box"]["y1"], ite[0]["box"]["x2"], ite[0]["box"]["y2"], ite[0]["confidence"]]
            output[n][name] = bbox
    return output

def get_color(label):
    cm = pylab.get_cmap('gist_rainbow')
    color = cm(30) 
    return color

def draw_bbox(detection_result, image_names, infer_images): 
    for image_name, bbox in detection_result.items():
        img_idx = image_names.index(image_name)
        image = infer_images[img_idx]
        draw = ImageDraw.Draw(image)
        for label, bbox in bbox.items():
            x1, y1, x2, y2, _ = bbox
            color = get_color(label)
            color = (int(color[0] * 255), int(color[1] * 255), int(color[2] * 255))
            font = ImageFont.truetype('/tmp/arial.ttf', 20)
            label_text = f"{label}"
            # bbox draw
            draw.rectangle([x1, y1, x2, y2], outline = color, width = 4)
            # text background draw
            draw.rectangle([x1, y1-20, x1+font.getsize(label)[0], y1], outline = color,  fill = color,  width = 0)
            draw.text((x1, y1-20), label_text, font=font, fill=(255,255,255))
        
        # s3 업로드
        image_buffer = io.BytesIO()
        image.save(image_buffer,'JPEG')
        image_buffer.seek(0)
        s3 = boto3.client('s3')    
        bucket = 'a1bnb-project'
        upload_path = 'detected/' + image_name.split("photos/")[1]
        s3.upload_fileobj(image_buffer, bucket, upload_path)

def get_final_result(result):
    for image in result:
        for ammenity in result[image]:
            temp = result[image][ammenity][4]
            result[image][ammenity] = temp
    return result