# booruget: danbooru downloader


```
$ python booruget.py -h
usage: booruget [-h] -t TAG [-T TRIGGER_TAGS] [--include_tags INCLUDE_TAGS] [--exclude_tags EXCLUDE_TAGS] -o OUTPUT_DIRECTORY
                                                                                                                             
Download and resize images, and download tags from Danbooru for AI training                                                  

options:
  -h, --help            show this help message and exit
  -t TAG, --tag TAG     tags (maximum 2 tags)
  -T TRIGGER_TAGS, --trigger-tags TRIGGER_TAGS
                        trigger tags
  --include-tags INCLUDE_TAGS
                        only include images with all of these tags (can be repeated)
  --exclude-tags EXCLUDE_TAGS
                        exclude all images with any of these tags (can be repeated)
  -o OUTPUT_DIRECTORY, --output-directory OUTPUT_DIRECTORY
                        output directory
```

This tool grabs the metadata for all images, groups them by aspect ratio, 
downloads the images from the biggest bucket, 
and resizes them to the size of the smallest image in that bucket.

This tool works best with a bunch of images with the same aspect ratio, 
but you'll still need to do some manual reviewing afterwards.

## Example output

```shell
python booruget.py -t t1kosewad -t "shiroko (blue_archive)" -o out --include-tags 1girl --exclude-tags 1boy --exclude-tags uncensored -T t1shiroko
```

![](https://image.pieland.xyz/file/923baa815ddc1612579a0.png)

![](https://image.pieland.xyz/file/e2b1023ab7b82da2c8bcd.png)