import argparse
import multiprocessing
import os
import sys
import urllib.parse
from io import BytesIO

import requests
from PIL import Image as PImage


def split_tag_string(tag_string: str) -> list[str]:
    return [t.replace(' ', '_').replace('(', '\\(').replace(')', '\\)') for t in tag_string.split(' ')]


def convert_tags_to_url(tags: list[str], page: int) -> str:
    base_url = "https://danbooru.donmai.us/posts.json"
    formatted_tags = '+'.join([urllib.parse.quote(tag.replace(' ', '_')) for tag in tags])
    url = f"{base_url}?tags={formatted_tags}&page={page}"
    return url


class Image:
    def __init__(self, obj):
        self.file_url: str = obj['file_url']
        self.tags: list[str] = split_tag_string(obj['tag_string_general'])
        self.tags_character: list[str] = split_tag_string(obj['tag_string_character'])
        self.width: int = obj['image_width']
        self.height: int = obj['image_height']
        self.ratio = round(self.width / self.height, 2)

    def download_image(self) -> PImage:
        response = requests.get(self.file_url)
        return PImage.open(BytesIO(response.content))


def download(im: Image, args, min_width: int, min_height: int):
    local_path = os.path.join(os.getcwd(), args.output_directory, os.path.basename(im.file_url))
    save_path = os.path.splitext(local_path)[0] + '.png'
    txt_path = os.path.splitext(local_path)[0] + '.txt'

    if args.verbose:
        print(f"downloading {im.file_url} to {save_path}", file=sys.stderr)

    with open(save_path, 'wb') as f:
        if not args.no_resize:
            im.download_image().resize((min_width, min_height)).save(f, format="png")
        else:
            im.download_image().save(f, format="png")
    with open(txt_path, 'w') as f:
        print(', '.join(args.trigger_tags + im.tags_character + im.tags), file=f)


def main():
    parser = argparse.ArgumentParser(prog='booruget', description='Download and resize images, and download tags from Danbooru for AI training')
    parser.add_argument('-t', '--tag', required=True, action='append', help='tags (maximum 2 tags)')
    parser.add_argument('-T', '--trigger-tags', required=False, default=[], action='append', help='trigger tags')
    parser.add_argument('--include-tags', required=False, default=[], action='append', help='only include images with all of these tags (can be repeated)')
    parser.add_argument('--exclude-tags', required=False, default=[], action='append', help='exclude all images with any of these tags (can be repeated)')
    parser.add_argument('-o', '--output-directory', required=True, help='output directory')
    parser.add_argument('-j', '--jobs', type=int, default=multiprocessing.cpu_count(), help='number of parallel download threads')
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose mode')
    parser.add_argument('--no-resize', action='store_true', help='disable image resizing')

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

    if args.verbose:
        print(f"parsed metadata for {len(images)} images", file=sys.stderr)

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

    if args.verbose:
        print(f"using {len(bucket_images)} images with ratio {ratio[0]}", file=sys.stderr)

    min_image: Image = min(bucket_images, key=lambda im: im.width * im.height)
    min_width: int = min_image.width
    min_height: int = min_image.height

    if args.verbose:
        print(f"resizing to {min_width}x{min_height}", file=sys.stderr)

    with multiprocessing.Pool(processes=args.jobs) as pool:
        pool.starmap(download, [(im, args, min_width, min_height) for im in bucket_images])


if __name__ == '__main__':
    main()
