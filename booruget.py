import argparse
import os
import urllib.parse
from io import BytesIO

import requests
from PIL import Image as PImage


def split(tag_string: str) -> list[str]:
    return [t.replace(' ', '_').replace('(', '\\(').replace(')', '\\)') for t in tag_string.split(' ')]


def convert_tags_to_url(tags: list[str], page: int) -> str:
    base_url = "https://danbooru.donmai.us/posts.json"
    formatted_tags = '+'.join([urllib.parse.quote(tag.replace(' ', '_')) for tag in tags])
    url = f"{base_url}?tags={formatted_tags}&page={page}"
    return url


class Image:
    def __init__(self, obj):
        self.file_url: str = obj['file_url']
        self.tags: list[str] = split(obj['tag_string_general'])
        self.tags_character: list[str] = split(obj['tag_string_character'])
        self.width: int = obj['image_width']
        self.height: int = obj['image_height']
        self.ratio = round(self.width / self.height, 2)

    def download_image(self) -> PImage:
        response = requests.get(self.file_url)
        return PImage.open(BytesIO(response.content))


def main():
    parser = argparse.ArgumentParser(prog='booruget', description='Download and resize images, and download tags from Danbooru for AI training')
    parser.add_argument('-t', '--tag', required=True, action='append', help='tags (maximum 2 tags)')
    parser.add_argument('-T', '--trigger-tags', required=False, default=[], action='append', help='trigger tags')
    parser.add_argument('--include-tags', required=False, default=[], action='append', help='only include images with all of these tags (can be repeated)')
    parser.add_argument('--exclude-tags', required=False, default=[], action='append', help='exclude all images with any of these tags (can be repeated)')
    parser.add_argument('-o', '--output-directory', required=True, help='output directory')
    args = parser.parse_args()

    if len(args.tag) > 2:
        raise Exception('Maximum 2 tags allowed')

    if len(args.tag) == 0:
        raise Exception('At least one tag required')

    os.makedirs(args.output_directory, exist_ok=True)

    images: list[Image] = []
    page: int = 1

    while True:
        url = convert_tags_to_url(args.tag, page)
        response = requests.get(url)
        json_response = response.json()
        if len(json_response) == 0:
            break
        page += 1
        [images.append(Image(obj)) for obj in json_response]

    resolution_buckets: [float, list[Image]] = {}

    for image in images:
        if len(args.include_tags) > 0 and not any(tag in args.include_tags for tag in image.tags):
            continue
        if len(args.exclude_tags) > 0 and any(tag in args.exclude_tags for tag in image.tags):
            continue
        if image.ratio not in resolution_buckets:
            resolution_buckets[image.ratio] = []
        resolution_buckets[image.ratio].append(image)

    ratio: tuple[float, list[Image]] = max(resolution_buckets.items(), key=lambda item: len(item[1]))
    bucket_images: list[Image] = resolution_buckets[ratio[0]]

    min_image: Image = min(bucket_images, key=lambda im: im.width * im.height)
    min_width: int = min_image.width
    min_height: int = min_image.height

    for image in bucket_images:
        local_path = os.path.join(os.getcwd(), args.output_directory, os.path.basename(image.file_url))
        save_path = os.path.splitext(local_path)[0] + '.png'
        txt_path = os.path.splitext(local_path)[0] + '.txt'

        with open(save_path, 'wb') as f:
            image.download_image().resize((min_width, min_height)).save(f, format="png")
        with open(txt_path, 'w') as f:
            print(', '.join(args.trigger_tags + image.tags_character + image.tags), file=f)


if __name__ == '__main__':
    main()
